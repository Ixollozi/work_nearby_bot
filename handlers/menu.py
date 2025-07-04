from handlers.find_job import *
from handlers.vacancy import create_job_name
from configuration.config import user_responses_list, user_response_index, geolocator, user_vacancies_list, user_vacancy_index
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
from deep_translator import GoogleTranslator


@bot.callback_query_handler(func=lambda call: call.data in
                                              ['find_job', 'create_job', 'favorite', 'settings', 'my_vacancy',
                                               'category', 'create', 'delete', 'main_menu', 'my_response',
                                               'user_responses', 'vacancy_prev', 'vacancy_next'])
def handle_main_menu(call):
    user_id = call.from_user.id
    user = get_user(user_id)
    language = user.language if user else 'ru'
    try:
        if call.data == 'find_job':
            bot.answer_callback_query(call.id, "Поиск работы...")
            bot.send_message(user_id, lang['please_wait'][language])
            categories = [c.name for c in get_user_categories(user_id)]

            if not categories:
                bot.send_message(user_id, lang['choose_category'][language], reply_markup=category_keyboard(language))
                bot.register_next_step_handler_by_chat_id(user_id, choose_category, language, 'add')
                return

            radius = user.prefered_radius if user.prefered_radius else lang['all_vacancies'][language]
            vacancies_with_distance = get_vacancies_nearby(user.latitude, user.longitude, radius_meters=radius,
                                                           categories=categories)
            random.shuffle(vacancies_with_distance)

            if not vacancies_with_distance:
                bot.send_message(user_id, lang['no_vacancy'][language], reply_markup=main_menu(user_id, language))
                return

            user_vacancies_list[user_id] = vacancies_with_distance
            user_vacancy_index[user_id] = 0
            show_current_vacancy(bot, user_id, language)

        elif call.data == 'create_job':
            bot.answer_callback_query(call.id, "Создание вакансии...")
            bot.send_message(user_id, lang['create_job_name'][language])
            bot.register_next_step_handler_by_chat_id(user_id, create_job_name, language)

        elif call.data == 'favorite':
            bot.answer_callback_query(call.id, "Избранные...")
            favorites_raw = get_favorites(user_id)
            vacancies = [get_vacancy_by_id(f.vacancy_id) for f in favorites_raw]
            vacancies = [v for v in vacancies if v]

            if vacancies:
                titles = [v.title for v in vacancies]
                user_fav = {
                    'ru': 'Ваши избранные:\n' + '\n'.join(titles),
                    'en': 'Your favorites:\n' + '\n'.join(titles),
                    'uz': 'Sizning tanlanganlaringiz:\n' + '\n'.join(titles)
                }
                bot.send_message(user_id, user_fav[language], reply_markup=create_or_delete(language, 'favorite'))
            else:
                user_fav = {'ru': 'Пусто.', 'en': 'Empty.', 'uz': 'Bosh.'}
                bot.send_message(user_id, user_fav[language], reply_markup=create_or_delete(language, 'favorite'))

        elif call.data == 'settings':
            bot.answer_callback_query(call.id, "Настройки...")
            bot.send_message(user_id, lang['settings_text'][language], reply_markup=settings_kb(language))

        elif call.data == 'my_vacancy':
            bot.answer_callback_query(call.id, "Мои вакансии...")
            vacancies = get_user_vacancies(user_id)
            random.shuffle(vacancies)

            if not vacancies:
                bot.send_message(user_id, lang['no_vacancy'][language], reply_markup=main_menu(user_id, language))
                return
            else:
                bot.send_message(user_id, lang['please_wait'][language])
                user_vacancies_list[user_id] = vacancies
                user_vacancy_index[user_id] = 0
                show_current_my_vacancy(bot, user_id, language)

        elif call.data == 'my_response':
            bot.answer_callback_query(call.id, "Мои отклики...")
            responses = get_user_responses(user_id)
            random.shuffle(responses)

            if not responses:
                bot.send_message(user_id, lang['no_response'][language], reply_markup=main_menu(user_id, language))
                return
            else:
                bot.send_message(user_id, lang['please_wait'][language])
                user_responses_list[user_id] = responses
                user_response_index[user_id] = 0
                show_current_response(bot, user_id, language)

        elif call.data == 'user_responses':
            bot.answer_callback_query(call.id, "Отклики...")
            responses = get_user_responses(user_id)
            random.shuffle(responses)

            if not responses:
                bot.send_message(user_id, lang['no_response'][language], reply_markup=main_menu(user_id, language))
                return
            else:
                bot.send_message(user_id, lang['please_wait'][language])
                user_responses_list[user_id] = responses
                user_response_index[user_id] = 0
                show_current_response(bot, user_id, language)


        elif call.data == 'category':
            bot.answer_callback_query(call.id, "Выберите категорию...")
            categories = get_user_categories(user_id)
            category_names = []
            for c in categories:
                try:
                    translated = GoogleTranslator(source='ru', target=language).translate(c.name)
                except Exception as e:
                    print(f"[ERROR translate category] {e}")
                    translated = c.name
                category_names.append(translated)
            if category_names:
                msg_text = {
                    'ru': 'Ваш выбор поиска по категориям:\n' + '\n'.join(category_names),
                    'en': 'Your selected job categories:\n' + '\n'.join(category_names),
                    'uz': 'Siz tanlagan ish kategoriyalari:\n' + '\n'.join(category_names)
                }
            else:
                msg_text = {
                    'ru': 'Вы не выбрали ни одной категории.',
                    'en': 'You have not selected any categories.',
                    'uz': 'Siz hali hech qanday kategoriya tanlamagansiz.'
                }
            bot.send_message(user_id, msg_text[language], reply_markup=create_or_delete(language, 'category'))

        elif call.data == 'create':
            bot.answer_callback_query(call.id, "Добавление...")
            bot.send_message(user_id, lang['choose_category'][language], reply_markup=category_keyboard(language))
            bot.register_next_step_handler_by_chat_id(user_id, lambda msg: choose_category(msg, language, 'add'))

        elif call.data == 'delete':
            bot.answer_callback_query(call.id, "Удаление...")
            bot.send_message(user_id, lang['del_category'][language], reply_markup=category_keyboard(language))
            bot.register_next_step_handler_by_chat_id(user_id, lambda msg: choose_category(msg, language, 'delete'))

        elif call.data == 'main_menu':
            bot.answer_callback_query(call.id, "Главное меню...")
            bot.send_message(user_id, 'MENU', reply_markup=main_menu(user_id, language))

    except Exception as e:
        print(f"[ERROR handle_main_menu] user_id: {user_id}, error: {e}")
        bot.answer_callback_query(call.id, lang['error'][language] if 'error' in lang else "Произошла ошибка")




def show_current_response(bot, user_id, language, call=None):
    responses = user_responses_list.get(user_id, [])
    index = user_response_index.get(user_id, 0)

    if not responses:
        bot.send_message(user_id, lang['no_response'][language], reply_markup=main_menu(user_id, language))
        return

    if index < 0 or index >= len(responses):
        index = 0

    response = responses[index]
    vacancy = get_vacancy_by_id(response.vacancy_id)
    user = get_user(response.user_id)

    try:
        translated_category = GoogleTranslator(source='ru', target=language).translate(vacancy.category)
    except Exception as e:
        print(f"[ERROR translate category] user_id: {user_id}, error: {e}")
        translated_category = vacancy.category  # fallback

    text = {
        'ru': f"📌 {vacancy.title}\n\n"
              f"📝 {vacancy.description}\n\n"
              f"💰 {vacancy.payment}\n"
              f"📂 Категория: {translated_category}\n"
              f"📍 Местоположение: {geolocator(vacancy.latitude, vacancy.longitude, language)}\n"
              f"📅 Создано: {vacancy.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
              f"👥 Откликнулся: {user.phone} {user.username}\n\n"
              f"📄 Отклик {index + 1} из {len(responses)}",
        'en': f"📌 {vacancy.title}\n\n"
              f"📝 {vacancy.description}\n\n"
              f"💰 {vacancy.payment}\n"
              f"📂 Category: {translated_category}\n"
              f"📍 Location: {geolocator(vacancy.latitude, vacancy.longitude, language)}\n"
              f"📅 Created: {vacancy.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
              f"👥 Responded: {user.phone} {user.username}\n\n"
              f"📄 Response {index + 1} of {len(responses)}",
        'uz': f"📌 {vacancy.title}\n\n"
              f"📝 {vacancy.description}\n\n"
              f"💰 {vacancy.payment}\n"
              f"📂 Kategoriya: {translated_category}\n"
              f"📍 Manzil: {geolocator(vacancy.latitude, vacancy.longitude, language)}\n"
              f"📅 Yaratilgan: {vacancy.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
              f"👥 Javob berdi: {user.phone} {user.username}\n\n"
              f"📄 Javob {index + 1} dan {len(responses)}"
    }

    markup = navigation(item_type='response')

    try:
        if call:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text[language],
                reply_markup=markup
            )
        else:
            bot.send_message(user_id, text[language], reply_markup=markup)
    except Exception as e:
        print(f"[ERROR show_current_response] user_id: {user_id}, error: {e}")
        bot.send_message(user_id, text[language], reply_markup=markup)

def show_current_my_vacancy(bot, user_id, language, call=None):
    vacancies = user_vacancies_list.get(user_id, [])
    index = user_vacancy_index.get(user_id, 0)

    if not vacancies:
        bot.send_message(user_id, lang['no_vacancy'][language], reply_markup=main_menu(user_id, language))
        return

    if index < 0 or index >= len(vacancies):
        index = 0

    vacancy = vacancies[index]
    responses_count = get_vacancy_responses_count(vacancy.id)

    try:
        translated_category = GoogleTranslator(source='ru', target=language).translate(vacancy.category)
    except Exception as e:
        print(f"[ERROR translate category] user_id: {user_id}, error: {e}")
        translated_category = vacancy.category  # fallback

    text = {
        'ru': f"📌 {vacancy.title}\n\n"
              f"📝 {vacancy.description}\n\n"
              f"💰 {vacancy.payment}\n"
              f"📂 Категория: {translated_category}\n"
              f"📍 Местоположение: {geolocator(vacancy.latitude, vacancy.longitude, language)}\n"
              f"👥 Откликов: {responses_count}\n"
              f"📅 Создано: {vacancy.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
              f"📄 Вакансия {index + 1} из {len(vacancies)}",
        'en': f"📌 {vacancy.title}\n\n"
              f"📝 {vacancy.description}\n\n"
              f"💰 {vacancy.payment}\n"
              f"📂 Category: {translated_category}\n"
              f"📍 Location: {geolocator(vacancy.latitude, vacancy.longitude, language)}\n"
              f"👥 Responses: {responses_count}\n"
              f"📅 Created: {vacancy.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
              f"📄 Vacancy {index + 1} of {len(vacancies)}",
        'uz': f"📌 {vacancy.title}\n\n"
              f"📝 {vacancy.description}\n\n"
              f"💰 {vacancy.payment}\n"
              f"📂 Kategoriya: {translated_category}\n"
              f"📍 Manzil: {geolocator(vacancy.latitude, vacancy.longitude, language)}\n"
              f"👥 Javoblar: {responses_count}\n"
              f"📅 Yaratilgan: {vacancy.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
              f"📄 Vakansiya {index + 1} dan {len(vacancies)}"
    }

    markup = navigation(item_type='vacancy')

    try:
        if call:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text[language],
                reply_markup=markup
            )
        else:
            bot.send_message(user_id, text[language], reply_markup=markup)
    except Exception as e:
        print(f"[ERROR show_current_my_vacancy] user_id: {user_id}, error: {e}")
        bot.send_message(user_id, text[language], reply_markup=markup)


@bot.callback_query_handler(
    func=lambda call: call.data in ['response_prev', 'response_next', 'job_prev', 'job_next'])
def paginate_items(call):
    user_id = call.from_user.id
    user = get_user(user_id)
    language = user.language if user else 'ru'
    try:
        if call.data in ['response_prev', 'response_next']:
            if user_id not in user_responses_list or not user_responses_list[user_id]:
                bot.answer_callback_query(call.id, lang['no_response'][language])
                bot.send_message(user_id, lang['no_response'][language], reply_markup=main_menu(user_id, language))
                return

            index = user_response_index.get(user_id, 0)
            if call.data == 'response_prev':
                user_response_index[user_id] = max(index - 1, 0)
            elif call.data == 'response_next':
                user_response_index[user_id] = min(index + 1, len(user_responses_list[user_id]) - 1)
            show_current_response(bot, user_id, language, call)

        elif call.data in ['job_prev', 'job_next']:
            if user_id not in user_vacancies_list or not user_vacancies_list[user_id]:
                bot.answer_callback_query(call.id, lang['no_vacancy'][language])
                bot.send_message(user_id, lang['no_vacancy'][language], reply_markup=main_menu(user_id, language))
                return

            index = user_vacancy_index.get(user_id, 0)
            if call.data == 'job_prev':
                user_vacancy_index[user_id] = max(index - 1, 0)
            elif call.data == 'job_next':
                user_vacancy_index[user_id] = min(index + 1, len(user_vacancies_list[user_id]) - 1)
            show_current_my_vacancy(bot, user_id, language, call)

    except Exception as e:
        print(f"[ERROR paginate_items] user_id: {user_id}, error: {e}")
        bot.answer_callback_query(call.id, lang['error'][language] if 'error' in lang else "Произошла ошибка")