from django.contrib import admin
from .models import SeafoodProduct, Order, EmailVerification, Favorite

# реєстрація існуючих моделей (якщо ще не зареєстровані)
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

# реєстрація Favorite
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__username', 'product__name')