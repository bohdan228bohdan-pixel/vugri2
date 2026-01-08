from django.conf import settings
from django.db import models
from django.utils import timezone


class SeafoodProduct(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price_per_100g = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        return self.name


class EmailVerification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} ({self.code})"


class Order(models.Model):
    product = models.ForeignKey(SeafoodProduct, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    full_name = models.CharField(max_length=200)   # ПІБ
    phone = models.CharField(max_length=32)        # телефон

    region = models.CharField(max_length=100)      # область
    city = models.CharField(max_length=100)        # місто
    postal = models.CharField(max_length=50)       # служба (nova/ukr)
    branch = models.CharField(max_length=150)      # відділення

    quantity_g = models.PositiveIntegerField(default=100)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=30, default='created')  # created/paid/shipped/...
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Order#{self.id} {self.full_name} {self.product.name}"
    
    from django.conf import settings
    from django.db import models

# (припускаю, що SeafoodProduct вже визначений у цьому файлі)
# Додаємо модель Favorite

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey('seafood.SeafoodProduct', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']
        verbose_name = 'Обране'
        verbose_name_plural = 'Обране'

    def __str__(self):
        return f'{self.user} — {self.product}'