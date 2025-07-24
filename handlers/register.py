from services.buttons import *
from configuration.utils import *
from services.service import *
from configuration.config import user_state


@bot.message_handler(commands=['start'])
def start(message):
    user_state.pop(message.from_user.id, None)
    user_id = message.from_user.id
    try:
        user = get_user(user_id)
        if user:
            bot.send_message(user_id, 'MENU: ', reply_markup=main_menu(user_id, user.language))
        else:
            bot.send_message(user_id, '\n🇺🇿 O\'zbek tili\n🇷🇺 Русский\n🇬🇧 English ', reply_markup=get_language())
    except Exception as e:
        print(f"[ERROR start] {e}")
        bot.send_message(user_id, "Произошла ошибка. Попробуйте позже.")


@bot.callback_query_handler(func=lambda call: call.data in ['uz', 'ru', 'en'])
def hello(call):
    user_state[call.from_user.id] = 'awaiting_lang'
    user_id = call.from_user.id
    try:
        language = call.data
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, lang['policy_of_confident'][language], reply_markup=agree(language))
        bot.register_next_step_handler_by_chat_id(user_id, get_user_agree, language)
    except Exception as e:
        print(f"[ERROR hello] {e}")
        bot.send_message(user_id, "Произошла ошибка при выборе языка.")

@safe_step
def get_user_agree(message, language):
    user_state['message.from_user.id'] = 'awaiting_agree'
    user_id = message.from_user.id
    if message.text.lower() == '✅ подтвердить' or message.text.lower() == '✅ agree' or message.text.lower() == '✅ qabul qilish':
        bot.send_message(user_id, lang['name'][language], reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_user_name, language)
    else:
        bot.send_message(user_id, lang['policy_of_confident'][language], reply_markup=agree(language))
        bot.register_next_step_handler(message, get_user_agree, language)

@safe_step
def get_user_name(message, language):
    user_state[message.from_user.id] = 'awaiting_name'
    user_id = message.from_user.id
    if message.text.isdigit():
        bot.send_message(user_id, lang['digit'][language])
        bot.register_next_step_handler(message, get_user_name, language)
    else:
        name = message.text
        bot.send_message(user_id, lang['role'][language], reply_markup=get_role_keyboard(language))
        bot.register_next_step_handler(message, get_user_role, name, language)

@safe_step
def get_user_role(message, name, language):
    user_state[message.from_user.id] = 'awaiting_role'
    user_id = message.from_user.id
    role = message.text.lower()
    print(role)
    valid_roles = ['👨‍🔧 arizachi', '🏢 ish beruvchi', '👨‍🔧 соискатель', '🏢 работодатель','👨‍🔧 seeker', '🏢 employer']
    if role not in valid_roles:
        bot.send_message(user_id, lang['role_error'][language], reply_markup=get_role_keyboard(language))
        bot.register_next_step_handler(message, get_user_role, name, language)
    else:
        bot.send_message(user_id, lang['phone'][language], reply_markup=get_phone(language))
        bot.register_next_step_handler(message, get_user_phone, name, role, language)

@safe_step
def get_user_phone(message, name, role, language):
    user_state[message.from_user.id] = 'awaiting_phone'
    user_id = message.from_user.id
    if message.contact:
        phone = message.contact.phone_number
        if role == '🏢 работодатель' or role == '🏢 ish beruvchi' or role == '🏢 employer':
            try:
                user_name = message.from_user.username
                create_user(user_id, f'@{user_name}', name, f'+{phone}', language, role = role,
                            latitude = None, longitude = None, prefered_radius = None)
                bot.send_message(user_id, lang['create_user'][language], reply_markup=ReplyKeyboardRemove())
                bot.send_message(user_id, 'MENU', reply_markup=main_menu(user_id, language))
            except Exception as e:
                print(f"[ERROR create_user] {e}")
                bot.send_message(user_id, "Произошла ошибка при создании пользователя.")
                bot.register_next_step_handler(message, get_user_phone, name, role, language)

        else:
            bot.send_message(user_id, lang['location'][language], reply_markup=ReplyKeyboardRemove())

            bot.register_next_step_handler(
            message,
            get_user_location,
            name, role, phone, language
        )
    else:
        bot.send_message(user_id, lang['phone_error'][language], reply_markup=get_phone(language))
        bot.register_next_step_handler(message, get_user_phone, name, role, language)
@safe_step
def get_user_location(message, name, role, phone, language):
    user_state[message.from_user.id] = 'awaiting_location'
    user_id = message.from_user.id
    if message.location:
        latitude = message.location.latitude
        longitude = message.location.longitude
        bot.send_message(user_id, lang['radius'][language], reply_markup=get_radius(language))
        bot.register_next_step_handler(message,get_user_radius, name, role, phone, latitude, longitude, language)
    else:
        bot.send_message(user_id, lang['location_error'][language])
        bot.register_next_step_handler(message,get_user_location,name, role, phone, language)

@safe_step
def get_user_radius(message, name, role, phone, latitude, longitude, language):
    user_state[message.from_user.id] = 'awaiting_radius'
    user_id = message.from_user.id
    prefered_radius = {'1000m': 1000, '5000m': 5000, '10000m': 10000, lang['all_vacancies'][language]: None}
    text = message.text
    allowed = ['1000m', '5000m', '10000m', lang['all_vacancies'][language]]
    if text in allowed:
        radius = text
        raw_username = message.from_user.username
        user_name = f"@{raw_username}" if raw_username else ""
        create_user(user_id, user_name, name, f'+{phone}', language, latitude, longitude, role, prefered_radius[radius])
        bot.send_message(user_id, lang['create_user'][language], reply_markup=ReplyKeyboardRemove())
        bot.send_message(user_id, 'MENU: ', reply_markup=main_menu(user_id, language))
    else:
        bot.send_message(user_id, lang['radius_error'][language])
        bot.register_next_step_handler(message, get_user_radius, name, role, phone, latitude, longitude, language)
