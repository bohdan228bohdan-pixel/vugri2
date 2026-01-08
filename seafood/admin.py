from django.contrib import admin
from .models import SeafoodProduct, Order, EmailVerification, Favorite, Review

# Register existing models if not already registered
try:
    admin.site.register(SeafoodProduct)
except Exception:
    pass

try:
    admin.site.register(Order)
except Exception:
    pass

try:
    admin.site.register(EmailVerification)
except Exception:
    pass

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__username', 'product__name')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'product__name', 'comment')