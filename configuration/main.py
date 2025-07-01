import logging
import traceback
from config import bot
from handlers import admin, find_job, register, vacancy, menu, favorites

# Настройка детального логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    try:
        print("Запуск бота...")
        print(f"Токен бота: {bot.token[:10]}...")  # Показываем только первые 10 символов

        # Проверяем соединение с Telegram API
        me = bot.get_me()
        print(f"Бот успешно подключен: @{me.username}")

        # Запускаем бота
        print("Бот готов к получению сообщений...")
        bot.infinity_polling(none_stop=True, interval=0, timeout=20)

    except Exception as e:
        print(f"Критическая ошибка при запуске бота: {e}")
        print("Подробная информация об ошибке:")
        traceback.print_exc()




if __name__ == '__main__':
    main()