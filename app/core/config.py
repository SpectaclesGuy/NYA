from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NYA_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        validation_alias=AliasChoices("NYA_MONGODB_URI", "MONGODB_URI"),
    )
    mongodb_db: str = Field(
        default="nya",
        validation_alias=AliasChoices("NYA_MONGODB_DB", "MONGODB_DB"),
    )

    jwt_secret: str = Field(
        default="change-me",
        validation_alias=AliasChoices("NYA_JWT_SECRET", "JWT_SECRET_KEY"),
    )
    jwt_algorithm: str = Field(
        default="HS256",
        validation_alias=AliasChoices("NYA_JWT_ALGORITHM", "JWT_ALGORITHM"),
    )
    jwt_access_minutes: int = Field(
        default=15,
        validation_alias=AliasChoices("NYA_JWT_ACCESS_MINUTES", "JWT_EXPIRES_MINUTES"),
    )
    jwt_refresh_days: int = Field(
        default=30,
        validation_alias=AliasChoices("NYA_JWT_REFRESH_DAYS", "JWT_REFRESH_DAYS"),
    )

    google_client_id: str = Field(
        default="",
        validation_alias=AliasChoices("NYA_GOOGLE_CLIENT_ID", "OAUTH_CLIENT_ID"),
    )
    google_client_secret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("NYA_GOOGLE_CLIENT_SECRET", "OAUTH_CLIENT_SECRET"),
    )
    oauth_redirect_uri: str | None = Field(
        default=None,
        validation_alias=AliasChoices("NYA_OAUTH_REDIRECT_URI", "OAUTH_REDIRECT_URI"),
    )

    cookie_domain: str | None = Field(
        default=None,
        validation_alias=AliasChoices("NYA_COOKIE_DOMAIN", "SESSION_COOKIE_DOMAIN"),
    )
    cookie_secure: bool = Field(
        default=True,
        validation_alias=AliasChoices("NYA_COOKIE_SECURE", "SESSION_COOKIE_SECURE"),
    )
    cookie_samesite: str = Field(
        default="lax",
        validation_alias=AliasChoices("NYA_COOKIE_SAMESITE", "SESSION_COOKIE_SAMESITE"),
    )
    session_cookie_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("NYA_SESSION_COOKIE_NAME", "SESSION_COOKIE_NAME"),
    )

    frontend_origin: str = Field(
        default="",
        validation_alias=AliasChoices("NYA_FRONTEND_ORIGIN", "FRONTEND_ORIGIN"),
    )
    dev_login_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("NYA_DEV_LOGIN_ENABLED", "DEV_LOGIN_ENABLED"),
    )
    allow_all_domains: bool = Field(
        default=False,
        validation_alias=AliasChoices("NYA_ALLOW_ALL_DOMAINS", "ALLOW_ALL_DOMAINS"),
    )
    admin_emails: str = Field(
        default="",
        validation_alias=AliasChoices("NYA_ADMIN_EMAILS", "ADMIN_EMAILS"),
    )

    smtp_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("NYA_SMTP_ENABLED", "SMTP_ENABLED"),
    )
    smtp_host: str = Field(
        default="smtp.gmail.com",
        validation_alias=AliasChoices("NYA_SMTP_HOST", "SMTP_HOST"),
    )
    smtp_port: int = Field(
        default=465,
        validation_alias=AliasChoices("NYA_SMTP_PORT", "SMTP_PORT"),
    )
    smtp_user: str = Field(
        default="",
        validation_alias=AliasChoices("NYA_SMTP_USER", "SMTP_USER"),
    )
    smtp_password: str = Field(
        default="",
        validation_alias=AliasChoices("NYA_SMTP_PASSWORD", "SMTP_PASSWORD"),
    )
    smtp_from: str | None = Field(
        default=None,
        validation_alias=AliasChoices("NYA_SMTP_FROM", "SMTP_FROM"),
    )
    smtp_use_starttls: bool = Field(
        default=False,
        validation_alias=AliasChoices("NYA_SMTP_USE_STARTTLS", "SMTP_USE_STARTTLS"),
    )

    @property
    def admin_email_list(self) -> list[str]:
        if not self.admin_emails:
            return []
        return [email.strip().lower() for email in self.admin_emails.split(",") if email.strip()]


settings = Settings()
