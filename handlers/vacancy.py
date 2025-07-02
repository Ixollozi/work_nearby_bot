from configuration.config import user_create_job_data, geolocator, CATEGORIES
from configuration.utils import *
from datetime import timezone
from services.buttons import *


@safe_step
def create_job_name(message, language):
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


@safe_step
def create_job_description(message, language, name):
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


@safe_step
def create_job_price(message, language, name, description, currency):
    user = get_user(message.from_user.id)
    contacts = user.phone if user.username is None else f"{user.phone}, username: {user.username}"
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


@safe_step
def create_job_location(message, language, name, description, currency, payment, contacts):
    if message.location:
        latitude = message.location.latitude
        longitude = message.location.longitude
        print(latitude, longitude)
        location = geolocator.reverse((latitude, longitude), language=language)
        print(location)
        update_user_field(message.from_user.id, latitude=latitude, longitude=longitude)

        bot.send_message(message.chat.id, lang['create_job_category'][language], reply_markup=category_keyboard(language))
        bot.register_next_step_handler(message, create_job_category, language, name, description, currency, payment, contacts, location)
    else:
        bot.send_message(message.chat.id, lang['location_error'][language])
        bot.register_next_step_handler(message, create_job_location, language, name, description, currency, payment, contacts)


@safe_step
def create_job_category(message, language, name, description, currency, payment, contacts, location):
    category = message.text.strip()
    existing_categories = [c.name.lower() for c in get_all_categories()]
    predefined_categories = [c.lower() for c in CATEGORIES]

    if category.lower() not in predefined_categories and category.lower() not in existing_categories:
        bot.send_message(message.chat.id, lang['create_job_category_error'][language])
        bot.register_next_step_handler(message, create_job_category, language, name, description, currency, payment, contacts, location)  # Добавлен параметр location
    else:
        if message.from_user.id not in user_create_job_data:
            user_create_job_data[message.from_user.id] = {}
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
                  f"💰 To'lov: {data['price']}\n"
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
        bot.register_next_step_handler(message, agree_job, language, name, description, category, payment, contacts)


@safe_step
def agree_job(message, language, name, description, category, payment, contacts):
    user = get_user(message.from_user.id)
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
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )

        bot.send_message(message.chat.id, lang['create_job_agree'][language], reply_markup=ReplyKeyboardRemove())
        bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))


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
        bot.answer_callback_query(call.id, "Произошла ошибка")  # Исправлено


@safe_step
def delete_job(message, language):
    vacancy_name = message.text
    if vacancy_name == '❌ Отменить':
        bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
        return

    success = delete_vacancy(vacancy_name, message.from_user.id)
    if success:
        bot.send_message(message.chat.id, lang['delete_vacancy_success'][language], reply_markup=main_menu(message.from_user.id, language))
    else:
        bot.send_message(message.chat.id, lang['delete_vacancy_error'][language])
        bot.register_next_step_handler(message, delete_job, language)
