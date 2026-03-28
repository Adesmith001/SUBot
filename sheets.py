from registration_bot.config import get_settings
from registration_bot.services.google_sheets import (
    HEADER_ROW,
    USER_COLUMNS,
    GoogleSheetsService,
)


_sheets_service = GoogleSheetsService(get_settings())


def get_or_create_sheet(sheet_name):
    return _sheets_service.get_or_create_sheet(sheet_name)


def add_user(user_data):
    return _sheets_service.add_user(user_data)


def get_all_unique_users():
    return _sheets_service.get_all_unique_users()


def get_user_by_telegram_id(telegram_id, semester=None, year=None):
    return _sheets_service.get_user_by_telegram_id(telegram_id, semester=semester, year=year)


def get_user_by_registration_number(registration_number):
    return _sheets_service.get_user_by_registration_number(registration_number)


def get_all_telegram_ids():
    return _sheets_service.get_all_telegram_ids()


def set_group_chat_link(group_type, link):
    return _sheets_service.set_group_chat_link(group_type, link)


def set_link(link_type, name, link):
    return _sheets_service.set_link(link_type, name, link)


def get_group_chat_link(subunit=None):
    return _sheets_service.get_group_chat_link(subunit)


def get_all_users():
    return _sheets_service.get_all_users()
