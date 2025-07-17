import logging
import traceback
from config import bot
from services.service import initialize_categories, delete_expired_vacancies, delete_expired_responses,create_cost
from handlers import admin, find_job, register, vacancy, menu, favorites, settings

# Настройка детального логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    try:
        print("Запуск бота...")
        print(f"Токен бота: {bot.token[:10]}...")
        me = bot.get_me()
        print(f"Бот успешно подключен: @{me.username}")
        print("Бот готов к получению сообщений...")
        bot.infinity_polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"Ошибка в polling: {e}")
        traceback.print_exc()




if __name__ == '__main__':
    initialize_categories()
    delete_expired_vacancies()
    delete_expired_responses()
    create_cost()
    main()