"""Flask webhook app for production deployments."""

from __future__ import annotations

import asyncio

from flask import Flask, request
from telegram import Update

from registration_bot.application import create_bot_application, initialize_application
from registration_bot.config import Settings, get_settings


def _run_in_new_loop(coroutine):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()


def create_web_app(settings: Settings | None = None) -> Flask:
    settings = settings or get_settings()
    bot_app = create_bot_application(settings=settings)

    async def _setup() -> None:
        await initialize_application(bot_app, start_app=True)
        if settings.webhook_url:
            await bot_app.bot.set_webhook(
                url=f"{settings.webhook_url}/{settings.bot_token}",
                allowed_updates=Update.ALL_TYPES,
            )
        else:
            print("WARNING: WEBHOOK_URL not set. Bot will not receive updates in production.")

    _run_in_new_loop(_setup())

    flask_app = Flask(__name__)
    flask_app.config["BOT_APP"] = bot_app

    @flask_app.route("/")
    def index():
        return "Bot is running!"

    @flask_app.route(f"/{settings.bot_token}", methods=["POST"])
    def webhook():
        update = Update.de_json(request.get_json(force=True), bot_app.bot)
        _run_in_new_loop(bot_app.process_update(update))
        return "ok", 200

    return flask_app
