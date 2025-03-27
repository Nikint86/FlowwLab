import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv


def start(update: Update, context: CallbackContext):
    """Отправляет приветственное сообщение и запрашивает согласие."""
    user = update.effective_user
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n"
        "Я бот, который поможет тебе с выбором букета.\n"
        "Продолжая, ты соглашаешься на обработку твоих данных. ✅\n"
        "Ты согласен?"
    )
    keyboard = [
        [KeyboardButton("Да"), KeyboardButton("Нет")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text(welcome_text, reply_markup=reply_markup)


def handle_consent(update: Update, context: CallbackContext):
    """Обрабатывает нажатие кнопки "Да" или "Нет"."""
    user_response = update.message.text
    if user_response == "Да":
        context.user_data['consent_given'] = True
        occasions = ["День рождения", "Свадьба", "Школа", "Без повода", "Другой повод"]
        keyboard = [[KeyboardButton(occasion)] for occasion in occasions]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        update.message.reply_text(
            "Отлично! Выбери повод:",
            reply_markup=reply_markup
        )
    elif user_response == "Нет":
        update.message.reply_text(
            "Хорошо, если передумаешь — возвращайся! 👋",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        update.message.reply_text("Пожалуйста, используй кнопки ниже.")


def handle_occasion_choice(update: Update, context: CallbackContext):
    """Обрабатывает выбор повода и предлагает выбор цвета."""
    occasion = update.message.text
    context.user_data['occasion'] = occasion

    if occasion == "Другой повод":
        update.message.reply_text("Напиши, пожалуйста, какой у тебя повод?")
    else:
        colors = ["Белый", "Розовый"]
        keyboard = [[KeyboardButton(color)] for color in colors]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        update.message.reply_text(
            "Какой цвет букета предпочитаешь?",
            reply_markup=reply_markup
        )


def handle_color_choice(update: Update, context: CallbackContext):
    """Обрабатывает выбор цвета и предлагает выбрать цену."""
    color = update.message.text
    context.user_data['color'] = color

    prices = ["~500", "~1000", "~2000", "Больше", "Не важно"]
    keyboard = [[KeyboardButton(price)] for price in prices]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        "На какую сумму рассчитываете?",
        reply_markup=reply_markup
    )


def route_message(update: Update, context: CallbackContext):
    """Промежуточная функция — распределитель сообщений."""
    text = update.message.text

    if 'consent_given' not in context.user_data:
        handle_consent(update, context)

    elif text in ["День рождения", "Свадьба", "Школа", "Без повода", "Другой повод"]:
        handle_occasion_choice(update, context)

    elif text in ["Белый", "Розовый"]:
        handle_color_choice(update, context)

    else:
        update.message.reply_text("Пожалуйста, выбери вариант из меню.")


def main():
    load_dotenv()
    tg_bot_token = os.getenv('TG_BOT_TOKEN')
    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    # Обработчики
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, route_message))

    print("Бот запущен!")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
