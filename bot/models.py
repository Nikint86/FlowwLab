from django.db import models


class Bouquet(models.Model):
    title = models.CharField('Название', max_length=200)
    photo = models.ImageField('Фото', upload_to='bouquets/')
    composition = models.TextField('Состав')
    description = models.TextField('Описание')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title
