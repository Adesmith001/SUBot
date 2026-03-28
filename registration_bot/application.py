"""Telegram application factory."""

from __future__ import annotations

import asyncio

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from registration_bot.config import Settings, get_settings
from registration_bot.constants import (
    AWAITING_FORM_STATUS,
    AWAITING_COLLEGE,
    AWAITING_CONTACT,
    AWAITING_GENDER,
    AWAITING_REG_NO_CHECK,
    AWAITING_REGISTERED_ALPHA,
    AWAITING_SEMESTER,
    AWAITING_SUBUNIT,
    REG_FIELD_INPUT,
)
from registration_bot.handlers import admin as admin_handlers
from registration_bot.handlers import registration as registration_handlers
from registration_bot.services import AdminService, GoogleSheetsService, SchedulerService


def build_services(settings: Settings | None = None) -> dict[str, object]:
    settings = settings or get_settings()
    sheets_service = GoogleSheetsService(settings)
    return {
        "settings": settings,
        "sheets_service": sheets_service,
        "admin_service": AdminService(settings),
        "scheduler_service": SchedulerService(sheets_service),
    }


async def start_runtime(application: Application) -> None:
    if application.bot_data.get("_runtime_started"):
        return

    scheduler_service: SchedulerService = application.bot_data["scheduler_service"]
    scheduler_service.set_send_message_func(
        lambda user_id, message: asyncio.create_task(
            application.bot.send_message(chat_id=user_id, text=message)
        )
    )
    scheduler_service.start()
    application.bot_data["_runtime_started"] = True


def create_bot_application(
    settings: Settings | None = None,
    services: dict[str, object] | None = None,
) -> Application:
    settings = settings or get_settings()
    services = services or build_services(settings)

    application = Application.builder().token(settings.bot_token).post_init(start_runtime).build()
    application.bot_data.update(services)

    registration_conversation = ConversationHandler(
        entry_points=[CommandHandler("start", registration_handlers.start)],
        states={
            AWAITING_FORM_STATUS: [
                CallbackQueryHandler(
                    registration_handlers.form_status_choice,
                    pattern=r"^filled_form_",
                )
            ],
            AWAITING_REG_NO_CHECK: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    registration_handlers.registration_number_check,
                )
            ],
            AWAITING_SEMESTER: [
                CallbackQueryHandler(registration_handlers.semester_choice, pattern=r"^semester_")
            ],
            AWAITING_REGISTERED_ALPHA: [
                CallbackQueryHandler(
                    registration_handlers.registered_alpha_choice,
                    pattern=r"^registered_alpha_",
                )
            ],
            REG_FIELD_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, registration_handlers.reg_handler)
            ],
            AWAITING_GENDER: [
                CallbackQueryHandler(
                    registration_handlers.handle_inline_keyboard_input,
                    pattern=r"^GENDER_",
                )
            ],
            AWAITING_COLLEGE: [
                CallbackQueryHandler(
                    registration_handlers.handle_inline_keyboard_input,
                    pattern=r"^COLLEGE_",
                )
            ],
            AWAITING_SUBUNIT: [
                CallbackQueryHandler(
                    registration_handlers.handle_inline_keyboard_input,
                    pattern=r"^SUBUNIT_",
                )
            ],
            AWAITING_CONTACT: [
                MessageHandler(filters.CONTACT, registration_handlers.contact_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", registration_handlers.cancel)],
    )

    application.add_handler(registration_conversation)
    application.add_handler(CommandHandler("admin", admin_handlers.admin_panel))
    application.add_handler(
        CallbackQueryHandler(admin_handlers.admin_button, pattern=admin_handlers.ADMIN_CALLBACK_PATTERN)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.admin_text_handler)
    )
    return application


async def initialize_application(application: Application, *, start_app: bool = False) -> None:
    await application.initialize()
    await start_runtime(application)
    if start_app:
        await application.start()
