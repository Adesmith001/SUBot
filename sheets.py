import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import base64

with open('config.json') as f:
    config = json.load(f)

SPREADSHEET_KEY = config['SPREADSHEET_KEY']

scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
]

# Try to load credentials from environment variable first
service_account_info = os.environ.get('GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_B64')
if service_account_info:
    try:
        creds_json = json.loads(base64.b64decode(service_account_info).decode('utf-8'))
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    except Exception as e:
        print(f"Error decoding or loading service account from environment variable: {e}")
        # Fallback to file if env var fails (e.g., malformed)
        creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
else:
    # Fallback to file if environment variable not set
    creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)

gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_KEY).sheet1

USER_COLUMNS = [
    'SURNAME', 'OTHER NAMES', 'DATE OF BIRTH', 'GENDER', 'REGISTRATION NUMBER',
    'COLLEGE', 'PROGRAM', 'LEVEL', 'SUBUNIT', 'TELEGRAM NUMBER', 'HALL & ROOM NUMBER', 'TELEGRAM USER ID'
]

def add_user(user_data):
    values = [user_data.get(col, '') for col in USER_COLUMNS]
    sheet.append_row(values)

def get_all_users():
    return sheet.get_all_records()

def get_user_by_telegram_id(telegram_id):
    users = get_all_users()
    for user in users:
        if str(user.get('TELEGRAM USER ID')) == str(telegram_id):
            return user
    return None

def get_all_telegram_ids():
    users = get_all_users()
    return [str(user['TELEGRAM USER ID']) for user in users if user.get('TELEGRAM USER ID')]
