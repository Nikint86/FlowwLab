import os
import sys
import django
from django.conf import settings

# Добавляем абсолютный путь до корня проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


import random
import pytz
import re

from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv
from bot.models import Bouquet, Order, ConsultationRequest


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
        context.user_data.clear()
    else:
        update.message.reply_text("Пожалуйста, используй кнопки ниже.")


def handle_occasion_choice(update: Update, context: CallbackContext):
    """Обрабатывает выбор повода и предлагает выбор цвета."""
    occasion = update.message.text
    context.user_data['occasion'] = occasion
    
    if occasion == "Другой повод":
        context.user_data['step'] = 'custom_occasion'
        update.message.reply_text("Напиши, пожалуйста, какой у тебя повод?")
    else:
        context.user_data['step'] = 'color_choice'
        colors = Bouquet.objects.values_list('color', flat=True).distinct()
        keyboard = [[KeyboardButton(color)] for color in colors]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        update.message.reply_text(
            "Какой цвет букета предпочитаешь?",
            reply_markup=reply_markup
        )


def handle_custom_occasion(update: Update, context: CallbackContext):
    """обрабатывает персональный повод"""
    context.user_data['custom_occasion'] = update.message.text
    context.user_data['step'] = 'color_choice'

    colors = Bouquet.objects.values_list('color',
                                         flat=True).distinct()
    keyboard = [[KeyboardButton(color)] for color in colors]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       resize_keyboard=True)

    update.message.reply_text(
        "Какой цвет букета предпочитаешь?",
        reply_markup=reply_markup
    )


def handle_color_choice(update: Update, context: CallbackContext):
    """Обрабатывает выбор цвета и предлагает выбрать цену."""
    color = update.message.text
    context.user_data['color'] = color
    context.user_data['step'] = 'price_choice'

    prices = list(Bouquet.objects.values_list('price_category',
                                              flat=True).distinct())
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
        f"{bouquet.description}\n\n"
        "Тебе нравится этот вариант?"
    )

    with open(bouquet.photo.path, 'rb') as image:
        update.message.reply_photo(
            photo=InputFile(image),
            caption=caption,
            parse_mode="Markdown"
        )
    keyboard = [[KeyboardButton("Заказать букет")],
                [KeyboardButton("Заказать консультацию"),
                 KeyboardButton("Посмотреть всю коллекцию")]]
    update.message.reply_text(
        "<b>Хотите что-то еще более уникальное?</b>\n\n"
        "Подберите другой букет из нашей коллекции или закажите консультацию флориста:",
        reply_markup=ReplyKeyboardMarkup(keyboard,
                                         resize_keyboard=True),
        parse_mode="HTML"
    )


def handle_review(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "Нравится":
        return handle_order_bouquet(update, context)
    elif text == "Не нравится":
        return handle_show_collection(update, context)
    elif text == "Заказать букет":
        return handle_order_bouquet(update, context)
    elif text == "Заказать консультацию":
        return handle_consultation(update, context)
    elif text == "Посмотреть всю коллекцию":
        return handle_show_collection(update, context)
    else:
        update.message.reply_text("Пожалуйста, выбери вариант из меню.")


def handle_dislike_options(update: Update, context: CallbackContext):
    choice = update.message.text
    if choice == "Посмотреть другой букет":
        bouquets = list(Bouquet.objects.all())
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
            f"{bouquet.description}\n\n"
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
        context.user_data['step'] = 'get_consultation_phone'


def handle_order_bouquet(update: Update, context: CallbackContext):
    """Обрабатывает кнопку - Заказать букет"""
    context.user_data['step'] = 'get_name'
    
    update.message.reply_text(
        "Отлично! Давайте оформим заказ.\n\n"
        "Пожалуйста, введите ваше ФИО:",
        reply_markup=ReplyKeyboardRemove()
    )


def handle_show_collection(update: Update, context: CallbackContext):
    """Обрабатывает кнопку - Посмотреть всю коллекцию"""
    bouquets = list(Bouquet.objects.all())
    if not bouquets:
        update.message.reply_text("К сожалению, в коллекции пока ничего нет.")
        return

    bouquet = random.choice(bouquets)
    context.user_data['selected_bouquet'] = bouquet
    context.user_data['step'] = 'review'

    caption = (
        f"💐 *{bouquet.title}*\n"
        f"🌸 Состав: {bouquet.composition}\n"
        f"💰 Цена: {bouquet.price} руб.\n\n"
        f"{bouquet.description}\n\n"
        "Тебе нравится этот вариант?"
    )
    with open(bouquet.photo.path, 'rb') as image:
        update.message.reply_photo(photo=InputFile(image), caption=caption, parse_mode="Markdown")

    keyboard = [[KeyboardButton("Заказать букет")],
                [KeyboardButton("Заказать консультацию"),
                KeyboardButton("Посмотреть всю коллекцию")]]
    update.message.reply_text(
        "**Хотите что-то еще более уникальное?**\n\n"
        "Подберите другой букет из нашей коллекции или закажите консультацию флориста:",
        reply_markup=ReplyKeyboardMarkup(keyboard,
                                         resize_keyboard=True)
    )


def handle_consultation(update: Update, context: CallbackContext):
    """Обрабатывает запрос консультации"""
    context.user_data['step'] = 'get_consultation_phone'
    update.message.reply_text("Пожалуйста, укажите номер телефона в формате +71234567890 или 81234567890:")


def is_valid_phone(phone):
    return re.match(r'^(\+7|8)[0-9]{10}$', phone.replace(" ", "")) is not None


def handle_get_phone_for_order(update: Update, context: CallbackContext):
    phone = update.message.text
    if not is_valid_phone(phone):
        update.message.reply_text(
            "Неверный формат номера. Пожалуйста, укажите номер в формате +71234567890 или 81234567890"
            )
        return

    context.user_data['phone'] = phone
    return finalize_order(update, context)


def finalize_order(update: Update, context: CallbackContext):
    """Сохраняет заказ, отправляет клиенту подтверждение и уведомляет курьера"""
    phone = context.user_data['phone']
    name = context.user_data['name']
    address = context.user_data['address']
    bouquet = context.user_data['selected_bouquet']
    date_str = context.user_data['delivery_date']
    time = context.user_data['delivery_time']

    today = datetime.today()
    if date_str == "Сегодня":
        date_obj = today
    elif date_str == "Завтра":
        date_obj = today + timedelta(days=1)
    elif date_str == "Послезавтра":
        date_obj = today + timedelta(days=2)
    else:
        date_obj = today

    time_start = time.split("-")[0]
    delivery_dt = datetime.strptime(
        f"{date_obj.strftime('%Y-%m-%d')} {time_start}",
                                    "%Y-%m-%d %H:%M"
                                    )

    # Сохраняем заказ в БД
    Order.objects.create(
        name=name,
        address=address,
        phone=phone,
        delivery_time=delivery_dt,
        bouquet=bouquet,
        comment="",
        is_consultation=False,
    )

    # Формируем и отправляем сводку
    order_summary = (
        "✅ Ваш заказ оформлен!\n\n"
        f"💐 Букет: {bouquet.title}\n"
        f"💰 Стоимость: {bouquet.price} руб.\n"
        f"🌸 Состав: {bouquet.composition}\n"
        f"{bouquet.description}\n\n"
        f"👤 Получатель: {name}\n"
        f"🏠 Адрес: {address}\n"
        f"📅 Дата: {date_str}\n"
        f"⏰ Время: {time}\n\n"
        "Спасибо за заказ! 🥰 С вами скоро свяжется наш менеджер."
    )

    with open(bouquet.photo.path, 'rb') as image:
        update.message.reply_photo(photo=InputFile(image), caption=order_summary)

    update.message.reply_text("Ваш заказ принят! 💐",
                              reply_markup=ReplyKeyboardRemove())
    
    notify_courier(context.bot, bouquet, order_summary)

    context.user_data.clear()


def handle_get_phone_for_consultation(update: Update, context: CallbackContext):
    phone = update.message.text
    if not is_valid_phone(phone):
        update.message.reply_text(
            "Неверный формат номера. Пожалуйста, укажите номер в формате +71234567890 или 81234567890"
            )
        return
    
    context.user_data['phone'] = phone
    name = context.user_data.get('name', 'неизвестно')
    username = update.message.from_user.username or ''

    ConsultationRequest.objects.create(
        name=name,
        telegram_username=username,
        phone=phone
    )

    florist_id = os.getenv("FLORIST_CHAT_ID")
    if florist_id:
        context.bot.send_message(
            chat_id=florist_id,
            text=f"Новая заявка на консультацию\nТелефон: {phone}\n\n"
            f"Пользователь: @{username}"
        )

    update.message.reply_text(
        "Номер принят. А пока можете присмотреть что-нибудь из уже готовой коллекции 👇"
        )
    return handle_show_collection(update, context)


def handle_get_phone(update: Update, context: CallbackContext):

    phone = update.message.text
    if not re.match(r'^(\+7|8)[0-9]{10}$', phone.replace(" ", "")):
        update.message.reply_text("Неверный формат номера. Пожалуйста, укажите номер в формате +71234567890 или 81234567890 (11 цифр без пробелов и разделителей)")
        return
    context.user_data['phone'] = phone
    name = context.user_data.get('name', 'неизвестно')
    username = update.message.from_user.username or ''
    
    ConsultationRequest.objects.create(
        name=name,
        telegram_username=username,
        phone=phone
    )

    florist_id = os.getenv("FLORIST_CHAT_ID")
    if florist_id:
        context.bot.send_message(
            chat_id=florist_id,
            text=f"Новая заявка на консультацию\n"
                 f"Телефон: {phone}\n"
                 f"Пользователь: @{username}"
        )
    update.message.reply_text(
        "Номер принят. А пока можете присмотреть что-нибудь из готовой коллекции 👇"
    )

    # Покажем букет
    bouquets = list(Bouquet.objects.all())
    if bouquets:
        bouquet = random.choice(bouquets)
        context.user_data['selected_bouquet'] = bouquet
        context.user_data['step'] = 'review'
        caption = (
            f"💐 *{bouquet.title}*\n"
            f"🌸 Состав: {bouquet.composition}\n"
            f"💰 Цена: {bouquet.price} руб.\n\n"
            f"{bouquet.description}\n\n"
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


def get_delivery_datetime(date_str: str, time_str: str) -> datetime:
    """Преобразует выбор пользователя в datetime доставки"""
    today = datetime.today()
    if date_str == "Сегодня":
        date_obj = today
    elif date_str == "Завтра":
        date_obj = today + timedelta(days=1)
    elif date_str == "Послезавтра":
        date_obj = today + timedelta(days=2)
    else:
        date_obj = today  # fallback, если пришло что-то странное

    time_start = time_str.split("-")[0]
    delivery_dt = datetime.strptime(
        f"{date_obj.strftime('%Y-%m-%d')} {time_start}",
        "%Y-%m-%d %H:%M"
    )
    return delivery_dt


def handle_date_input(update: Update, context: CallbackContext):
    """Обрабатывает ввод даты и предлагает выбрать временной интервал"""
    user_data_choice = update.message.text
    now = datetime.now(pytz.timezone('Europe/Moscow'))

    if user_data_choice not in ["Сегодня", "Завтра", "Послезавтра"]:
        update.message.reply_text("Пожалуйста, выберите дату из предложенных вариантов.")
        return

    context.user_data['delivery_date'] = user_data_choice
    context.user_data['step'] = 'get_time'

    # Определяем доступные интервалы
    all_slots = [
        ("10:00-12:00", 10),
        ("12:00-14:00", 12),
        ("14:00-16:00", 14),
        ("16:00-18:00", 16)
    ]

    if user_data_choice == "Сегодня":
        current_hour = now.hour
        available_slots = [slot for slot, hour in all_slots if hour > current_hour]
        if not available_slots:
            update.message.reply_text(
                "❌ На сегодня все временные интервалы уже прошли.\n"
                "Пожалуйста, выберите другую дату:",
                reply_markup=ReplyKeyboardMarkup(
                    [[KeyboardButton("Завтра")], [KeyboardButton("Послезавтра")]],
                    resize_keyboard=True
                )
            )
            return
    else:
        available_slots = [slot for slot, _ in all_slots]

    keyboard = [[KeyboardButton(slot)] for slot in available_slots]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        "Выберите удобный интервал доставки:",
        reply_markup=reply_markup
    )


def handle_time_input(update: Update, context: CallbackContext):
    """Обрабатывает ввод времени и переходит к сбору номера телефона"""
    time_str = update.message.text
    context.user_data['delivery_time'] = time_str

    date_str = context.user_data.get('delivery_date')
    try:
        delivery_dt = get_delivery_datetime(date_str, time_str)
    except ValueError:
        update.message.reply_text(
            "Ошибка в формате времени. Попробуйте снова."
            )
        return

    context.user_data['delivery_dt'] = delivery_dt
    context.user_data['step'] = 'get_order_phone'

    update.message.reply_text(
        "Пожалуйста, укажите номер телефона для доставки (в формате +71234567890 или 81234567890):",
        reply_markup=ReplyKeyboardRemove()
    )


def notify_courier(bot, bouquet, order_summary):
    courier_id = os.getenv("COURIER_CHAT_ID")
    if not courier_id:
        print("COURIER_CHAT_ID не установлен в переменных окружения")
        return
    with open(bouquet.photo.path, 'rb') as image:
        bot.send_photo(
            chat_id=courier_id,
            photo=InputFile(image),
            caption=order_summary
        )


def route_message(update: Update, context: CallbackContext):
    """Маршрутизирует входящие сообщения в зависимости от текущего шага пользователя."""
    step = context.user_data.get('step')
    text = update.message.text

    handlers = {
        'consent': handle_consent,
        'occasion_choice': handle_occasion_choice,
        'custom_occasion': handle_custom_occasion,
        'color_choice': handle_color_choice,
        'price_choice': handle_price_choice,
        'review': handle_review,
        'get_name': handle_name_input,
        'get_address': handle_address_input,
        'get_date': handle_date_input,
        'get_time': handle_time_input,
        'get_consultation_phone': handle_get_phone_for_consultation,
        'get_order_phone': handle_get_phone_for_order,
        'dislike_options': handle_dislike_options,
    }

    handler = handlers.get(step)
    if handler:
        handler(update, context)
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
