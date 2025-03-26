from django.contrib import admin

from .models import Bouquet


@admin.register(Bouquet)
class BouquetAdmin(admin.ModelAdmin):
    list_display = ('title', 'price')
    search_fields = ('title',)
