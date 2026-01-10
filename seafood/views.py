
import random
import requests
from decimal import Decimal
from types import SimpleNamespace

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Avg
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_http_methods
from django.urls import reverse
from django.templatetags.static import static
from django.core.files.uploadedfile import InMemoryUploadedFile

from django.contrib.admin.views.decorators import staff_member_required

import stripe

from .models import (
    EmailVerification,
    Order,
    SeafoodProduct,
    Favorite,
    Review,
    ProductImage,
    Conversation,
    Message,
)
# Configure Stripe
stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", None)


SAMPLES = {
    1: {
        'name': 'Вугор',
        'description': 'Свіжий вугор — ідеальний для запікання, смаження та копчення.',
        'price_per_100g': '250.00',
        'image': 'images/png/vugor.png'
    },
    2: {
        'name': 'Натуральна ікра',
        'description': 'Солона натуральна ікра високої якості.',
        'price_per_100g': '1200.00',
        'image': 'images/png/ikra.png'
    },
    3: {
        'name': 'Раки / Краби',
        'description': 'Свіжі раки та краби для замовлення оптом.',
        'price_per_100g': '180.00',
        'image': 'images/png/redfish.png'
    },
    4: {
    'name': 'Ікра кети',
    'description': 'Свіжі раки та краби для замовлення оптом.',
    'price_per_100g': '580.00',
    'image': 'images/ікра кети 1.jpg'
},
    5: {
    'name': 'Ікра кети Преміум',
    'description': 'Свіжі раки та краби для замовлення оптом.',
    'price_per_100g': '560.00',
    'image': 'images/ікра кети преміум 1.jpg'
},
     6: {
    'name': 'Ікра форелі пастераизована',
    'description': 'Свіжі раки та краби для замовлення оптом.',
    'price_per_100g': '375.00',
    'image': 'images/ікра форелі пастеризована 1.jpg'
},
    7: {
    'name': 'Ікра чорна',
    'description': 'Свіжі раки та краби для замовлення оптом.',
    'price_per_100g': '2648.00',
    'image': 'images/ікра чорна 1.jpg'
},
    8: {
    'name': 'Ікра щуки слабосолона',
    'description': 'Свіжі раки та краби для замовлення оптом.',
    'price_per_100g': '220.00',
    'image': 'images/ікра щуки слабосолона 1.jpg'
},
    9: {
    'name': 'медальйони із шматочків тунця',
    'description': 'Свіжі раки та краби для замовлення оптом.',
    'price_per_100g': '50.00',
    'image': 'images/медальйони із шматочків тунця 1.jpg'
},
    10: {
    'name': 'мясо краба',
    'description': 'Свіжі раки та краби для замовлення оптом.',
    'price_per_100g': '720.00',
    'image': 'images/мясо краба 1.jpg'
},
    11: {
    'name': 'печінка тріски',
    'description': 'Свіжі раки та краби для замовлення оптом.',
    'price_per_100g': '140.00',
    'image': 'images/печінка тріски 1.jpg'
},
    12: {
    'name': 'червона ікра кети',
    'description': 'Свіжі раки та краби для замовлення оптом.',
    'price_per_100g': '220.00',
    'image': 'images/червона ікра кети 1.jpg'
},
}


def _product_from_db_or_sample(product_id):
    """
    Return (product_obj_for_templates, db_product_or_none).
    product_obj_for_templates has attributes: id, name, description, price_per_100g, image.url
    """
    prod = SeafoodProduct.objects.filter(id=product_id).first()
    if prod:
        img = None
        try:
            img = SimpleNamespace(url=prod.image.url)
        except Exception:
            img = SimpleNamespace(url=static('images/png/placeholder.png'))
        product_obj = SimpleNamespace(
            id=prod.id,
            name=prod.name,
            description=prod.description,
            price_per_100g=str(prod.price_per_100g),
            image=img,
        )
        return product_obj, prod

    data = SAMPLES.get(product_id)
    if not data:
        return None, None

    image_path = data.get('image')
    if image_path:
        image_url = static(image_path)
    else:
        image_url = static('images/png/placeholder.png')

    product_obj = SimpleNamespace(
        id=product_id,
        name=data['name'],
        description=data['description'],
        price_per_100g=data['price_per_100g'],
        image=SimpleNamespace(url=image_url),
    )
    return product_obj, None


# -----------------------
# Public site views
# -----------------------

def homepage(request):
    products = SeafoodProduct.objects.all()

    has_chats = False
    chats_count = 0
    try:
        if request.user.is_authenticated:
            qs = Conversation.objects.filter(participants=request.user)
            has_chats = qs.exists()
            chats_count = qs.count()
    except Exception:
        has_chats = False
        chats_count = 0

    return render(request, 'homepage.html', {
        'products': products,
        'has_chats': has_chats,
        'chats_count': chats_count,
    })


def products(request):
    """
    Catalog page with optional category filter and sorting.
    Query params:
      ?category=Категорія&sort=price_asc|price_desc|name_asc|name_desc|newest
    """
    qs = SeafoodProduct.objects.all()

    # --- Подготовка списка категорий (автоматически из модели, иначе fallback) ---
    categories = []
    cat_field_name = None
    try:
        # найти подходящее поле категории в модели (если есть)
        for f in SeafoodProduct._meta.get_fields():
            if f.name in ('category', 'category_name', 'cat', 'section'):
                cat_field_name = f.name
                break

        if cat_field_name:
            # если поле реляционное — вытянем названия связанных объектов
            field = SeafoodProduct._meta.get_field(cat_field_name)
            if getattr(field, 'is_relation', False) and hasattr(field.related_model, 'name'):
                categories = list(
                    field.related_model.objects.filter(
                        pk__in=SeafoodProduct.objects.exclude(**{f'{cat_field_name}__isnull': True}).values_list(f'{cat_field_name}', flat=True)
                    ).values_list('name', flat=True)
                )
            else:
                # обычное текстовое поле
                categories = list(SeafoodProduct.objects.exclude(**{f'{cat_field_name}__isnull': True}).values_list(cat_field_name, flat=True).distinct())
                # убрать пустые значения
                categories = [c for c in categories if c]
    except Exception:
        categories = []

    # Фоллбек-список категорий (если в модели нет данных)
    if not categories:
        categories = [
            "Ікра", "Печінка тріски", "В'ялена риба та ікра",
            "Делікатеси", "М'ясо краба", "Креветки", "Морепродукти"
        ]

    # --- Применяем фильтр по категории (если передан параметр) ---
    selected_category = request.GET.get('category', '').strip()
    if selected_category:
        try:
            if cat_field_name:
                # пытаемся корректно отфильтровать по полю модели
                field = SeafoodProduct._meta.get_field(cat_field_name)
                if getattr(field, 'is_relation', False):
                    # relation: пробуем фильтровать по имени связанной модели
                    qs = qs.filter(**{f'{cat_field_name}__name__iexact': selected_category})
                else:
                    qs = qs.filter(**{f'{cat_field_name}__iexact': selected_category})
            else:
                # если нет определённого поля — фильтруем по вхождению имени категории в название/описание
                qs = qs.filter(name__icontains=selected_category)
        except Exception:
            qs = qs.filter(name__icontains=selected_category)

    # --- Сортировка ---
    sort = request.GET.get('sort', '').strip()
    if sort == 'price_asc':
        qs = qs.order_by('price_per_100g')
    elif sort == 'price_desc':
        qs = qs.order_by('-price_per_100g')
    elif sort == 'name_asc':
        qs = qs.order_by('name')
    elif sort == 'name_desc':
        qs = qs.order_by('-name')
    elif sort == 'newest':
        # попытка сортировать по полю created/updated, иначе по id убыв.
        if hasattr(SeafoodProduct, 'created_at'):
            qs = qs.order_by('-created_at')
        else:
            qs = qs.order_by('-id')

    # Постраничная выдача (опционально можно добавить), но пока вернём все
    favorited_ids = set()
    if request.user.is_authenticated:
        try:
            favorited_ids = set(Favorite.objects.filter(user=request.user).values_list('product_id', flat=True))
        except Exception:
            favorited_ids = set()

    return render(request, 'products.html', {
        'products': qs,
        'favorited_ids': favorited_ids,
        'categories': categories,
        'selected_category': selected_category,
        'current_sort': sort,
    })


def product_details(request, product_id):
    """
    Show product page. Uses DB product if exists; otherwise falls back to SAMPLES.
    Provides 'images' as a list of dicts with keys: url, alt, is_main
    """
    product_obj, _db_prod = _product_from_db_or_sample(product_id)
    if not product_obj:
        return render(request, '404.html', status=404)

    # build images list
    images = []
    try:
        if _db_prod:
            imgs = _db_prod.images.all()
            for im in imgs:
                try:
                    url = im.image.url
                except Exception:
                    url = static('images/png/placeholder.png')
                images.append({'url': url, 'alt': getattr(im, 'alt', ''), 'is_main': getattr(im, 'is_main', False)})
            if not images:
                # fallback to product.image if no ProductImage entries
                try:
                    images.append({'url': _db_prod.image.url, 'alt': _db_prod.name, 'is_main': True})
                except Exception:
                    images.append({'url': static('images/png/placeholder.png'), 'alt': product_obj.name, 'is_main': True})
        else:
            images.append({'url': product_obj.image.url, 'alt': product_obj.name, 'is_main': True})
    except Exception:
        images = [{'url': product_obj.image.url, 'alt': product_obj.name, 'is_main': True}]

    # is_favorited
    is_favorited = False
    if request.user.is_authenticated:
        try:
            is_favorited = Favorite.objects.filter(user=request.user, product_id=product_id).exists()
        except Exception:
            is_favorited = False

    # reviews & average rating
    reviews = []
    average_rating = None
    try:
        if _db_prod:
            qs = Review.objects.filter(product=_db_prod).select_related('user')
            reviews = qs.order_by('-created_at')
            avg = qs.aggregate(avg=Avg('rating'))['avg']
            if avg is not None:
                average_rating = round(float(avg), 2)
    except Exception:
        reviews = []
        average_rating = None

    return render(request, 'product_details.html', {
        'product': product_obj,
        'images': images,
        'is_favorited': is_favorited,
        'reviews': reviews,
        'average_rating': average_rating,
    })


def order_form(request, product_id):
    product_obj, _db_prod = _product_from_db_or_sample(product_id)
    if not product_obj:
        return render(request, '404.html', status=404)
    return render(request, 'order_form.html', {'product': product_obj})

def payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.status = 'paid'
        order.save()
        return render(request, 'payment_done.html', {'order': order})
    return render(request, 'payment.html', {'order': order})


def fetch_postal_branches(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    city = request.GET.get('city', '')
    postal_service = request.GET.get('postal', '')

    if postal_service == 'nova':
        api_url = 'https://api.novaposhta.ua/v2.0/json/'
        payload = {
            "modelName": "AddressGeneral",
            "calledMethod": "getWarehouses",
            "methodProperties": {"CityName": city},
            "apiKey": "your-nova-poshta-api-key"
        }
    elif postal_service == 'ukr':
        api_url = f'https://ukrposhta-api.example.com/branches?city={city}'
        payload = {}
    else:
        return JsonResponse({'error': 'Invalid postal service'}, status=400)

    response = requests.post(api_url, json=payload)
    if response.status_code == 200:
        return JsonResponse(response.json())
    return JsonResponse({'error': 'Failed to fetch branches'}, status=500)


def register(request):
    context = {}
    if request.method == 'POST':
        if 'password1' in request.POST:
            form = UserCreationForm(request.POST)
            if not form.is_valid():
                context['register_error'] = form.errors.as_ul()
                context['form'] = form
                return render(request, 'registration/register.html', context)

            email = request.POST.get('email', '').strip()
            if not email:
                context['register_error'] = 'Вкажіть email.'
                context['form'] = form
                return render(request, 'registration/register.html', context)

            user = form.save(commit=False)
            user.email = email
            user.is_active = False
            user.save()

            code = str(random.randint(100000, 999999))
            EmailVerification.objects.update_or_create(user=user, defaults={'code': code})

            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)

            try:
                send_mail(
                    'Підтвердження email — VugriUkraine',
                    f'Ваш код підтвердження: {code}',
                    from_email,
                    [email],
                    fail_silently=False,
                )
            except Exception:
                user.delete()
                context['register_error'] = (
                    'Не вдалося надіслати лист підтвердження. '
                    'Перевірте налаштування пошти та спробуйте пізніше.'
                )
                context['form'] = UserCreationForm()
                return render(request, 'registration/register.html', context)

            request.session['verify_user_id'] = user.id
            return redirect('verify_email')

        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is None:
            context['login_error'] = 'Невірний логін або пароль'
            context['form'] = UserCreationForm()
            return render(request, 'registration/register.html', context)

        if not user.is_active:
            context['login_error'] = 'Підтвердіть email перед входом'
            context['form'] = UserCreationForm()
            return render(request, 'registration/register.html', context)

        auth_login(request, user)
        return redirect('profile')

    context['form'] = UserCreationForm()
    return render(request, 'registration/register.html', context)


def verify_email(request):
    user_id = request.session.get('verify_user_id')
    if not user_id:
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)
        verification = EmailVerification.objects.get(user=user)
    except (User.DoesNotExist, EmailVerification.DoesNotExist):
        return redirect('register')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        if verification.code == code:
            user.is_active = True
            user.save()
            verification.delete()
            request.session.pop('verify_user_id', None)
            auth_login(request, user)
            return redirect('profile')
        return render(request, 'verify_email.html', {'error': 'Невірний код'})
    return render(request, 'verify_email.html')


@login_required
def profile(request):
    return render(request, 'profile.html')


def about(request):
    return render(request, 'about.html')


def contacts(request):
    return render(request, 'contacts.html')


# -----------------------
# Session-based cart API
# -----------------------

def _get_cart(request):
    return request.session.setdefault('cart', {})


def cart_count(request):
    return sum(int(item.get('quantity', 0)) for item in _get_cart(request).values())


@require_POST
def add_to_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'ok': False,
            'error': 'login required',
            'login_url': reverse('login') + '?next=' + request.path
        }, status=401)

    product_id = request.POST.get('product_id')
    if not product_id:
        return JsonResponse({'ok': False, 'error': 'product_id required'}, status=400)

    name = request.POST.get('name', 'Товар')
    try:
        price = int(float(request.POST.get('price', 0)))
    except (TypeError, ValueError):
        price = 0
    currency = request.POST.get('currency', 'UAH')

    raw_q = request.POST.get('quantity', '1')
    try:
        q = int(float(raw_q))
    except (TypeError, ValueError):
        q = 1

    if q >= 10 and q % 100 == 0:
        quantity = max(1, q // 100)
    else:
        quantity = max(1, q)

    image = request.POST.get('image', '')

    cart = _get_cart(request)
    if product_id in cart:
        cart[product_id]['quantity'] = int(cart[product_id].get('quantity', 0)) + quantity
    else:
        cart[product_id] = {
            'name': name,
            'price': price,
            'currency': currency,
            'quantity': quantity,
            'image': image,
        }
    request.session.modified = True
    return JsonResponse({'ok': True, 'cart_count': cart_count(request)})


def cart_view(request):
    cart = _get_cart(request)
    totals = {}
    for pid, item in cart.items():
        cur = item.get('currency', 'UAH')
        totals.setdefault(cur, 0)
        totals[cur] += int(item.get('price', 0)) * int(item.get('quantity', 0))

    recommended = []
    try:
        recommended = SeafoodProduct.objects.all()[:6]
    except Exception:
        recommended = []

    first_pid = None
    for k in cart.keys():
        first_pid = k
        break

    return render(request, 'cart.html', {
        'cart': cart,
        'totals': totals,
        'cart_count': cart_count(request),
        'products': recommended,
        'first_pid': first_pid,
    })


@require_POST
def update_cart_item(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'ok': False,
            'error': 'login required',
            'login_url': reverse('login') + '?next=' + request.path
        }, status=401)

    product_id = request.POST.get('product_id')
    if not product_id:
        return JsonResponse({'ok': False, 'error': 'product_id required'}, status=400)
    try:
        quantity = int(request.POST.get('quantity', 0))
    except (TypeError, ValueError):
        quantity = 0

    cart = _get_cart(request)
    if product_id not in cart:
        return JsonResponse({'ok': False, 'error': 'product not found'}, status=404)

    if quantity <= 0:
        del cart[product_id]
    else:
        if quantity >= 10 and quantity % 100 == 0:
            quantity = max(1, quantity // 100)
        cart[product_id]['quantity'] = quantity

    request.session.modified = True

    totals = {}
    for pid, item in cart.items():
        cur = item.get('currency', 'UAH')
        totals.setdefault(cur, 0)
        totals[cur] += int(item.get('price', 0)) * int(item.get('quantity', 0))

    return JsonResponse({'ok': True, 'cart_count': cart_count(request), 'totals': totals})


@require_POST
def checkout_session(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'ok': False,
            'error': 'login required',
            'login_url': reverse('login') + '?next=' + request.path
        }, status=401)

    cart = _get_cart(request)
    if not cart:
        return JsonResponse({'ok': False, 'error': 'cart empty'}, status=400)

    currencies = {item.get('currency', 'UAH') for item in cart.values()}
    if len(currencies) > 1:
        return JsonResponse({'ok': False, 'error': 'cart has multiple currencies; checkout one currency at a time'}, status=400)
    currency = currencies.pop()

    if not stripe.api_key:
        return JsonResponse({'ok': False, 'error': 'stripe not configured on server'}, status=500)

    line_items = []
    for pid, item in cart.items():
        unit_amount = int(item.get('price', 0)) * 100
        line_items.append({
            'price_data': {
                'currency': currency.lower(),
                'product_data': {
                    'name': item.get('name'),
                },
                'unit_amount': unit_amount,
            },
            'quantity': int(item.get('quantity', 1)),
        })

    success_url = request.build_absolute_uri('/payment-success/')
    cancel_url = request.build_absolute_uri('/cart/')

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='payment',
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return JsonResponse({'ok': True, 'url': session.url})


@require_http_methods(["GET"])
def clear_cart(request):
    request.session.pop('cart', None)
    request.session.modified = True
    return redirect('cart')


@require_POST
def toggle_favorite(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'ok': False,
            'error': 'login required',
            'login_url': reverse('login') + '?next=' + request.path
        }, status=401)

    product_id = request.POST.get('product_id')
    if not product_id:
        return JsonResponse({'ok': False, 'error': 'product_id required'}, status=400)

    try:
        pid = int(product_id)
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'invalid product_id'}, status=400)

    product_obj, db_prod = _product_from_db_or_sample(pid)
    if not product_obj:
        return JsonResponse({'ok': False, 'error': 'product not found'}, status=404)

    if db_prod is None:
        try:
            price_per_100g = Decimal(str(product_obj.price_per_100g))
        except Exception:
            price_per_100g = Decimal('0')
        db_prod = SeafoodProduct.objects.create(
            name=product_obj.name,
            description=product_obj.description,
            price_per_100g=price_per_100g,
        )

    fav, created = Favorite.objects.get_or_create(user=request.user, product=db_prod)
    if not created:
        fav.delete()
        favorited = False
    else:
        favorited = True

    count = Favorite.objects.filter(user=request.user).count()
    return JsonResponse({'ok': True, 'favorited': favorited, 'favorites_count': count})


@login_required
def favorites_view(request):
    favs = Favorite.objects.filter(user=request.user).select_related('product')
    products = []
    for f in favs:
        p = f.product
        try:
            img_url = p.image.url if p.image else static('images/png/placeholder.png')
        except Exception:
            img_url = static('images/png/placeholder.png')
        products.append({
            'id': p.id,
            'name': p.name,
            'price_per_100g': p.price_per_100g,
            'description': p.description,
            'image_url': img_url,
        })
    return render(request, 'favorites.html', {'products': products})


@require_POST
def submit_review(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'ok': False,
            'error': 'login required',
            'login_url': reverse('login') + '?next=' + request.path
        }, status=401)

    import traceback
    try:
        try:
            rating = int(request.POST.get('rating', 0))
        except (TypeError, ValueError):
            rating = 0
        if rating < 1 or rating > 5:
            return JsonResponse({'ok': False, 'error': 'invalid rating (1-5 required)'}, status=400)

        comment = (request.POST.get('comment') or '').strip()

        product_obj, db_prod = _product_from_db_or_sample(product_id)
        if not product_obj:
            return JsonResponse({'ok': False, 'error': 'product not found'}, status=404)

        # create DB product if sample
        if db_prod is None:
            try:
                price_per_100g = Decimal(str(product_obj.price_per_100g))
            except Exception:
                price_per_100g = Decimal('0')
            db_prod = SeafoodProduct.objects.create(
                name=product_obj.name,
                description=product_obj.description,
                price_per_100g=price_per_100g,
            )

        # create review
        Review.objects.create(
            user=request.user,
            product=db_prod,
            rating=rating,
            comment=comment,
        )

        return JsonResponse({'ok': True, 'message': 'Дякуємо за відгук.'})

    except Exception:
        traceback.print_exc()
        from django.conf import settings as _settings
        tb = traceback.format_exc() if getattr(_settings, 'DEBUG', False) else None
        return JsonResponse({'ok': False, 'error': 'server error', 'traceback': tb}, status=500)


@staff_member_required
def product_create(request):
    """
    Простий інтерфейс для додавання товару з кількома зображеннями.
    Доступний лише для staff. Форма в template використовує поля: name, description, price_per_100g, images[].
    """
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price_per_100g', '0').strip()

        if not name:
            return render(request, 'product_create.html', {'error': 'Вкажіть назву', 'form': request.POST})

        try:
            price_val = Decimal(price)
        except Exception:
            price_val = Decimal('0')

        prod = SeafoodProduct.objects.create(
            name=name,
            description=description,
            price_per_100g=price_val,
        )

        # обробка декількох файлів images[]
        files = request.FILES.getlist('images')
        for i, f in enumerate(files):
            # Виконаємо просту перевірку типу файлу
            if isinstance(f, InMemoryUploadedFile) or hasattr(f, 'read'):
                ProductImage.objects.create(product=prod, image=f, alt=name if i == 0 else '')
        return redirect('product_details', product_id=prod.id)

    return render(request, 'product_create.html')
 
from django.shortcuts import render, redirect
from django.utils import timezone
from django.urls import reverse
import random

def checkout_view(request):
    """
    Показує форму оформлення. При POST валідовано — зберігає в сесії last_order і редіректить на success.
    Використовує session['cart'] якщо є, або параметр product_id (GET) для одиночного товару.
    """
    cart = request.session.get('cart')  # очікується список dict {'id','name','price','quantity'}
    product = None
    total_price = 0.0

    if cart:
        for it in cart:
            total_price += float(it.get('price', 0)) * int(it.get('quantity', 1))
    else:
        pid = request.GET.get('product_id')
        if pid:
            try:
                from .models import SeafoodProduct
                prod = SeafoodProduct.objects.filter(id=pid).first()
                if prod:
                    product = {
                        'id': prod.id,
                        'name': prod.name,
                        'price': float(getattr(prod, 'price_per_100g', 0)),
                    }
                    total_price = product['price']
            except Exception:
                product = None

    errors = []
    posted = {}

    if request.method == 'POST':
        posted['full_name'] = request.POST.get('full_name', '').strip()
        posted['phone'] = request.POST.get('phone', '').strip()
        posted['email'] = request.POST.get('email', '').strip()
        posted['delivery_method'] = request.POST.get('delivery_method', 'courier')
        posted['address'] = request.POST.get('address', '').strip()
        posted['payment_method'] = request.POST.get('payment_method', 'card')
        posted['comment'] = request.POST.get('comment', '').strip()
        posted['agree'] = request.POST.get('agree')

        # Проста валідація
        if not posted['full_name']:
            errors.append("Вкажіть ім'я.")
        if not posted['phone']:
            errors.append("Вкажіть телефон.")
        if not posted['agree']:
            errors.append("Підтвердіть згоду з умовами.")

        if not errors:
            order_id = f"VG{timezone.now().strftime('%Y%m%d')}{random.randint(1000,9999)}"
            request.session['last_order'] = {
                'order_id': order_id,
                'created': timezone.now().isoformat(),
                'full_name': posted['full_name'],
                'phone': posted['phone'],
                'email': posted['email'],
                'delivery_method': posted['delivery_method'],
                'address': posted['address'],
                'payment_method': posted['payment_method'],
                'comment': posted['comment'],
                'total': "{:.2f}".format(total_price),
                'items': cart or ([product] if product else []),
            }
            # опціонально очистити кошик:
            # request.session['cart'] = []
            return redirect(reverse('checkout_success'))
        # якщо є помилки — покажемо форму з помилками

    context = {
        'cart': cart,
        'product': product,
        'total_price': "{:.2f}".format(total_price),
        'errors': errors,
        'posted': posted,
    }
    return render(request, 'checkout.html', context)


def checkout_success(request):
    """
    Показує сторінку-підтвердження. Якщо в сесії немає last_order — редірект на products.
    """
    last = request.session.get('last_order')
    if not last:
        return redirect(reverse('products'))
    return render(request, 'checkout_success.html', {'order': last, 'order_id': last.get('order_id')})
def products_list(request, *args, **kwargs):
    return products(request, *args, **kwargs)
# backward compatibility wrapper — якщо urls.py чекає products_list
def products_list(request, *args, **kwargs):
    return products(request, *args, **kwargs)


from django.contrib.auth import get_user_model

def order_complete(request, order_id):
    """Показує сторінку підтвердження замовлення і гарантує Conversation."""
    order = get_object_or_404(Order, id=order_id)
    User = get_user_model()
    seller, _ = User.objects.get_or_create(username='VugriUa', defaults={'email': 'vugriua@example.com', 'is_active': True})
    conv, _ = Conversation.objects.get_or_create(order=order)
    if order.user:
        conv.participants.add(order.user)
    conv.participants.add(seller)
    conv.save()
    messages = conv.messages.select_related('sender').all()
    return render(request, 'order_complete.html', {'order': order, 'conversation': conv, 'messages': messages})


@require_http_methods(["GET", "POST"])
def chat_view(request, conv_id):
    conv = get_object_or_404(Conversation, id=conv_id)
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user not in conv.participants.all():
        return render(request, '403.html', status=403)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            Message.objects.create(conversation=conv, sender=request.user, text=text)
            return redirect('chat', conv_id=conv.id)
    messages = conv.messages.select_related('sender').all()
    return render(request, 'chat.html', {'conversation': conv, 'messages': messages})

@require_POST
def submit_order(request):
    # очікуємо POST
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    product_id = int(request.POST.get('product_id') or 0)
    product_obj, db_prod = _product_from_db_or_sample(product_id)
    if not product_obj:
        return render(request, '404.html', status=404)

    delivery_type = request.POST.get('delivery_type', '').strip()
    postal = request.POST.get('postal', '').strip()
    region = request.POST.get('region', '').strip()
    city = request.POST.get('city', '').strip()
    branch = request.POST.get('branch', '').strip()
    address = request.POST.get('address', '').strip()

    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    middle_name = request.POST.get('middle_name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()

    full_name = f"{last_name} {first_name} {middle_name}".strip()
    if address:
        branch = address

    try:
        quantity = int(request.POST.get('quantity', 100))
    except (TypeError, ValueError):
        quantity = 100

    price_per_100g = Decimal(str(product_obj.price_per_100g))
    total_price = (Decimal(quantity) / Decimal(100)) * price_per_100g

    if not (delivery_type and postal and region and city and branch and first_name and last_name and middle_name and email and phone):
        return render(request, 'order_form.html', {
            'product': product_obj,
            'error': "Заповніть всі поля (служба доставки, дані доставки, контактні дані)."
        })

    # створюємо/отримуємо DB-продукт
    if db_prod is None:
        db_prod = SeafoodProduct.objects.create(
            name=product_obj.name,
            description=product_obj.description,
            price_per_100g=price_per_100g,
        )

    # створюємо order
    order = Order.objects.create(
        product=db_prod,
        user=request.user if request.user.is_authenticated else None,
        full_name=full_name,
        phone=phone,
        region=region,
        city=city,
        postal=postal,
        branch=branch,
        quantity_g=quantity,
        total_price=total_price,
        status='created',
    )

    # ensure seller user exists
    try:
        seller = User.objects.filter(username='VugriUa').first()
        if not seller:
            seller = User.objects.create(username='VugriUa', email='vugriua@example.com', is_active=True)
            seller.set_unusable_password()
            seller.save()
    except Exception:
        seller = None

    # create/get conversation tied to order
    conv, _ = Conversation.objects.get_or_create(order=order)
    if order.user:
        conv.participants.add(order.user)
    if seller:
        conv.participants.add(seller)
    conv.save()

    # initial message for seller
    initial_msg_text = (
        f"Нове замовлення #{order.id}\n"
        f"Товар: {order.product.name}\n"
        f"Кількість (г): {order.quantity_g}\n"
        f"Сума: {order.total_price}\n"
        f"Клієнт: {order.full_name}\n"
        f"Телефон: {order.phone}\n"
        f"Місто: {order.city}\n"
        f"Адреса/Відділення: {order.branch}\n"
        f"Email: {email}"
    )
    # створюємо повідомлення; якщо немає seller — використовуємо sender=None не дозволяється, тому ставимо sender=seller коли є
    if seller:
        Message.objects.create(conversation=conv, sender=seller, text=initial_msg_text)
    else:
        Message.objects.create(conversation=conv, sender=conv.participants.first(), text=initial_msg_text)

    # сформувати лист
    subject = f"Нове замовлення #{order.id} — VugriUkraine"
    chat_url = request.build_absolute_uri(reverse('chat', args=[conv.id]))
    message = (
        f"Нове замовлення #{order.id}\n\n"
        f"Товар: {order.product.name}\nКількість (г): {order.quantity_g}\nСума: {order.total_price}\n\n"
        f"Дані замовника:\nІм'я: {order.full_name}\nТелефон: {order.phone}\nEmail: {email}\nМісто: {order.city}\nАдреса: {order.branch}\n\n"
        f"Посилання на чат: {chat_url}\n"
    )
    html_message = f"<p>Нове замовлення #{order.id}</p><p>Товар: {order.product.name}<br>Кількість (г): {order.quantity_g}<br>Сума: {order.total_price}</p><p>Клієнт: {order.full_name}<br>Телефон: {order.phone}<br>Email: {email}</p><p>Чат: <a href='{chat_url}'>{chat_url}</a></p>"

    # отримувачі
    recipients = []
    if getattr(settings, 'ORDER_NOTIFICATION_EMAIL', None):
        recipients.append(settings.ORDER_NOTIFICATION_EMAIL)
    if seller and seller.email:
        recipients.append(seller.email)
    recipients = list(dict.fromkeys([r for r in recipients if r]))

    # SEND synchronously (console backend will print it)
    if recipients:
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients, html_message=html_message, fail_silently=False)
        except Exception as e:
            import logging
            logging.exception("Failed to send order email: %s", e)

    # redirect to confirmation page (with chat link)
    return redirect('order_complete', order_id=order.id)

# Додати в кінець файлу seafood/views.py (після існуючих view-ів)

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

@login_required
def my_conversations(request):
    """
    Показує список розмов, в яких учасник — поточний користувач.
    """
    qs = Conversation.objects.filter(participants=request.user).select_related('order').prefetch_related('participants').order_by('-created_at')
    return render(request, 'conversations_list.html', {'conversations': qs, 'title': 'Мої чати'})


@staff_member_required
def all_conversations(request):
    """
    Показує всі розмови для продавця/staff.
    """
    qs = Conversation.objects.select_related('order').prefetch_related('participants').order_by('-created_at')
    return render(request, 'conversations_list.html', {'conversations': qs, 'title': 'Всі чати (для продавця)'})