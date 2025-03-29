import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from dotenv import load_dotenv
from yookassa import Configuration, Payment


# Заглушка "базы данных" букетов
BOUQUETS_DB = {
    "Белый": {
        "~500": {
            "photo": "https://violetflowers.ru/upload/resize_cache/iblock/210/800_800_1445b4302703fbf0bc9433e7bed9bfe3d/210b4d1c9970e1fcdd65812bbac7b7c8.jpeg",
            "name": "Нежность",
            "composition": "5 белых роз, гипсофила",
            "price_payment": 500.00,
            "price": "500 руб."
        },
        "~1000": {
            "photo": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRBOg1pSSompNpXp8C0nvbUzFDpNWCoGq_PMQ&s",
            "name": "Снежная королева",
            "composition": "15 белых роз, эвкалипт",
            "price_payment": 1000.00,
            "price": "1000 руб."
        }
    },
    "Розовый": {
        "~1000": {
            "photo": "https://www.beauty-flowers-moscow.ru/wp-content/uploads/2017/12/11-rozovyh-pionov-v-rozovoj-upakovke.jpg",
            "name": "Розовые мечты",
            "composition": "11 розовых роз, пионы",
            "price_payment": 1000.00,
            "price": "1000 руб."
        }
    }
}


def setup_yookassa():
    """Настраивает подключение к ЮKassa."""
    load_dotenv()
    shop_id = os.getenv('YOOKASSA_SHOP_ID')
    secret_key = os.getenv('YOOKASSA_SECRET_KEY')
    Configuration.account_id = shop_id
    Configuration.secret_key = secret_key


def start(update: Update, context: CallbackContext):
    """Отправляет приветственное сообщение и запрашивает согласие."""
    user = update.effective_user
    context.user_data.clear()
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
    context.user_data['step'] = 'consent'


def handle_consent(update: Update, context: CallbackContext):
    """Обрабатывает нажатие кнопки "Да" или "Нет"."""
    user_response = update.message.text
    if user_response == "Да":
        context.user_data['consent_given'] = True
        context.user_data['step'] = 'occasion_choice'
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
        context.user_data.clear() # можно и без этого - при старте обновится
    else:
        update.message.reply_text("Пожалуйста, используй кнопки ниже.")


def handle_occasion_choice(update: Update, context: CallbackContext):
    """Обрабатывает выбор повода и предлагает выбор цвета."""
    occasion = update.message.text
    context.user_data['occasion'] = occasion
    context.user_data['step'] = 'color_choice'

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
    context.user_data['step'] = 'price_choice'

    prices = ["~500", "~1000", "~2000", "Больше", "Не важно"]
    keyboard = [[KeyboardButton(price)] for price in prices]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        "На какую сумму рассчитываете?",
        reply_markup=reply_markup
    )


def handle_price_choice(update: Update, context: CallbackContext):
    """Показывает подобранный букет и спрашивает 'Нравится?'"""
    price = update.message.text
    color = context.user_data['color']
    bouquet = BOUQUETS_DB.get(color, {}).get(price)

    context.user_data['step'] = 'review'

    if not bouquet:
        update.message.reply_text(
            "К сожалению, сейчас нет букетов с такими параметрами 😢\n"
            "Попробуй изменить критерии поиска (/start)",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    context.user_data['bouquet_price'] = bouquet['price_payment']
    context.user_data['selected_bouquet'] = bouquet

    decription = (
        f"💐 *{bouquet['name']}*\n"
        f"🎨 Цвет: {color}\n"
        f"💰 Цена: {bouquet['price']}\n"
        f"🌸 Состав: {bouquet['composition']}\n\n"
        "Тебе нравится этот вариант?"
    )
    context.user_data['selected_bouquet'] = bouquet
    update.message.reply_photo(
        photo=bouquet['photo'],
        caption=decription,
        parse_mode="Markdown"
    )
    keyboard = [[KeyboardButton("Нравится"), KeyboardButton("Не нравится")]]
    update.message.reply_text(
        "Выбери вариант:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


def handle_review(update: Update, context: CallbackContext):
    """Обрабатывает ответ 'Нравится?'"""
    response = update.message.text
    bouquet = context.user_data.get('selected_bouquet')

    if not bouquet:
        return start(update, context)

    if response == "Нравится":
        keyboard = [
            [InlineKeyboardButton("💳 Оплатить заказ", callback_data="payment")],
            [InlineKeyboardButton("🚚 Узнать о доставке", callback_data="delivery")],
            [InlineKeyboardButton("💐 Посмотреть другие букеты", callback_data="other_bouquets")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text(
            "Супер! Вот доступные варианты:",
            reply_markup=reply_markup
        )
        context.user_data['step'] = 'final_options'
    elif response == "Не нравится":
        update.message.reply_text(
            "Хочешь:\n"
            "1️⃣ Подобрать другой букет (/start)\n"
            "2️⃣ Позвать флориста\n\n"
            "Напиши номер варианта",
            reply_markup=ReplyKeyboardRemove()
        )
        # context.user_data['step'] = '?' перенаправление на консультацию или новый букет
    else:
        update.message.reply_text("Пожалуйста, ответь 'Нравится' или 'Не нравится'")


def handle_callback_query(update: Update, context: CallbackContext):
    """Обрабатывает нажатия inline кнопок"""
    query = update.callback_query
    query.answer()

    if query.data == "payment":
        bouquet = context.user_data.get('selected_bouquet', {})
        bouquet_price = bouquet.get('price_payment', 100.00)
        bouquet_name = bouquet.get('name', 'букет')

        payment = Payment.create({
            "amount": {
                "value": f"{bouquet_price:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/your_bot_username"
            },
            "capture": True,
            "description": f"Оплата букета '{bouquet_name}'",
            "metadata": {
                "user_id": query.from_user.id,
                "bouquet": bouquet_name
            }
        })

        keyboard = [[InlineKeyboardButton("Перейти к оплате", url=payment.confirmation.confirmation_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(
            text=f"Для оплаты {bouquet['price']} за букет '{bouquet_name}' перейдите по ссылке:",
            reply_markup=reply_markup
        )

    elif query.data == "delivery":
        query.edit_message_text(
            text="🚚 Доставка осуществляется в течение 2 часов после оплаты заказа. "
                 "Стоимость доставки - 200 руб. в пределах города."
        )
    elif query.data == "other_bouquets":
        context.user_data.clear()
        start(update, context)


def route_message(update: Update, context: CallbackContext):
    """Промежуточная функция — распределитель сообщений."""
    step = context.user_data.get('step')
    text = update.message.text  # для логов оставим пока

    if step == 'consent':
        handle_consent(update, context)
    elif step == 'occasion_choice':
        handle_occasion_choice(update, context)
    elif step == 'color_choice':
        handle_color_choice(update, context)
    elif step == 'price_choice':
        handle_price_choice(update, context)
    elif step == 'review':
        handle_review(update, context)
    else:
        update.message.reply_text("Пожалуйста, выбери вариант из меню.")


def main():
    load_dotenv()
    setup_yookassa()

    tg_bot_token = os.getenv('TG_BOT_TOKEN')
    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher

    # Обработчики
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, route_message))
    dispatcher.add_handler(CallbackQueryHandler(handle_callback_query))

    print("Бот запущен!")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

