import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import base64
from datetime import datetime

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

try:
    links_sheet = gc.open_by_key(SPREADSHEET_KEY).worksheet('Links')
except gspread.exceptions.WorksheetNotFound:
    links_sheet = gc.open_by_key(SPREADSHEET_KEY).add_worksheet(title='Links', rows="100", cols="3")
    links_sheet.update('A1:C1', [['Type', 'Name', 'Link']])

USER_COLUMNS = [
    'SURNAME', 'OTHER NAMES', 'DATE OF BIRTH', 'GENDER', 'REGISTRATION NUMBER',
    'COLLEGE', 'PROGRAM', 'LEVEL', 'SUBUNIT', 'HALL & ROOM NUMBER', 'TELEGRAM USER ID', 'TELEGRAM NUMBER'
]

HEADER_ROW = [
    'SURNAME', 'OTHER NAMES', 'DATE OF BIRTH', 'GENDER', 'REGISTRATION NUMBER',
    'COLLEGE', 'PROGRAM', 'LEVEL', 'SUBUNIT', 'HALL & ROOM NUMBER', 'TELEGRAM USER ID', 'TELEGRAM NUMBER'
]

def get_or_create_sheet(sheet_name):
    try:
        worksheet = gc.open_by_key(SPREADSHEET_KEY).worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = gc.open_by_key(SPREADSHEET_KEY).add_worksheet(title=sheet_name, rows="100", cols="20")
        worksheet.append_row(HEADER_ROW)
    return worksheet

def add_user(user_data):
    from datetime import datetime
    year = str(datetime.now().year)
    semester = user_data.get('SEMESTER') or user_data.get('semester')
    values = [user_data.get(col, '') for col in USER_COLUMNS]
    # If registering for Omega and not registered for Alpha, add to both
    if semester == 'Both':
        alpha_sheet = get_or_create_sheet(f"Alpha_{year}")
        omega_sheet = get_or_create_sheet(f"Omega_{year}")
        alpha_sheet.append_row(values)
        omega_sheet.append_row(values)
    elif semester == 'Omega':
        omega_sheet = get_or_create_sheet(f"Omega_{year}")
        omega_sheet.append_row(values)
    else:
        alpha_sheet = get_or_create_sheet(f"Alpha_{year}")
        alpha_sheet.append_row(values)

def get_all_unique_users():
    all_sheets = gc.open_by_key(SPREADSHEET_KEY).worksheets()
    all_users = []
    seen_ids = set()
    for sheet in all_sheets:
        if sheet.title.startswith(('Alpha_', 'Omega_')):
            records = sheet.get_all_records()
            for record in records:
                uid = str(record.get('TELEGRAM USER ID'))
                if uid and uid not in seen_ids:
                    all_users.append(record)
                    seen_ids.add(uid)
    return all_users

def get_user_by_telegram_id(telegram_id, semester=None, year=None):
    if semester and year:
        sheet_name = f"{semester}_{year}"
        try:
            target_sheet = gc.open_by_key(SPREADSHEET_KEY).worksheet(sheet_name)
            records = target_sheet.get_all_records()
            for user in records:
                if str(user.get('TELEGRAM USER ID')) == str(telegram_id):
                    return user
        except gspread.exceptions.WorksheetNotFound:
            return None
    else:
        all_sheets = gc.open_by_key(SPREADSHEET_KEY).worksheets()
        for sheet in all_sheets:
            if sheet.title.startswith(('Alpha_', 'Omega_')):
                records = sheet.get_all_records()
                for user in records:
                    if str(user.get('TELEGRAM USER ID')) == str(telegram_id):
                        return user
    return None

def get_all_telegram_ids():
    all_sheets = gc.open_by_key(SPREADSHEET_KEY).worksheets()
    all_ids = set()
    for sheet in all_sheets:
        if sheet.title.startswith(('Alpha_', 'Omega_')):
            records = sheet.get_all_records()
            for record in records:
                uid = str(record.get('TELEGRAM USER ID'))
                if uid:
                    all_ids.add(uid)
    return list(all_ids)

def set_group_chat_link(group_type, link):
    """Set a group chat link. For general unit, use group_type='General'.
    For subunits, use the subunit name as group_type."""
    if group_type == 'General':
        set_link('General', '', link)
    else:
        set_link('Subunit', group_type, link)

def set_link(type, name, link):
    records = links_sheet.get_all_records()
    for i, record in enumerate(records, start=2):
        if record['Type'] == type and record['Name'] == name:
            links_sheet.update_cell(i, 3, link)
            return
    links_sheet.append_row([type, name, link])

def get_group_chat_link(subunit=None):
    """Get a group chat link. If subunit is None, returns the general unit link.
    Otherwise returns the link for the specified subunit."""
    if subunit is None:
        # Get general unit link
        records = links_sheet.get_all_records()
        for record in records:
            if record['Type'] == 'General':
                return record.get('Link')
    else:
        # Get subunit link
        records = links_sheet.get_all_records()
        for record in records:
            if record['Type'] == 'Subunit' and record.get('Name') == subunit:
                return record.get('Link')
    return None

def get_all_users():
    """Get all users from all semester sheets. This function is primarily used for birthday checks."""
    all_sheets = gc.open_by_key(SPREADSHEET_KEY).worksheets()
    all_users = []
    for sheet in all_sheets:
        if sheet.title.startswith(('Alpha_', 'Omega_')):
            records = sheet.get_all_records()
            all_users.extend(records)
    return all_users