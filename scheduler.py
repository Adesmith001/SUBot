from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from sheets import get_all_users
import pytz

scheduler = BackgroundScheduler()
reminders = []  # In production, persist reminders

# This will be set by bot.py after import
send_message_func = None

def set_send_message_func(func):
    global send_message_func
    send_message_func = func

def check_birthdays():
    today = datetime.now().strftime('%m-%d') # Changed to MM-DD for birthday check consistency with new DOB format
    users = get_all_users()
    for user in users:
        dob = user.get('DATE OF BIRTH', '')
        if dob and dob[0:5] == today: # Slicing for MM-DD
            if send_message_func:
                send_message_func(user['TELEGRAM USER ID'], f"🎉 Happy Birthday, {user['OTHER NAMES']}!")

def send_reminders():
    now_date = datetime.now().strftime('%Y-%m-%d')
    now_time_hour = datetime.now().hour
    now_time_minute = datetime.now().minute
    for reminder in list(reminders): # Iterate over a copy to allow modification during iteration
        if reminder['date'] == now_date and reminder['hour'] == now_time_hour and reminder['minute'] == now_time_minute:
            if send_message_func:
                for uid in reminder['user_ids']:
                    send_message_func(uid, reminder['message'])
            reminders.remove(reminder) # Remove reminder after sending (for non-recurring ones)

def add_reminder(date, hour, minute, message, user_ids):
    reminders.append({'date': date, 'hour': hour, 'minute': minute, 'message': message, 'user_ids': user_ids})

def start():
    scheduler.add_job(check_birthdays, 'cron', hour=7, minute=0)
    # The send_reminders job will now run more frequently to check for exact time matches
    scheduler.add_job(send_reminders, 'interval', minutes=1) # Check every minute for reminders
    scheduler.start() 