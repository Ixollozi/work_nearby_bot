from configuration.config import *
from configuration.utils import *
from services.buttons import *

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


@safe_step
def handle_admin_menu(message):
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
                         reply_markup=types.ReplyKeyboardRemove())

    else:
        bot.send_message(message.chat.id, 'Выберите команду из меню.')
        bot.register_next_step_handler(message, handle_admin_menu)


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

@safe_step
def add_admin_by_phone(message):
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

@safe_step
def remove_admin_by_phone(message):
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

@safe_step
def add_category(message):
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

@safe_step
def remove_category(message):
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
