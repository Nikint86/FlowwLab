from django.contrib import admin

from .models import Bouquet, Order, ConsultationRequest
from django.urls import path
from django import forms
from django.shortcuts import render, redirect
from django.contrib import messages
import csv
from urllib.request import urlopen
from django.core.files.temp import NamedTemporaryFile
from django.core.files import File
from .models import Bouquet


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label='CSV-файл с букетами')


@admin.register(Bouquet)
class BouquetAdmin(admin.ModelAdmin):
    list_display = ('title', 'color', 'price_category', 'price', 'occasion')
    list_filter = ('color', 'price_category', 'occasion')
    search_fields = ('title', 'composition', 'occasion')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='import-bouquets'),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        if request.method == 'POST':
            form = CSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                decoded = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded)
                for row in reader:
                    bouquet = Bouquet(
                        title=row['title'],
                        color=row['color'],
                        price_category=row['price_category'],
                        price=row['price'],
                        composition=row['composition'],
                        description=row['description'],
                    )

                    try:
                        img_temp = NamedTemporaryFile(delete=True)
                        with urlopen(row['photo']) as u:
                            img_temp.write(u.read())
                        img_temp.flush()

                        file_name = row['photo'].split("/")[-1]
                        bouquet.photo.save(file_name, File(img_temp), save=True)
                    except Exception as e:
                        messages.error(request, f"Ошибка загрузки изображения для {row['title']}: {e}")
                        continue

                messages.success(request, "CSV-файл успешно импортирован!")
                return redirect('..')
        else:
            form = CSVImportForm()
        return render(request, 'admin/csv_form.html', {'form': form})


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'bouquet', 'delivery_time', 'is_consultation')
    list_filter = ('is_consultation',)
    search_fields = ('name', 'address')


@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ('phone', 'created_at')
    search_fields = ('phone',)