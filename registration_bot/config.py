"""Application configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config.json"
DEFAULT_SERVICE_ACCOUNT_PATH = BASE_DIR / "service_account.json"


@dataclass(frozen=True)
class Settings:
    bot_token: str
    spreadsheet_key: str
    super_admin_id: str
    webhook_url: str | None
    port: int
    service_account_file: Path
    google_credentials_b64: str | None


def _load_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as config_file:
        return json.load(config_file)


def _normalize_webhook_url(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().rstrip("/")
    return normalized or None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    config_path = Path(os.environ.get("BOT_CONFIG_PATH", DEFAULT_CONFIG_PATH))
    config = _load_json_file(config_path)

    bot_token = os.environ.get("BOT_TOKEN") or config.get("BOT_TOKEN")
    spreadsheet_key = os.environ.get("SPREADSHEET_KEY") or config.get("SPREADSHEET_KEY")
    super_admin_id = os.environ.get("SUPER_ADMIN_ID") or config.get("SUPER_ADMIN_ID")

    if not bot_token:
        raise ValueError("BOT_TOKEN not found in environment variables or config file.")
    if not spreadsheet_key:
        raise ValueError("SPREADSHEET_KEY not found in environment variables or config file.")
    if not super_admin_id:
        raise ValueError("SUPER_ADMIN_ID not found in environment variables or config file.")

    webhook_url = _normalize_webhook_url(
        os.environ.get("WEBHOOK_URL") or config.get("WEBHOOK_URL")
    )
    port = int(os.environ.get("PORT", config.get("PORT", 8000)))
    service_account_file = Path(
        os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", DEFAULT_SERVICE_ACCOUNT_PATH)
    )

    return Settings(
        bot_token=bot_token,
        spreadsheet_key=spreadsheet_key,
        super_admin_id=str(super_admin_id),
        webhook_url=webhook_url,
        port=port,
        service_account_file=service_account_file,
        google_credentials_b64=os.environ.get("GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_B64"),
    )

