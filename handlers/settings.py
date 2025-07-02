from handlers.register import *
from services.buttons import *
from services.service import *

@bot.callback_query_handler(func=lambda call: call.data in [
    'edit_profile', 'change_language', 'change_radius', 'switch_role',
    'change_uz', 'change_ru', 'change_en'
])
def unified_settings_handler(call):
    user_id = call.from_user.id
    user = get_user(user_id)
    data = call.data

    # Смена языка
    if data == 'change_language':
        bot.send_message(user_id, lang['change_language'][user.language], reply_markup=change_language())
        return

    # Применение выбранного языка
    if data in ['change_uz', 'change_ru', 'change_en']:
        language_map = {
            'change_uz': 'uz',
            'change_ru': 'ru',
            'change_en': 'en'
        }
        new_lang = language_map[data]
        update_user_field(user_id, language=new_lang)
        bot.answer_callback_query(call.id, text=lang['successfully_changed'][new_lang])
        bot.send_message(user_id, lang['successfully_changed'][new_lang], reply_markup=main_menu(user_id, new_lang))
        return

    # Смена радиуса
    if data == 'change_radius':
        bot.send_message(user_id, lang['change_radius'][user.language], reply_markup=get_radius(user.language))
        bot.register_next_step_handler_by_chat_id(user_id, handle_radius_change, user)
        return

    # Смена роли
    if data == 'switch_role':
        bot.send_message(user_id, lang['switch_role'][user.language], reply_markup=get_role_keyboard(user.language))
        bot.register_next_step_handler_by_chat_id(user_id, handle_role_change, user)
        return

    # Редактировать имя
    if data == 'edit_profile':
        language = user.language
        bot.send_message(user_id, lang['change_name'][user.language], reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler_by_chat_id(user_id, get_user_name, language)
        return


def handle_radius_change(message, user):
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
    role = message.text.lower()
    valid_roles = [
        '👨‍🔧 соискатель', '🏢 работодатель',
        '👨‍🔧 arizachi', '🏢 ish beruvchi'
    ]

    if role not in valid_roles:
        bot.send_message(message.chat.id, lang['role_error'][user.language], reply_markup=get_role_keyboard(user.language))
        bot.register_next_step_handler(message, handle_role_change, user)
    else:
        update_user_field(user.tg_id, role=role)
        bot.send_message(message.chat.id, lang['successfully_changed'][user.language], reply_markup=main_menu(user.tg_id, user.language))
