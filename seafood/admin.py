from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from .models import (
    SeafoodProduct,
    Order,
    EmailVerification,
    Favorite,
    Review,
    ProductImage,
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt', 'is_main')
    readonly_fields = ()

@admin.register(SeafoodProduct)
class SeafoodProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price_per_100g')
    inlines = [ProductImageInline]


# Register other models safely (skip if already registered)
for mdl in (Order, EmailVerification, Favorite, Review, ProductImage):
    try:
        admin.site.register(mdl)
    except AlreadyRegistered:
        # model already registered (e.g. during autoreload) — skip
        pass