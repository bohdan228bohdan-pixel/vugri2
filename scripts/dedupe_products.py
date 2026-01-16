# scripts/dedupe_products.py
from django.db import transaction
from django.db.models import Count
from seafood.models import SeafoodProduct, ProductImage, OrderItem, Favorite, Review, Order
from django.core.files import File
import sys

DRY_RUN = False  # встановіть False щоб виконати зміни

def normalize_name(name):
    if not name:
        return ''
    return ' '.join(name.lower().strip().split())

def find_duplicates():
    # Збираємо продукти і групуємо за нормалізованою назвою
    prods = list(SeafoodProduct.objects.all().values('id','name','image','created_at'))
    groups = {}
    for p in prods:
        key = normalize_name(p['name'])
        if not key:
            continue
        groups.setdefault(key, []).append(p)
    # повертаємо тільки ті, де >1
    return {k:v for k,v in groups.items() if len(v)>1}

def show_plan(dups):
    if not dups:
        print("No duplicate-name groups found.")
        return
    print("Found duplicate-name groups:")
    for name, items in dups.items():
        print(f"\nName key: '{name}' -> {len(items)} items")
        for it in sorted(items, key=lambda x: x['id']):
            print(f"  id={it['id']} name={it['name']!r} image={it['image']} created_at={it.get('created_at')}")
        keeper = min(items, key=lambda x: x['id'])
        print(f"  -> keeper will be id={keeper['id']}\n")

def merge_group(key, items):
    # items are dicts with id,name,image
    keeper_id = min(items, key=lambda x: x['id'])['id']
    keeper = SeafoodProduct.objects.get(pk=keeper_id)
    others = [SeafoodProduct.objects.get(pk=i['id']) for i in items if i['id'] != keeper_id]
    print(f"Merging group '{key}': keeper id={keeper_id}, others={[o.id for o in others]}")
    if DRY_RUN:
        print("DRY RUN: would reassign relations and delete others.")
        return

    with transaction.atomic():
        # If keeper.image empty, try take from first other that has image
        if not keeper.image:
            for o in others:
                if o.image:
                    print(f" - moving image from {o.id} -> keeper {keeper.id}")
                    keeper.image = o.image
                    keeper.save(update_fields=['image'])
                    break

        # Move ProductImage
        for o in others:
            pi_count = ProductImage.objects.filter(product=o).count()
            if pi_count:
                print(f" - reassigning {pi_count} ProductImage(s) from {o.id} -> {keeper.id}")
                ProductImage.objects.filter(product=o).update(product=keeper)

        # Move OrderItem.product
        oi_count = OrderItem.objects.filter(product__in=others).count()
        if oi_count:
            print(f" - reassigning {oi_count} OrderItem(s) product -> keeper")
            OrderItem.objects.filter(product__in=others).update(product=keeper)

        # Move Favorites
        fav_count = Favorite.objects.filter(product__in=others).count()
        if fav_count:
            print(f" - reassigning {fav_count} Favorite(s) -> keeper (duplicates may remain unique constraint will apply)")
            # handle unique_together: avoid creating duplicates that violate constraint
            # We'll reassign only those favorites that would not cause duplicate (user,keeper) pair
            for fav in Favorite.objects.filter(product__in=others).select_related('user'):
                exists = Favorite.objects.filter(user=fav.user, product=keeper).exists()
                if exists:
                    print(f"   - removing duplicate favorite for user {fav.user} (keep existing)")
                    fav.delete()
                else:
                    fav.product = keeper
                    fav.save(update_fields=['product'])

        # Move Reviews
        rev_count = Review.objects.filter(product__in=others).count()
        if rev_count:
            print(f" - reassigning {rev_count} Review(s) -> keeper")
            Review.objects.filter(product__in=others).update(product=keeper)

        # Orders.product field (nullable)
        ord_count = Order.objects.filter(product__in=others).count()
        if ord_count:
            print(f" - reassigning {ord_count} Order.product references -> keeper")
            Order.objects.filter(product__in=others).update(product=keeper)

        # Finally delete duplicates
        for o in others:
            print(f" - deleting product id={o.id} name={o.name!r}")
            o.delete()

def main():
    dups = find_duplicates()
    show_plan(dups)
    if not dups:
        return
    if DRY_RUN:
        print("\nDRY_RUN is True — no changes performed. Set DRY_RUN=False in script to apply changes.")
        return
    # Apply merges
    for key, items in dups.items():
        merge_group(key, items)
    print("Done merging duplicates.")

if __name__ == '__main__':
    main()