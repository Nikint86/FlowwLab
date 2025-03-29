import os
import sys
import django
from django.conf import settings

# Добавляем абсолютный путь до корня проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


import os
import random

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv
from bot.models import Bouquet


# Заглушка "базы данных" букетов
BOUQUETS_DB = {
    "Белый": {
        "~500": {
            "photo": "https://violetflowers.ru/upload/resize_cache/iblock/210/800_800_1445b4302703fbf0bc9433e7bed9bfe3d/210b4d1c9970e1fcdd65812bbac7b7c8.jpeg",
            "name": "Нежность",
            "composition": "5 белых роз, гипсофила",
            "price": "500 руб."
        },
        "~1000": {
            "photo": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRBOg1pSSompNpXp8C0nvbUzFDpNWCoGq_PMQ&s",
            "name": "Снежная королева",
            "composition": "15 белых роз, эвкалипт",
            "price": "1000 руб."
        }
    },
    "Розовый": {
        "~1000": {
            "photo": "https://www.beauty-flowers-moscow.ru/wp-content/uploads/2017/12/11-rozovyh-pionov-v-rozovoj-upakovke.jpg",
            "name": "Розовые мечты",
            "composition": "11 розовых роз, пионы",
            "price": "1000 руб."
        }
    }
}


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
        colors = Bouquet.objects.values_list('color', flat=True).distinct()
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

    prices = list(Bouquet.objects.values_list('price_category', flat=True).distinct())
    keyboard = [[KeyboardButton(price)] for price in prices]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        "На какую сумму рассчитываете?",
        reply_markup=reply_markup
    )


def handle_price_choice(update: Update, context: CallbackContext):
    """Показывает подобранный букет и спрашивает 'Нравится?'"""
    price_category = update.message.text
    color = context.user_data['color']
    bouquet = Bouquet.objects.filter(color=color,
                                     price_category=price_category).order_by('?').first()

    context.user_data['step'] = 'review'

    if not bouquet:
        update.message.reply_text(
            "К сожалению, сейчас нет букетов с такими параметрами 😢\n"
            "Попробуй изменить критерии поиска (/start)",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    context.user_data['selected_bouquet'] = bouquet

    caption = (
        f"💐 *{bouquet.title}*\n"
        f"🎨 Цвет: {bouquet.color}\n"
        f"💰 Цена: {bouquet.price} руб.\n"
        f"🌸 Состав: {bouquet.composition}\n\n"
        "Тебе нравится этот вариант?"
    )

    with open(bouquet.photo.path, 'rb') as image:
        update.message.reply_photo(
            photo=InputFile(image),
            caption=caption,
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
        context.user_data['step'] = 'get_name'
        update.message.reply_text(
            "Отлично! Давайте оформим заказ.\n\n"
            "Пожалуйста, введите ваше ФИО:",
            reply_markup=ReplyKeyboardRemove()
        )
    elif response == "Не нравится":
        keyboard = [[KeyboardButton("Заказать консультацию")], [KeyboardButton("Посмотреть другой букет")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        update.message.reply_text(
            "**Хотите что-то более уникальное?**\n\n"
            "Подберите другой букет из нашей коллекции или закажите консультацию флориста:",
            reply_markup=reply_markup
        )
        context.user_data['step'] = 'dislike_options'

        # context.user_data['step'] = '?' перенаправление на консультацию или новый букет
    else:
        update.message.reply_text("Пожалуйста, ответь 'Нравится' или 'Не нравится'")


def handle_dislike_options(update: Update, context: CallbackContext):
    choice = update.message.text
    if choice == "Посмотреть другой букет":
        bouquets = list(Bouquet.objects.all()) # все наверное перебор, но хз
        if not bouquets:
            update.message.reply_text("Пока нет букетов в базе. Попробуй позже.")
            return

        bouquet = random.choice(bouquets)
        context.user_data['selected_bouquet'] = bouquet
        context.user_data['step'] = 'review'

        caption = (
            f"💐 *{bouquet.title}*\n"
            f"🌸 Состав: {bouquet.composition}\n"
            f"💰 Цена: {bouquet.price} руб.\n\n"
            "Тебе нравится этот вариант?"
        )

        with open(bouquet.photo.path, 'rb') as image:
            update.message.reply_photo(
                photo=InputFile(image),
                caption=caption,
                parse_mode="Markdown"
            )

        keyboard = [[KeyboardButton("Нравится"),
                     KeyboardButton("Не нравится")]]
        update.message.reply_text("Выбери вариант:",
                                  reply_markup=ReplyKeyboardMarkup(keyboard,
                                                                   resize_keyboard=True))

    elif choice == "Заказать консультацию":
        update.message.reply_text("Пожалуйста, укажите номер телефона:")
        context.user_data['step'] = 'get_phone'


def handle_get_phone(update: Update, context: CallbackContext):
    phone = update.message.text
    # florist_id = 987654321  # нужен айди - при отправке сейчас будет ошибка

    # context.bot.send_message(
    #     chat_id=florist_id,
    #     text=f"📞 Заявка на консультацию!\nНомер: {phone}"
    # )

    update.message.reply_text(
        "Флорист скоро свяжется с вами. А пока можете присмотреть что-нибудь из готовой коллекции 👇"
    )

    # Покажем букет
    bouquets = list(Bouquet.objects.all()) # возможно стоит не all использовать
    if bouquets:
        bouquet = random.choice(bouquets)

        context.user_data['selected_bouquet'] = bouquet

        caption = (
            f"💐 *{bouquet.title}*\n"
            f"🌸 Состав: {bouquet.composition}\n"
            f"💰 Цена: {bouquet.price} руб.\n\n"
            "Тебе нравится этот вариант?"
        )

        with open(bouquet.photo.path, 'rb') as image:
            update.message.reply_photo(
                photo=InputFile(image),
                caption=caption,
                parse_mode="Markdown"
            )

        keyboard = [[KeyboardButton("Нравится"),
                     KeyboardButton("Не нравится")]]
        update.message.reply_text("Выбери вариант:",
                                  reply_markup=ReplyKeyboardMarkup(keyboard,
                                                                   resize_keyboard=True))


def handle_name_input(update: Update, context: CallbackContext):
    """Обрабатывает ввод ФИО"""
    name = update.message.text
    # Микро проверка
    if len(name.split()) < 2:
        update.message.reply_text("Пожалуйста, введите Фамилию Имя Отчество (полностью)")
        return
    context.user_data['name'] = name
    context.user_data['step'] = 'get_address'
    update.message.reply_text(
        "Теперь введите адрес доставки (город, улица, дом, квартира):"
    )


def handle_address_input(update: Update, context: CallbackContext):
    """Обрабатывает ввод адреса"""
    address = update.message.text
    context.user_data['address'] = address
    context.user_data['step'] = 'get_date'
    keyboard = [
        [KeyboardButton("Сегодня"), KeyboardButton("Завтра")],
        [KeyboardButton("Послезавтра")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        "Выберите дату доставки:",
        reply_markup=reply_markup
    )


def handle_date_input(update: Update, context: CallbackContext):
    """Обрабатывает ввод даты"""
    date = update.message.text
    context.user_data['delivery_date'] = date
    context.user_data['step'] = 'get_time'

    # Клавиатура с временными интервалами
    keyboard = [
        [KeyboardButton("10:00-12:00"), KeyboardButton("12:00-14:00")],
        [KeyboardButton("14:00-16:00"), KeyboardButton("16:00-18:00")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        "Выберите удобный интервал доставки:",
        reply_markup=reply_markup
    )


def handle_time_input(update: Update, context: CallbackContext):
    """Обрабатывает ввод времени и завершает заказ"""
    time = update.message.text
    context.user_data['delivery_time'] = time
    # Формируем сводку заказа
    bouquet = context.user_data['selected_bouquet']
    order_summary = (
        "✅ Ваш заказ оформлен!\n\n"
        f"💐 Букет: {bouquet.title}\n"
        f"💰 Стоимость: {bouquet.price} руб.\n"
        f"🌸 Состав: {bouquet.composition}\n"
        f"👤 Получатель: {context.user_data['name']}\n"
        f"🏠 Адрес: {context.user_data['address']}\n"
        f"📅 Дата: {context.user_data['delivery_date']}\n"
        f"⏰ Время: {time}\n\n"
        "Спасибо за заказ! 🥰 С вами скоро свяжется наш менеджер."
    )

    with open(bouquet.photo.path, 'rb') as image:
        update.message.reply_photo(
            photo=InputFile(image),
            caption=order_summary
        )

    update.message.reply_text("Ваш заказ принят! 💐",
                              reply_markup=ReplyKeyboardRemove())
    # notify_courier(context.bot, bouquet, order_summary)
    # courier_id = os.getenv("COURIER_ID")
    # with open(bouquet.photo.path, 'rb') as image:
    #     context.bot.send_photo(
    #         chat_id=courier_id,
    #         photo=InputFile(image),
    #         caption=order_summary
    #     ) -- наверное стоит вынести в отдельную функцию notify_courier и заиметь чат айди 
    # context.user_data.clear()
    # context.user_data['step'] = 'order_complete'


def notify_courier(bot, bouquet, order_summary):
    courier_id = os.getenv("COURIER_ID")
    if not courier_id:
        return  # можно логгер добавить
    with open(bouquet.photo.path, 'rb') as image:
        bot.send_photo(
            chat_id=courier_id,
            photo=InputFile(image),
            caption=order_summary
        )


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
    elif step == 'get_name':
        handle_name_input(update, context)
    elif step == 'get_address':
        handle_address_input(update, context)
    elif step == 'get_date':
        handle_date_input(update, context)
    elif step == 'get_time':
        handle_time_input(update, context)
    elif step == 'dislike_options':
        handle_dislike_options(update, context)
    elif step == 'get_phone':
        handle_get_phone(update, context)
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
