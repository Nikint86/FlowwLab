from django.db import models


class Bouquet(models.Model):
    title = models.CharField('Название', max_length=200)
    photo = models.ImageField('Фото', upload_to='bouquets/')
    composition = models.TextField('Состав')
    description = models.TextField('Описание')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title


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
