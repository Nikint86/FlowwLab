from django.contrib import admin

from .models import Bouquet, Order, ConsultationRequest


@admin.register(Bouquet)
class BouquetAdmin(admin.ModelAdmin):
    list_display = ('title', 'price')
    search_fields = ('title',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'bouquet', 'delivery_time', 'is_consultation')
    list_filter = ('is_consultation',)
    search_fields = ('name', 'address')


@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ('phone', 'created_at')
    search_fields = ('phone',)