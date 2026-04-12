# Telegram Registration Bot

A modular Telegram bot for user registration, admin controls, and scheduled messaging, integrated with Google Sheets.

## Features
- User registration with Google Sheets storage
- Admin and super admin controls
- Broadcast and reminders
- Birthday and scheduled messages
- Flask webhook for deployment (Render/Railway ready)

## Project Structure
- `bot.py` - Main bot logic and handlers
- `sheets.py` - Google Sheets integration
- `admin.py` - Admin/superadmin logic
- `scheduler.py` - Birthday and reminder scheduling
- `app.py` - Flask app for webhook
- `registration_bot/config.py` - App settings loader (env first, optional local file fallback)

## Secure Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create your local config from the template:
   ```powershell
   Copy-Item config.example.json config.json
   ```
3. Fill `config.json` with real values (`BOT_TOKEN`, `SPREADSHEET_KEY`, `SUPER_ADMIN_ID`, optional `WEBHOOK_URL`).
4. Create your local Google credentials file:
   ```powershell
   Copy-Item service_account.example.json service_account.json
   ```
   Replace the example content with your actual Google service account JSON.
5. Keep both `config.json` and `service_account.json` local-only. They are gitignored and must never be committed.
6. Optional: use environment variables from `.env.example` as your template.

## Environment Variables (Recommended in Production)
`registration_bot/config.py` loads values in this order:
1. Environment variable
2. `config.json` local fallback

Required values:
- `BOT_TOKEN`
- `SPREADSHEET_KEY`
- `SUPER_ADMIN_ID`

Optional values:
- `WEBHOOK_URL`
- `PORT` (defaults to `8000`)
- `GOOGLE_SERVICE_ACCOUNT_FILE` (defaults to `service_account.json`)
- `GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_B64` (base64-encoded full Google credentials JSON)

## Google Sheets Setup
- Create a Google Sheet with columns:
  `SURNAME, OTHER NAMES, DATE OF BIRTH, GENDER, REGISTRATION NUMBER, COLLEGE, PROGRAM, LEVEL, SUBUNIT, TELEGRAM NUMBER, HALL & ROOM NUMBER, TELEGRAM USER ID`
- Create a Google service account, download its key JSON, and share the sheet with that service account email.

## Webhook Deployment
- Set `WEBHOOK_URL` in host environment variables.
- Use `app.py` as the entry point.

---
MIT License
