"""Google Sheets integration."""

from __future__ import annotations

import base64
import json
from datetime import datetime
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
    "ARE YOU A NEW MEM",
    "TELEGRAM USER ID",
    "TELEGRAM NUMBER",
]

HEADER_ROW = USER_COLUMNS[:]
FORM_RESPONSE_SHEET_CANDIDATES = ("Form Responses 1", "Form Response 1")


class GoogleSheetsService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = gspread.authorize(self._load_credentials())
        self.spreadsheet = self.client.open_by_key(settings.spreadsheet_key)
        self.registration_sheet = self._get_or_create_registration_sheet()
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

    def _registration_sheets(self):
        sheets = []
        for title in FORM_RESPONSE_SHEET_CANDIDATES:
            try:
                sheets.append(self.spreadsheet.worksheet(title))
            except gspread.exceptions.WorksheetNotFound:
                continue
        return sheets

    def _get_or_create_registration_sheet(self):
        for title in FORM_RESPONSE_SHEET_CANDIDATES:
            try:
                return self.spreadsheet.worksheet(title)
            except gspread.exceptions.WorksheetNotFound:
                continue

        worksheet = self.spreadsheet.add_worksheet(
            title=FORM_RESPONSE_SHEET_CANDIDATES[0],
            rows="100",
            cols="20",
        )
        worksheet.append_row(HEADER_ROW)
        return worksheet

    def _all_user_data_sheets(self):
        unique_by_title = {}
        for worksheet in self._registration_sheets():
            unique_by_title[worksheet.title] = worksheet
        return list(unique_by_title.values())

    def get_or_create_sheet(self, sheet_name: str):
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20")
            worksheet.append_row(HEADER_ROW)
            return worksheet

    def add_user(self, user_data: dict[str, Any]) -> None:
        headers = self.registration_sheet.row_values(1)
        if not headers:
            self.registration_sheet.append_row(HEADER_ROW)
            headers = HEADER_ROW[:]

        values = self._build_row_for_headers(headers, user_data)
        self.registration_sheet.append_row(values)

    def get_all_unique_users(self) -> list[dict[str, Any]]:
        all_users = []
        seen_ids = set()
        for worksheet in self._all_user_data_sheets():
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
            for worksheet in self._registration_sheets():
                for user in worksheet.get_all_records():
                    if str(user.get("TELEGRAM USER ID")).strip() != str(telegram_id).strip():
                        continue
                    if self._record_matches_semester_and_year(user, semester, year):
                        return user
            return None

        for worksheet in self._all_user_data_sheets():
            for user in worksheet.get_all_records():
                if str(user.get("TELEGRAM USER ID")).strip() == str(telegram_id).strip():
                    return user
        return None

    def get_user_by_registration_number(self, registration_number: str) -> dict[str, Any] | None:
        target_registration_number = self._normalize_lookup_value(registration_number)
        if not target_registration_number:
            return None

        for worksheet in self._all_user_data_sheets():
            for user in worksheet.get_all_records():
                if (
                    self._normalize_lookup_value(user.get("REGISTRATION NUMBER"))
                    == target_registration_number
                ):
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
        return datetime.now().year

    @staticmethod
    def _normalize_lookup_value(value: Any) -> str:
        if value is None:
            return ""
        return " ".join(str(value).strip().upper().split())

    @classmethod
    def _normalize_header_key(cls, value: Any) -> str:
        normalized = cls._normalize_lookup_value(value)
        return "".join(char for char in normalized if char.isalnum())

    @staticmethod
    def _split_hall_and_room(hall_room: Any) -> tuple[str, str]:
        text = str(hall_room or "").strip()
        if not text:
            return "", ""
        parts = text.split(maxsplit=1)
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], parts[1]

    def _build_row_for_headers(self, headers: list[str], user_data: dict[str, Any]) -> list[Any]:
        normalized_user_data = {
            self._normalize_header_key(key): value for key, value in user_data.items()
        }
        hall_room = user_data.get("HALL & ROOM NUMBER", "")
        hall, room = self._split_hall_and_room(hall_room)
        timestamp_value = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        year_value = str(self._current_year())

        values = []
        for header in headers:
            normalized_header = self._normalize_header_key(header)
            if normalized_header == "TIMESTAMP":
                values.append(timestamp_value)
            elif normalized_header in ("HALLROOMNUMBER", "HALLANDROOMNUMBER"):
                values.append(hall_room)
            elif normalized_header == "HALL":
                values.append(hall)
            elif normalized_header == "ROOMNUMBER":
                values.append(room)
            elif normalized_header == "YEAR":
                values.append(year_value)
            elif normalized_header in normalized_user_data:
                values.append(normalized_user_data[normalized_header])
            else:
                values.append("")
        return values

    def _record_matches_semester_and_year(
        self,
        record: dict[str, Any],
        semester: str,
        year: int | str,
    ) -> bool:
        target_semester = self._normalize_lookup_value(semester)
        record_semester = self._normalize_lookup_value(
            record.get("SEMESTER") or record.get("Semester")
        )
        if not record_semester:
            return False
        if record_semester != target_semester and not (
            record_semester == "BOTH" and target_semester in {"ALPHA", "OMEGA"}
        ):
            return False

        target_year = str(year).strip()
        record_year = self._extract_record_year(record)
        return bool(record_year and str(record_year).strip() == target_year)

    def _extract_record_year(self, record: dict[str, Any]) -> str | None:
        year_value = record.get("YEAR") or record.get("Year")
        if year_value:
            return str(year_value).strip()

        timestamp = record.get("TIMESTAMP") or record.get("Timestamp")
        if not timestamp:
            return None

        for date_format in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                return str(datetime.strptime(str(timestamp), date_format).year)
            except ValueError:
                continue
        return None
