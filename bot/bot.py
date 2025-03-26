import os
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv


def start(update):
    event_buttons = [
        ["День рождения", "Свадьба"],
        ["В школу", "Без повода"],
        ["Другой повод"]
    ]
    update.message.reply_text(
        "К какому событию готовимся? Выберите вариант:",
        reply_markup=ReplyKeyboardMarkup(event_buttons, one_time_keyboard=True)
    )


def main():
    load_dotenv()
    tg_bot_token = os.getenv('TG_BOT_TOKEN')
    updater = Updater(tg_bot_token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    print("Бот запущен!")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
