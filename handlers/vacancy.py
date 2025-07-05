from configuration.config import user_create_job_data, geolocator
from configuration.utils import *
from datetime import timezone
from services.buttons import *
from configuration.config import user_state


@safe_step
def create_job_name(message, language):
    user_state[message.from_user.id] = 'awaiting_create_job_name'
    if message.text.isdigit():
        bot.send_message(message.chat.id, lang['create_job_name_error'][language], reply_markup=cancel())
        bot.register_next_step_handler(message, create_job_name, language)
    elif message.text == '❌ Отменить' or message.text == '❌ Cancel' or message.text == '❌ Bekor qilish':
        user_state[message.from_user.id] = None
        bot.send_message(message.chat.id, 'MENU:', reply_markup=main_menu(message.from_user.id, language))
    else:
        name = message.text
        if len(name) < 10 or len(name) > 50:
            bot.send_message(message.chat.id, lang['create_job_name_len'][language], reply_markup=cancel())
            bot.register_next_step_handler(message, create_job_name, language)
        else:
            bot.send_message(message.chat.id, lang['create_job_description'][language])
            bot.register_next_step_handler(message, create_job_description, language, name)


@safe_step
def create_job_description(message, language, name):
    user_state[message.from_user.id] = 'awaiting_create_job_description'
    description = message.text
    user_create_job_data[message.from_user.id] = {
        'language': language,
        'name': name,
        'description': description,
        'currency': None
    }
    if message.text == '❌ Отменить' or message.text == '❌ Cancel' or message.text == '❌ Bekor qilish':
        user_state[message.from_user.id] = None
        bot.send_message(message.chat.id, 'MENU:', reply_markup=main_menu(message.from_user.id, language))

    elif len(description) < 200 or len(description) > 1500:
        bot.send_message(message.chat.id, lang['create_job_description_error'][language],reply_markup=cancel())
        bot.register_next_step_handler(message, create_job_description, language, name)
    else:
        bot.send_message(message.chat.id, lang['choose_currency'][language],
                         reply_markup=get_currency_keyboard())


@bot.callback_query_handler(func=lambda call: call.data.startswith('currency_'))
def handle_currency_selection(call):
    user_state[call.from_user.id] = 'awaiting_currency_selection'
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
    user_state[message.from_user.id] = 'awaiting_create_job_price'
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
    user_state[message.from_user.id] = 'awaiting_create_job_location'
    if message.location:
        latitude = message.location.latitude
        longitude = message.location.longitude
        language = get_user(message.from_user.id).language
        location = geolocator(latitude, longitude, language)

        update_user_field(message.from_user.id, latitude=latitude, longitude=longitude)

        bot.send_message(message.chat.id, lang['please_wait'][language])
        bot.send_message(message.chat.id, lang['create_job_category'][language], reply_markup=category_keyboard(language))
        bot.register_next_step_handler(message, create_job_category, language, name, description, currency, payment, contacts, location)
    else:
        bot.send_message(message.chat.id, lang['location_error'][language])
        bot.register_next_step_handler(message, create_job_location, language, name, description, currency, payment, contacts)


@safe_step
def create_job_category(message, language, name, description, currency, payment, contacts, location):
    user_state[message.from_user.id] = 'awaiting_create_job_category'
    user_input = message.text.strip()
    category_ru = match_category_from_user_input(user_input, language)
    print(f"[DEBUG] Ввод пользователя: {user_input}")
    print(f"[DEBUG] Сопоставленная категория (RU): {category_ru}")

    if not category_ru:
        bot.send_message(message.chat.id, lang['create_job_category_error'][language])
        bot.register_next_step_handler(message, create_job_category, language, name, description, currency, payment, contacts, location)
        return

    # Перевод названия категории обратно в язык пользователя (для отображения)
    try:
        category_translated = GoogleTranslator(source='auto', target=language).translate(category_ru)
    except Exception as e:
        print(f"[ERROR translate category_ru -> lang] {e}")
        category_translated = category_ru  # fallback

    # Сохраняем категорию на русском
    if message.from_user.id not in user_create_job_data:
        user_create_job_data[message.from_user.id] = {}
    user_create_job_data[message.from_user.id]['category'] = category_ru

    data = user_create_job_data.get(message.from_user.id)

    text = {
        'ru': f"Вы уверены, что хотите создать вакансию:\n"
              f"📌 Название: {data['name']}\n"
              f"📝 Описание:\n {data['description']}\n"
              f"💰 Заработная плата: {data['price']}\n"
              f"📂 Категория: {category_translated}\n"
              f'📍 Местоположение: {location}\n'
              f"📞 Контакты: {data['contacts']}",
        'uz': f"Ish vakansiyasini yaratmoqchimisiz:\n"
              f"📌 Nomi: {data['name']}\n"
              f"📝 Tavsif:\n {data['description']}\n"
              f"💰 To'lov: {data['price']}\n"
              f"📂 Kategoriya: {category_translated}\n"
              f'📍 Manzil: {location}\n'
              f"📞 Kontaktlar: {data['contacts']}",
        'en': f"Are you sure you want to create this job posting:\n"
              f"📌 Title: {data['name']}\n"
              f"📝 Description:\n {data['description']}\n"
              f"💰 Salary: {data['price']}\n"
              f"📂 Category: {category_translated}\n"
              f'📍 Location: {location}\n'
              f"📞 Contacts: {data['contacts']}"
    }

    bot.send_message(message.chat.id, text[language], reply_markup=agree(language))
    bot.register_next_step_handler(message, agree_job, language, name, description, category_ru, payment, contacts)


@safe_step
def agree_job(message, language, name, description, category, payment, contacts):
    user_state[message.from_user.id] = 'awaiting_create_job_agree'
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


@bot.callback_query_handler(func=lambda call: call.data.startswith('job_delete'))
def handle_vacancy_callback(call):
    user_state[call.from_user.id] = 'awaiting_vacancy_callback'
    user = get_user(call.from_user.id)
    # vacacy_id = user_vacancies_list[user.tg_id][user_vacancy_index[user.tg_id]].id
    vacancy_id = call.data.replace('job_delete_', '')
    try:
        if call.data == 'main_menu':
            bot.answer_callback_query(call.id, "MENU")
            bot.edit_message_text("MENU", chat_id=call.message.chat.id, message_id=call.message.message_id)
        elif call.data == f'job_delete_{vacancy_id}':
            bot.send_message(call.from_user.id, lang['delete_vacancy_agree'][user.language], reply_markup=agree(user.language))
            bot.register_next_step_handler(call.message, delete_job, user.language, vacancy_id)
    except Exception as e:
        print(f"[ERROR handle_vacancy_callback] {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")  # Исправлено


@safe_step
def delete_job(message, language, vacancy_id):
    user_state[message.from_user.id] = 'awaiting_delete_job'
    text = message.text
    if text == '❌ Отменить' or text == '❌ Cancel' or text == '❌ Bekor qilish':
        bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
        return

    elif text == '✅ Подтвердить' or text == '✅ Confirm' or text == '✅ Tasdiqlash':
        try:
            delete_vacancy(vacancy_id, message.from_user.id)
            bot.send_message(message.chat.id, lang['delete_vacancy_success'][language], reply_markup=ReplyKeyboardRemove())
            bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
        except Exception as e:
            print(f"[ERROR delete_job] {e}")
