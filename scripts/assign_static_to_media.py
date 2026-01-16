# assign_static_to_media.py
# Запуск: python manage.py shell -> exec(open('scripts/assign_static_to_media.py').read())
from django.core.files import File
from django.conf import settings
import os
from seafood.models import SeafoodProduct

# Налаштування
STATIC_IMAGES_DIR = os.path.join(settings.BASE_DIR, 'static', 'images')
MEDIA_SUBDIR = 'products'
DRY_RUN = False  # True = лише показати що було б зроблено

# Мапінг product.id -> відносний шлях у static/images
mapping = {
    1: 'png/vugor.png',
    2: 'карась печений 2.jpg',
    3: 'ціла стейк філе 1.jpg',
    4: 'ікра кети 1.jpg',
    5: 'ікра кети преміум 1.jpg',
    6: 'ікра форелі пастеризована.jpg',
    7: 'ікра чорна 1.jpg',
    8: 'ікра щуки слабосолена 1.jpg',
    9: 'медальйони із шматочків тунця.jpg',
    10: 'мясо краба 1.jpg',
    11: 'печінка тріски 1.jpg',
    12: 'червона ікра кета.jpg',
}

print("Static dir:", STATIC_IMAGES_DIR)
if not os.path.isdir(STATIC_IMAGES_DIR):
    raise SystemExit("Static images dir not found: " + STATIC_IMAGES_DIR)

for pid, fname in mapping.items():
    try:
        p = SeafoodProduct.objects.get(id=pid)
    except SeafoodProduct.DoesNotExist:
        print("No product with id", pid)
        continue

    src = os.path.join(STATIC_IMAGES_DIR, fname)
    if not os.path.isfile(src):
        print("File not found for product", pid, ":", src)
        continue

    print("Match:", pid, p.name, "<-", fname)
    if not DRY_RUN:
        with open(src, 'rb') as f:
            django_file = File(f)
            dest_name = os.path.join(MEDIA_SUBDIR, os.path.basename(fname))
            # This saves file into MEDIA_ROOT/products/ and sets p.image
            p.image.save(dest_name, django_file, save=True)
        print("Assigned and saved to media:", dest_name)