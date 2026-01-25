import argparse
import json
import os
from datetime import datetime
from typing import Any, Iterable

import requests

API_URL = "https://api.unstop.com/api/public/opportunity/search"
SOURCE_URL = "https://unstop.com/hackathons?oppstatus=open"


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def format_date(value: str | None) -> str | None:
    parsed = parse_iso(value)
    if not parsed:
        return None
    # Windows strftime does not support %-d.
    return parsed.strftime("%b %d, %Y").replace(" 0", " ")


def format_window(start: str | None, end: str | None) -> str | None:
    start_label = format_date(start)
    end_label = format_date(end)
    if start_label and end_label:
        if start_label == end_label:
            return start_label
        return f"{start_label} - {end_label}"
    return start_label or end_label


def format_team_size(regn: dict[str, Any] | None) -> str:
    if not regn:
        return "Varies"
    min_team = regn.get("min_team_size")
    max_team = regn.get("max_team_size")
    if min_team and max_team:
        if min_team == max_team == 1:
            return "Solo"
        return f"{min_team} - {max_team}"
    if min_team == 1:
        return "Solo"
    return "Varies"


def pick_tags(filters: Iterable[dict[str, Any]] | None, fallback: str | None) -> list[str]:
    tags: list[str] = []
    if filters:
        for entry in filters:
            name = entry.get("name")
            if not name or name.lower() == "all":
                continue
            if name not in tags:
                tags.append(name)
            if len(tags) >= 3:
                break
    if not tags and fallback:
        tags.append(fallback.replace("_", " ").title())
    return tags


def build_item(opportunity: dict[str, Any]) -> dict[str, Any]:
    organisation = opportunity.get("organisation") or {}
    regn = opportunity.get("regnRequirements") or {}
    location = opportunity.get("location")
    region = opportunity.get("region")
    if not location:
        location = "Remote" if region == "online" else "Location TBA"

    url = opportunity.get("seo_url") or opportunity.get("public_url") or ""
    if url and not url.startswith("http"):
        url = f"https://unstop.com/{url.lstrip('/')}"

    return {
        "title": opportunity.get("title") or "Untitled Hackathon",
        "organizer": organisation.get("name") or "Unstop",
        "mode": (region or "online").title(),
        "location": location,
        "prize": opportunity.get("overall_prizes") or "Details on Unstop",
        "deadline": format_date(regn.get("end_regn_dt")),
        "window": format_window(opportunity.get("start_date"), opportunity.get("end_date")),
        "teamSize": format_team_size(regn),
        "tags": pick_tags(opportunity.get("filters"), opportunity.get("subtype")),
        "logo": opportunity.get("logoUrl2") or opportunity.get("logoUrl"),
        "url": url,
    }


def fetch_page(page: int, per_page: int, insecure: bool) -> dict[str, Any]:
    params = {
        "opportunity_type": "hackathons",
        "oppstatus": "open",
        "per_page": per_page,
        "page": page,
    }
    response = requests.get(
        API_URL,
        params=params,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
        verify=not insecure,
    )
    response.raise_for_status()
    return response.json()


def scrape(limit: int, per_page: int, insecure: bool) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    page = 1
    max_pages = 100
    while len(collected) < limit and page <= max_pages:
        payload = fetch_page(page, per_page, insecure)
        data = payload.get("data", {}).get("data", [])
        if not data:
            break
        for entry in data:
            if entry.get("type") != "hackathons":
                continue
            collected.append(build_item(entry))
            if len(collected) >= limit:
                break
        page += 1
    return collected


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape top open hackathons from Unstop.")
    parser.add_argument("--limit", type=int, default=50, help="Number of hackathons to collect.")
    parser.add_argument("--per-page", type=int, default=50, help="Requested page size for the API.")
    parser.add_argument(
        "--out",
        default=os.path.join("Pages", "data", "hackathons.json"),
        help="Output JSON path.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification if needed.",
    )
    args = parser.parse_args()

    items = scrape(args.limit, args.per_page, args.insecure)
    payload = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source_url": SOURCE_URL,
        "items": items,
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)

    print(f"Wrote {len(items)} hackathons to {args.out}")


if __name__ == "__main__":
    main()
