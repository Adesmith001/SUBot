from registration_bot.config import get_settings
from registration_bot.services.admins import AdminService


_admin_service = AdminService(get_settings())


def is_super_admin(user_id):
    return _admin_service.is_super_admin(user_id)


def is_admin(user_id):
    return _admin_service.is_admin(user_id)


def add_admin(user_id):
    return _admin_service.add_admin(user_id)


def remove_admin(user_id):
    return _admin_service.remove_admin(user_id)


def add_super_admin(user_id):
    return _admin_service.add_super_admin(user_id)


def remove_super_admin(user_id):
    return _admin_service.remove_super_admin(user_id)


def get_admins():
    return _admin_service.get_admins()


def get_super_admins():
    return _admin_service.get_super_admins()

