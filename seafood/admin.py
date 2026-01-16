from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from django.utils.safestring import mark_safe
import re

from .models import (
    Category,
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


@admin.register(SeafoodProduct)
class SeafoodProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price_per_100g', 'in_stock', 'youtube_preview_short')
    list_editable = ('in_stock',)
    inlines = [ProductImageInline]

    # show youtube_url in the edit form and a small preview
    fields = ('name', 'description', 'price_per_100g', 'image', 'youtube_url', 'youtube_preview', 'category', 'in_stock')
    readonly_fields = ('youtube_preview',)

    def youtube_preview(self, obj):
        """
        Full preview shown on the change form. Embeds the YouTube iframe if possible,
        otherwise provides a link to the URL.
        """
        url = getattr(obj, 'youtube_url', None)
        if not url:
            return '-'
        m = re.search(r'(?:v=|embed/|youtu\.be/|shorts/)([0-9A-Za-z_-]{11})', url)
        vid = m.group(1) if m else None
        if vid:
            embed = f'https://www.youtube.com/embed/{vid}'
            return mark_safe(f'<iframe width="420" height="236" src="{embed}" frameborder="0" allowfullscreen></iframe>')
        return mark_safe(f'<a href="{url}" target="_blank" rel="noopener">Відкрити відео</a>')
    youtube_preview.short_description = "Перегляд відео"

    def youtube_preview_short(self, obj):
        """
        Small thumbnail for list_display (keeps list compact).
        Shows a small clickable thumbnail that opens YouTube in a new tab.
        """
        url = getattr(obj, 'youtube_url', None)
        if not url:
            return '-'
        m = re.search(r'(?:v=|embed/|youtu\.be/|shorts/)([0-9A-Za-z_-]{11})', url)
        vid = m.group(1) if m else None
        if vid:
            thumb = f'https://img.youtube.com/vi/{vid}/hqdefault.jpg'
            return mark_safe(
                f'<a href="https://youtu.be/{vid}" target="_blank" rel="noopener">'
                f'<img src="{thumb}" alt="YouTube" style="width:100px;height:auto;border-radius:6px;object-fit:cover;"></a>'
            )
        return mark_safe(f'<a href="{url}" target="_blank" rel="noopener">Відео</a>')
    youtube_preview_short.short_description = 'Відео'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'ordering')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('ordering', 'name')


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