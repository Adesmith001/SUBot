"""Admin role management."""

from __future__ import annotations

import json
from pathlib import Path

from registration_bot.config import BASE_DIR, Settings


class AdminService:
    def __init__(self, settings: Settings, storage_path: Path | None = None):
        self.settings = settings
        self.storage_path = storage_path or (BASE_DIR / "admins.json")
        self.admins: set[str] = set()
        self.super_admins: set[str] = {settings.super_admin_id}
        self._load()

    def _load(self) -> None:
        if not self.storage_path.exists():
            self._save()
            return

        with self.storage_path.open(encoding="utf-8") as admins_file:
            raw_data = json.load(admins_file)

        self.admins = {str(user_id) for user_id in raw_data.get("admins", [])}
        self.super_admins = {
            str(user_id) for user_id in raw_data.get("super_admins", [self.settings.super_admin_id])
        }
        self.super_admins.add(self.settings.super_admin_id)

    def _save(self) -> None:
        payload = {
            "admins": sorted(self.admins),
            "super_admins": sorted(self.super_admins),
        }
        with self.storage_path.open("w", encoding="utf-8") as admins_file:
            json.dump(payload, admins_file, indent=2)

    def is_super_admin(self, user_id: str) -> bool:
        return str(user_id) in self.super_admins

    def is_admin(self, user_id: str) -> bool:
        user_id = str(user_id)
        return user_id in self.admins or user_id in self.super_admins

    def add_admin(self, user_id: str) -> bool:
        user_id = str(user_id)
        if user_id in self.admins:
            return False
        self.admins.add(user_id)
        self._save()
        return True

    def remove_admin(self, user_id: str) -> bool:
        user_id = str(user_id)
        if user_id not in self.admins:
            return False
        self.admins.remove(user_id)
        self._save()
        return True

    def add_super_admin(self, user_id: str) -> bool:
        user_id = str(user_id)
        if user_id in self.super_admins:
            return False
        self.super_admins.add(user_id)
        self._save()
        return True

    def remove_super_admin(self, user_id: str) -> bool:
        user_id = str(user_id)
        if user_id == self.settings.super_admin_id or user_id not in self.super_admins:
            return False
        self.super_admins.remove(user_id)
        self._save()
        return True

    def get_admins(self) -> list[str]:
        return sorted(self.admins)

    def get_super_admins(self) -> list[str]:
        return sorted(self.super_admins)

