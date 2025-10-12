import os
import asyncio
from flask import Flask, request
from telegram import Update
import json

# Import bot functions
from bot import create_bot_app, initialize_bot

# Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    # Fallback to config.json for local testing
    try:
        with open('config.json') as f:
            config = json.load(f)
        BOT_TOKEN = config['BOT_TOKEN']
    except FileNotFoundError:
        raise ValueError("BOT_TOKEN not found in environment variables or config.json")

WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
PORT = int(os.environ.get('PORT', 8000))

# Flask app
app = Flask(__name__)
bot_app = None

@app.route("/")
def index():
    return "Bot is running!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Webhook endpoint to receive updates from Telegram."""
    update_data = request.get_json(force=True)
    update = Update.de_json(update_data, bot_app.bot)
    
    # Process update in a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(bot_app.process_update(update))
    finally:
        loop.close()
    
    return "ok", 200

async def setup_webhook():
    """Set up the webhook."""
    global bot_app
    bot_app = create_bot_app()
    await initialize_bot(bot_app)
    
    if WEBHOOK_URL:
        await bot_app.bot.set_webhook(
            url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            allowed_updates=Update.ALL_TYPES
        )
        print(f"Webhook set to: {WEBHOOK_URL}/{BOT_TOKEN}")

if __name__ == '__main__':
    if not WEBHOOK_URL:
        print("ERROR: WEBHOOK_URL environment variable not set.")
        exit(1)
    
    # Set up webhook
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(setup_webhook())
    finally:
        loop.close()
    
    # Start Flask app
    app.run(host="0.0.0.0", port=PORT)