import json
from sheets import get_all_telegram_ids

with open('config.json') as f:
    config = json.load(f)

SUPER_ADMIN_ID = config['SUPER_ADMIN_ID']

# In production, store admin IDs in a persistent store or Google Sheet
ADMINS = set()
SUPER_ADMINS = {str(SUPER_ADMIN_ID)}

def is_super_admin(user_id):
    return str(user_id) in SUPER_ADMINS

def is_admin(user_id):
    return str(user_id) in ADMINS or is_super_admin(user_id)

def add_admin(user_id):
    ADMINS.add(str(user_id))

def remove_admin(user_id):
    ADMINS.discard(str(user_id))

def add_super_admin(user_id):
    SUPER_ADMINS.add(str(user_id))

def remove_super_admin(user_id):
    SUPER_ADMINS.discard(str(user_id))

def get_admins():
    return list(ADMINS)

def get_super_admins():
    return list(SUPER_ADMINS) 