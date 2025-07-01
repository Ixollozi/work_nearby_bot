from configuration.config import user_vacancy_index, user_vacancies_list
from configuration.utils import *
from services.service import *
from services.buttons import *


def show_current_vacancy(bot, user_id, language):
    index = user_vacancy_index.get(user_id, 0)
    vacancies = user_vacancies_list.get(user_id)

    if not vacancies or index >= len(vacancies):
        bot.send_message(user_id, lang['no_vacancy'][language], reply_markup=main_menu(user_id, language))
        return

    vacancy, distance = vacancies[index]
    user_obj = get_user(user_id)
    if user_obj.prefered_radius is not None and user_obj.prefered_radius > 0:
        distance_text = f"{int(user_obj.prefered_radius)} м"
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


@bot.callback_query_handler(func=lambda call: call.data in ['next_vacancy', 'add_to_favorite', 'respond'])
def handle_vacancy_actions(call):
    user_id = call.from_user.id
    user = get_user(user_id)
    language = user.language
    index = user_vacancy_index.get(user_id, 0)

    # Проверяем, что у пользователя есть вакансии
    if user_id not in user_vacancies_list or not user_vacancies_list[user_id]:
        bot.answer_callback_query(call.id, lang['no_vacancy'][language])
        return

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



@safe_step
def choose_category(message, language, mode):
    category_name = message.text
    user_categories = get_user_categories(message.from_user.id)
    user_category_names = [c.name for c in user_categories] if user_categories else []
    all_categories = get_all_categories()
    category_obj = next((c for c in all_categories if c.name == category_name), None)
    category_id = get_category_id(category_name)

    if not category_obj:
        bot.send_message(message.chat.id, lang['category_error'][language], reply_markup=category_keyboard(language))
        bot.register_next_step_handler(message, lambda msg: choose_category(msg, language, mode))
        return

    if mode == 'add':
        if category_name in user_category_names:
            bot.send_message(message.chat.id, lang['category_exists'][language],
                             reply_markup=category_keyboard(language))
            bot.register_next_step_handler(message, lambda msg: choose_category(msg, language, mode))
        elif message.text == '❌ Отменить':
            bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
        else:
            add_user_category(user_id=message.from_user.id, category_id=category_id)
            bot.send_message(message.chat.id, lang['category_selected'][language],
                             reply_markup=main_menu(message.from_user.id, language))

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
