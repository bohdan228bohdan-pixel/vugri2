from django.contrib import admin
from .models import SeafoodProduct

@admin.register(SeafoodProduct)
class SeafoodProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_100g')
    search_fields = ('name',)