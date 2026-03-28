"""Google Sheets integration."""

from __future__ import annotations

import base64
import json
from typing import Any

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from registration_bot.config import Settings


SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

USER_COLUMNS = [
    "SURNAME",
    "OTHER NAMES",
    "DATE OF BIRTH",
    "GENDER",
    "REGISTRATION NUMBER",
    "COLLEGE",
    "PROGRAM",
    "LEVEL",
    "SUBUNIT",
    "HALL & ROOM NUMBER",
    "TELEGRAM USER ID",
    "TELEGRAM NUMBER",
]

HEADER_ROW = USER_COLUMNS[:]


class GoogleSheetsService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = gspread.authorize(self._load_credentials())
        self.spreadsheet = self.client.open_by_key(settings.spreadsheet_key)
        self.links_sheet = self._get_or_create_links_sheet()

    def _load_credentials(self) -> ServiceAccountCredentials:
        if self.settings.google_credentials_b64:
            try:
                decoded = base64.b64decode(self.settings.google_credentials_b64).decode("utf-8")
                creds_json = json.loads(decoded)
                return ServiceAccountCredentials.from_json_keyfile_dict(creds_json, SCOPE)
            except Exception as exc:
                print(f"Error loading service account from environment variable: {exc}")

        if not self.settings.service_account_file.exists():
            raise FileNotFoundError(
                f"Service account file not found: {self.settings.service_account_file}"
            )

        return ServiceAccountCredentials.from_json_keyfile_name(
            str(self.settings.service_account_file),
            SCOPE,
        )

    def _get_or_create_links_sheet(self):
        try:
            return self.spreadsheet.worksheet("Links")
        except gspread.exceptions.WorksheetNotFound:
            links_sheet = self.spreadsheet.add_worksheet(title="Links", rows="100", cols="3")
            links_sheet.update("A1:C1", [["Type", "Name", "Link"]])
            return links_sheet

    def _semester_sheets(self):
        return [
            worksheet
            for worksheet in self.spreadsheet.worksheets()
            if worksheet.title.startswith(("Alpha_", "Omega_"))
        ]

    def get_or_create_sheet(self, sheet_name: str):
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")
            worksheet.append_row(HEADER_ROW)
            return worksheet

    def add_user(self, user_data: dict[str, Any]) -> None:
        year = str(self._current_year())
        semester = user_data.get("SEMESTER") or user_data.get("semester")
        values = [user_data.get(column, "") for column in USER_COLUMNS]

        if semester == "Both":
            self.get_or_create_sheet(f"Alpha_{year}").append_row(values)
            self.get_or_create_sheet(f"Omega_{year}").append_row(values)
        elif semester == "Omega":
            self.get_or_create_sheet(f"Omega_{year}").append_row(values)
        else:
            self.get_or_create_sheet(f"Alpha_{year}").append_row(values)

    def get_all_unique_users(self) -> list[dict[str, Any]]:
        all_users = []
        seen_ids = set()
        for worksheet in self._semester_sheets():
            for record in worksheet.get_all_records():
                raw_telegram_id = record.get("TELEGRAM USER ID")
                telegram_id = str(raw_telegram_id).strip()
                if raw_telegram_id and telegram_id and telegram_id != "None" and telegram_id not in seen_ids:
                    all_users.append(record)
                    seen_ids.add(telegram_id)
        return all_users

    def get_user_by_telegram_id(
        self,
        telegram_id: str,
        semester: str | None = None,
        year: int | str | None = None,
    ) -> dict[str, Any] | None:
        if semester and year:
            try:
                target_sheet = self.spreadsheet.worksheet(f"{semester}_{year}")
            except gspread.exceptions.WorksheetNotFound:
                return None
            for user in target_sheet.get_all_records():
                if str(user.get("TELEGRAM USER ID")).strip() == str(telegram_id).strip():
                    return user
            return None

        for worksheet in self._semester_sheets():
            for user in worksheet.get_all_records():
                if str(user.get("TELEGRAM USER ID")).strip() == str(telegram_id).strip():
                    return user
        return None

    def get_all_telegram_ids(self) -> list[str]:
        return [str(user["TELEGRAM USER ID"]) for user in self.get_all_unique_users()]

    def set_group_chat_link(self, group_type: str, link: str) -> None:
        if group_type == "General":
            self.set_link("General", "", link)
            return
        self.set_link("Subunit", group_type, link)

    def set_link(self, link_type: str, name: str, link: str) -> None:
        records = self.links_sheet.get_all_records()
        for index, record in enumerate(records, start=2):
            if record["Type"] == link_type and record["Name"] == name:
                self.links_sheet.update_cell(index, 3, link)
                return
        self.links_sheet.append_row([link_type, name, link])

    def get_group_chat_link(self, subunit: str | None = None) -> str | None:
        records = self.links_sheet.get_all_records()
        if subunit is None:
            for record in records:
                if record["Type"] == "General":
                    return record.get("Link")
            return None

        for record in records:
            if record["Type"] == "Subunit" and record.get("Name") == subunit:
                return record.get("Link")
        return None

    def get_all_users(self) -> list[dict[str, Any]]:
        return self.get_all_unique_users()

    @staticmethod
    def _current_year() -> int:
        from datetime import datetime

        return datetime.now().year
