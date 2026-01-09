# E:\soft\vugri\seafood\management\commands\add_products.py
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from django.db import transaction
import os
from decimal import Decimal

from seafood.models import SeafoodProduct, ProductImage

# Список продуктів: name, slug (для імен файлів), price_per_100g, description, images (відносні до static/images/products/)
PRODUCTS = [
    {
        "name": "Ікра преміум кети",
        "slug": "ikra_premium_keta",
        "price_per_100g": "1200.00",
        "description": "Преміум ікра кети — вибір гурманів.",
        "images": ["ikra_premium_keta_1.png", "ikra_premium_keta_2.png"]
    },
    {
        "name": "Червона ікра кети",
        "slug": "chervona_ikra_keta",
        "price_per_100g": "1100.00",
        "description": "Червона ікра кети — свіжий смак і аромати.",
        "images": ["chervona_ikra_keta_1.png", "chervona_ikra_keta_2.png"]
    },
    {
        "name": "Чорна ікра caviar",
        "slug": "chorna_ikra_caviar",
        "price_per_100g": "2500.00",
        "description": "Чорна ікра Caviar — елітний продукт.",
        "images": ["chorna_ikra_caviar_1.png"]
    },
    {
        "name": "Печінка тріски",
        "slug": "pechinka_trisky",
        "price_per_100g": "220.00",
        "description": "Ніжна печінка тріски у розсолі.",
        "images": ["pechinka_trisky_1.png"]
    },
    {
        "name": "Карась печений",
        "slug": "karas_pecheny",
        "price_per_100g": "150.00",
        "description": "Ароматний карась печений за домашнім рецептом.",
        "images": ["karas_pecheny_1.png"]
    },
    {
        "name": "Ціла стейк філе",
        "slug": "tsila_steik_file",
        "price_per_100g": "900.00",
        "description": "Ціла стейк філе — ідеально для гриля.",
        "images": ["steik_file_1.png"]
    },
    {
        "name": "Ікра щуки слабосолена",
        "slug": "ikra_shchuky_slabosolena",
        "price_per_100g": "800.00",
        "description": "Щуча ікра, слабосолона — делікатес.",
        "images": ["ikra_shchuky_1.png"]
    },
    {
        "name": "Мʼясо краба",
        "slug": "miaso_kraba",
        "price_per_100g": "1400.00",
        "description": "Мʼясо краба — ніжне і соковите.",
        "images": ["miaso_kraba_1.png"]
    },
    # Додай інші товари сюди за тим же форматом...
]

STATIC_PRODUCTS_DIR = os.path.join(settings.BASE_DIR, 'static', 'images', 'products')
# MEDIA path where ImageField буде зберігати файли (за замовчуванням settings.MEDIA_ROOT + upload_to)
# Ми будемо зберігати через ProductImage.image.save(...) — Django сам помістить у MEDIA_ROOT

class Command(BaseCommand):
    help = 'Create/update sample products and attach images from static/images/products/'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        images_attached = 0

        # Переконайся, що каталог існує
        if not os.path.isdir(STATIC_PRODUCTS_DIR):
            self.stdout.write(self.style.WARNING(
                f"Static products dir not found: {STATIC_PRODUCTS_DIR}. "
                "Розмісти файли туди або змініть шлях у команді."
            ))
            # не завершуємо — все одно створимо товари без зображень
        for item in PRODUCTS:
            name = item.get('name')
            slug = item.get('slug')
            desc = item.get('description', '')
            price_s = item.get('price_per_100g', '0')
            imgs = item.get('images', [])

            try:
                price = Decimal(str(price_s))
            except Exception:
                price = Decimal('0')

            with transaction.atomic():
                prod, is_created = SeafoodProduct.objects.get_or_create(name=name, defaults={
                    'description': desc,
                    'price_per_100g': price,
                })
                if not is_created:
                    # обновлюємо поля
                    prod.description = desc
                    prod.price_per_100g = price
                    prod.save()
                    updated += 1
                else:
                    created += 1

                # Attach images: for each filename in imgs, try to find file in STATIC_PRODUCTS_DIR
                attached = 0
                for idx, fname in enumerate(imgs):
                    src_path = os.path.join(STATIC_PRODUCTS_DIR, fname)
                    if os.path.exists(src_path) and os.path.isfile(src_path):
                        # Open and save to ProductImage (will copy into MEDIA_ROOT)
                        try:
                            with open(src_path, 'rb') as f:
                                djfile = File(f)
                                pi = ProductImage.objects.create(product=prod, is_main=(idx == 0))
                                # Save file to ImageField; use same filename to keep extension
                                pi.image.save(fname, djfile, save=True)
                                if idx == 0:
                                    # also set main product.image if model has this field
                                    try:
                                        prod.image.save(fname, File(open(src_path, 'rb')), save=True)
                                    except Exception:
                                        # if product has no image field or save fails — ignore
                                        pass
                                attached += 1
                                images_attached += 1
                                self.stdout.write(self.style.SUCCESS(f"Attached image {fname} to {name}"))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Failed to attach {fname} to {name}: {e}"))
                    else:
                        self.stdout.write(self.style.NOTICE(f"Image not found for {name}: {src_path}"))

        self.stdout.write(self.style.SUCCESS(f"Products created: {created}; updated: {updated}; images attached: {images_attached}"))