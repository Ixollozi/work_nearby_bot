from configuration.config import user_create_job_data, geolocator, PAYMENT_PROVIDER_TOKEN
from configuration.utils import *
from datetime import timezone
from services.buttons import *
from configuration.config import user_state, PAYMENT_AMOUNT, user_payment


# ID группы администраторов
ADMIN_GROUP_ID = -4879632469


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

    elif len(description) < 100 or len(description) > 1000:
        bot.send_message(message.chat.id, lang['create_job_description_error'][language], reply_markup=cancel())
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
    user_name = user.username.replace('@', '')
    contacts = user.phone if user_name is None else f"{user.phone}, username: {user.username}"
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
        bot.register_next_step_handler(message, create_job_location, language, name, description, currency, payment,
                                       contacts)


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
        bot.send_message(message.chat.id, lang['create_job_category'][language],
                         reply_markup=category_keyboard(language))
        bot.register_next_step_handler(message, create_job_category, language, name, description, currency, payment,
                                       contacts, location)
    else:
        bot.send_message(message.chat.id, lang['location_error'][language])
        bot.register_next_step_handler(message, create_job_location, language, name, description, currency, payment,
                                       contacts)


@safe_step
def create_job_category(message, language, name, description, currency, payment, contacts, location):
    user_state[message.from_user.id] = 'awaiting_create_job_category'
    user_input = message.text.strip()
    category_ru = match_category_from_user_input(user_input, language)
    print(f"[DEBUG] Ввод пользователя: {user_input}")
    print(f"[DEBUG] Сопоставленная категория (RU): {category_ru}")

    if not category_ru:
        bot.send_message(message.chat.id, lang['create_job_category_error'][language])
        bot.register_next_step_handler(message, create_job_category, language, name, description, currency, payment,
                                       contacts, location)
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

    # Добавляем предложение загрузить фото
    photo_text = {
        'ru': "Хотите добавить фото к вакансии?",
        'uz': "Vakansiyaga rasm qo'shmoqchimisiz?",
        'en': "Would you like to add a photo to the job posting?"
    }

    bot.send_message(message.chat.id, photo_text[language], reply_markup=photo_choice_keyboard(language))
    bot.register_next_step_handler(message, handle_photo_choice, language, name, description, category_ru, payment,
                                   contacts, location, category_translated)


def photo_choice_keyboard(language):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    if language == 'ru':
        keyboard.add(KeyboardButton("📸 Отправить фото"))
        keyboard.add(KeyboardButton("📝 Вакансия без фото"))
        keyboard.add(KeyboardButton("❌ Отменить"))
    elif language == 'uz':
        keyboard.add(KeyboardButton("📸 Rasm yuborish"))
        keyboard.add(KeyboardButton("📝 Rasmsiz vakansiya"))
        keyboard.add(KeyboardButton("❌ Bekor qilish"))
    else:  # en
        keyboard.add(KeyboardButton("📸 Send photo"))
        keyboard.add(KeyboardButton("📝 Job without photo"))
        keyboard.add(KeyboardButton("❌ Cancel"))

    return keyboard


@safe_step
def handle_photo_choice(message, language, name, description, category, payment, contacts, location,
                        category_translated):
    user_state[message.from_user.id] = 'awaiting_photo_choice'

    if message.text == '❌ Отменить' or message.text == '❌ Cancel' or message.text == '❌ Bekor qilish':
        user_state[message.from_user.id] = None
        bot.send_message(message.chat.id, 'MENU:', reply_markup=main_menu(message.from_user.id, language))
        return

    # Пользователь выбрал отправить фото
    if message.text in ['📸 Отправить фото', '📸 Rasm yuborish', '📸 Send photo']:
        photo_request_text = {
            'ru': "Отправьте фото для вакансии:",
            'uz': "Vakansiya uchun rasm yuboring:",
            'en': "Send a photo for the job posting:"
        }
        bot.send_message(message.chat.id, photo_request_text[language], reply_markup=cancel())
        bot.register_next_step_handler(message, handle_photo_upload, language, name, description, category, payment,
                                       contacts, location, category_translated)

    # Пользователь выбрал вакансию без фото
    elif message.text in ['📝 Вакансия без фото', '📝 Rasmsiz vakansiya', '📝 Job without photo']:
        show_job_preview(message, language, name, description, category, payment, contacts, location,
                         category_translated, photo_id=None)

    else:
        bot.send_message(message.chat.id, "Пожалуйста, выберите один из вариантов:",
                         reply_markup=photo_choice_keyboard(language))
        bot.register_next_step_handler(message, handle_photo_choice, language, name, description, category, payment,
                                       contacts, location, category_translated)


@safe_step
def handle_photo_upload(message, language, name, description, category, payment, contacts, location,
                        category_translated):
    user_state[message.from_user.id] = 'awaiting_photo_upload'

    if message.text == '❌ Отменить' or message.text == '❌ Cancel' or message.text == '❌ Bekor qilish':
        user_state[message.from_user.id] = None
        bot.send_message(message.chat.id, 'MENU:', reply_markup=main_menu(message.from_user.id, language))
        return

    if message.photo:
        # Получаем фото с наибольшим разрешением
        photo_id = message.photo[-1].file_id

        # Сохраняем фото в данные пользователя
        user_create_job_data[message.from_user.id]['photo_id'] = photo_id

        show_job_preview(message, language, name, description, category, payment, contacts, location,
                         category_translated, photo_id)
    else:
        error_text = {
            'ru': "Пожалуйста, отправьте фото или выберите 'Отменить'",
            'uz': "Iltimos, rasm yuboring yoki 'Bekor qilish'ni tanlang",
            'en': "Please send a photo or choose 'Cancel'"
        }
        bot.send_message(message.chat.id, error_text[language])
        bot.register_next_step_handler(message, handle_photo_upload, language, name, description, category, payment,
                                       contacts, location, category_translated)


def show_job_preview(message, language, name, description, category, payment, contacts, location, category_translated,
                     photo_id=None):
    data = user_create_job_data.get(message.from_user.id)
    if photo_id:
        data['photo_id'] = photo_id

    text = {
        'ru': f"Вы уверены, что хотите создать вакансию:\n"
              f"📌 Название: {name}\n"
              f"📝 Описание:\n {description}\n"
              f"💰 Заработная плата: {payment}\n"
              f"📂 Категория: {category_translated}\n"
              f'📍 Местоположение: {location}\n'
              f"📞 Контакты: {contacts}\n"
              f"{'📸 С фото' if photo_id else ''}",
        'uz': f"Ish vakansiyasini yaratmoqchimisiz:\n"
              f"📌 Nomi: {name}\n"
              f"📝 Tavsif:\n {description}\n"
              f"💰 To'lov: {payment}\n"
              f"📂 Kategoriya: {category_translated}\n"
              f'📍 Manzil: {location}\n'
              f"📞 Kontaktlar: {contacts}\n"
              f"{'📸 Rasm bilan' if photo_id else ''}",
        'en': f"Are you sure you want to create this job posting:\n"
              f"📌 Title: {name}\n"
              f"📝 Description:\n {description}\n"
              f"💰 Salary: {payment}\n"
              f"📂 Category: {category_translated}\n"
              f'📍 Location: {location}\n'
              f"📞 Contacts: {contacts}\n"
              f"{'📸 With photo' if photo_id else ''}"
    }

    if photo_id:
        bot.send_photo(message.chat.id, photo_id, caption=text[language], reply_markup=agree(language))
    else:
        bot.send_message(message.chat.id, text[language], reply_markup=agree(language))

    bot.register_next_step_handler(message, agree_job, language, name, description, category, payment, contacts,
                                   photo_id)



@safe_step
def agree_job(message, language, name, description, category, payment, contacts, photo=None):
    user_state[message.from_user.id] = 'awaiting_create_job_agree'
    user = get_user(message.from_user.id)

    if message.text in ['❌ Отменить', '❌ Cancel', '❌ Bekor qilish']:
        user_state[message.from_user.id] = None
        bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
        return

    if message.text in ['✅ Подтвердить', '✅ Confirm', '✅ Qabul qilish']:
        # Сохраняем данные вакансии временно
        user_create_job_data[message.from_user.id] = {
            'language': language,
            'name': name,
            'description': description,
            'category': category,
            'payment': payment,
            'contacts': contacts,
            'photo_id': photo,
            'latitude': user.latitude,
            'longitude': user.longitude
        }

        # Формируем данные для счёта
        invoice_title = lang['invoice_title'][language].format(name=name)
        invoice_description = lang['invoice_description'][language].format(name=name)
        payload = f"job_posting_{message.from_user.id}_{vacancy_id_generator()}"  # Уникальный идентификатор платежа
        currency = "UZS"  # Валюта для Click
        prices = [LabeledPrice(label=lang['job_posting_fee'][language], amount=PAYMENT_AMOUNT)]

        user_payment[message.from_user.id] = {
            'payload': payload,
            'prices': prices
        }

        # Отправляем счёт пользователю
        try:
            bot.send_invoice(
                chat_id=message.chat.id,
                title=invoice_title,
                description=invoice_description,
                invoice_payload=payload,
                provider_token=PAYMENT_PROVIDER_TOKEN,
                currency=currency,
                prices=prices,
                start_parameter=f"job-posting-{message.from_user.id}",
                need_name=False,
                need_phone_number=False,
                need_email=False,
                need_shipping_address=False,
                is_flexible=False
            )

            # Сообщаем пользователю, что нужно оплатить
            bot.send_message(
                message.chat.id,
                lang['payment_required'][language],
                reply_markup=ReplyKeyboardRemove()
            )
        except Exception as e:
            print(f"[ERROR send_invoice] {e}")
            bot.send_message(message.chat.id, lang['payment_error'][language], reply_markup=main_menu(message.from_user.id, language))
    else:
        bot.send_message(message.chat.id, "Пожалуйста, выберите один из вариантов:", reply_markup=agree(language))
        bot.register_next_step_handler(message, agree_job, language, name, description, category, payment, contacts, photo)

def send_job_to_admin_group(vacancy_id, user, name, description, payment, category, contacts, latitude, longitude,
                            photo_id=None):
    try:
        # Получаем местоположение
        location = geolocator(latitude, longitude, 'ru')

        # Формируем текст сообщения
        admin_text = f"""
🔍 НОВАЯ ВАКАНСИЯ НА РАССМОТРЕНИЕ

👤 Пользователь: {user.name}
📱 Telegram: {user.username or 'без username'}
🆔 User ID: {user.tg_id}
🆔 Vacancy ID: {vacancy_id}

📌 Название: {name}
📝 Описание: {description}
💰 Заработная плата: {payment}
📂 Категория: {category}
📍 Местоположение: {location}
📞 Контакты: {contacts}

🕒 Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        # Создаем клавиатуру для админов
        admin_keyboard = InlineKeyboardMarkup(row_width=2)
        admin_keyboard.add(
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_job_{vacancy_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_job_{vacancy_id}")
        )

        # Отправляем сообщение с фото или без
        if photo_id:
            bot.send_photo(
                ADMIN_GROUP_ID,
                photo_id,
                caption=admin_text,
                reply_markup=admin_keyboard
            )
        else:
            bot.send_message(
                ADMIN_GROUP_ID,
                admin_text,
                reply_markup=admin_keyboard
            )

        print(f"[INFO] Вакансия {vacancy_id} отправлена в группу админов")

    except Exception as e:
        print(f"[ERROR send_job_to_admin_group] {e}")


# Обработчики для админских кнопок
@bot.callback_query_handler(
    func=lambda call: call.data.startswith('approve_job_') or call.data.startswith('reject_job_'))
def handle_admin_job_decision(call):
    """Обрабатывает решение админа по вакансии"""
    try:
        action = call.data.split('_')[0]  # approve или reject
        vacancy_id = call.data.split('_')[2]

        if action == 'approve':
            # Логика одобрения вакансии
            # Например, обновить статус в базе данных
            update_vacancy(vacancy_id, status='approved')

            bot.answer_callback_query(call.id, "✅ Вакансия одобрена!")
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )

            # Добавляем текст к сообщению
            new_text = call.message.text or call.message.caption
            new_text += f"\n\n✅ ОДОБРЕНО администратором @{call.from_user.username}"

            if call.message.photo:
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=new_text
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=new_text
                )

        elif action == 'reject':
            # Логика отклонения вакансии
            update_vacancy(vacancy_id, status='rejected', expires_at=datetime.now() + timedelta(days=1))


            bot.answer_callback_query(call.id, "❌ Вакансия отклонена!")
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )

            # Добавляем текст к сообщению
            new_text = call.message.text or call.message.caption
            new_text += f"\n\n❌ ОТКЛОНЕНО администратором @{call.from_user.username}"

            if call.message.photo:
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=new_text
                )
            else:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=new_text
                )

    except Exception as e:
        print(f"[ERROR handle_admin_job_decision] {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


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
            bot.send_message(call.from_user.id, lang['delete_vacancy_agree'][user.language],
                             reply_markup=agree(user.language))
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
            bot.send_message(message.chat.id, lang['delete_vacancy_success'][language],
                             reply_markup=ReplyKeyboardRemove())
            bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
        except Exception as e:
            print(f"[ERROR delete_job] {e}")

# Обработчик предпроверки платежа
@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout_query(pre_checkout_query):
    user_id = pre_checkout_query.from_user.id
    payload = pre_checkout_query.invoice_payload
    language = get_user(user_id).language

    try:
        if not payload.startswith('job_posting_'):
            bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=False,
                error_message=lang['invalid_payment'][language]
            )
            return

        if user_id not in user_create_job_data:
            bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=False,
                error_message=lang['data_missing'][language]
            )
            return

        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except Exception as e:
        print(f"[ERROR handle_pre_checkout_query] {e}")
        bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message=lang['payment_error'][language]
        )

# Обработчик успешного платежа
@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    user_id = message.from_user.id
    user_state[user_id] = 'payment_successful'
    language = get_user(user_id).language

    # Получаем данные вакансии
    job_data = user_create_job_data.get(user_id)
    if not job_data:
        bot.send_message(message.chat.id, lang['data_missing'][language], reply_markup=main_menu(user_id, language))
        return

    # Извлекаем данные
    name = job_data['name']
    description = job_data['description']
    category = job_data['category']
    payment = job_data['payment']
    contacts = job_data['contacts']
    photo = job_data['photo_id']
    latitude = job_data['latitude']
    longitude = job_data['longitude']

    try:
        # Создаём вакансию в базе данных
        vacancy_id = create_vacancy(
            user_id=user_id,
            title=name,
            description=description,
            payment=payment,
            latitude=latitude,
            longitude=longitude,
            contact=contacts,
            category=category,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            photo_id=photo
        )
        write_payment(user_id, vacancy_id, user_payment[user_id]['prices'][0].amount, user_payment[user_id]['payload'])

        # Уведомляем пользователя об успешной оплате
        bot.send_message(
            message.chat.id,
            lang['payment_success'][language].format(
                amount=message.successful_payment.total_amount / 100,
                currency=message.successful_payment.currency
            ),
            reply_markup=main_menu(user_id, language)
        )

        # Отправляем вакансию в группу админов
        send_job_to_admin_group(vacancy_id, get_user(user_id), name, description, payment, category, contacts, latitude, longitude, photo)

        # Очищаем временные данные
        user_create_job_data.pop(user_id, None)
        user_payment.pop(user_id, None)
        user_state[user_id] = None
    except Exception as e:
        print(f"[ERROR handle_successful_payment] {e}")
        bot.send_message(message.chat.id, lang['payment_error'][language], reply_markup=main_menu(user_id, language))

# Генератор уникального ID для вакансии
def vacancy_id_generator():
    import uuid
    return str(uuid.uuid4())
