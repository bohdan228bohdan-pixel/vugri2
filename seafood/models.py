from django.conf import settings
from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    description = models.TextField(blank=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name']
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or 'cat'
            slug = base
            i = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)


class SeafoodProduct(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price_per_100g = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    youtube_url = models.URLField(blank=True, null=True)

    # Category relation (optional)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='products')

    # Availability flag
    in_stock = models.BooleanField(
        default=True,
        help_text="True — в наявності; False — немає в наявності"
    )

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
    # product kept for compatibility; nullable because order may contain many items
    product = models.ForeignKey(SeafoodProduct, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=32)

    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal = models.CharField(max_length=50, blank=True)
    branch = models.CharField(max_length=150, blank=True)

    quantity_g = models.PositiveIntegerField(default=100)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    status = models.CharField(max_length=30, default='created')

    PAYMENT_METHOD_CHOICES = (
        ('card', 'Оплата на картку'),
        ('cash', 'Готівкою (самовивіз)'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('not_paid', 'Не оплачено'),
        ('processing', 'В процесі'),
        ('paid', 'Оплачено'),
    )

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='not_paid')

    payment_confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='confirmed_payments'
    )
    payment_confirmed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'

    def __str__(self):
        prod_name = self.product.name if self.product else '(множинні позиції)'
        return f"Order#{self.id} {self.full_name} {prod_name}"

    def recalc_totals(self):
        items = self.items.all()
        total_qty = 0
        total_sum = Decimal('0.00')
        for it in items:
            total_qty += int(it.quantity_g or 0)
            total_sum += (it.total_price or Decimal('0.00'))
        self.quantity_g = total_qty or self.quantity_g
        self.total_price = total_sum
        self.save(update_fields=['quantity_g', 'total_price'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(SeafoodProduct, null=True, blank=True, on_delete=models.SET_NULL, related_name='order_items')
    quantity_g = models.PositiveIntegerField(default=100)   # grams
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))  # price per 100g
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Позиція замовлення'
        verbose_name_plural = 'Позиції замовлення'

    def __str__(self):
        return f"OrderItem #{self.id} for Order #{self.order_id}"

    def save(self, *args, **kwargs):
        try:
            self.total_price = (Decimal(self.unit_price) * Decimal(self.quantity_g)) / Decimal('100')
        except Exception:
            self.total_price = Decimal('0.00')
        super().save(*args, **kwargs)


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

    image = models.ImageField(upload_to='receipts/%Y/%m/', blank=True, null=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Повідомлення'
        verbose_name_plural = 'Повідомлення'

    def __str__(self):
        return f"Message #{self.id} by {self.sender}"