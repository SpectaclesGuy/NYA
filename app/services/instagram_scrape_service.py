from __future__ import annotations

import glob
import os
from datetime import datetime
from random import randint
from time import sleep

from fastapi import HTTPException
from pydantic import BaseModel


class InstagramScrapeResult(BaseModel):
    target_username: str
    output_filename: str
    videos_processed: int
    skipped_posts: int
    started_at: str
    completed_at: str
    recipient_email: str | None = None
    email_sent: bool = False


def _first_mp4(path: str) -> str | None:
    files = glob.glob(os.path.join(path, "*.mp4"))
    if files:
        return files[0]
    return None


def scrape_instagram_videos(config: dict, ig_username: str, ig_password: str) -> InstagramScrapeResult:
    try:
        import instaloader
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="instaloader is not installed") from exc

    try:
        import whisper
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="openai-whisper is not installed") from exc

    target_username = config["target_username"]
    start_at_post_index = int(config["start_at_post_index"])
    max_videos_to_process = int(config["max_videos_to_process"])
    download_folder = str(config["download_folder"]).strip() or "instagram_downloads"
    output_filename = str(config["output_filename"]).strip() or "combined_transcripts.txt"
    delete_after_transcription = bool(config["delete_after_transcription"])
    whisper_model = str(config["whisper_model"]).strip() or "base"

    os.makedirs(download_folder, exist_ok=True)

    if not os.path.exists(output_filename):
        with open(output_filename, "w", encoding="utf-8") as handle:
            handle.write(f"--- TRANSCRIPTS FOR: {target_username} ---\n\n")

    loader = instaloader.Instaloader(
        dirname_pattern=download_folder,
        download_pictures=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        max_connection_attempts=5,
        request_timeout=30,
    )

    if ig_username and ig_password:
        loader.login(ig_username, ig_password)

    model = whisper.load_model(whisper_model)
    started_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    try:
        profile = instaloader.Profile.from_username(loader.context, target_username)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to load Instagram profile: {exc}") from exc

    current_post_index = 0
    videos_processed = 0

    for post in profile.get_posts():
        if current_post_index < start_at_post_index:
            current_post_index += 1
            sleep(randint(3, 6))
            continue

        if videos_processed >= max_videos_to_process:
            break

        if post.is_video:
            try:
                loader.download_post(post, target=download_folder)
            except Exception:
                sleep(10)
                current_post_index += 1
                continue

            video_path = _first_mp4(download_folder)
            if video_path:
                try:
                    result = model.transcribe(video_path)
                    transcript = result.get("text", "").strip()
                    with open(output_filename, "a", encoding="utf-8") as handle:
                        handle.write("=" * 50 + "\n")
                        handle.write(f"Index: {current_post_index} | Date: {post.date_local}\n")
                        handle.write(f"URL: https://www.instagram.com/p/{post.shortcode}/\n")
                        handle.write("-" * 20 + "\n")
                        handle.write(f"{transcript}\n")
                        handle.write("=" * 50 + "\n\n")
                    videos_processed += 1
                except Exception:
                    pass

            if delete_after_transcription:
                for file_path in glob.glob(os.path.join(download_folder, "*")):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass

            sleep(randint(15, 30))
        else:
            sleep(randint(2, 5))

        current_post_index += 1

    return InstagramScrapeResult(
        target_username=target_username,
        output_filename=output_filename,
        videos_processed=videos_processed,
        skipped_posts=start_at_post_index,
        started_at=started_at,
        completed_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
    )
