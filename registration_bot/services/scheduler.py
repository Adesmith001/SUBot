"""Scheduled bot jobs."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler

from registration_bot.services.google_sheets import GoogleSheetsService


SendMessageFunc = Callable[[str, str], None]


class SchedulerService:
    def __init__(self, sheets_service: GoogleSheetsService):
        self.sheets_service = sheets_service
        self.scheduler = BackgroundScheduler()
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
        self.scheduler.add_job(self.send_reminders, "interval", minutes=1)
        self.scheduler.start()
        self.started = True
