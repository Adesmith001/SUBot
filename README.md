# Telegram Registration Bot

A modular Telegram bot for user registration, admin controls, and scheduled messaging, integrated with Google Sheets.

## Features
- User registration with Google Sheets storage
- Admin and super admin controls
- Broadcast and reminders
- Birthday and scheduled messages
- Flask webhook for deployment (Render/Railway ready)

## Project Structure
- `bot.py` — Main bot logic and handlers
- `sheets.py` — Google Sheets integration
- `admin.py` — Admin/superadmin logic
- `scheduler.py` — Birthday and reminder scheduling
- `app.py` — Flask app for webhook
- `config.json` — Configuration (token, spreadsheet, admin)

## Setup
1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set up your Google Service Account and share your sheet with its email.
3. Fill in `config.json` with your bot token, spreadsheet key, and super admin ID.
4. Deploy on Render/Railway:
   - Set `WEBHOOK_URL` and `PORT` as environment variables if needed.
   - Use `app.py` as the entry point.

## Google Sheets Setup
- Create a Google Sheet with columns:
  `SURNAME, OTHER NAMES, DATE OF BIRTH, GENDER, REGISTRATION NUMBER, COLLEGE, PROGRAM, LEVEL, SUBUNIT, TELEGRAM NUMBER, HALL & ROOM NUMBER, TELEGRAM USER ID`
- Download your service account JSON and save as `service_account.json` in the project root.

## Webhook Deployment
- Set your webhook URL in Render/Railway environment variables.
- The bot will listen for Telegram updates via Flask.

---
MIT License 