from django.conf import settings
from django.db import models
from django.utils import timezone


class SeafoodProduct(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price_per_100g = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукти"
        ordering = ['name']

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

    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=32)

    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal = models.CharField(max_length=50, blank=True)
    branch = models.CharField(max_length=150, blank=True)

    quantity_g = models.PositiveIntegerField(default=100)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=30, default='created')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'

    def __str__(self):
        return f"Order#{self.id} {self.full_name} {self.product.name}"


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(SeafoodProduct, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']
        verbose_name = 'Обране'
        verbose_name_plural = 'Обране'

    def __str__(self):
        return f'{self.user} — {self.product}'


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(SeafoodProduct, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Відгук'
        verbose_name_plural = 'Відгуки'

    def __str__(self):
        return f'Review {self.rating} by {self.user}'


class ProductImage(models.Model):
    product = models.ForeignKey(SeafoodProduct, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/%Y/%m/')
    alt = models.CharField(max_length=200, blank=True)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_main', 'created_at']
        verbose_name = 'Зображення продукту'
        verbose_name_plural = 'Зображення продуктів'

    def __str__(self):
        return f'{self.product} — image #{self.id}'


class Conversation(models.Model):
    """
    Приватна розмова між учасниками. Не використовуємо кастомний through —
    Django створить проміжну таблицю participants автоматично.
    """
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    order = models.OneToOneField(Order, on_delete=models.CASCADE, null=True, blank=True, related_name='conversation')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Розмова'
        verbose_name_plural = 'Розмови'

    def __str__(self):
        parts = ', '.join([str(u) for u in self.participants.all()[:3]])
        return f"Conversation #{self.id} ({parts})"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Повідомлення'
        verbose_name_plural = 'Повідомлення'

    def __str__(self):
        return f"Message #{self.id} by {self.sender}"