# Security Incident Response (Compromised Tokens/Keys)

Use this checklist if `BOT_TOKEN`, Google service account credentials, or other secrets were exposed.

## 1. Rotate credentials immediately

### Telegram bot token
1. Open `@BotFather` in Telegram.
2. Select your bot and revoke the current token.
3. Generate a new token.
4. Update `BOT_TOKEN` in your local `config.json` or environment variables.

### Google service account key
1. Open Google Cloud Console -> IAM & Admin -> Service Accounts.
2. Select the service account used by this bot.
3. Create a new JSON key.
4. Update local `service_account.json` (or `GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_B64`).
5. Delete old compromised key(s) from the same service account.

### Other values
- `SPREADSHEET_KEY` is an identifier (not a credential) but rotate to a new sheet if data access risk is unacceptable.
- `SUPER_ADMIN_ID` is not secret, but verify admin workflows after incident response.

## 2. Remove secrets from Git tracking (already prepared in this repo)

Run once on your branch:

```powershell
git rm --cached config.json service_account.json
git add .gitignore config.example.json service_account.example.json .env.example README.md SECURITY_INCIDENT_RESPONSE.md
git commit -m "Stop tracking secrets and add safe config templates"
git push
```

This keeps local files on disk while removing them from future commits.

## 3. Purge leaked secrets from Git history (recommended)

If secrets were committed in the past, remove them from history and force-push rewritten refs:

```powershell
python -m pip install git-filter-repo
git filter-repo --force --path config.json --path service_account.json --invert-paths
git push --force --all
git push --force --tags
```

After history rewrite:
- Ask collaborators to reclone the repository.
- Invalidate any old credentials again if they were exposed during the old history window.

## 4. Reconfigure deployment and verify bot is live

1. Update host environment variables (`BOT_TOKEN`, `SPREADSHEET_KEY`, `SUPER_ADMIN_ID`, and Google credentials).
2. Redeploy/restart the app.
3. Confirm webhook health endpoint (`/`) returns `Bot is running!`.
4. Run a quick `/start` test in Telegram.
5. Run an admin flow to confirm Sheets write access still works.
