from services.buttons import *
from services.service import *
from configuration.utils import *
from configuration.config import user_state

@bot.callback_query_handler(func=lambda call: call.data in [ 'favorite_delete'])
def favorites(call):
    user_state[call.from_user.id] = 'awaiting_favorites'
    user_id = call.from_user.id
    user = get_user(user_id)
    language = user.language
    if call.data == 'favorite_delete':
        bot.send_message(call.message.chat.id, lang['delete_favorites'][language], reply_markup=delete_favorite_kb(user_id))
        bot.register_next_step_handler(call.message, delete_favorite, language)

@safe_step
def delete_favorite(message, language):
    user_state[message.from_user.id] = 'awaiting_delete_favorites'
    favorite_name = message.text
    vacancy = get_vacancy_by_title(favorite_name)
    if favorite_name == '❌ Отменить':
        bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
        return

    success = delete_user_favorite(user_id=message.from_user.id, vacancy_id=vacancy.id)
    if success:
        bot.send_message(message.chat.id, lang['delete_favorite_success'][language], reply_markup=main_menu(message.from_user.id, language))
    else:
        bot.send_message(message.chat.id, lang['delete_favorite_error'][language])
        bot.register_next_step_handler(message, delete_favorite, language)
