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
    AWAITING_FORM_STATUS,
    AWAITING_GENDER,
    AWAITING_REG_NO_CHECK,
    AWAITING_REGISTERED_ALPHA,
    AWAITING_SEMESTER,
    AWAITING_SUBUNIT,
    REG_FIELD_INPUT,
    REG_FIELDS_CONFIG,
    REG_NO_LOOKUP_MODE_KEY,
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
    context.user_data.pop(REG_NO_LOOKUP_MODE_KEY, None)


async def _ask_form_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="filled_form_yes")],
        [InlineKeyboardButton("No", callback_data="filled_form_no")],
        [InlineKeyboardButton("Not Sure", callback_data="filled_form_not_sure")],
    ]
    await context.bot.send_message(
        chat_id=chat_id,
        text="Have you already filled the registration form?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return AWAITING_FORM_STATUS


async def _ask_semester_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keyboard = [
        [InlineKeyboardButton("Alpha", callback_data="semester_Alpha")],
        [InlineKeyboardButton("Omega", callback_data="semester_Omega")],
    ]
    context.user_data[REGISTRATION_INDEX_KEY] = 0
    context.user_data[REGISTRATION_DATA_KEY] = {}
    await context.bot.send_message(
        chat_id=chat_id,
        text="Which semester are you registering for?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return AWAITING_SEMESTER


async def _show_group_links(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_record: dict,
    intro_text: str,
):
    sheets_service = _sheets_service(context)
    subunit = user_record.get("SUBUNIT")
    subunit_link = sheets_service.get_group_chat_link(subunit) or "Not set yet"
    general_link = sheets_service.get_group_chat_link() or "Not set yet"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f"{intro_text}\n"
            f"Subunit Group: {subunit_link}\n"
            f"General Unit: {general_link}"
        ),
        reply_markup=ReplyKeyboardRemove(),
    )
    _clear_registration_state(context)
    return ConversationHandler.END


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

    if field_name == "ARE YOU A NEW MEMBER?":
        keyboard = [
            [InlineKeyboardButton("Yes", callback_data=f"{field_name}_Yes")],
            [InlineKeyboardButton("No", callback_data=f"{field_name}_No")],
        ]
        await context.bot.send_message(
            chat_id=chat_id,
            text="Are you a new member?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return AWAITING_SUBUNIT

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
    _clear_registration_state(context)
    return await _ask_form_status(update, context)


async def form_status_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data.removeprefix("filled_form_")
    sheets_service = _sheets_service(context)
    telegram_id = str(query.from_user.id)

    if choice == "yes":
        existing_user = sheets_service.get_user_by_telegram_id(telegram_id)
        if existing_user:
            await query.edit_message_text("I found your registration details.")
            return await _show_group_links(
                update,
                context,
                existing_user,
                "Here are your group links:",
            )

        context.user_data[REG_NO_LOOKUP_MODE_KEY] = "existing_user_confirmation"
        await query.edit_message_text(
            "I couldn't find a registration linked to this Telegram account. "
            "Send your registration number so I can check."
        )
        return AWAITING_REG_NO_CHECK

    if choice == "not_sure":
        context.user_data[REG_NO_LOOKUP_MODE_KEY] = "uncertain"
        await query.edit_message_text("Send your registration number so I can check for you.")
        return AWAITING_REG_NO_CHECK

    await query.edit_message_text("Alright, let's get you registered.")
    return await _ask_semester_selection(update, context)


async def registration_number_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    registration_number = (update.message.text or "").strip()
    if not registration_number:
        await update.message.reply_text("Please send your registration number.")
        return AWAITING_REG_NO_CHECK

    sheets_service = _sheets_service(context)
    existing_user = sheets_service.get_user_by_registration_number(registration_number)

    if existing_user:
        return await _show_group_links(
            update,
            context,
            existing_user,
            "I found your registration. Here are your group links:",
        )

    await update.message.reply_text(
        "I couldn't find that registration number, so I'll take you through registration now."
    )
    return await _ask_semester_selection(update, context)


async def semester_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    semester = query.data.split("_", 1)[1]
    current_year = datetime.now().year
    sheets_service = _sheets_service(context)

    if semester == "Alpha":
        existing_user = sheets_service.get_user_by_telegram_id(
            user_id,
            semester="Alpha",
            year=current_year,
        )
        if existing_user:
            await query.edit_message_text("You are already registered for Alpha semester.")
            return await _show_group_links(
                update,
                context,
                existing_user,
                "Here are your group links:",
            )
        context.user_data[SEMESTER_KEY] = "Alpha"
        await query.edit_message_text("You chose Alpha semester.")
    else:
        existing_user = sheets_service.get_user_by_telegram_id(
            user_id,
            semester="Omega",
            year=current_year,
        )
        if existing_user:
            await query.edit_message_text("You are already registered for Omega semester.")
            return await _show_group_links(
                update,
                context,
                existing_user,
                "Here are your group links:",
            )
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

    return await _show_group_links(
        update,
        context,
        registration_data,
        "Registration complete! Here are your group links:",
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _clear_registration_state(context)
    await update.message.reply_text("Registration cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
