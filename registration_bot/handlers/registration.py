"""Registration conversation handlers."""

from __future__ import annotations

import re
from datetime import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler

from registration_bot.constants import (
    AWAITING_COLLEGE,
    AWAITING_CONTACT,
    AWAITING_GENDER,
    AWAITING_REGISTERED_ALPHA,
    AWAITING_SEMESTER,
    AWAITING_SUBUNIT,
    REG_FIELD_INPUT,
    REG_FIELDS_CONFIG,
    REGISTRATION_DATA_KEY,
    REGISTRATION_INDEX_KEY,
    SEMESTER_KEY,
)


def _sheets_service(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data["sheets_service"]


def _registration_data(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.setdefault(REGISTRATION_DATA_KEY, {})


def _clear_registration_state(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop(REGISTRATION_DATA_KEY, None)
    context.user_data.pop(REGISTRATION_INDEX_KEY, None)
    context.user_data.pop(SEMESTER_KEY, None)


async def _send_next_registration_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    field_idx = context.user_data.get(REGISTRATION_INDEX_KEY, 0)

    if field_idx >= len(REG_FIELDS_CONFIG):
        keyboard = [[KeyboardButton(text="Share My Phone Number", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="Please share your Telegram phone number:",
            reply_markup=reply_markup,
        )
        return AWAITING_CONTACT

    field_info = REG_FIELDS_CONFIG[field_idx]
    field_name = field_info["name"]
    field_type = field_info["type"]

    if field_type == "dob":
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Enter your {field_name} in MM-DD-YYYY format (e.g., 01-23-2000):",
        )
        return REG_FIELD_INPUT

    if field_type == "text":
        await context.bot.send_message(chat_id=chat_id, text=f"Enter your {field_name}:")
        return REG_FIELD_INPUT

    keyboard = [
        [InlineKeyboardButton(option, callback_data=f"{field_name}_{option}")]
        for option in field_info["options"]
    ]
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Select your {field_name}:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    if field_name == "GENDER":
        return AWAITING_GENDER
    if field_name == "COLLEGE":
        return AWAITING_COLLEGE
    return AWAITING_SUBUNIT


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Alpha", callback_data="semester_Alpha")],
        [InlineKeyboardButton("Omega", callback_data="semester_Omega")],
    ]
    _clear_registration_state(context)
    context.user_data[REGISTRATION_INDEX_KEY] = 0
    context.user_data[REGISTRATION_DATA_KEY] = {}
    await update.message.reply_text(
        "Which semester are you registering for?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return AWAITING_SEMESTER


async def semester_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    semester = query.data.split("_", 1)[1]
    current_year = datetime.now().year
    sheets_service = _sheets_service(context)

    if semester == "Alpha":
        if sheets_service.get_user_by_telegram_id(user_id, semester="Alpha", year=current_year):
            await query.edit_message_text("You are already registered for Alpha semester.")
            _clear_registration_state(context)
            return ConversationHandler.END
        context.user_data[SEMESTER_KEY] = "Alpha"
        await query.edit_message_text("You chose Alpha semester.")
    else:
        if sheets_service.get_user_by_telegram_id(user_id, semester="Omega", year=current_year):
            await query.edit_message_text("You are already registered for Omega semester.")
            _clear_registration_state(context)
            return ConversationHandler.END
        keyboard = [
            [InlineKeyboardButton("Yes", callback_data="registered_alpha_Yes")],
            [InlineKeyboardButton("No", callback_data="registered_alpha_No")],
        ]
        await query.edit_message_text(
            "Did you register for Alpha semester?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return AWAITING_REGISTERED_ALPHA

    context.user_data[REGISTRATION_DATA_KEY] = {}
    context.user_data[REGISTRATION_INDEX_KEY] = 0
    return await _send_next_registration_field(update, context)


async def registered_alpha_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data.split("_", 2)[2]
    context.user_data[SEMESTER_KEY] = "Omega" if choice == "Yes" else "Both"
    context.user_data[REGISTRATION_DATA_KEY] = {}
    context.user_data[REGISTRATION_INDEX_KEY] = 0

    await query.edit_message_text(f"You chose {choice}.")
    return await _send_next_registration_field(update, context)


async def reg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field_idx = context.user_data.get(REGISTRATION_INDEX_KEY, 0)
    if field_idx >= len(REG_FIELDS_CONFIG):
        return await _send_next_registration_field(update, context)

    registration_data = _registration_data(context)
    current_field_info = REG_FIELDS_CONFIG[field_idx]
    current_field_name = current_field_info["name"]
    input_text = (update.message.text or "").strip()

    if current_field_name == "DATE OF BIRTH":
        if not re.match(r"^(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])-\d{4}$", input_text):
            await update.message.reply_text(
                "Invalid date format. Please use MM-DD-YYYY (e.g., 01-23-2000)."
            )
            return REG_FIELD_INPUT
        try:
            datetime.strptime(input_text, "%m-%d-%Y")
        except ValueError:
            await update.message.reply_text(
                "Invalid date. Please enter a real date in MM-DD-YYYY format."
            )
            return REG_FIELD_INPUT

    registration_data[current_field_name] = input_text
    context.user_data[REGISTRATION_INDEX_KEY] = field_idx + 1
    return await _send_next_registration_field(update, context)


async def handle_inline_keyboard_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    field_idx = context.user_data.get(REGISTRATION_INDEX_KEY, 0)
    current_field_info = REG_FIELDS_CONFIG[field_idx]
    current_field_name = current_field_info["name"]
    selected_option = query.data.split("_", 1)[1]

    _registration_data(context)[current_field_name] = selected_option
    context.user_data[REGISTRATION_INDEX_KEY] = field_idx + 1
    await query.edit_message_text(text=f"Selected {current_field_name}: {selected_option}")
    return await _send_next_registration_field(update, context)


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    contact = update.message.contact
    if not contact or str(contact.user_id) != user_id:
        await update.message.reply_text("Please share your own contact by pressing the button.")
        return AWAITING_CONTACT

    semester = context.user_data.get(SEMESTER_KEY)
    if not semester:
        await update.message.reply_text(
            "Your registration session expired. Please use /start to begin again.",
            reply_markup=ReplyKeyboardRemove(),
        )
        _clear_registration_state(context)
        return ConversationHandler.END

    registration_data = _registration_data(context)
    registration_data["TELEGRAM NUMBER"] = contact.phone_number
    registration_data["TELEGRAM USER ID"] = user_id
    registration_data["SEMESTER"] = semester

    sheets_service = _sheets_service(context)
    sheets_service.add_user(registration_data)

    subunit = registration_data["SUBUNIT"]
    subunit_link = sheets_service.get_group_chat_link(subunit) or "Not set yet"
    general_link = sheets_service.get_group_chat_link() or "Not set yet"

    await update.message.reply_text(
        "Registration complete! Here are your group links:\n"
        f"Subunit Group: {subunit_link}\n"
        f"General Unit: {general_link}",
        reply_markup=ReplyKeyboardRemove(),
    )
    _clear_registration_state(context)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _clear_registration_state(context)
    await update.message.reply_text("Registration cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

