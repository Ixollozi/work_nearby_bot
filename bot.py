import telebot
from buttons import *
from service import *
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from datetime import datetime, timedelta, timezone
from geopy.geocoders import Nominatim

bot = telebot.TeleBot('7981973749:AAE_3acJdzQTfCMsuH9zi46oXtwS_w6Gj5Q')
ADMINS = [385688612]
CATEGORIES = ['Разработка и IT', 'Дизайн', 'Маркетинг', 'Продажи', 'Сопровождение', 'Другое']
chat_pages = {}
user_create_job_data = {}
user_vacancy_index = {}
user_vacancies_list = {}
existing_category_names = [c.name for c in get_all_categories()]
geolocator = Nominatim(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                  "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")

for i in CATEGORIES:
    if i not in existing_category_names:
        create_category(i)

update_user_role(385688612, '👨‍🔧 соискатель')
# update_user_role(385688612, '🏢 работодатель')

update_user_prefered_radius(385688612, 1000)
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
            bot.send_message(user_id, lang['role'][language], reply_markup=get_role_keyboard(language))
            bot.register_next_step_handler(message, get_user_role, name, language)
    except Exception as e:
        print(f"[ERROR get_user_name] {e}")
        bot.send_message(user_id, "Ошибка при вводе имени.")
        bot.register_next_step_handler(message, get_user_name, language)


def get_user_role(message, name, language):
    user_id = message.from_user.id
    try:
        role = message.text.lower()
        print(role)
        valid_roles = ['👨‍🔧 arizachi', '🏢 ish beruvchi', '👨‍🔧 соискатель', '🏢 работодатель']
        if role not in valid_roles:
            bot.send_message(user_id, lang['role_error'][language], reply_markup=get_role_keyboard(language))
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

            if role == '🏢 работодатель' or role == '🏢 ish beruvchi':
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
                    return


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
    except Exception as e:
        print(f"[ERROR get_user_phone] {e}")
        bot.send_message(user_id, "Ошибка при получении номера телефона.")
        bot.register_next_step_handler(message, get_user_phone, name, role, language)

def get_user_location(message, name, role, phone, language):
    user_id = message.from_user.id
    try:
        if message.location:
            latitude = message.location.latitude
            longitude = message.location.longitude
            bot.send_message(user_id, lang['radius'][language], reply_markup=get_radius(language))
            bot.register_next_step_handler(
                message,
                get_user_radius,
                name, role, phone, latitude, longitude, language
            )
        else:
            bot.send_message(user_id, lang['location_error'][language])
            bot.register_next_step_handler(
                message,
                get_user_location,
                name, role, phone, language
            )
    except Exception as e:
        print(f"[ERROR get_user_location] {e}")
        bot.send_message(user_id, lang['location_error'][language])
        bot.register_next_step_handler(
            message,
            get_user_location,
            name, role, phone, language
        )

def get_user_radius(message, name, role, phone, latitude, longitude, language):
    user_id = message.from_user.id
    prefered_radius = {
        '1000m': 1000,
        '5000m': 5000,
        '10000m': 10000,
        lang['all_vacancies'][language]: None}
    try:
        text = message.text
        allowed = ['1000m', '5000m', '10000m', lang['all_vacancies'][language]]
        if text in allowed:
            radius = text
            user_name = message.from_user.username or ''
            create_user(user_id, f'@{user_name}', name, f'+{phone}', language, latitude, longitude, role, prefered_radius[radius])
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

@bot.callback_query_handler(func=lambda call: call.data in
    ['find_job', 'create_job', 'favorite','settings', 'my_vacancy','category','create','delete', 'main_menu'])
def handle_main_menu(call):
    user_id = call.from_user.id
    try:
        user = get_user(user_id)
        language = user.language if user else 'ru'

        categories = get_user_categories(user_id)
        category_names = [c.name for c in categories]
        msg_text = {
            'ru': f'Ваш выбор поиска по категориям:\n' + '\n'.join(category_names) if category_names else 'Вы не выбрали ни одной категории.',
            'en': f'Your selected job categories:\n' + '\n'.join(category_names) if category_names else 'You have not selected any categories.',
            'uz': f'Siz tanlagan ish kategoriyalari:\n' + '\n'.join(category_names) if category_names else 'Siz hali hech qanday kategoriya tanlamagansiz.'
        }

        vacancy = get_user_vacancies(user_id)
        vacancy_names = [v.title for v in vacancy]
        user_vac_text = {
            'ru': f'Ваши вакансии:\n' + '\n'.join(vacancy_names) if vacancy_names else 'Пусто.',
            'en': f'Your vacancies:\n' + '\n'.join(vacancy_names) if vacancy_names else 'Empty.',
            'uz': f'Sizning vakansiyalaringiz:\n' + '\n'.join(vacancy_names) if vacancy_names else 'Bo‘sh.'
        }
        favorites_raw = get_favorites(user_id)
        vacancy_ids = [f.vacancy_id for f in favorites_raw]

        vacancies = []
        for vid in vacancy_ids:
            v = get_vacancy_by_id(vid)
            if v:
                vacancies.append(v)

        if vacancies:
            titles = [v.title for v in vacancies]
            user_fav = {
                'ru': 'Ваши избранные:\n' + '\n'.join(titles),
                'en': 'Your favorites:\n' + '\n'.join(titles),
                'uz': 'Sizning tanlanganlaringiz:\n' + '\n'.join(titles)
            }
        else:
            user_fav = {
                'ru': 'Пусто.',
                'en': 'Empty.',
                'uz': 'Bo‘sh.'
            }

        if call.data == 'find_job':
            bot.answer_callback_query(call.id, "Поиск работы...")
            user = get_user(user_id)
            language = user.language
            categories = [c.name for c in get_user_categories(user_id)]

            if not categories:
                bot.send_message(user_id, lang['choose_category'][language], reply_markup=category_keyboard(language))
                bot.register_next_step_handler_by_chat_id(user_id, choose_category, language, 'add')
                return

            radius = user.prefered_radius
            print(radius)
            if radius is None:
                radius = lang['all_vacancies'][language]

            # Получаем список вакансий
            vacancies_with_distance = get_vacancies_nearby(
                user.latitude,
                user.longitude,
                radius_meters=radius,
                categories=categories
            )

            if not vacancies_with_distance:
                bot.send_message(user_id, lang['no_vacancy'][language], reply_markup=main_menu(user_id, language))
                return

            # Сохраняем состояние
            user_vacancies_list[user_id] = vacancies_with_distance
            user_vacancy_index[user_id] = 0

            # Показываем первую вакансию
            show_current_vacancy(bot, user_id, language)

        elif call.data == 'create_job':
            bot.answer_callback_query(call.id, "Создание вакансии...")
            bot.send_message(user_id, lang['create_job_name'][language])
            bot.register_next_step_handler_by_chat_id(user_id, create_job_name, language)

        elif call.data == 'favorite':
            bot.answer_callback_query(call.id, "Избранные...")
            bot.send_message(user_id, user_fav[language], reply_markup=create_or_delete(language, 'favorite'))

        elif call.data == 'settings':
            bot.answer_callback_query(call.id, "Настройки...")

        elif call.data == 'my_vacancy':
            bot.answer_callback_query(call.id, "Мои вакансии...")
            bot.send_message(user_id, user_vac_text[language], reply_markup=create_or_delete(language, 'vacancy'))

        elif call.data == 'category':
            bot.answer_callback_query(call.id, "Выберите категорию...")
            bot.send_message(user_id, msg_text[language], reply_markup=create_or_delete(language, 'category'))

        elif call.data == 'create':
            bot.answer_callback_query(call.id, "Добавление категории...")
            bot.send_message(user_id, lang['choose_category'][language], reply_markup=category_keyboard(language))
            bot.register_next_step_handler_by_chat_id(user_id, lambda msg: choose_category(msg, language, 'add'))

        elif call.data == 'delete':
            bot.answer_callback_query(call.id, "Удаление категории...")
            bot.send_message(user_id, lang['del_category'][language], reply_markup=category_keyboard(language))
            bot.register_next_step_handler_by_chat_id(user_id, lambda msg: choose_category(msg, language, 'delete'))

        elif call.data == 'main_menu':
            bot.answer_callback_query(call.id, "Главное меню...")
            bot.send_message(user_id, 'MENU', reply_markup=main_menu(user_id, language))

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
        if len(description) < 200 or len(description) > 1000:
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

        msg = bot.send_message(user_id, lang['create_job_price'][language])
        bot.register_next_step_handler(msg, create_job_price,
                                       data['language'], data['name'], data['description'], data['currency'])

    except Exception as e:
        print(f"[ERROR handle_currency_selection] {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


def create_job_price(message, language, name, description, currency):
    user = get_user(message.from_user.id)
    contacts = user.phone if user.username is None else f"{user.phone}, username: {user.username}"

    try:
        price_text = message.text
        if not price_text.isdigit():
            bot.send_message(message.chat.id, lang['create_job_price_error'][language])
            bot.register_next_step_handler(message, create_job_price, language, name, description, currency)
        else:
            price = int(price_text)
            payment = f"{price} {currency}"

            # Сохраняем текущие данные
            user_create_job_data[message.from_user.id] = {
                'language': language,
                'name': name,
                'description': description,
                'currency': currency,
                'price': payment,
                'contacts': contacts
            }

            bot.send_message(message.chat.id, lang['location_for_job'][language])
            bot.register_next_step_handler(message, create_job_location, language, name, description, currency, payment, contacts)

    except Exception as e:
        print(f"[ERROR create_job_price] {e}")
        bot.register_next_step_handler(message, create_job_price, language, name, description, currency)

def create_job_location(message, language, name, description, currency, payment, contacts):
    try:
        if message.location:
            latitude = message.location.latitude
            longitude = message.location.longitude
            location = geolocator.reverse(f"{latitude}, {longitude}", language=language)
            update_user_location(message.from_user.id, latitude, longitude)

            bot.send_message(message.chat.id, lang['create_job_category'][language], reply_markup=category_keyboard(language))
            bot.register_next_step_handler(message, create_job_category, language, name, description, currency, payment, contacts, location)
        else:
            bot.send_message(message.chat.id, lang['location_error'][language])
            bot.register_next_step_handler(message, create_job_location, language, name, description, currency, payment, contacts)

    except Exception as e:
        print(f"[ERROR create_job_location] {e}")
        bot.send_message(message.chat.id, lang['create_job_location_error'][language])
        bot.register_next_step_handler(message, create_job_location, language, name, description, currency, payment, contacts)

def create_job_category(message, language, name, description, currency, payment, contacts, location):
    try:
        category = message.text.strip()
        existing_categories = [c.name.lower() for c in get_all_categories()]
        predefined_categories = [c.lower() for c in CATEGORIES]

        if category.lower() not in predefined_categories and category.lower() not in existing_categories:
            bot.send_message(message.chat.id, lang['create_job_category_error'][language])
            bot.register_next_step_handler(message, create_job_category, language, name, description, currency, payment, contacts)
        else:
            user_create_job_data[message.from_user.id]['category'] = category

            data = user_create_job_data.get(message.from_user.id)

            text = {
                'ru': f"Вы уверены, что хотите создать вакансию:\n"
                      f"📌 Название: {data['name']}\n"
                      f"📝 Описание:\n {data['description']}\n"
                      f"💰 Заработная плата: {data['price']}\n"
                      f"📂 Категория: {data['category']}\n"
                      f'📍 Местоположение: {location.address}\n'
                      f"📞 Контакты: {data['contacts']}",
                'uz': f"Ish vakansiyasini yaratmoqchimisiz:\n"
                      f"📌 Nomi: {data['name']}\n"
                      f"📝 Tavsif:\n {data['description']}\n"
                      f"💰 To‘lov: {data['price']}\n"
                      f"📂 Kategoriya: {data['category']}\n"
                      f'📍 Manzil: {location.address}\n'
                      f"📞 Kontaktlar: {data['contacts']}",
                'en': f"Are you sure you want to create this job posting:\n"
                      f"📌 Title: {data['name']}\n"
                      f"📝 Description:\n {data['description']}\n"
                      f"💰 Salary: {data['price']}\n"
                      f"📂 Category: {data['category']}\n"
                      f'📍 Location: {location.address}\n'
                      f"📞 Contacts: {data['contacts']}"
            }

            bot.send_message(message.chat.id, text[language], reply_markup=agree(language))
            bot.register_next_step_handler(message, agree_job, language, name, description, currency, category, payment, contacts)

    except Exception as e:
        print(f"[ERROR create_job_category] {e}")
        bot.send_message(message.chat.id, lang['create_job_category_error'][language])
        bot.register_next_step_handler(message, create_job_category, language, name, description, currency, payment, contacts)


def agree_job(message, language, name, description, currency, category, payment, contacts):
    user = get_user(message.from_user.id)
    try:
        if message.text == '❌ Отменить':
            bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
        else:
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

            bot.send_message(message.chat.id, lang['create_job_agree'][language], reply_markup=ReplyKeyboardRemove())
            bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
    except Exception as e:
        print(f"[ERROR agree_job] {e}")
        bot.send_message(message.chat.id, lang['create_job_agree_error'][language])
        bot.register_next_step_handler(message, agree_job, language, name, description, currency, category, payment, contacts)
#################################### favorites ########################################
@bot.callback_query_handler(func=lambda call: call.data in ['favorite_create', 'favorite_delete'])
def favorites(call):
    user_id = call.from_user.id
    user = get_user(user_id)
    language = user.language
    if call.data == 'favorite_create':
        bot.send_message(call.message.chat.id, lang['create_favorites'][language], reply_markup=main_menu(user_id, language))
    elif call.data == 'favorite_delete':
        bot.send_message(call.message.chat.id, lang['delete_favorites'][language], reply_markup=delete_favorite_kb(user_id))
        bot.register_next_step_handler(call.message, delete_favorite, language)


def delete_favorite(message, language):
    favorite_name = message.text
    vacancy = get_vacancy_by_title(favorite_name)
    try:
        if favorite_name == '❌ Отменить':
            bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
            return

        success = delete_user_favorite(user_id=message.from_user.id, vacancy_id=vacancy.id)
        if success:
            bot.send_message(message.chat.id, lang['delete_favorite_success'][language], reply_markup=main_menu(message.from_user.id, language))
        else:
            bot.send_message(message.chat.id, lang['delete_favorite_error'][language])
            bot.register_next_step_handler(message, delete_favorite, language)

    except Exception as e:
        print(f"[ERROR delete_favorite] {e}")
        bot.send_message(message.chat.id, lang['delete_favorite_error'][language])
        bot.register_next_step_handler(message, delete_favorite, language)
####################################### find job ########################################

def show_current_vacancy(bot, user_id, language):
    index = user_vacancy_index.get(user_id, 0)
    vacancies = user_vacancies_list.get(user_id)

    if not vacancies or index >= len(vacancies):
        bot.send_message(user_id, lang['no_vacancy'][language], reply_markup=main_menu(user_id, language))
        return

    vacancy, distance = vacancies[index]
    distance = get_user(user_id)
    if distance.prefered_radius is not None and distance.prefered_radius > 0:
        distance_text = f"{int(distance.prefered_radius)} м"
    else:
        distance_text = lang['all_vacancies'][language]

    text = {
        'ru': f"📌 {vacancy.title}\n\n"
              f"📝 {vacancy.description}...\n\n"
              f"💰 {vacancy.payment}\n"
              f"📍 Расстояние: {distance_text}\n"
              f"📞 {vacancy.contact}",
        'uz': f"📌 {vacancy.title}\n\n"
              f"📝 {vacancy.description}...\n\n"
              f"💰 {vacancy.payment}\n"
              f"📍 Masofa: {distance_text}\n"
              f" 📞 {vacancy.contact}",
        'en': f"📌 {vacancy.title}\n\n"
              f"📝 {vacancy.description}...\n\n"
              f"💰 {vacancy.payment}\n"
              f"📍 Distance: {distance_text}\n"
              f" 📞 {vacancy.contact}"
    }

    markup = get_vacancy_keyboard(language)
    msg = bot.send_message(user_id, text[language], reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ['next_vacancy', 'add_to_favorite', 'respond', 'main_menu'])
def handle_vacancy_actions(call):
    user_id = call.from_user.id
    user = get_user(user_id)
    language = user.language
    index = user_vacancy_index.get(user_id, 0)
    vacancy_id = user_vacancies_list[user_id][index][0].id



    if call.data == 'next_vacancy':
        if user_id in user_vacancy_index:
            user_vacancy_index[user_id] += 1
        show_current_vacancy(bot, user_id, language)
    elif call.data == 'add_to_favorite':
        if not is_favorite(user_id, vacancy_id):
            add_to_favorites(user_id, vacancy_id)
            bot.answer_callback_query(call.id, lang['added_to_favorites'][user.language])
        else:
            bot.answer_callback_query(call.id, lang['already_in_favorites'][user.language])
    elif call.data == 'respond':
        index = user_vacancy_index.get(user_id, 0)
        vacancy_id = user_vacancies_list[user_id][index][0].id
        respond_to_vacancy(user_id, vacancy_id)
        bot.answer_callback_query(call.id, lang['response_sent'][language])
    elif call.data == 'main_menu':
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(user_id, "MENU", reply_markup=main_menu(user_id, language))




def choose_category(message, language, mode):
    category_name = message.text
    user_categories = get_user_categories(message.from_user.id)
    user_category_names = [c.name for c in user_categories] if user_categories else []

    try:
        all_categories = get_all_categories()
        category_obj = next((c for c in all_categories if c.name == category_name), None)
        category_id = get_category_id(category_name)

        if not category_obj:
            bot.send_message(message.chat.id, lang['category_error'][language], reply_markup=category_keyboard(language))
            bot.register_next_step_handler(message, lambda msg: choose_category(msg, language, mode))
            return

        if mode == 'add':
            if category_name in user_category_names:
                bot.send_message(message.chat.id, lang['category_exists'][language], reply_markup=category_keyboard(language))
                bot.register_next_step_handler(message, lambda msg: choose_category(msg, language, mode))
            elif message.text == '❌ Отменить':
                bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
            else:
                add_user_category(user_id=message.from_user.id, category_id=category_id)
                bot.send_message(message.chat.id, lang['category_selected'][language], reply_markup=main_menu(message.from_user.id, language))

        elif mode == 'delete':
            print(user_category_names)
            if category_name not in user_category_names:
                bot.send_message(message.chat.id, lang['category_not_exists'][language],
                                 reply_markup=category_keyboard(language))
                bot.register_next_step_handler(message, lambda msg: choose_category(msg, language, mode))
            elif message.text == '❌ Отменить':
                bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
            else:
                delete_user_category(user_id=message.from_user.id, category_id=category_id)
                bot.send_message(message.chat.id, lang['category_deleted'][language],
                                 reply_markup=main_menu(message.from_user.id, language))

    except Exception as e:
        print(f"[ERROR choose_category] {e}")
        bot.send_message(message.chat.id, lang['category_error'][language])

#################################### vacancies ####################################

@bot.callback_query_handler(func=lambda call: call.data.startswith('vacancy_'))
def handle_vacancy_callback(call):
    user = get_user(call.from_user.id)
    try:
        if call.data == 'main_menu':
            bot.answer_callback_query(call.id, "MENU")
            bot.edit_message_text("MENU", chat_id=call.message.chat.id, message_id=call.message.message_id)
        elif call.data == 'vacancy_create':
            bot.send_message(call.from_user.id, lang['create_job_name'][user.language], reply_markup=ReplyKeyboardRemove())
            bot.register_next_step_handler(call.message, create_job_name, user.language)
        elif call.data == 'vacancy_delete':
            bot.send_message(call.from_user.id, lang['delete_vacancy'][user.language], reply_markup=delete_vacancy_keyboard(user.tg_id))
            bot.register_next_step_handler(call.message, delete_job, user.language)
    except Exception as e:
        print(f"[ERROR handle_vacancy_callback] {e}")
        bot.register_next_step_handler(call.message, handle_vacancy_callback, call)


def delete_job(message, language):
    vacancy_name = message.text
    try:
        if vacancy_name == '❌ Отменить':
            bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
            return

        success = delete_vacancy(vacancy_name, message.from_user.id)
        if success:
            bot.send_message(message.chat.id, lang['delete_vacancy_success'][language], reply_markup=main_menu(message.from_user.id, language))
        else:
            bot.send_message(message.chat.id, lang['delete_vacancy_error'][language])
            bot.register_next_step_handler(message, delete_job, language)

    except Exception as e:
        print(f"[ERROR delete_job] {e}")
        bot.send_message(message.chat.id, lang['delete_vacancy_error'][language])
        bot.register_next_step_handler(message, delete_job, language)



bot.infinity_polling()
