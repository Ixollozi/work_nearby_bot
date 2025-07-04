from configuration.config import user_vacancy_index, user_vacancies_list, user_state
from configuration.utils import *
from services.buttons import *
from deep_translator import GoogleTranslator


def show_current_vacancy(bot, user_id, language):
    index = user_vacancy_index.get(user_id, 0)
    vacancies = user_vacancies_list.get(user_id)

    if not vacancies or index >= len(vacancies):
        bot.send_message(user_id, lang['no_vacancy'][language], reply_markup=main_menu(user_id, language))
        return

    vacancy, distance = vacancies[index]
    user_obj = get_user(user_id)
    if user_obj.prefered_radius:
        distance_text = f"{int(user_obj.prefered_radius)} м"
    else:
        distance_text = lang['all_vacancies'][language]

    try:
        translated_category = GoogleTranslator(source='auto', target=language).translate(vacancy.category)
    except:
        translated_category = vacancy.category

    text = (
        f"📌 {vacancy.title}\n\n"
        f"📂 {translated_category}\n\n"
        f"📝 {vacancy.description[:400]}...\n\n"
        f"💰 {vacancy.payment}\n"
        f"📍 {distance_text}\n"
        f"📞 {vacancy.contact}"
    )

    markup = get_vacancy_keyboard(language)
    bot.send_message(user_id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ['next_vacancy', 'add_to_favorite', 'respond'])
def handle_vacancy_actions(call):
    user_state[call.from_user.id] = 'awaiting_vacancy_actions'
    user_id = call.from_user.id
    user = get_user(user_id)
    language = user.language
    index = user_vacancy_index.get(user_id, 0)

    if user_id not in user_vacancies_list or not user_vacancies_list[user_id]:
        bot.answer_callback_query(call.id, lang['no_vacancy'][language])
        return

    vacancy_id = user_vacancies_list[user_id][index][0].id

    if call.data == 'next_vacancy':
        user_vacancy_index[user_id] = index + 1
        show_current_vacancy(bot, user_id, language)

    elif call.data == 'add_to_favorite':
        if not is_favorite(user_id, vacancy_id):
            add_to_favorites(user_id, vacancy_id)
            bot.answer_callback_query(call.id, lang['added_to_favorites'][language])
        else:
            bot.answer_callback_query(call.id, lang['already_in_favorites'][language])

    elif call.data == 'respond':
        if has_user_responded(user_id, vacancy_id):
            bot.answer_callback_query(call.id, lang['already_responded'][language])
        else:
            respond_to_vacancy(user_id, vacancy_id)
            bot.answer_callback_query(call.id, lang['response_sent'][language])

@safe_step
def choose_category(message, language, mode):
    user_state[message.from_user.id] = 'awaiting_choose_category'
    user_input = message.text.strip()

    if user_input == '❌ Отменить':
        bot.send_message(message.chat.id, "MENU", reply_markup=main_menu(message.from_user.id, language))
        return

    try:
        translated_to_ru = GoogleTranslator(source=language, target='ru').translate(user_input)
        print(f"[DEBUG] Перевод '{user_input}' -> '{translated_to_ru}'")
    except Exception as e:
        print(f"[ERROR translation] {e}")
        translated_to_ru = user_input

    all_categories = get_all_categories()
    category_names_ru = [c.name for c in all_categories]

    match = get_close_matches(translated_to_ru, category_names_ru, n=1, cutoff=0.7)
    category_obj = next((c for c in all_categories if c.name == match[0]), None) if match else None

    if not category_obj:
        bot.send_message(message.chat.id, lang['category_error'][language], reply_markup=category_keyboard(language))
        bot.register_next_step_handler(message, lambda msg: choose_category(msg, language, mode))
        return

    category_id = category_obj.id
    user_categories = get_user_categories(message.from_user.id)
    user_category_names = [c.name for c in user_categories] if user_categories else []

    if mode == 'add':
        if category_obj.name in user_category_names:
            bot.send_message(message.chat.id, lang['category_exists'][language], reply_markup=category_keyboard(language))
            bot.register_next_step_handler(message, lambda msg: choose_category(msg, language, mode))
        else:
            add_user_category(user_id=message.from_user.id, category_id=category_id)
            bot.send_message(message.chat.id, lang['category_selected'][language], reply_markup=ReplyKeyboardRemove())
            bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))

    elif mode == 'delete':
        if category_obj.name not in user_category_names:
            bot.send_message(message.chat.id, lang['category_not_exists'][language], reply_markup=category_keyboard(language))
            bot.register_next_step_handler(message, lambda msg: choose_category(msg, language, mode))
        else:
            delete_user_category(user_id=message.from_user.id, category_id=category_id)
            bot.send_message(message.chat.id, lang['category_deleted'][language], reply_markup=ReplyKeyboardRemove())
            bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
    else:
        bot.send_message(message.chat.id, lang['category_error'][language], reply_markup=main_menu(message.from_user.id, language))
