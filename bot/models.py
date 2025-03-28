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

    title = models.CharField('Название', max_length=200)
    photo = models.ImageField('Фото', upload_to='bouquets/')
    composition = models.TextField('Состав')
    description = models.TextField('Описание')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)

    color = models.CharField('Цвет', max_length=50, choices=COLOR_CHOICES, default="Розовый")
    price_category = models.CharField('Ценовая категория', max_length=50, choices=PRICE_CHOICES, default="~1000")

    def __str__(self):
        return f"{self.title} ({self.color}, {self.price} руб.)"


class Order(models.Model):
    name = models.CharField('Имя клиента', max_length=100)
    address = models.TextField('Адрес доставки')
    delivery_time = models.DateTimeField('Дата и время доставки')
    bouquet = models.ForeignKey('Bouquet', on_delete=models.CASCADE, verbose_name='Букет')
    comment = models.TextField('Комментарий', blank=True)
    is_consultation = models.BooleanField('Нужна консультация', default=False)

    def __str__(self):
        return f'Заказ от {self.name} ({self.delivery_time.strftime("%Y-%m-%d %H:%M")})'


class ConsultationRequest(models.Model):
    phone = models.CharField('Телефон', max_length=30)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    def __str__(self):
        return f'Запрос: {self.phone} ({self.created_at.strftime("%Y-%m-%d %H:%M")})'
