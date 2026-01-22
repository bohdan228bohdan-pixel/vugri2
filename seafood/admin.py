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
    # Показуємо категорії через helper (щоб відображати M2M у списку)
    list_display = ('id', 'name', 'categories_list', 'price_per_100g', 'in_stock', 'package_size_grams', 'youtube_preview_short')
    list_editable = ('in_stock',)
    inlines = [ProductImageInline]

    # У формі редагування даємо можливість вибрати кілька категорій
    fields = (
        'name',
        'description',
        'price_per_100g',
        'package_size_grams',
        'image',
        'youtube_url',
        'youtube_preview',
        'categories',   # M2M поле
        'category',     # legacy FK (залишено для плавного переходу)
        'in_stock',
    )
    readonly_fields = ('youtube_preview',)

    # Зручний віджет у адмінці для many-to-many
    filter_horizontal = ('categories',)

    def categories_list(self, obj):
        qs = obj.categories.all()
        if not qs:
            return '-'
        return ", ".join([c.name for c in qs])
    categories_list.short_description = "Категорії"

    def youtube_preview(self, obj):
        """
        Full preview shown on the change form. Embed only if possible; otherwise provide link/thumbnail.
        """
        url = getattr(obj, 'youtube_url', None)
        if not url:
            return '-'
        m = re.search(r'(?:v=|embed/|youtu\.be/|shorts/)([0-9A-Za-z_-]{11})', url)
        vid = m.group(1) if m else None
        if vid:
            # safer preview: show thumbnail + links to YouTube and embed (avoid automatic iframe to prevent 153)
            thumb = f'https://img.youtube.com/vi/{vid}/hqdefault.jpg'
            watch = f'https://youtu.be/{vid}'
            embed = f'https://www.youtube.com/embed/{vid}'
            html = (
                f'<div style="display:flex;gap:10px;align-items:center;">'
                f'  <a href="{watch}" target="_blank" rel="noopener">'
                f'    <img src="{thumb}" alt="YouTube thumbnail" style="width:260px;height:auto;border-radius:6px;object-fit:cover;">'
                f'  </a>'
                f'  <div style="display:flex;flex-direction:column;gap:6px;">'
                f'    <a class="button" href="{watch}" target="_blank" rel="noopener">Відкрити на YouTube</a>'
                f'    <a class="button" href="{embed}" target="_blank" rel="noopener">Відкрити embed</a>'
                f'    <div style="color:#999;font-size:90%;">Якщо вбудовування заборонене — відкрийте на YouTube.</div>'
                f'  </div>'
                f'</div>'
            )
            return mark_safe(html)
        return mark_safe(f'<a href="{url}" target="_blank" rel="noopener">Відкрити відео</a>')
    youtube_preview.short_description = "Перегляд відео"

    def youtube_preview_short(self, obj):
        """
        Small thumbnail for list_display (keeps list compact).
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