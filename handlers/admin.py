from configuration.config import *
from configuration.utils import *
from services.buttons import *
import os
import sys

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_state[message.from_user.id] = 'awaiting_admin'
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
    user_state[message.from_user.id] = 'awaiting_admin_menu'
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

    elif message.text == '⚙️ Настройки':
        bot.send_message(message.chat.id, 'Настройки бота:', reply_markup=settings_menu())
        bot.register_next_step_handler(message, handle_settings)

    elif message.text == '🔍 Найти и удалить вакансию':
        bot.send_message(message.chat.id, 'Введите ID или название вакансии для поиска:', reply_markup=cancel())
        bot.register_next_step_handler(message, search_vacancy)
    elif message.text == '$ Изменить стоимость вакансий':
        bot.send_message(message.chat.id, 'Введите цену, сколько будет стоить вакансия (например, 1000):', reply_markup=cancel())
        bot.register_next_step_handler(message, change_vacancy_price)

    elif message.text == '❌ Выход из админки':
        user = get_user(message.from_user.id)
        bot.send_message(message.chat.id, 'Вы вышли из админ-панели.',
                         reply_markup=types.ReplyKeyboardRemove())
        bot.send_message(message.chat.id, 'MENU: ', reply_markup=main_menu(message.from_user.id, user.language))

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
    user_state[call.from_user.id] = 'awaiting_admin_menu_paginate_users'
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
    user_state[message.from_user.id] = 'awaiting_admin_menu_add_admin_by_phone'
    phone = message.text.strip()
    if message.text == '❌ Отменить':
        bot.send_message(message.chat.id, 'Вы в админ-панели.', reply_markup=admin_menu())
        bot.register_next_step_handler(message, handle_admin_menu)
        return
    elif not phone.startswith('+'):
        bot.send_message(message.chat.id,
                         'Пожалуйста, введите номер телефона в международном формате, например: +998901234567',
                         reply_markup=cancel())
        bot.register_next_step_handler(message, add_admin_by_phone)
    else:
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
    user_state[message.from_user.id] = 'awaiting_admin_menu_remove_admin_by_phone'
    phone = message.text.strip()
    if message.text == '❌ Отменить':
        bot.send_message(message.chat.id, 'Вы в админ-панели.', reply_markup=admin_menu())
        bot.register_next_step_handler(message, handle_admin_menu)
        return
    elif not phone.startswith('+'):
        bot.send_message(message.chat.id,
                         'Пожалуйста, введите номер телефона в международном формате, например: +998901234567',
                         reply_markup=cancel())
        bot.register_next_step_handler(message, remove_admin_by_phone)
    else:
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
    user_state[message.from_user.id] = 'awaiting_admin_menu_add_category'
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
    user_state[message.from_user.id] = 'awaiting_admin_menu_remove_category'
    category_name = message.text.strip()
    if message.text == '❌ Отменить':
        bot.send_message(message.chat.id, 'Вы в админ-панели.', reply_markup=admin_menu())
        bot.register_next_step_handler(message, handle_admin_menu)
        return
    elif category_name not in [c.name for c in get_all_categories()]:
        bot.send_message(message.chat.id, 'Категория не существует.', reply_markup=admin_menu())
        bot.register_next_step_handler(message, handle_admin_menu)
    else:
        delete_category(category_name)
        bot.send_message(message.chat.id, f'Категория "{category_name}" успешно удалена.',
                         reply_markup=admin_menu())
        bot.register_next_step_handler(message, handle_admin_menu)


@safe_step
def handle_settings(message):
    user_state[message.from_user.id] = 'awaiting_admin_menu_settings'
    if message.text == '🔄 Перезапуск бота':
        bot.send_message(message.chat.id, '♻️ Бот перезапускается...')
        restart_bot()
    elif message.text == '⬅️ Назад':
        bot.send_message(message.chat.id, 'Вы в админ-панели.', reply_markup=admin_menu())
        bot.register_next_step_handler(message, handle_admin_menu)
    else:
        bot.send_message(message.chat.id, 'Выберите команду из меню.', reply_markup=settings_menu())
        bot.register_next_step_handler(message, handle_settings)




@safe_step
def search_vacancy(message):
    user_state[message.from_user.id] = 'awaiting_admin_menu_search_vacancy'
    if message.text == '❌ Отменить':
        bot.send_message(message.chat.id, 'Вы в админ-панели.', reply_markup=admin_menu())
        bot.register_next_step_handler(message, handle_admin_menu)
        return

    search_query = message.text.strip()
    vacancies = search_vacancies(search_query)  # Assumes a function to search vacancies by ID or name
    if not vacancies:
        bot.send_message(message.chat.id, 'Вакансии не найдены.', reply_markup=admin_menu())
        bot.register_next_step_handler(message, handle_admin_menu)
        return

    markup = InlineKeyboardMarkup()
    for vacancy in vacancies:
        markup.add(InlineKeyboardButton(f"{vacancy.title} (ID: {vacancy.id})", callback_data=f"vacancy_{vacancy.id}"))

    bot.send_message(message.chat.id, 'Найденные вакансии:', reply_markup=markup)
    bot.register_next_step_handler(message, search_vacancy)

@safe_step
def change_vacancy_price(message):
    user_state[message.from_user.id] = 'awaiting_admin_menu_change_vacancy_price'
    if message.text == '❌ Отменить':
        bot.send_message(message.chat.id, 'Вы в админ-панели.', reply_markup=admin_menu())
        bot.register_next_step_handler(message, handle_admin_menu)
        return

    try:
        cost = int(message.text.strip())
        if cost < 0:
            bot.send_message(message.chat.id, 'Цена не может быть отрицательной.', reply_markup=admin_menu())
            bot.register_next_step_handler(message, change_vacancy_price)
            return

        update_cost(cost)
        bot.send_message(message.chat.id, f'Цена вакансии изменена на {cost} UZS.', reply_markup=admin_menu())
        bot.send_message(message.chat.id, 'Вы в админ-панели.', reply_markup=admin_menu())
        bot.register_next_step_handler(message, handle_admin_menu)
    except ValueError:
        bot.send_message(message.chat.id, 'Введите цену в виде числа.', reply_markup=admin_menu())
        bot.register_next_step_handler(message, change_vacancy_price)


@bot.callback_query_handler(func=lambda call: call.data.startswith('vacancy_'))
def confirm_delete_vacancy(call):
    user_state[call.from_user.id] = 'awaiting_admin_menu_confirm_delete_vacancy'
    vacancy_id = int(call.data.split('_')[1])
    vacancy = get_vacancy_by_id(vacancy_id)
    if vacancy:
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("Удалить", callback_data=f"delete_vacancy_{vacancy_id}"),
                   InlineKeyboardButton("Отмена", callback_data="cancel_vacancy"))
        bot.send_message(call.message.chat.id,
                         f"Вакансия: {vacancy.title}\nID: {vacancy_id}\nУдалить эту вакансию?",
                         reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, 'Вакансия не найдена.', reply_markup=admin_menu())
        bot.register_next_step_handler(call.message, handle_admin_menu)


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_vacancy_') or call.data == 'cancel_vacancy')
def handle_vacancy_action(call):
    user_state[call.from_user.id] = 'awaiting_admin_menu_handle_vacancy_action'
    if call.data == 'cancel_vacancy':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, 'Вы в админ-панели.', reply_markup=admin_menu())
        bot.register_next_step_handler(call.message, handle_admin_menu)
        return

    vacancy_id = int(call.data.split('_')[2])
    delete_vacancy_by_admin(vacancy_id)  # Assumes a function to delete vacancy by ID
    db.commit()
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, f'Вакансия ID {vacancy_id} удалена.', reply_markup=admin_menu())
    bot.register_next_step_handler(call.message, handle_admin_menu)


def settings_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🔄 Перезапуск бота')
    markup.add('⬅️ Назад')
    return markup


def search_vacancies(query):
    try:
        # Поиск по ID
        if query.isdigit():
            vacancy_by_id = get_vacancy_by_id(int(query))
            return [vacancy_by_id] if vacancy_by_id else []

        # Поиск по названию (частичное совпадение, без учёта регистра)
        all_vacancies = get_all_vacancies()
        matching_vacancies = [
            vacancy for vacancy in all_vacancies
            if query.lower() in vacancy.title.lower()
        ]
        return matching_vacancies
    except Exception as e:
        print(f"[WARN search_vacancies] {e}")
        return []


def restart_bot():
    python = sys.executable
    os.execl(python, python, *sys.argv)