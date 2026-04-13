"""Registration conversation handlers."""

from __future__ import annotations

import calendar
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
    AWAITING_DOB_DAY,
    AWAITING_DOB_MONTH,
    AWAITING_DOB_YEAR,
    AWAITING_FORM_STATUS,
    AWAITING_GENDER,
    AWAITING_REG_NO_CHECK,
    AWAITING_SEMESTER,
    AWAITING_SUBUNIT,
    REG_FIELD_INPUT,
    REG_FIELDS_CONFIG,
    REG_NO_LOOKUP_MODE_KEY,
    REGISTRATION_DATA_KEY,
    REGISTRATION_INDEX_KEY,
    SEMESTER_KEY,
)

DOB_YEAR_KEY = "dob_year"
DOB_MONTH_KEY = "dob_month"
DOB_DAY_KEY = "dob_day"


def _sheets_service(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data["sheets_service"]


def _registration_data(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.setdefault(REGISTRATION_DATA_KEY, {})


def _clear_registration_state(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop(REGISTRATION_DATA_KEY, None)
    context.user_data.pop(REGISTRATION_INDEX_KEY, None)
    context.user_data.pop(SEMESTER_KEY, None)
    context.user_data.pop(REG_NO_LOOKUP_MODE_KEY, None)
    context.user_data.pop(DOB_YEAR_KEY, None)
    context.user_data.pop(DOB_MONTH_KEY, None)
    context.user_data.pop(DOB_DAY_KEY, None)


def _build_option_keyboard(
    options: list[str],
    *,
    prefix: str,
    row_size: int = 1,
) -> InlineKeyboardMarkup:
    rows = []
    for index in range(0, len(options), row_size):
        chunk = options[index : index + row_size]
        rows.append(
            [InlineKeyboardButton(option, callback_data=f"{prefix}{option}") for option in chunk]
        )
    return InlineKeyboardMarkup(rows)


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
        current_year = datetime.now().year
        years = [str(year) for year in range(current_year - 40, current_year + 1)]
        years.reverse()
        await context.bot.send_message(
            chat_id=chat_id,
            text="Select your birth year:",
            reply_markup=_build_option_keyboard(years, prefix="dob_year_", row_size=3),
        )
        return AWAITING_DOB_YEAR

    if field_type == "text":
        await context.bot.send_message(chat_id=chat_id, text=f"Enter your {field_name}:")
        return REG_FIELD_INPUT

    if field_name == "ARE YOU A NEW MEM":
        await context.bot.send_message(
            chat_id=chat_id,
            text="Are you a new member?",
            reply_markup=_build_option_keyboard(["Yes", "No"], prefix=f"{field_name}_"),
        )
        return AWAITING_SUBUNIT

    row_size = 1 if field_name == "PROGRAM" else 2
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Select your {field_name}:",
        reply_markup=_build_option_keyboard(field_info["options"], prefix=f"{field_name}_", row_size=row_size),
    )
    if field_name == "GENDER":
        return AWAITING_GENDER
    if field_name == "COLLEGE":
        return AWAITING_COLLEGE
    return AWAITING_SUBUNIT


async def dob_year_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    year = query.data.removeprefix("dob_year_")
    context.user_data[DOB_YEAR_KEY] = year

    months = [
        "JAN",
        "FEB",
        "MAR",
        "APR",
        "MAY",
        "JUN",
        "JUL",
        "AUG",
        "SEP",
        "OCT",
        "NOV",
        "DEC",
    ]
    await query.edit_message_text(
        text=f"Selected YEAR: {year}\nNow select your birth month:",
        reply_markup=_build_option_keyboard(months, prefix="dob_month_", row_size=3),
    )
    return AWAITING_DOB_MONTH


async def dob_month_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    month_text = query.data.removeprefix("dob_month_")
    month_map = {
        "JAN": 1,
        "FEB": 2,
        "MAR": 3,
        "APR": 4,
        "MAY": 5,
        "JUN": 6,
        "JUL": 7,
        "AUG": 8,
        "SEP": 9,
        "OCT": 10,
        "NOV": 11,
        "DEC": 12,
    }
    month = month_map[month_text]
    context.user_data[DOB_MONTH_KEY] = month

    year = int(context.user_data[DOB_YEAR_KEY])
    max_days = calendar.monthrange(year, month)[1]
    day_options = [f"{day:02d}" for day in range(1, max_days + 1)]

    await query.edit_message_text(
        text=f"Selected MONTH: {month_text}\nNow select your birth day:",
        reply_markup=_build_option_keyboard(day_options, prefix="dob_day_", row_size=7),
    )
    return AWAITING_DOB_DAY


async def dob_day_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    day_text = query.data.removeprefix("dob_day_")
    context.user_data[DOB_DAY_KEY] = int(day_text)

    year = int(context.user_data[DOB_YEAR_KEY])
    month = int(context.user_data[DOB_MONTH_KEY])
    day = int(context.user_data[DOB_DAY_KEY])
    formatted_dob = f"{month:02d}-{day:02d}-{year}"

    _registration_data(context)["DATE OF BIRTH"] = formatted_dob
    context.user_data[REGISTRATION_INDEX_KEY] = context.user_data.get(REGISTRATION_INDEX_KEY, 0) + 1
    context.user_data.pop(DOB_YEAR_KEY, None)
    context.user_data.pop(DOB_MONTH_KEY, None)
    context.user_data.pop(DOB_DAY_KEY, None)

    await query.edit_message_text(text=f"Selected DATE OF BIRTH: {formatted_dob}")
    return await _send_next_registration_field(update, context)


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

    existing_user = sheets_service.get_user_by_telegram_id(
        user_id,
        semester=semester,
        year=current_year,
    )
    if existing_user:
        await query.edit_message_text(f"You are already registered for {semester} semester.")
        return await _show_group_links(
            update,
            context,
            existing_user,
            "Here are your group links:",
        )

    context.user_data[SEMESTER_KEY] = semester
    await query.edit_message_text(f"You chose {semester} semester.")
    context.user_data[REGISTRATION_DATA_KEY] = {}
    context.user_data[REGISTRATION_INDEX_KEY] = 0
    return await _send_next_registration_field(update, context)


async def reg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field_idx = context.user_data.get(REGISTRATION_INDEX_KEY, 0)
    if field_idx >= len(REG_FIELDS_CONFIG):
        return await _send_next_registration_field(update, context)

    registration_data = _registration_data(context)
    current_field_info = REG_FIELDS_CONFIG[field_idx]
    current_field_name = current_field_info["name"]
    input_text = (update.message.text or "").strip()

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
