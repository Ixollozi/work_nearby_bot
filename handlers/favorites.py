from services.buttons import *
from services.service import *
from configuration.utils import *
from configuration.config import user_state

@bot.callback_query_handler(func=lambda call: call.data.startswith('favorite_delete_'))
def favorites(call):
    user_state[call.from_user.id] = 'awaiting_favorites'
    user_id = call.from_user.id
    user = get_user(user_id)
    language = user.language
    # favorite_id = user_favorites_list[user_id][user_favorite_index[user_id]].id
    favorite_id = call.data.replace('favorite_delete_', '')
    if call.data == f'favorite_delete_{favorite_id}':
        bot.send_message(call.message.chat.id, lang['delete_favorites'][language], reply_markup=agree(language))
        bot.register_next_step_handler(call.message, delete_favorite, language, favorite_id)

@safe_step
def delete_favorite(message, language, favorite_id):
    user_state[message.from_user.id] = 'awaiting_delete_favorites'
    text = message.text
    if text == '❌ Отменить' or text == '❌ Cancel' or text == '❌ Bekor qilish':
        bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
        return

    elif text == '✅ Подтвердить' or text == '✅ Confirm' or text == '✅ Tasdiqlash':
        try:
            delete_user_favorite(message.from_user.id, favorite_id)
            bot.send_message(message.chat.id, lang['delete_favorite_success'][language],
                             reply_markup=ReplyKeyboardRemove())
            bot.send_message(message.chat.id, 'MENU', reply_markup=main_menu(message.from_user.id, language))
        except Exception as e:
            print(f"[ERROR delete_favorite] {e}")
