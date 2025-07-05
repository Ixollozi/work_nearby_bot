from handlers.register import *
from services.buttons import *
from services.service import *

@bot.callback_query_handler(func=lambda call: call.data in [
    'edit_profile', 'change_language', 'change_radius', 'switch_role',
    'change_uz', 'change_ru', 'change_en'
])
def unified_settings_handler(call):
    user_state[call.from_user.id] = 'awaiting_unified_settings_handler'
    user_id = call.from_user.id
    user = get_user(user_id)
    data = call.data

    if data == 'change_language':
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, lang['change_language'][user.language], reply_markup=change_language())
        return


    if data in ['change_uz', 'change_ru', 'change_en']:
        language_map = {
            'change_uz': 'uz',
            'change_ru': 'ru',
            'change_en': 'en'
        }
        new_lang = language_map[data]
        update_user_field(user_id, language=new_lang)
        bot.answer_callback_query(call.id, text=lang['successfully_changed'][new_lang])
        bot.send_message(user_id, lang['successfully_changed'][new_lang], reply_markup=ReplyKeyboardRemove())
        bot.send_message(user_id, 'MENU', reply_markup=main_menu(user_id, new_lang))
        return

    # Смена радиуса
    if data == 'change_radius':
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, lang['change_radius'][user.language], reply_markup=get_radius(user.language))
        bot.register_next_step_handler_by_chat_id(user_id, handle_radius_change, user)
        return

    if data == 'switch_role':
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, lang['switch_role'][user.language], reply_markup=get_role_keyboard(user.language))
        bot.register_next_step_handler_by_chat_id(user_id, handle_role_change, user)
        return

    if data == 'edit_profile':
        bot.delete_message(user_id, call.message.message_id)
        language = user.language
        bot.send_message(user_id, lang['change_name'][language], reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler_by_chat_id(user_id, get_user_name_edit, language)
        return


def handle_radius_change(message, user):
    user_state[message.from_user.id] = 'awaiting_radius_change'
    text = message.text
    radius_map = {
        '1000m': 1000,
        '5000m': 5000,
        '10000m': 10000,
        lang['all_vacancies'][user.language]: None
    }

    if text in radius_map:
        update_user_field(user.tg_id, prefered_radius=radius_map[text])
        bot.send_message(message.chat.id, lang['successfully_changed'][user.language], reply_markup=main_menu(user.tg_id, user.language))
    else:
        bot.send_message(message.chat.id, lang['radius_error'][user.language])
        bot.register_next_step_handler(message, handle_radius_change, user)


def handle_role_change(message, user):
    user_state[message.from_user.id] = 'awaiting_role_change'
    role = message.text.lower()
    valid_roles = [
        '👨‍🔧 соискатель', '🏢 работодатель',
        '👨‍🔧 seeker', '🏢 employer',
        '👨‍🔧 arizachi', '🏢 ish beruvchi'
    ]

    if role not in valid_roles:
        bot.send_message(message.chat.id, lang['role_error'][user.language], reply_markup=get_role_keyboard(user.language))
        bot.register_next_step_handler(message, handle_role_change, user)
    else:
        update_user_field(user.tg_id, role=role)
        bot.send_message(message.chat.id, lang['successfully_changed'][user.language], reply_markup=main_menu(user.tg_id, user.language))


@safe_step
def get_user_name_edit(message, language):
    user_state[message.from_user.id] = 'awaiting_user_name_edit'
    user_id = message.from_user.id
    if message.text.isdigit():
        bot.send_message(user_id, lang['digit'][language])
        bot.register_next_step_handler(message, get_user_name_edit, language)
    else:
        name = message.text
        bot.send_message(user_id, lang['role'][language], reply_markup=get_role_keyboard(language))
        bot.register_next_step_handler(message, get_user_role_edit, name, language)

@safe_step
def get_user_role_edit(message, name, language):
    user_state[message.from_user.id] = 'awaiting_user_role_edit'
    user_id = message.from_user.id
    role = message.text.lower()
    valid_roles = ['👨‍🔧 arizachi', '🏢 ish beruvchi', '👨‍🔧 соискатель', '🏢 работодатель']
    if role not in valid_roles:
        bot.send_message(user_id, lang['role_error'][language], reply_markup=get_role_keyboard(language))
        bot.register_next_step_handler(message, get_user_role_edit, name, language)
    else:
        bot.send_message(user_id, lang['phone'][language], reply_markup=get_phone(language))
        bot.register_next_step_handler(message, get_user_phone_edit, name, role, language)

@safe_step
def get_user_phone_edit(message, name, role, language):
    user_state[message.from_user.id] = 'awaiting_user_phone_edit'
    user_id = message.from_user.id
    if message.contact:
        phone = message.contact.phone_number
        if role == '🏢 работодатель' or role == '🏢 ish beruvchi':
            try:
                user_name = message.from_user.username
                update_user_field(user_id,
                                username=f'@{user_name}',
                                name=name,
                                phone=f'+{phone}',
                                language=language,
                                role=role,
                                latitude=None,
                                longitude=None,
                                prefered_radius=None)
                bot.send_message(user_id, lang['successfully_changed'][language], reply_markup=ReplyKeyboardRemove())
                bot.send_message(user_id, 'MENU', reply_markup=main_menu(user_id, language))
            except Exception as e:
                print(f"[ERROR update_user] {e}")
                bot.send_message(user_id, "Произошла ошибка при обновлении пользователя.")
                bot.register_next_step_handler(message, get_user_phone_edit, name, role, language)
        else:
            bot.send_message(user_id, lang['location'][language], reply_markup=ReplyKeyboardRemove())
            bot.register_next_step_handler(message, get_user_location_edit, name, role, phone, language)
    else:
        bot.send_message(user_id, lang['phone_error'][language], reply_markup=get_phone(language))
        bot.register_next_step_handler(message, get_user_phone_edit, name, role, language)

@safe_step
def get_user_location_edit(message, name, role, phone, language):
    user_state[message.from_user.id] = 'awaiting_user_location_edit'
    user_id = message.from_user.id
    if message.location:
        latitude = message.location.latitude
        longitude = message.location.longitude
        bot.send_message(user_id, lang['radius'][language], reply_markup=get_radius(language))
        bot.register_next_step_handler(message, get_user_radius_edit, name, role, phone, latitude, longitude, language)
    else:
        bot.send_message(user_id, lang['location_error'][language])
        bot.register_next_step_handler(message, get_user_location_edit, name, role, phone, language)

@safe_step
def get_user_radius_edit(message, name, role, phone, latitude, longitude, language):
    user_state[message.from_user.id] = 'awaiting_user_radius_edit'
    user_id = message.from_user.id
    prefered_radius = {'1000m': 1000, '5000m': 5000, '10000m': 10000, lang['all_vacancies'][language]: None}
    text = message.text
    allowed = ['1000m', '5000m', '10000m', lang['all_vacancies'][language]]
    if text in allowed:
        radius = text
        user_name = message.from_user.username or ''
        update_user_field(user_id,
                        username=f'@{user_name}',
                        name=name,
                        phone=f'+{phone}',
                        language=language,
                        latitude=latitude,
                        longitude=longitude,
                        role=role,
                        prefered_radius=prefered_radius[radius])
        bot.send_message(user_id, lang['successfully_changed'][language], reply_markup=ReplyKeyboardRemove())
        bot.send_message(user_id, 'MENU: ', reply_markup=main_menu(user_id, language))
    else:
        bot.send_message(user_id, lang['radius_error'][language])
        bot.register_next_step_handler(message, get_user_radius_edit, name, role, phone, latitude, longitude, language)