from registration_bot.config import get_settings
from registration_bot.services.google_sheets import GoogleSheetsService
from registration_bot.services.scheduler import SchedulerService


_scheduler_service = SchedulerService(GoogleSheetsService(get_settings()))


def set_send_message_func(func):
    return _scheduler_service.set_send_message_func(func)


def check_birthdays():
    return _scheduler_service.check_birthdays()


def send_reminders():
    return _scheduler_service.send_reminders()


def add_reminder(date, hour, minute, message, user_ids):
    return _scheduler_service.add_reminder(date, hour, minute, message, user_ids)


def start():
    return _scheduler_service.start()

