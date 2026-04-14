"""Scheduled bot jobs."""

from __future__ import annotations

from datetime import datetime
from typing import Callable
try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - fallback for older Python versions
    ZoneInfo = None

from apscheduler.schedulers.background import BackgroundScheduler

from registration_bot.services.google_sheets import GoogleSheetsService


SendMessageFunc = Callable[[str, str], None]


class SchedulerService:
    def __init__(self, sheets_service: GoogleSheetsService):
        self.sheets_service = sheets_service
        timezone = ZoneInfo("Africa/Lagos") if ZoneInfo else None
        self.scheduler = BackgroundScheduler(timezone=timezone) if timezone else BackgroundScheduler()
        self.reminders: list[dict[str, object]] = []
        self.send_message_func: SendMessageFunc | None = None
        self.started = False

    def set_send_message_func(self, func: SendMessageFunc) -> None:
        self.send_message_func = func

    def check_birthdays(self) -> None:
        today = datetime.now().strftime("%m-%d")
        for user in self.sheets_service.get_all_users():
            dob = user.get("DATE OF BIRTH", "")
            if dob and dob[:5] == today and self.send_message_func:
                self.send_message_func(
                    str(user["TELEGRAM USER ID"]),
                    f"Happy Birthday, {user['OTHER NAMES']}!",
                )

    def _broadcast_to_user_ids(self, user_ids: list[str], message: str) -> None:
        if not self.send_message_func:
            return
        for user_id in user_ids:
            self.send_message_func(str(user_id), message)

    def _broadcast_to_all_users(self, message: str) -> None:
        self._broadcast_to_user_ids(self.sheets_service.get_all_telegram_ids(), message)

    def _broadcast_to_colleges(self, colleges: list[str], message: str) -> None:
        user_ids = self.sheets_service.get_telegram_ids_by_colleges(colleges)
        self._broadcast_to_user_ids(user_ids, message)

    def send_coe_clds_preservice_reminder(self) -> None:
        self._broadcast_to_colleges(
            ["COE", "CLDS"],
            (
                "Reminder for COE/CLDS: Pre-service holds at Joy Gallery today from "
                "7:00am to 7:25am. Please be punctual."
            ),
        )

    def send_cmss_cst_preservice_reminder(self) -> None:
        self._broadcast_to_colleges(
            ["CMSS", "CST"],
            (
                "Reminder for CMSS/CST: Pre-service holds at Joy Gallery today from "
                "7:00am to 7:25am. Please be punctual."
            ),
        )

    def send_prayer_meeting_reminder(self) -> None:
        self._broadcast_to_all_users(
            "Reminder: Prayer meeting is today by 6:00pm at the back of the shuttle stand."
        )

    def send_monday_cleaning_reminder(self) -> None:
        self._broadcast_to_all_users(
            "Reminder: Cleaning is today by 6:30pm."
        )

    def send_bible_study_and_cleaning_reminder(self) -> None:
        self._broadcast_to_all_users(
            (
                "Reminder: Bible Study is by 2:00pm opposite Peace entrance, "
                "and cleaning follows by 3:00pm."
            )
        )

    def send_reminders(self) -> None:
        now = datetime.now()
        now_date = now.strftime("%Y-%m-%d")
        now_hour = now.hour
        now_minute = now.minute

        for reminder in list(self.reminders):
            if (
                reminder["date"] == now_date
                and reminder["hour"] == now_hour
                and reminder["minute"] == now_minute
            ):
                if self.send_message_func:
                    for user_id in reminder["user_ids"]:
                        self.send_message_func(str(user_id), str(reminder["message"]))
                self.reminders.remove(reminder)

    def add_reminder(
        self,
        date: str,
        hour: int,
        minute: int,
        message: str,
        user_ids: list[str],
    ) -> None:
        self.reminders.append(
            {
                "date": date,
                "hour": hour,
                "minute": minute,
                "message": message,
                "user_ids": user_ids,
            }
        )

    def start(self) -> None:
        if self.started:
            return
        self.scheduler.add_job(self.check_birthdays, "cron", hour=7, minute=0)

        # Monday 5pm and Tuesday 4am reminders for COE/CLDS.
        self.scheduler.add_job(
            self.send_coe_clds_preservice_reminder,
            "cron",
            day_of_week="mon",
            hour=17,
            minute=0,
        )
        self.scheduler.add_job(
            self.send_coe_clds_preservice_reminder,
            "cron",
            day_of_week="tue",
            hour=4,
            minute=0,
        )

        # Wednesday 5pm and Thursday 4am reminders for CMSS/CST.
        self.scheduler.add_job(
            self.send_cmss_cst_preservice_reminder,
            "cron",
            day_of_week="wed",
            hour=17,
            minute=0,
        )
        self.scheduler.add_job(
            self.send_cmss_cst_preservice_reminder,
            "cron",
            day_of_week="thu",
            hour=4,
            minute=0,
        )

        # Thursday 2pm reminder for prayer meeting by 6pm.
        self.scheduler.add_job(
            self.send_prayer_meeting_reminder,
            "cron",
            day_of_week="thu",
            hour=14,
            minute=0,
        )

        # Monday 2pm reminder for cleaning by 6:30pm.
        self.scheduler.add_job(
            self.send_monday_cleaning_reminder,
            "cron",
            day_of_week="mon",
            hour=14,
            minute=0,
        )

        # Friday 7pm and Saturday 10am reminders for Bible Study and cleaning.
        self.scheduler.add_job(
            self.send_bible_study_and_cleaning_reminder,
            "cron",
            day_of_week="fri",
            hour=19,
            minute=0,
        )
        self.scheduler.add_job(
            self.send_bible_study_and_cleaning_reminder,
            "cron",
            day_of_week="sat",
            hour=10,
            minute=0,
        )

        self.scheduler.add_job(self.send_reminders, "interval", minutes=1)
        self.scheduler.start()
        self.started = True
