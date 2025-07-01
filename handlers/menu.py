from handlers.find_job import *
from handlers.vacancy import create_job_name
import random


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
            if radius is None:
                radius = lang['all_vacancies'][language]


            vacancies_with_distance = get_vacancies_nearby(
                user.latitude,
                user.longitude,
                radius_meters=radius,
                categories=categories
            )

            random.shuffle(vacancies_with_distance)

            if not vacancies_with_distance:
                print('menu has no vacancy')
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

