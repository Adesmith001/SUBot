"""Admin handlers."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from registration_bot.constants import ADMIN_ACTION_KEY, SUBUNIT_OPTIONS


ADMIN_CALLBACK_PATTERN = (
    r"^(broadcast|set_subunit_link|set_general_link|assign_admin|assign_super_admin|"
    r"delete_admin|delete_super_admin|set_link_.*)$"
)


def _admin_service(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data["admin_service"]


def _sheets_service(context: ContextTypes.DEFAULT_TYPE):
    return context.application.bot_data["sheets_service"]


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    admin_service = _admin_service(context)

    if not admin_service.is_admin(user_id):
        await update.message.reply_text("You are not an admin.")
        return

    keyboard = [
        [InlineKeyboardButton("Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("Set Subunit Link", callback_data="set_subunit_link")],
    ]
    if admin_service.is_super_admin(user_id):
        keyboard.extend(
            [
                [InlineKeyboardButton("Set General Link", callback_data="set_general_link")],
                [InlineKeyboardButton("Assign Admin", callback_data="assign_admin")],
                [InlineKeyboardButton("Assign Super Admin", callback_data="assign_super_admin")],
                [InlineKeyboardButton("Delete Admin", callback_data="delete_admin")],
                [InlineKeyboardButton("Delete Super Admin", callback_data="delete_super_admin")],
            ]
        )

    await update.message.reply_text(
        "Admin Panel:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def admin_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    admin_service = _admin_service(context)

    await query.answer()
    if not admin_service.is_admin(user_id):
        await query.edit_message_text("You are not authorized to use the admin panel.")
        context.user_data.pop(ADMIN_ACTION_KEY, None)
        return

    if query.data == "broadcast":
        context.user_data[ADMIN_ACTION_KEY] = "broadcast"
        await query.edit_message_text("Send the message to broadcast:")
        return

    if query.data == "set_general_link":
        if not admin_service.is_super_admin(user_id):
            await query.edit_message_text("Only super admins can set the general link.")
            return
        context.user_data[ADMIN_ACTION_KEY] = "set_general_link"
        await query.edit_message_text("Send the general unit link:")
        return

    if query.data == "set_subunit_link":
        keyboard = [
            [InlineKeyboardButton(subunit, callback_data=f"set_link_{subunit}")]
            for subunit in SUBUNIT_OPTIONS
        ]
        await query.edit_message_text(
            "Choose the subunit to set the link for:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if query.data.startswith("set_link_"):
        subunit = query.data.split("_", 2)[2]
        context.user_data[ADMIN_ACTION_KEY] = f"set_link_{subunit}"
        await query.edit_message_text(f"Send the link for {subunit}:")
        return

    if not admin_service.is_super_admin(user_id):
        await query.edit_message_text("Only super admins can perform this action.")
        return

    action_messages = {
        "assign_admin": "Send the Telegram user ID to assign as admin:",
        "assign_super_admin": "Send the Telegram user ID to assign as super admin:",
        "delete_admin": "Send the Telegram user ID to delete as admin:",
        "delete_super_admin": "Send the Telegram user ID to delete as super admin:",
    }
    context.user_data[ADMIN_ACTION_KEY] = query.data
    await query.edit_message_text(action_messages[query.data])


async def admin_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get(ADMIN_ACTION_KEY)
    if not action:
        return

    user_id = str(update.effective_user.id)
    admin_service = _admin_service(context)
    if not admin_service.is_admin(user_id):
        await update.message.reply_text("You are not an admin.")
        context.user_data.pop(ADMIN_ACTION_KEY, None)
        return

    message_text = (update.message.text or "").strip()
    sheets_service = _sheets_service(context)

    if action == "broadcast":
        for telegram_id in sheets_service.get_all_telegram_ids():
            try:
                await context.bot.send_message(chat_id=telegram_id, text=message_text)
            except Exception as exc:
                print(f"Could not send message to {telegram_id}: {exc}")
        await update.message.reply_text("Broadcast sent to all registered users.")
    elif action == "set_general_link":
        if not admin_service.is_super_admin(user_id):
            await update.message.reply_text("Only super admins can set the general link.")
            context.user_data.pop(ADMIN_ACTION_KEY, None)
            return
        sheets_service.set_link("General", "", message_text)
        await update.message.reply_text("General unit link set.")
    elif action.startswith("set_link_"):
        subunit = action.split("_", 2)[2]
        sheets_service.set_link("Subunit", subunit, message_text)
        await update.message.reply_text(f"Link for {subunit} set.")
    elif action == "assign_admin":
        if not admin_service.is_super_admin(user_id):
            await update.message.reply_text("Only super admins can assign admins.")
            context.user_data.pop(ADMIN_ACTION_KEY, None)
            return
        added = admin_service.add_admin(message_text)
        await update.message.reply_text(
            f"User {message_text} is now an admin."
            if added
            else f"User {message_text} is already an admin."
        )
    elif action == "assign_super_admin":
        if not admin_service.is_super_admin(user_id):
            await update.message.reply_text("Only super admins can assign super admins.")
            context.user_data.pop(ADMIN_ACTION_KEY, None)
            return
        added = admin_service.add_super_admin(message_text)
        await update.message.reply_text(
            f"User {message_text} is now a super admin."
            if added
            else f"User {message_text} is already a super admin."
        )
    elif action == "delete_admin":
        if not admin_service.is_super_admin(user_id):
            await update.message.reply_text("Only super admins can delete admins.")
            context.user_data.pop(ADMIN_ACTION_KEY, None)
            return
        removed = admin_service.remove_admin(message_text)
        await update.message.reply_text(
            f"User {message_text} is no longer an admin."
            if removed
            else f"User {message_text} is not currently an admin."
        )
    elif action == "delete_super_admin":
        if not admin_service.is_super_admin(user_id):
            await update.message.reply_text("Only super admins can delete super admins.")
            context.user_data.pop(ADMIN_ACTION_KEY, None)
            return
        removed = admin_service.remove_super_admin(message_text)
        if removed:
            reply = f"User {message_text} is no longer a super admin."
        elif message_text == admin_service.settings.super_admin_id:
            reply = "The primary super admin from settings cannot be removed."
        else:
            reply = f"User {message_text} is not currently a super admin."
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("Invalid action or state.")

    context.user_data.pop(ADMIN_ACTION_KEY, None)
