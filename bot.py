import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler, ContextTypes)
from sheets import (
    add_user, get_user_by_telegram_id, get_all_telegram_ids, get_or_create_sheet, 
    get_group_chat_link, set_link
)
from admin import is_admin, is_super_admin, add_admin, add_super_admin, remove_admin, remove_super_admin, get_admins, get_super_admins
import scheduler
from datetime import datetime
import re

with open('config.json') as f:
    config = json.load(f)

BOT_TOKEN = config['BOT_TOKEN']
SUPER_ADMIN_ID = str(config['SUPER_ADMIN_ID'])

REG_FIELD_INPUT, AWAITING_GENDER, AWAITING_COLLEGE, AWAITING_SUBUNIT, AWAITING_CONTACT, AWAITING_REMINDER_DATE, AWAITING_REMINDER_TIME, AWAITING_ADMIN_ID_TO_DELETE, AWAITING_SUPER_ADMIN_ID_TO_DELETE, AWAITING_SEMESTER, AWAITING_REGISTERED_ALPHA = range(11)

REG_FIELDS_CONFIG = [
    {'name': 'SURNAME', 'type': 'text'},
    {'name': 'OTHER NAMES', 'type': 'text'},
    {'name': 'DATE OF BIRTH', 'type': 'dob'}, 
    {'name': 'GENDER', 'type': 'inline_keyboard', 'options': ['Male', 'Female']},
    {'name': 'REGISTRATION NUMBER', 'type': 'text'},
    {'name': 'COLLEGE', 'type': 'inline_keyboard', 'options': ['College of Science and Technology', 'College of Engineering', 'College of Management and Social Science', 'College of Leadersip Developement Studies']},
    {'name': 'PROGRAM', 'type': 'text'},
    {'name': 'LEVEL', 'type': 'text'},
    {'name': 'SUBUNIT', 'type': 'inline_keyboard', 'options': ['Alpha', 'Omega', 'Cobbwebs and Dustbins', 'Altar and Toilet', 'Windows and Doors', 'Royal Chairs', 'Store']},
    {'name': 'HALL & ROOM NUMBER', 'type': 'text'}
]

user_reg_data = {}

async def _send_next_registration_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id
    field_idx = context.user_data.get('reg_field_idx', 0)

    if field_idx < len(REG_FIELDS_CONFIG):
        field_info = REG_FIELDS_CONFIG[field_idx]
        field_name = field_info['name']
        field_type = field_info['type']

        if field_type == 'text' or field_type == 'dob':
            await context.bot.send_message(chat_id=chat_id, text=f"Enter your {field_name}:")
            return REG_FIELD_INPUT
        elif field_type == 'inline_keyboard':
            keyboard = [[InlineKeyboardButton(option, callback_data=f"{field_name}_{option}")] for option in field_info['options']]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=chat_id, text=f"Select your {field_name}:", reply_markup=reply_markup)
            if field_name == 'GENDER':
                return AWAITING_GENDER
            elif field_name == 'COLLEGE':
                return AWAITING_COLLEGE
            elif field_name == 'SUBUNIT':
                return AWAITING_SUBUNIT
    else:
        keyboard = [[KeyboardButton(text="Share My Phone Number", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await context.bot.send_message(chat_id=chat_id, text="Please share your Telegram phone number:", reply_markup=reply_markup)
        return AWAITING_CONTACT
    return ConversationHandler.END

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    keyboard = [
        [InlineKeyboardButton("Alpha", callback_data='semester_Alpha')],
        [InlineKeyboardButton("Omega", callback_data='semester_Omega')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Which semester are you registering for?", reply_markup=reply_markup)
    context.user_data['reg_field_idx'] = 0
    user_reg_data[user_id] = {}
    return AWAITING_SEMESTER

async def semester_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    semester = query.data.split('_')[1]
    year = datetime.now().year

    if semester == 'Alpha':
        if get_user_by_telegram_id(user_id, semester='Alpha', year=year):
            await query.edit_message_text("You are already registered for Alpha semester.")
            return ConversationHandler.END
        context.user_data['semester'] = 'Alpha'
        await query.edit_message_text("You chose Alpha semester.")
    elif semester == 'Omega':
        if get_user_by_telegram_id(user_id, semester='Omega', year=year):
            await query.edit_message_text("You are already registered for Omega semester.")
            return ConversationHandler.END
        keyboard = [
            [InlineKeyboardButton("Yes", callback_data='registered_alpha_Yes')],
            [InlineKeyboardButton("No", callback_data='registered_alpha_No')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Did you register for Alpha semester?", reply_markup=reply_markup)
        return AWAITING_REGISTERED_ALPHA

    user_reg_data[user_id] = {}
    context.user_data['reg_field_idx'] = 0
    return await _send_next_registration_field(update, context)

async def registered_alpha_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    choice = query.data.split('_')[2]

    if choice == 'Yes':
        context.user_data['semester'] = 'Omega'
    elif choice == 'No':
        context.user_data['semester'] = 'Both'
    await query.edit_message_text(f"You chose {choice}.")

    user_reg_data[user_id] = {}
    context.user_data['reg_field_idx'] = 0
    return await _send_next_registration_field(update, context)

async def reg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    field_idx = context.user_data.get('reg_field_idx', 0)
    current_field_info = REG_FIELDS_CONFIG[field_idx]
    current_field_name = current_field_info['name']
    input_text = update.message.text

    if current_field_name == 'DATE OF BIRTH':
        if not re.match(r'^(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])-\d{4}$', input_text):
            await update.message.reply_text("Invalid date format. Please use MM-DD-YYYY (e.g., 01-23-2000).")
            return REG_FIELD_INPUT
        try:
            datetime.strptime(input_text, '%m-%d-%Y')
            user_reg_data[user_id][current_field_name] = input_text
            context.user_data['reg_field_idx'] += 1
            return await _send_next_registration_field(update, context)
        except ValueError:
            await update.message.reply_text("Invalid date. Please enter a real date in MM-DD-YYYY format.")
            return REG_FIELD_INPUT
    else:
        user_reg_data[user_id][current_field_name] = input_text
        context.user_data['reg_field_idx'] += 1
        return await _send_next_registration_field(update, context)

async def handle_inline_keyboard_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    field_idx = context.user_data.get('reg_field_idx', 0)
    current_field_info = REG_FIELDS_CONFIG[field_idx]
    current_field_name = current_field_info['name']

    selected_option = query.data.split('_', 1)[1]
    user_reg_data[user_id][current_field_name] = selected_option
    context.user_data['reg_field_idx'] += 1
    await query.edit_message_text(text=f"Selected {current_field_name}: {selected_option}")
    return await _send_next_registration_field(update, context)

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if update.message.contact and str(update.message.contact.user_id) == user_id:
        user_reg_data[user_id]['TELEGRAM NUMBER'] = update.message.contact.phone_number
        user_reg_data[user_id]['TELEGRAM USER ID'] = user_id
        year = datetime.now().year
        # Ensure semester is set in user_reg_data
        user_reg_data[user_id]['SEMESTER'] = context.user_data.get('semester')
        semester = context.user_data['semester']
        if semester == 'Alpha':
            sheet_name = f"Alpha_{year}"
            sheets = [get_or_create_sheet(sheet_name)]
        elif semester == 'Omega':
            sheet_name = f"Omega_{year}"
            sheets = [get_or_create_sheet(sheet_name)]
        elif semester == 'Both':            
            alpha_sheet = get_or_create_sheet(f"Alpha_{year}")
            omega_sheet = get_or_create_sheet(f"Omega_{year}")
            sheets = [alpha_sheet, omega_sheet]
        
        add_user(user_reg_data[user_id])
        
        subunit = user_reg_data[user_id]['SUBUNIT']
        subunit_link = get_group_chat_link(subunit) or "Not set yet"
        general_link = get_group_chat_link() or "Not set yet"
        await update.message.reply_text(
            f"Registration complete! Here are your group links:\n"
            f"Subunit Group: {subunit_link}\n"
            f"General Unit: {general_link}",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("Please share your own contact by pressing the button.")
        return AWAITING_CONTACT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("You are not an admin or registered.")
        return
    keyboard = [
        [InlineKeyboardButton("Broadcast", callback_data='broadcast')],
        [InlineKeyboardButton("Set Subunit Link", callback_data='set_subunit_link')],
    ]
    if is_super_admin(user_id):
        keyboard.append([InlineKeyboardButton("Set General Link", callback_data='set_general_link')])
        keyboard.append([InlineKeyboardButton("Assign Admin", callback_data='assign_admin')])
        keyboard.append([InlineKeyboardButton("Assign Super Admin", callback_data='assign_super_admin')])
        keyboard.append([InlineKeyboardButton("Delete Admin", callback_data='delete_admin')])
        keyboard.append([InlineKeyboardButton("Delete Super Admin", callback_data='delete_super_admin')])
    await update.message.reply_text("Admin Panel:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()
    if query.data == 'broadcast':
        context.user_data['admin_action'] = 'broadcast'
        await query.edit_message_text("Send the message to broadcast:")
    elif query.data == 'set_general_link' and is_super_admin(user_id):
        context.user_data['admin_action'] = 'set_general_link'
        await query.edit_message_text("Send the general unit link:")
    elif query.data == 'set_subunit_link':
        subunits = [option for option in REG_FIELDS_CONFIG if option['name'] == 'SUBUNIT'][0]['options']
        keyboard = [[InlineKeyboardButton(subunit, callback_data=f'set_link_{subunit}')] for subunit in subunits]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Choose the subunit to set the link for:", reply_markup=reply_markup)
    elif query.data.startswith('set_link_'):
        subunit = query.data.split('_', 2)[2]
        context.user_data['admin_action'] = f'set_link_{subunit}'
        await query.edit_message_text(f"Send the link for {subunit}:")
    elif query.data == 'assign_admin' and is_super_admin(user_id):
        context.user_data['admin_action'] = 'assign_admin'
        await query.edit_message_text("Send the Telegram user ID to assign as admin:")
    elif query.data == 'assign_super_admin' and is_super_admin(user_id):
        context.user_data['admin_action'] = 'assign_super_admin'
        await query.edit_message_text("Send the Telegram user ID to assign as super admin:")
    elif query.data == 'delete_admin' and is_super_admin(user_id):
        context.user_data['admin_action'] = 'delete_admin'
        await query.edit_message_text("Send the Telegram user ID to delete as admin:")
    elif query.data == 'delete_super_admin' and is_super_admin(user_id):
        context.user_data['admin_action'] = 'delete_super_admin'
        await query.edit_message_text("Send the Telegram user ID to delete as super admin:")

async def admin_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    action = context.user_data.get('admin_action')
    if not is_admin(user_id):
        await update.message.reply_text("You are not an admin.")
        return
    if action == 'broadcast':
        msg = update.message.text
        all_telegram_ids = get_all_telegram_ids()
        for uid in all_telegram_ids:
            try:
                await context.bot.send_message(chat_id=uid, text=msg)
            except Exception as e:
                print(f"Could not send message to {uid}: {e}")
        await update.message.reply_text("Broadcast sent to all registered users.")
        context.user_data['admin_action'] = None
    elif action == 'set_general_link' and is_super_admin(user_id):
        link = update.message.text
        set_link("General", "", link)
        await update.message.reply_text("General unit link set.")
        context.user_data['admin_action'] = None
    elif action.startswith('set_link_'):
        subunit = action.split('_', 2)[2]
        link = update.message.text
        set_link("Subunit", subunit, link)
        await update.message.reply_text(f"Link for {subunit} set.")
        context.user_data['admin_action'] = None
    elif action == 'assign_admin' and is_super_admin(user_id):
        new_admin = update.message.text.strip()
        add_admin(new_admin)
        await update.message.reply_text(f"User {new_admin} is now an admin.")
        context.user_data['admin_action'] = None
    elif action == 'assign_super_admin' and is_super_admin(user_id):
        new_super = update.message.text.strip()
        add_super_admin(new_super)
        await update.message.reply_text(f"User {new_super} is now a super admin.")
        context.user_data['admin_action'] = None
    elif action == 'delete_admin' and is_super_admin(user_id):
        target_admin = update.message.text.strip()
        remove_admin(target_admin)
        await update.message.reply_text(f"User {target_admin} is no longer an admin.")
        context.user_data['admin_action'] = None
    elif action == 'delete_super_admin' and is_super_admin(user_id):
        target_super_admin = update.message.text.strip()
        remove_super_admin(target_super_admin)
        await update.message.reply_text(f"User {target_super_admin} is no longer a super admin.")
        context.user_data['admin_action'] = None
    else:
        await update.message.reply_text("Invalid action or state.")

scheduler_send_message = lambda uid, msg: Application.builder().token(BOT_TOKEN).build().bot.send_message(chat_id=uid, text=msg)
scheduler.set_send_message_func(scheduler_send_message)

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    reg_conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AWAITING_SEMESTER: [CallbackQueryHandler(semester_choice, pattern=r'^semester_')],
            AWAITING_REGISTERED_ALPHA: [CallbackQueryHandler(registered_alpha_choice, pattern=r'^registered_alpha_')],
            REG_FIELD_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_handler)],
            AWAITING_GENDER: [CallbackQueryHandler(handle_inline_keyboard_input, pattern=r'^GENDER_')],
            AWAITING_COLLEGE: [CallbackQueryHandler(handle_inline_keyboard_input, pattern=r'^COLLEGE_')],
            AWAITING_SUBUNIT: [CallbackQueryHandler(handle_inline_keyboard_input, pattern=r'^SUBUNIT_')],
            AWAITING_CONTACT: [MessageHandler(filters.CONTACT, contact_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(reg_conv)
    app.add_handler(CommandHandler('admin', admin_panel))
    app.add_handler(CallbackQueryHandler(admin_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_text_handler))

    app.run_polling()

if __name__ == '__main__':
    main()