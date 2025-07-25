from configuration.config import bot

def safe_step(handler):
    def wrapper(message, *args, **kwargs):
        try:
            return handler(message, *args, **kwargs)
        except Exception as e:
            user_id = message.from_user.id
            print(f"[ERROR {handler.__name__}] {e}")
            bot.send_message(user_id, "Произошла ошибка. Попробуйте снова.")
            bot.register_next_step_handler(message, handler, *args, **kwargs)
    return wrapper