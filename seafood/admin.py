from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from .models import (
    SeafoodProduct,
    Order,
    EmailVerification,
    Favorite,
    Review,
    ProductImage,
    Conversation,
    Message,
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt', 'is_main')
    readonly_fields = ()

@admin.register(SeafoodProduct)
class SeafoodProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price_per_100g')
    search_fields = ('name', 'description')
    inlines = [ProductImageInline]

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'created_at')
    filter_horizontal = ('participants',)
    search_fields = ('order__id',)

# Register remaining models safely (skip if already registered)
for mdl in (Order, EmailVerification, Favorite, Review, ProductImage, Message):
    try:
        admin.site.register(mdl)
    except AlreadyRegistered:
        pass