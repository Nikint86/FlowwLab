from django.db import models


class Bouquet(models.Model):
    COLOR_CHOICES = [
        ("Белый", "Белый"),
        ("Розовый", "Розовый"),
        ("Красный", "Красный"),
        # добавим по мере надобности
    ]

    PRICE_CHOICES = [
        ("~500", "~500"),
        ("~1000", "~1000"),
        ("~2000", "~2000"),
        ("Больше", "Больше"),
        ("Не важно", "Не важно"),
    ]

    OCCASION_CHOICES = [
        ("День рождения", "День рождения"),
        ("Свадьба", "Свадьба"),
        ("Школа", "Школа"),
        ("Без повода", "Без повода"),
        ("Другой", "Другой"),
    ]

    title = models.CharField('Название', max_length=200)
    photo = models.ImageField('Фото', upload_to='bouquets/')
    composition = models.TextField('Состав')
    description = models.TextField('Описание')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)

    color = models.CharField(
        'Цвет',
        max_length=50,
        choices=COLOR_CHOICES,
        default="Розовый"
    )
    occasion = models.CharField(
        'Повод',
        max_length=50,
        choices=OCCASION_CHOICES,
        blank=True,
        default='',
        help_text='Например: День рождения, Свадьба и т.д.'
    )

    price_category = models.CharField('Ценовая категория', max_length=50, choices=PRICE_CHOICES, default="~1000")

    def __str__(self):
        return f"{self.title} ({self.color}, {self.price} руб.)"


class Order(models.Model):
    name = models.CharField('Имя клиента', max_length=100, blank=True, default='не указано')
    phone = models.CharField('Телефон клиента', max_length=30, blank=True, default='не указан')
    address = models.TextField('Адрес доставки')
    delivery_time = models.DateTimeField('Дата и время доставки')
    bouquet = models.ForeignKey('Bouquet', on_delete=models.CASCADE, verbose_name='Букет')
    comment = models.TextField('Комментарий', blank=True)
    is_consultation = models.BooleanField('Нужна консультация', default=False)

    def __str__(self):
        return f'Заказ от {self.name} ({self.delivery_time.strftime("%Y-%m-%d %H:%M")})'


class ConsultationRequest(models.Model):
    name = models.CharField('Имя клиента', max_length=100, blank=True, default='неизвестно')
    telegram_username = models.CharField('Telegram username', max_length=100, blank=True)
    phone = models.CharField('Телефон', max_length=30, blank=True, default='не указан')
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    def __str__(self):
        return f'Запрос: {self.name} ({self.created_at.strftime("%Y-%m-%d %H:%M")})'
