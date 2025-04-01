import os
import sys
import django
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django.setup()

from telegram_bot.handlers import route_message, start


def main():
    load_dotenv()
    tg_bot_token = os.getenv("TG_BOT_TOKEN")
    updater = Updater(tg_bot_token)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, route_message))

    print("Бот запущен!")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
