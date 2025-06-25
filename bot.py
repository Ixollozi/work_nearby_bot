import telebot
from buttons import *
from all_txt import lang
from service import *
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from datetime import datetime, timedelta, timezone

bot = telebot.TeleBot('7835900288:AAFS_WFHUkk-MQsDed8m2itlYjsijuS-odQ')
ADMINS = [385688612]
CATEGORIES = ['Разработка и IT', 'Дизайн', 'Маркетинг', 'Продажи', 'Сопровождение', 'Другое']
chat_pages = {}
user_create_job_data = {}


############################## registration ##############################
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    try:
        user = get_user(user_id)
        if user:
            bot.send_message(user_id, 'MENU: ', reply_markup=main_menu(user_id, user.language))
        else:
            bot.send_message(user_id, '\n🇺🇿 O\'zbek tili\n🇷🇺 Русский ', reply_markup=get_language())
    except Exception as e:
        print(f"[ERROR start] {e}")
        bot.send_message(user_id, "Произошла ошибка. Попробуйте позже.")


@bot.callback_query_handler(func=lambda call: call.data in ['uz', 'ru'])
def hello(call):
    user_id = call.from_user.id
    try:
        language = call.data
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, lang['hello'][language])
        bot.register_next_step_handler_by_chat_id(user_id, get_user_name, language)
    except Exception as e:
        print(f"[ERROR hello] {e}")
        bot.send_message(user_id, "Произошла ошибка при выборе языка.")


def get_user_name(message, language):
    user_id = message.from_user.id
    try:
        if message.text.isdigit():
            bot.send_message(user_id, lang['digit'][language])
            bot.register_next_step_handler(message, get_user_name, language)
        else:
            name = message.text
            bot.send_message(user_id, lang['role'][language], reply_markup=get_role(language))
            bot.register_next_step_handler(message, get_user_role, name, language)
    except Exception as e:
        print(f"[ERROR get_user_name] {e}")
        bot.send_message(user_id, "Ошибка при вводе имени.")
        bot.register_next_step_handler(message, get_user_name, language)


def get_user_role(message, name, language):
    user_id = message.from_user.id
    try:
        role = message.text.lower()
        valid_roles = ['искатель', 'работодатель', 'ish izlovchi', 'ish beruvchi']
        if role not in valid_roles:
            bot.send_message(user_id, lang['role_error'][language], reply_markup=get_role(language))
            bot.register_next_step_handler(message, get_user_role, name, language)
        else:
            bot.send_message(user_id, lang['phone'][language], reply_markup=get_phone(language))
            bot.register_next_step_handler(message, get_user_phone, name, role, language)
    except Exception as e:
        print(f"[ERROR get_user_role] {e}")
        bot.send_message(user_id, "Ошибка при выборе роли.")
        bot.register_next_step_handler(message, get_user_role, name, language)


def get_user_phone(message, name, role, language):
    user_id = message.from_user.id
    try:
        print(message.contact)
        if message.contact:
            phone = message.contact.phone_number
            bot.send_message(user_id, lang['location'][language], reply_markup=ReplyKeyboardRemove())
            bot.register_next_step_handler(message, get_user_location, name, phone, language, role)
        else:
            bot.send_message(user_id, lang['phone_error'][language], reply_markup=get_phone(language))
            bot.register_next_step_handler(message, get_user_phone, name, role, language)
    except Exception as e:
        print(f"[ERROR get_user_phone] {e}")
        bot.send_message(user_id, "Ошибка при получении номера телефона.")
        bot.register_next_step_handler(message, get_user_phone, name, role, language)


def get_user_location(message, name, phone, language, role):
    user_id = message.from_user.id
    try:
        if message.location:
            latitude = message.location.latitude
            longitude = message.location.longitude
            bot.send_message(user_id, lang['radius'][language], reply_markup=get_radius(language))
            bot.register_next_step_handler(message, get_user_radius, name, role, phone, latitude, longitude, language)
        else:
            bot.send_message(user_id, "Пожалуйста, отправьте геолокацию.")
            bot.register_next_step_handler(message, get_user_location, name, phone, language, role)
    except Exception as e:
        print(f"[ERROR get_user_location] {e}")
        bot.send_message(user_id, "Ошибка при получении локации.")
        bot.register_next_step_handler(message, get_user_location, name, phone, language, role)


def get_user_radius(message, name, role, phone, latitude, longitude, language):
    user_id = message.from_user.id
    try:
        text = message.text
        allowed = ['1000m', '5000m', '10000m', lang['all_vacancies'][language]]
        if text in allowed:
            radius = text
            user_name = message.from_user.username or ''
            create_user(user_id, f'@{user_name}', name, f'+{phone}', language, latitude, longitude, role, radius)
            bot.send_message(user_id, lang['create_user'][language], reply_markup=ReplyKeyboardRemove())
            bot.send_message(user_id, 'MENU: ', reply_markup=main_menu(user_id, language))
        else:
            bot.send_message(user_id, lang['radius_error'][language])
            bot.register_next_step_handler(message, get_user_radius, name, role, phone, latitude, longitude, language)
    except Exception as e:
        print(f"[ERROR get_user_radius] {e}")
        bot.send_message(user_id, "Ошибка при выборе радиуса.")
        bot.register_next_step_handler(message, get_user_radius, name, role, phone, latitude, longitude, language)


######################## admin panel #########################

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    try:
        admin_user = get_admin(user_id)
    except Exception as e:
        print(f"[WARN get_admin] {e}")
        admin_user = None

    if user_id in ADMINS or (admin_user and getattr(admin_user, 'is_admin', False)):
        bot.send_message(message.chat.id, 'Добро пожаловать в админ-панель 👮‍♂️', reply_markup=admin_menu())
        bot.register_next_step_handler(message, handle_admin_menu)
    else:
        bot.send_message(message.chat.id, 'У вас нет доступа к админ-панели.')


def handle_admin_menu(message):
    try:
        if message.text == '📋 Список пользователей':
            chat_id = message.chat.id
            chat_pages[chat_id] = 1
            show_users_page(chat_id, page=1)
            bot.register_next_step_handler(message, handle_admin_menu)

        elif message.text == '⭐️ Все админы ⭐️':
            names = [i.name for i in get_all_admins()]
            if names:
                formatted = '\n'.join(names)
            else:
                formatted = 'Пусто'
            bot.send_message(message.chat.id, f'Список админов:\n{formatted}', reply_markup=admin_menu())
            bot.register_next_step_handler(message, handle_admin_menu)

        elif message.text == '⭐️ Добавить админа':
            bot.send_message(message.chat.id, 'Введите *номер телефона* пользователя (например, +998901234567):',
                             reply_markup=cancel())
            bot.register_next_step_handler(message, add_admin_by_phone)

        elif message.text == '⭐️ Удалить админа':
            bot.send_message(message.chat.id, 'Введите *номер телефона* пользователя (например, +998901234567):',
                             reply_markup=cancel())
            bot.register_next_step_handler(message, remove_admin_by_phone)

        elif message.text == '🗂 Все категории 🗂':
            categories = [i.name for i in get_all_categories()]
            if categories:
                formatted = '\n'.join(categories)
            else:
                formatted = 'Пусто'
            bot.send_message(message.chat.id, f'Список категорий:\n{formatted}', reply_markup=admin_menu())
            bot.register_next_step_handler(message, handle_admin_menu)

        elif message.text == '🗂 Добавить категорию':
            bot.send_message(message.chat.id, 'Введите название категории:', reply_markup=cancel())
            bot.register_next_step_handler(message, add_category)

        elif message.text == '🗂 Удалить категорию':
            bot.send_message(message.chat.id, 'Введите название категории:', reply_markup=cancel())
            bot.register_next_step_handler(message, remove_category)

        elif message.text == '❌ Выход из админки':
            bot.send_message(message.chat.id, 'Вы вышли из админ-панели.',
                             reply_markup=telebot.types.ReplyKeyboardRemove())

        else:
            bot.send_message(message.chat.id, 'Выберите команду из меню.')
            bot.register_next_step_handler(message, handle_admin_menu)
    except Exception as e:
        print(f"[ERROR handle_admin_menu] {e}")
        bot.send_message(message.chat.id, 'Ошибка при работе с админкой.')


def show_users_page(chat_id, page):
    users = get_users_paginated(page=page)
    total_users = count_users()
    total_pages = (total_users + 9) // 10

    if not users:
        bot.send_message(chat_id, "Пользователи не найдены.")
        return

    text = '\n'.join([f'{u.name} | {u.phone}' for u in users])
    text += f"\n\nСтраница {page} из {total_pages}"

    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton("⏮ Назад", callback_data="prev_users"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton("Далее ⏭", callback_data="next_users"))

    markup = InlineKeyboardMarkup()
    markup.row(*buttons)

    bot.send_message(chat_id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ['next_users', 'prev_users'])
def paginate_users(call):
    chat_id = call.message.chat.id
    current_page = chat_pages.get(chat_id, 1)

    if call.data == 'next_users':
        chat_pages[chat_id] = current_page + 1
    elif call.data == 'prev_users':
        chat_pages[chat_id] = max(1, current_page - 1)

    bot.delete_message(chat_id, call.message.message_id)
    show_users_page(chat_id, chat_pages[chat_id])


def add_admin_by_phone(message):
    try:
        phone = message.text.strip()
        if message.text == '❌ Отменить':
            bot.send_message(message.chat.id, 'Вы в админ-панели.', reply_markup=admin_menu())
            bot.register_next_step_handler(message, handle_admin_menu)
            return
        elif not phone.startswith('+'):
            bot.send_message(message.chat.id,
                             'Пожалуйста, введите номер телефона в международном формате, например: +998901234567',
                             reply_markup=cancel())

        user = get_user_by_phone(phone)
        if user:
            user.is_admin = True
            db.commit()
            bot.send_message(message.chat.id, f'Пользователь {user.name} с номером {phone} назначен админом.',
                             reply_markup=admin_menu())
            bot.register_next_step_handler(message, handle_admin_menu)
        else:
            bot.send_message(message.chat.id, f'Пользователь с номером {phone} не найден.')
            bot.register_next_step_handler(message, add_admin_by_phone)
    except Exception as e:
        print(f"[ERROR add_admin_by_phone] {e}")
        bot.send_message(message.chat.id, 'Ошибка при добавлении админа.')


def remove_admin_by_phone(message):
    try:
        phone = message.text.strip()
        if message.text == '❌ Отменить':
            bot.send_message(message.chat.id, 'Вы в админ-панели.', reply_markup=admin_menu())
            bot.register_next_step_handler(message, handle_admin_menu)
            return
        elif not phone.startswith('+'):
            bot.send_message(message.chat.id,
                             'Пожалуйста, введите номер телефона в международном формате, например: +998901234567')

        user = get_user_by_phone(phone)
        if user:
            user.is_admin = False
            db.commit()
            bot.send_message(message.chat.id, f'Пользователь {user.name} с номером {phone} удален из админов.',
                             reply_markup=admin_menu())
            bot.register_next_step_handler(message, handle_admin_menu)
        else:
            bot.send_message(message.chat.id, f'Пользователь с номером {phone} не найден.')
            bot.register_next_step_handler(message, remove_admin_by_phone)
    except Exception as e:
        print(f"[ERROR remove_admin_by_phone] {e}")
        bot.send_message(message.chat.id, 'Ошибка при удалении админа.')


def add_category(message):
    try:
        category_name = message.text.strip()

        if message.text == '❌ Отменить':
            bot.send_message(message.chat.id, 'Вы в админ-панели.', reply_markup=admin_menu())
            bot.register_next_step_handler(message, handle_admin_menu)
            return

        existing_categories = [c.name.lower() for c in get_all_categories()]
        if category_name.lower() in [c.lower() for c in CATEGORIES] or category_name.lower() in existing_categories:
            bot.send_message(message.chat.id, 'Категория уже существует.', reply_markup=admin_menu())
            bot.register_next_step_handler(message, handle_admin_menu)
        else:
            create_category(category_name)
            bot.send_message(message.chat.id, f'Категория "{category_name}" успешно добавлена.',
                             reply_markup=admin_menu())
            bot.register_next_step_handler(message, handle_admin_menu)

    except Exception as e:
        print(f"[ERROR add_category] {e}")
        bot.send_message(message.chat.id, 'Ошибка при добавлении категории.')


def remove_category(message):
    try:
        category_name = message.text.strip()
        if message.text == '❌ Отменить':
            bot.send_message(message.chat.id, 'Вы в админ-панели.', reply_markup=admin_menu())
            bot.register_next_step_handler(message, handle_admin_menu)
        elif category_name not in [c.name for c in get_all_categories()]:
            bot.send_message(message.chat.id, 'Категория не существует.', reply_markup=admin_menu())
            bot.register_next_step_handler(message, handle_admin_menu)
        else:
            delete_category(category_name)
            bot.send_message(message.chat.id, f'Категория "{category_name}" успешно удалена.',
                             reply_markup=admin_menu())
            bot.register_next_step_handler(message, handle_admin_menu)
    except Exception as e:
        print(f"[ERROR remove_category] {e}")


####################################### main menu #######################################

@bot.callback_query_handler(func=lambda call: call.data in ['find_job', 'create_job', 'favorite', 'settings'])
def handle_main_menu(call):
    user_id = call.from_user.id

    try:
        user = get_user(user_id)
        language = user.language if user else 'ru'

        if call.data == 'find_job':
            bot.answer_callback_query(call.id, "Поиск работы...")
            # Здесь добавьте логику поиска работы

        elif call.data == 'create_job':
            bot.answer_callback_query(call.id, "Создание вакансии...")
            bot.send_message(user_id, lang['create_job_name'][language])
            bot.register_next_step_handler_by_chat_id(user_id, create_job_name, language)

        elif call.data == 'favorite':
            bot.answer_callback_query(call.id, "Избранные...")
            # Здесь добавьте логику избранного

        elif call.data == 'settings':
            bot.answer_callback_query(call.id, "Настройки...")
            # Здесь добавьте логику настроек

    except Exception as e:
        print(f"[ERROR handle_main_menu] {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


###################################### create job #######################################

def create_job_name(message, language):
    try:
        if message.text.isdigit():
            bot.send_message(message.chat.id, lang['create_job_name_error'][language])
            bot.register_next_step_handler(message, create_job_name, language)
        else:
            name = message.text
            if len(name) < 10 or len(name) > 50:
                bot.send_message(message.chat.id, lang['create_job_name_len'][language])
                bot.register_next_step_handler(message, create_job_name, language)
            else:
                bot.send_message(message.chat.id, lang['create_job_description'][language])
                bot.register_next_step_handler(message, create_job_description, language, name)
    except Exception as e:
        print(f"[ERROR create_job_name] {e}")
        bot.send_message(message.chat.id, lang['create_job_name_error'][language])
        bot.register_next_step_handler(message, create_job_name, language)


def create_job_description(message, language, name):
    try:
        description = message.text
        user_create_job_data[message.from_user.id] = {
            'language': language,
            'name': name,
            'description': description,
            'currency': None
        }
        if len(description) < 200:
            bot.send_message(message.chat.id, lang['create_job_description_error'][language])
            bot.register_next_step_handler(message, create_job_description, language, name)
        else:
            bot.send_message(message.chat.id, lang['choose_currency'][language],
                             reply_markup=get_currency_keyboard())
    except Exception as e:
        print(f"[ERROR create_job_description] {e}")
        bot.send_message(message.chat.id, lang['create_job_description_error'][language])
        bot.register_next_step_handler(message, create_job_description, language, name)


@bot.callback_query_handler(func=lambda call: call.data.startswith('currency_'))
def handle_currency_selection(call):
    try:
        user_id = call.from_user.id
        currency = call.data.replace('currency_', '')

        user = get_user(user_id)
        language = user.language

        bot.answer_callback_query(call.id, f'{lang["currency_selected"][language]}: {currency}')
        bot.edit_message_text(
            f"{lang['currency_selected'][language]}: {currency}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        data = user_create_job_data.get(user_id)

        if not data:
            bot.send_message(user_id, "Ошибка. Попробуйте заново.")
            return

        data['currency'] = currency

        msg = bot.send_message(user_id, lang['create_job_category'][language])
        bot.register_next_step_handler(msg, create_job_category,
                                       data['language'], data['name'], data['description'], data['currency'])

    except Exception as e:
        print(f"[ERROR handle_currency_selection] {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")



def create_job_category(message, language, name, description, currency):
    try:
        category = message.text.strip()
        print(f"category: {category}")

        existing_categories = [c.name.lower() for c in get_all_categories()]
        predefined_categories = [c.lower() for c in CATEGORIES]

        if category.lower() not in predefined_categories and category.lower() not in existing_categories:
            bot.send_message(message.chat.id, lang['create_job_category_error'][language])
            bot.register_next_step_handler(message, create_job_category, language, name, description, currency)
        else:
            bot.send_message(message.chat.id, lang['create_job_price'][language])
            bot.register_next_step_handler(message, create_job_price, language, name, description, currency, category)
    except Exception as e:
        print(f"[ERROR create_job_category] {e}")
        bot.send_message(message.chat.id, lang['create_job_category_error'][language])
        bot.register_next_step_handler(message, create_job_category, language, name, description, currency)



def create_job_price(message, language, name, description, currency, category):
    user = get_user(message.from_user.id)
    contacts = user.phone if user.username is None else f"{user.phone}, username: {user.username}"

    try:
        price_text = message.text
        if not price_text.isdigit():
            bot.send_message(message.chat.id, lang['create_job_price_error'][language])
            bot.register_next_step_handler(message, create_job_price, language, name, description, currency, category)
        else:
            price = int(price_text)
            payment = f"{price} {currency}"

            create_vacancy(
                user_id=message.from_user.id,
                title=name,
                description=description,
                payment=payment,
                latitude=user.latitude,
                longitude=user.longitude,
                contact=contacts,
                category=category,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7)
            )

            bot.send_message(message.chat.id, "✅ Вакансия успешно создана!")

    except Exception as e:
        print(f"[ERROR create_job_price] {e}")
        bot.register_next_step_handler(message, create_job_price, language, name, description, currency, category)


bot.infinity_polling()