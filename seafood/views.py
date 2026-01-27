
from itertools import product
from itertools import product
import random
import requests
from decimal import Decimal, ROUND_HALF_UP
from types import SimpleNamespace

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Avg
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
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
    OrderItem,
    SeafoodProduct,
    Category,
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
    'price_per_500g': '280.00',
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
    product_obj_for_templates has attributes: id, name, description, price_per_100g, image.url, in_stock
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
            in_stock=bool(prod.in_stock),
            youtube_url = prod.youtube_url or ''   # <- додано
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
        in_stock=True,  # sample items available by default
    )
    return product_obj, None

# -----------------------
# Public site views
# -----------------------

def homepage(request):
    # products shown on main page (DB)
    products = SeafoodProduct.objects.all()

    # categories: якщо є модель Category, візьмемо всі
    try:
        categories = list(Category.objects.all().order_by('ordering', 'name'))
    except Exception:
        categories = []

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
        'categories': categories,
        'has_chats': has_chats,
        'chats_count': chats_count,
    })


def products(request):
    """
    Catalog page with optional category filter and sorting.
    Query params:
      ?category=<slug>&sort=price_asc|price_desc|name_asc|name_desc|newest
    """
    qs = SeafoodProduct.objects.all()

    # --- Попробуем загрузить категории как объекты Category (если модель есть) ---
    categories = []
    using_category_model = False
    try:
        from .models import Category
        categories = list(Category.objects.all().order_by('ordering', 'name'))
        using_category_model = True
    except Exception:
        categories = []

    # Фоллбек — если в БД нет категорий, используем статичный список имен
    if not categories:
        categories = [
            "Ікра", "Печінка тріски", "В'ялена риба та ікра",
            "Делікатеси", "М'ясо краба", "Креветки", "Морепродукти"
        ]

    # --- Применяем фильтр по категории (ожидаем slug если Category есть) ---
    selected_category = request.GET.get('category', '').strip()
    if selected_category:
        try:
            if using_category_model:
                # Поддерживаем и новое M2M `categories`, и временно legacy FK `category`
                from django.db.models import Q
                qs = qs.filter(
                    Q(categories__slug__iexact=selected_category) |
                    Q(category__slug__iexact=selected_category)
                ).distinct()
            else:
                # fallback: фильтруем по вхождению имени в название/описание
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
        if hasattr(SeafoodProduct, 'created_at'):
            qs = qs.order_by('-created_at')
        else:
            qs = qs.order_by('-id')

    # --- Подготовка списка продуктов (включая пакетную цену для шаблонов) ---
    # Превращаем qs в список, чтобы можно было добавить временные атрибуты для шаблонов
    products_list = list(qs.select_related('category').prefetch_related('categories'))

    # вычисляем package_price_display для карточек (если product.package_size_grams задан)
    try:
        for p in products_list:
            try:
                pkg = getattr(p, 'package_size_grams', None)
                if pkg:
                    price100 = Decimal(str(getattr(p, 'price_per_100g', '0') or '0'))
                    pkg_price = (price100 * (Decimal(pkg) / Decimal(100))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    p.package_price = pkg_price
                    p.package_price_display = "{:.2f}".format(pkg_price)
                    p.package_size = int(pkg)
                else:
                    p.package_price = None
                    p.package_price_display = None
                    p.package_size = None
            except Exception:
                p.package_price = None
                p.package_price_display = None
                p.package_size = None
    except Exception:
        # не ломаем страницу, если что-то пошло не так
        pass

    # favorites for current user
    favorited_ids = set()
    if request.user.is_authenticated:
        try:
            favorited_ids = set(Favorite.objects.filter(user=request.user).values_list('product_id', flat=True))
        except Exception:
            favorited_ids = set()

    return render(request, 'products.html', {
        'products': products_list,
        'favorited_ids': favorited_ids,
        'categories': categories,
        'selected_category': selected_category,
        'current_sort': sort,
    })

def product_details(request, product_id):
    """
    Show product page. Uses DB product if exists; otherwise falls back to SAMPLES.

    Context:
      - product: lightweight object for templates (id, name, description, price_per_100g, image.url, in_stock, (optional) youtube_url)
      - images: list of dicts { url, alt, is_main(bool), is_video(bool), thumb_url(optional) }
      - is_favorited: bool
      - reviews, average_rating
      - package_size: (int) grams if product sold in packages (e.g. 500)
      - package_price: (string) formatted price for one package (e.g. "2800.00")
    """
    product_obj, _db_prod = _product_from_db_or_sample(product_id)
    if not product_obj:
        return render(request, '404.html', status=404)

    images = []
    try:
        # If we have a DB product, prefer ProductImage rows
        if _db_prod:
            try:
                imgs_qs = _db_prod.images.all()  # model ordering already prefers is_main
            except Exception:
                imgs_qs = []

            for im in imgs_qs:
                try:
                    url = im.image.url
                except Exception:
                    url = static('images/png/placeholder.png')
                images.append({
                    'url': url,
                    'alt': (getattr(im, 'alt', '') or _db_prod.name),
                    'is_main': bool(getattr(im, 'is_main', False)),
                    'is_video': False,
                    'thumb_url': url,  # can be replaced with a true thumbnail generator
                })

            # Fallback to product.image if no ProductImage entries were found
            if not images:
                try:
                    main_img_url = _db_prod.image.url
                except Exception:
                    main_img_url = static('images/png/placeholder.png')
                images.append({
                    'url': main_img_url,
                    'alt': _db_prod.name,
                    'is_main': True,
                    'is_video': False,
                    'thumb_url': main_img_url,
                })
        else:
            # Non-DB sample product: use the product_obj.image.url provided by _product_from_db_or_sample
            try:
                main_img_url = product_obj.image.url
            except Exception:
                main_img_url = static('images/png/placeholder.png')
            images.append({
                'url': main_img_url,
                'alt': getattr(product_obj, 'name', ''),
                'is_main': True,
                'is_video': False,
                'thumb_url': main_img_url,
            })
    except Exception:
        # On any unexpected error, ensure at least one placeholder image
        images = [{
            'url': static('images/png/placeholder.png'),
            'alt': getattr(product_obj, 'name', ''),
            'is_main': True,
            'is_video': False,
            'thumb_url': static('images/png/placeholder.png'),
        }]

    # If the DB product has a YouTube URL (or product_obj provided one), append a video thumb
    # Video item is appended at the end unless no other images exist.
    youtube_url = None
    try:
        if _db_prod and getattr(_db_prod, 'youtube_url', None):
            youtube_url = _db_prod.youtube_url
        elif hasattr(product_obj, 'youtube_url') and product_obj.youtube_url:
            youtube_url = product_obj.youtube_url
    except Exception:
        youtube_url = None

    if youtube_url:
        # Use a small placeholder thumb for video; front-end JS will extract video id and render embed when clicked
        video_thumb = static('images/thumbs/video_placeholder.png')
        # If there are no real images, mark video as is_main
        is_main_for_video = not any(item.get('is_main') for item in images)
        images.append({
            'url': youtube_url,
            'alt': 'video',
            'is_main': bool(is_main_for_video),
            'is_video': True,
            'thumb_url': video_thumb,
        })

    # Reorder images so that the first is the one with is_main=True (stable)
    try:
        main_index = next((i for i, it in enumerate(images) if it.get('is_main')), None)
        if main_index is not None and main_index != 0:
            main_item = images.pop(main_index)
            images.insert(0, main_item)
    except Exception:
        # ignore reorder errors
        pass

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

    # NEW: compute package price if product stored in DB has package_size_grams
    package_size = None
    package_price_display = None
    try:
        if _db_prod and getattr(_db_prod, 'package_size_grams', None):
            package_size = int(_db_prod.package_size_grams)
            # price_per_100g may be Decimal or None
            try:
                price_per_100g = Decimal(str(_db_prod.price_per_100g or '0'))
            except Exception:
                price_per_100g = Decimal('0')
            package_price = (price_per_100g * (Decimal(package_size) / Decimal(100))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            # formatted string for template (e.g. "2800.00")
            package_price_display = "{:.2f}".format(package_price)
    except Exception:
        package_size = None
        package_price_display = None

        display_currency = 'UAH'
# приклад: якщо хочеш, щоб конкретний продукт був у USD (поки без зміни моделі)
        if product_obj and 'Ікра чорна' in product_obj.name:
         display_currency = 'USD'

    return render(request, 'product_details.html', {
        'product': product_obj,
        'images': images,
        'is_favorited': is_favorited,
        'reviews': reviews,
        'average_rating': average_rating,
        'youtube_url': youtube_url,
        'package_size': package_size,
        'package_price': package_price_display,
    })


def cart_view(request):
    session_cart = request.session.get('cart', {}) or {}
    cart_for_template = {}
    totals_decimal = {}  # currency -> Decimal
    cart_count_total = 0
    first_pid = None

    for pid, it in session_cart.items():
        try:
            qty = int(it.get('quantity', 0))
        except Exception:
            qty = 0

        cart_count_total += qty

        # compute line total (Decimal)
        line_total = Decimal('0.00')
        currency = (it.get('currency') or 'UAH')

        try:
            if it.get('unit') == 'package':
                tp = it.get('total_price')
                if tp is not None and tp != '':
                    line_total = Decimal(str(tp)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    price100 = Decimal(str(it.get('unit_price_per_100g', '0')))
                    pkg = int(it.get('package_size_grams') or 0)
                    line_total = (price100 * (Decimal(pkg) * Decimal(qty)) / Decimal(100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                # unit price per single package:
                try:
                    pkg = int(it.get('package_size_grams') or 0)
                    if tp is not None and tp != '':
                        unit_price = Decimal(str(tp))
                    else:
                        unit_price = (Decimal(str(it.get('unit_price_per_100g', '0'))) * (Decimal(pkg) / Decimal(100))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                except Exception:
                    unit_price = Decimal('0.00')
                unit_label = '1 шт'
                package_size = it.get('package_size_grams')
            else:
                # unit items
                if it.get('price_per_100g') is not None or it.get('unit_price_per_100g') is not None:
                    price100 = Decimal(str(it.get('price_per_100g') or it.get('unit_price_per_100g') or '0'))
                    line_total = (price100 * Decimal(qty)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    unit_price = price100
                    unit_label = '100г'
                    package_size = None
                elif it.get('price') is not None:
                    unit_price = Decimal(str(it.get('price')))
                    line_total = (unit_price * Decimal(qty)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    unit_label = 'шт'
                    package_size = None
                else:
                    unit_price = Decimal('0.00')
                    line_total = Decimal('0.00')
                    unit_label = ''
                    package_size = None
        except Exception:
            line_total = Decimal('0.00')
            unit_price = Decimal('0.00')
            unit_label = ''
            package_size = None

        totals_decimal.setdefault(currency, Decimal('0.00'))
        totals_decimal[currency] += line_total

        cart_for_template[str(pid)] = {
            'name': it.get('name', ''),
            'image': it.get('image', ''),
            'price': "{:.2f}".format(line_total),   # line total formatted as string
            'currency': currency,
            'quantity': qty,
            'unit': it.get('unit', 'unit'),
            'package_size_grams': package_size,
            'unit_price_display': "{:.2f}".format(unit_price) if unit_price is not None else None,
            'unit_label': unit_label,
        }

        if first_pid is None:
            first_pid = pid

    totals_str = {cur: "{:.2f}".format(amount) for cur, amount in totals_decimal.items()}

    # recommended products
    try:
        recommended = list(SeafoodProduct.objects.all()[:8])
        for p in recommended:
            try:
                pkg = getattr(p, 'package_size_grams', None)
                if pkg:
                    p.package_size = int(pkg)
                    price100 = Decimal(str(getattr(p, 'price_per_100g', '0') or '0'))
                    pkg_price = (price100 * (Decimal(p.package_size) / Decimal(100))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    p.package_price = pkg_price
                    p.package_price_display = "{:.2f}".format(pkg_price)
                else:
                    p.package_size = None
                    p.package_price = None
                    p.package_price_display = None
            except Exception:
                p.package_size = None
                p.package_price = None
                p.package_price_display = None
    except Exception:
        recommended = []

    context = {
        'cart': cart_for_template,
        'totals': totals_str,
        'first_pid': first_pid,
        'cart_count': cart_count_total,
        'products': recommended,
    }
    return render(request, 'cart.html', context)


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

    # validate product exists and is available
    try:
        product = get_object_or_404(SeafoodProduct, pk=int(product_id))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Продукт не знайдено'}, status=404)

    if not product.in_stock:
        return JsonResponse({'ok': False, 'error': 'Товар тимчасово відсутній', 'in_stock': False}, status=400)

    # client-provided metadata (fallbacks)
    name = request.POST.get('name', product.name or 'Товар')
    try:
        # prefer product.price_per_100g if client didn't provide a valid price
        client_price = request.POST.get('price', None)
        if client_price is None or client_price == '':
            price = int(float(product.price_per_100g or 0))
        else:
            price = int(float(client_price))
    except (TypeError, ValueError):
        price = int(float(product.price_per_100g or 0))

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

    # get or create cart (keeps existing helper)
    cart = _get_cart(request)

    # use string key for session-stored product id to be consistent
    pid_key = str(product.id)
    if pid_key in cart:
        cart[pid_key]['quantity'] = int(cart[pid_key].get('quantity', 0)) + quantity
    else:
        cart[pid_key] = {
            'name': name,
            'price': price,
            'currency': currency,
            'quantity': quantity,
            'image': image,
        }
    request.session.modified = True

    return JsonResponse({'ok': True, 'cart_count': cart_count(request)})

def cart_view(request):
    """
    Рендерить сторінку кошика. Повертає:
      - 'cart' : dict { pid: { name, image, price (line total), currency, quantity } }
      - 'totals': dict { currency: "1234.56" } (рядки для шаблону)
      - 'first_pid': перший product id або None (для checkout link)
      - 'cart_count': сумарна кількість одиниць
    Підтримує обидві структури сесійних item-ів:
      - package items: {'unit': 'package', 'total_price' (string) , 'unit_price_per_100g', 'package_size_grams', 'quantity'}
      - unit items: {'price_per_100g' або 'price', 'quantity'}
    """
    session_cart = request.session.get('cart', {}) or {}
    cart_for_template = {}
    totals_decimal = {}  # currency -> Decimal
    cart_count_total = 0
    first_pid = None

    for pid, it in session_cart.items():
        # normalize quantity
        try:
            qty = int(it.get('quantity', 0))
        except Exception:
            qty = 0

        cart_count_total += qty

        # compute line total (Decimal)
        line_total = Decimal('0.00')
        currency = (it.get('currency') or 'UAH')

        try:
            if it.get('unit') == 'package':
                # prefer stored total_price (string), otherwise compute from unit_price_per_100g * pkg * qty
                tp = it.get('total_price')
                if tp is not None and tp != '':
                    line_total = Decimal(str(tp)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    price100 = Decimal(str(it.get('unit_price_per_100g', '0')))
                    pkg = int(it.get('package_size_grams') or 0)
                    line_total = (price100 * (Decimal(pkg) * Decimal(qty)) / Decimal(100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                # unit items: prefer price_per_100g * qty, fallback to price * qty
                if it.get('price_per_100g') is not None:
                    price100 = Decimal(str(it.get('price_per_100g')))
                    line_total = (price100 * Decimal(qty)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                elif it.get('price') is not None:
                    line_total = (Decimal(str(it.get('price'))) * Decimal(qty)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    line_total = Decimal('0.00')
        except Exception:
            line_total = Decimal('0.00')

        # accumulate totals by currency
        totals_decimal.setdefault(currency, Decimal('0.00'))
        totals_decimal[currency] += line_total

        # prepare cart item for template: price shown is line total
        cart_for_template[str(pid)] = {
            'name': it.get('name', ''),
            'image': it.get('image', ''),
            'price': "{:.2f}".format(line_total),   # line total formatted as string
            'currency': currency,
            'quantity': qty,
        }

        if first_pid is None:
            first_pid = pid

    # format totals for template
    totals_str = {cur: "{:.2f}".format(amount) for cur, amount in totals_decimal.items()}

    # recommended products for bottom section (simple sample — choose some DB products)
    try:
        recommended = list(SeafoodProduct.objects.all()[:8])
    except Exception:
        recommended = []

    context = {
        'cart': cart_for_template,
        'totals': totals_str,
        'first_pid': first_pid,
        'cart_count': cart_count_total,
        'products': recommended,
    }
    return render(request, 'cart.html', context)


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
    Показує форму оформлення і підготовлює дані для оформлення.
    Підтримує дві ситуації:
      - session['cart'] існує і це dict {pid: {name, price, currency, quantity, image}}
      - fallback: GET product_id (одиночний товар)
    При POST валідовано — зберігає в сесії last_order і редіректить на success.
    """
    from decimal import Decimal

    cart = request.session.get('cart', {})  # dict pid -> item
    product = None

    total_price = Decimal('0.00')
    totals = {}   # totals by currency as Decimal
    items_list = []  # list of normalized items for template/last_order

    # If cart is a mapping (standard case)
    if cart and isinstance(cart, dict):
        for pid, it in cart.items():
            try:
                price = Decimal(str(it.get('price', 0)))          # price per 100g (as stored)
                qty = int(it.get('quantity', 1))                  # number of 100g units as stored
            except Exception:
                # skip malformed entry
                continue
            line_total = price * Decimal(qty)                    # price * qty (both in same unit)
            cur = it.get('currency', 'UAH') or 'UAH'
            totals.setdefault(cur, Decimal('0.00'))
            totals[cur] += line_total
            total_price += line_total

            items_list.append({
                'product_id': str(pid),
                'name': it.get('name', ''),
                'price': "{:.2f}".format(price),
                'quantity': qty,
                'currency': cur,
                'image': it.get('image', ''),
                'line_total': "{:.2f}".format(line_total),
            })
    else:
        # fallback single product via GET product_id
        pid = request.GET.get('product_id')
        if pid:
            try:
                prod = SeafoodProduct.objects.filter(id=pid).first()
                if prod:
                    price = Decimal(str(getattr(prod, 'price_per_100g', 0)))
                    # allow GET quantity param (in grams) but default to 100
                    q_raw = request.GET.get('quantity', '100')
                    try:
                        q_val = int(q_raw)
                    except Exception:
                        q_val = 100
                    # convert grams -> number of 100g units if caller passed grams that are multiples of 100
                    if q_val >= 10 and q_val % 100 == 0:
                        qty_unit = max(1, q_val // 100)
                    else:
                        qty_unit = max(1, q_val)
                    line_total = price * Decimal(qty_unit)
                    total_price = line_total
                    totals = {'UAH': line_total}
                    items_list.append({
                        'product_id': str(prod.id),
                        'name': prod.name,
                        'price': "{:.2f}".format(price),
                        'quantity': qty_unit,
                        'currency': 'UAH',
                        'image': getattr(prod.image, 'url', ''),
                        'line_total': "{:.2f}".format(line_total),
                    })
                    product = {'id': prod.id, 'name': prod.name, 'price': "{:.2f}".format(price), 'quantity': qty_unit}
            except Exception:
                product = None

    # format totals for template (strings)
    totals_str = {cur: "{:.2f}".format(amount) for cur, amount in totals.items()}

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

        # Simple validation
        if not posted['full_name']:
            errors.append("Вкажіть ім'я.")
        if not posted['phone']:
            errors.append("Вкажіть телефон.")
        if not posted['agree']:
            errors.append("Підтвердіть згоду з умовами.")

        if not errors:
            # Build last_order payload to show on success page
            order_id = f"VG{timezone.now().strftime('%Y%m%d')}{random.randint(1000,9999)}"
            # totals_str may be empty dict -> put total as formatted string
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
                'totals': totals_str,
                'items': items_list,
            }
            # Optionally clear the cart after successful checkout:
            # request.session.pop('cart', None)
            request.session.modified = True
            return redirect(reverse('checkout_success'))

    context = {
        'cart': cart,
        'product': product,
        'total_price': "{:.2f}".format(total_price),
        'totals': totals_str,
        'items': items_list,
        'errors': errors,
        'posted': posted,
        'cart_count': cart_count(request),
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

    # allow staff to view any conversation; regular users only their own
    if not (request.user.is_staff or conv.participants.filter(pk=request.user.pk).exists()):
        return render(request, '403.html', status=403)

    # compute order_closed flag (order may be None)
    order = getattr(conv, 'order', None)
    order_closed = False
    if order and getattr(order, 'status', None) == 'closed':
        order_closed = True

    if request.method == 'POST':
        # If order closed: reject any attempt to post (AJAX or normal POST)
        if order_closed:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': 'Order closed; cannot send messages'}, status=403)
            messages = conv.messages.select_related('sender').all()
            return render(request, 'chat.html', {'conversation': conv, 'messages': messages, 'order_closed': True}, status=403)

        # handle file upload (receipt)
        receipt = request.FILES.get('receipt')
        text = request.POST.get('text', '').strip()

        if receipt:
            # optional: validate file size/type here
            msg = Message.objects.create(conversation=conv, sender=request.user, text='[Квитанція]', image=receipt)
            if conv.order:
                conv.order.payment_status = 'processing'
                conv.order.save()
            # notify seller in chat (system message) if seller exists
            from django.contrib.auth import get_user_model
            seller = get_user_model().objects.filter(username='VugriUa').first()
            if seller:
                Message.objects.create(conversation=conv, sender=seller, text='Дякуємо, квитанцію отримано. Очікуйте підтвердження оплати.')
            # respond to AJAX or redirect
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': True})
            return redirect('chat', conv_id=conv.id)

        # normal text message
        if text:
            Message.objects.create(conversation=conv, sender=request.user, text=text)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': True})
            return redirect('chat', conv_id=conv.id)

    messages = conv.messages.select_related('sender').all()
    return render(request, 'chat.html', {'conversation': conv, 'messages': messages, 'order_closed': order_closed})
@require_POST
def submit_order(request):
    """
    Створює замовлення. Підтримує багатопозиційний кошик у session['cart'].
    Коректно обробляє кілька форматів збереження елементів корзини:
      - package items: {'unit':'package', 'total_price', 'unit_price_per_100g', 'package_size_grams', 'quantity'}
      - unit items: {'price_per_100g' or 'price', 'quantity'}
    """
    from django.contrib.auth import get_user_model
    from decimal import Decimal, ROUND_HALF_UP
    import traceback

    # Read cart from session
    cart = request.session.get('cart', {}) or {}
    # Parse common form fields (delivery/contact)
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

    payment_method = request.POST.get('payment_method', '').strip()
    full_name = f"{last_name} {first_name} {middle_name}".strip()
    if address:
        branch = address

    # Basic validation
    if not (delivery_type and postal and region and city and branch and first_name and last_name and middle_name and email and phone):
        product_id = int(request.POST.get('product_id') or 0)
        product_obj, _ = _product_from_db_or_sample(product_id) if product_id else (None, None)
        return render(request, 'order_form.html', {
            'product': product_obj,
            'error': "Заповніть всі поля (служба доставки, дані доставки, контактні дані)."
        })

    # If payment_method is cash but not allowed for delivery method -> adjust business rule
    if payment_method == 'cash' and delivery_type != 'nova_branch':
        payment_method = 'card'

    # Build items list either from cart or from POST product_id (fallback to single product)
    items_data = []  # each item: dict with keys product_obj (db), name, unit_price (Decimal per 100g), qty_units (int number of 100g units), line_total (Decimal), pid
    total_price = Decimal('0.00')
    total_qty_grams = 0

    # Case: multi-item cart from session
    if isinstance(cart, dict) and cart:
        for pid_str, it in cart.items():
            try:
                pid = int(pid_str)
            except Exception:
                continue

            # Try to use DB product if exists
            db_prod = SeafoodProduct.objects.filter(pk=pid).first()

            # Normalize quantity and compute line total depending on structure
            try:
                qty = int(it.get('quantity', 1))
            except Exception:
                qty = 1

            # Default values
            unit_price_per_100g = Decimal('0.00')  # price per 100g
            line_total = Decimal('0.00')
            qty_units = 0
            try:
                if it.get('unit') == 'package':
                    # package: quantity = number of packages
                    pkg_size = int(it.get('package_size_grams') or 0)
                    # If total_price stored, prefer it
                    tp = it.get('total_price')
                    if tp:
                        # total_price likely string
                        line_total = Decimal(str(tp))
                        # compute unit_price_per_100g for record (if present)
                        try:
                            unit_price_per_100g = Decimal(str(it.get('unit_price_per_100g', '0')))
                        except Exception:
                            unit_price_per_100g = Decimal('0.00')
                    else:
                        # compute from unit_price_per_100g and pkg_size
                        unit_price_per_100g = Decimal(str(it.get('unit_price_per_100g', '0')))
                        total_grams = pkg_size * qty
                        line_total = (unit_price_per_100g * (Decimal(total_grams) / Decimal(100))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    # qty_units = total number of 100g units represented by these packages
                    qty_units = (pkg_size * qty) // 100 if pkg_size else qty
                    total_qty_grams += pkg_size * qty if pkg_size else qty_units * 100
                else:
                    # unit items: assume quantity counts 100g-units or simple units depending on stored fields
                    # prefer explicit price_per_100g
                    if it.get('price_per_100g') is not None:
                        unit_price_per_100g = Decimal(str(it.get('price_per_100g')))
                        qty_units = qty
                        line_total = (unit_price_per_100g * Decimal(qty_units)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        total_qty_grams += qty_units * 100
                    elif it.get('unit_price_per_100g') is not None:
                        unit_price_per_100g = Decimal(str(it.get('unit_price_per_100g')))
                        qty_units = qty
                        line_total = (unit_price_per_100g * Decimal(qty_units)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        total_qty_grams += qty_units * 100
                    elif it.get('price') is not None:
                        # legacy: price field may be price per 100g or per unit — assume per 100g to keep compatibility
                        unit_price_per_100g = Decimal(str(it.get('price')))
                        qty_units = qty
                        line_total = (unit_price_per_100g * Decimal(qty_units)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        total_qty_grams += qty_units * 100
                    else:
                        # unknown structure -> skip
                        unit_price_per_100g = Decimal('0.00')
                        qty_units = qty
                        line_total = Decimal('0.00')
                        total_qty_grams += qty_units * 100
            except Exception:
                # fallback defaults if any conversion fails
                line_total = Decimal('0.00')

            total_price += line_total

            items_data.append({
                'product_obj': db_prod,
                'name': it.get('name') or (db_prod.name if db_prod else 'Товар'),
                'unit_price': unit_price_per_100g,
                'qty_units': qty_units or qty,
                'line_total': line_total,
                'pid': pid,
            })
    else:
        # Fallback: single product_id from POST (old behaviour)
        product_id = int(request.POST.get('product_id') or 0)
        product_obj, db_prod = _product_from_db_or_sample(product_id) if product_id else (None, None)
        if not product_obj:
            return render(request, '404.html', status=404)
        try:
            qty = int(request.POST.get('quantity', 100))
        except Exception:
            qty = 100
        # We expect qty as grams in older form; convert to 100g units
        if qty >= 10 and qty % 100 == 0:
            qty_units = max(1, qty // 100)
        else:
            qty_units = max(1, qty)
        unit_price = Decimal(str(product_obj.price_per_100g))
        line_total = (Decimal(qty) / Decimal(100) * unit_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if qty >= 10 else (unit_price * Decimal(qty_units)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_price = line_total
        total_qty_grams = qty if isinstance(qty, int) else qty_units * 100
        # Ensure db_prod exists
        if db_prod is None:
            db_prod = SeafoodProduct.objects.create(
                name=product_obj.name,
                description=product_obj.description,
                price_per_100g=unit_price,
            )
        items_data.append({
            'product_obj': db_prod,
            'name': product_obj.name,
            'unit_price': unit_price,
            'qty_units': qty_units,
            'line_total': line_total,
            'pid': product_id,
        })

    # Create Order (product kept nullable — set first product for convenience)
    first_product = items_data[0]['product_obj'] if items_data and items_data[0].get('product_obj') else None
    order = Order.objects.create(
        product=first_product,
        user=request.user if request.user.is_authenticated else None,
        full_name=full_name,
        phone=phone,
        region=region,
        city=city,
        postal=postal,
        branch=branch,
        quantity_g=total_qty_grams or (items_data[0]['qty_units'] * 100 if items_data else 100),
        total_price=total_price,
        status='created',
        payment_method=payment_method or 'card',
        payment_status='not_paid',
    )

    # Create OrderItem records
    for it in items_data:
        prod_obj = it.get('product_obj')
        # if product not in DB, create a DB record
        if prod_obj is None:
            try:
                prod_obj = SeafoodProduct.objects.create(
                    name=it.get('name') or 'Товар',
                    description='',
                    price_per_100g=it.get('unit_price') or Decimal('0.00'),
                )
            except Exception:
                prod_obj = None
        # quantity in grams
        qty_g = int(it.get('qty_units', 1)) * 100
        OrderItem.objects.create(
            order=order,
            product=prod_obj,
            quantity_g=qty_g,
            unit_price=it.get('unit_price', Decimal('0.00')),
            # total_price will be set by OrderItem.save() / order.recalc_totals()
        )

    # Recalculate totals to ensure consistency
    try:
        order.recalc_totals()
    except Exception:
        # fallback: ensure total_price set
        order.total_price = total_price
        order.quantity_g = total_qty_grams
        order.save(update_fields=['total_price', 'quantity_g'])

    # create seller user and conversation, messages, etc (keeps your existing logic)
    try:
        User = get_user_model()
        seller = User.objects.filter(username='VugriUa').first()
        if not seller:
            seller = User.objects.create(username='VugriUa', email='vugriua@example.com', is_active=True)
            seller.set_unusable_password()
            seller.save()
    except Exception:
        seller = None

    conv, _ = Conversation.objects.get_or_create(order=order)
    if order.user:
        conv.participants.add(order.user)
    if seller:
        conv.participants.add(seller)
    conv.save()

    # Build initial chat message listing all items
    items_lines = []
    for oi in order.items.all():
        prod_name = oi.product.name if oi.product else '(товар)'
        items_lines.append(f"- {prod_name}: {oi.quantity_g} г — {oi.total_price} грн")
    items_text = "\n".join(items_lines)

    initial_msg_text = (
        f"Нове замовлення #{order.id}\n"
        f"Позиції:\n{items_text}\n\n"
        f"Клієнт: {order.full_name}\n"
        f"Телефон: {order.phone}\n"
        f"Місто: {order.city}\n"
        f"Адреса/Відділення: {order.branch}\n"
        f"Email: {email}\n"
        f"Оплата: {order.get_payment_method_display() if order.payment_method else 'не вказано'}\n"
    )

    sender = seller if seller else conv.participants.first()
    if sender:
        Message.objects.create(conversation=conv, sender=sender, text=initial_msg_text)

    # payment instruction if card
    if order.payment_method == 'card' and sender:
        instruction_text = (
            f"Вітаю!\n\n"
            f"1) Зайдіть у свій банк або мобільний додаток.\n"
            f"2) Перекажіть кошти на ФОП Шовка Юрій Васильович: IBAN UA733220010000026009350109011\n"
            f"   Сума: {order.total_price}\n"
            f"3) Зробіть фото квитанції та натисніть «Оплачено» в чаті або прикріпіть файл у повідомленні.\n\n"
            f"Після отримання квитанції ми перевіримо оплату та підтвердимо."
        )
        Message.objects.create(conversation=conv, sender=sender, text=instruction_text)

    # Optionally clear cart after successful order creation
    try:
        request.session.pop('cart', None)
        request.session.modified = True
    except Exception:
        pass

    # Send notification email (existing behavior)
    subject = f"Нове замовлення #{order.id} — VugriUkraine"
    chat_url = request.build_absolute_uri(reverse('chat', args=[conv.id]))
    message_body = (
        f"Нове замовлення #{order.id}\n\n"
        f"Позиції:\n{items_text}\n\n"
        f"Дані замовника:\nІм'я: {order.full_name}\nТелефон: {order.phone}\nEmail: {email}\nМісто: {order.city}\nАдреса: {order.branch}\n\n"
        f"Посилання на чат: {chat_url}\n"
    )
    html_message = f"<p>Нове замовлення #{order.id}</p><p>Позиції:<br/>{'<br/>'.join([line for line in items_lines])}</p><p>Клієнт: {order.full_name}<br>Телефон: {order.phone}<br>Email: {email}</p><p>Чат: <a href='{chat_url}'>{chat_url}</a></p>"

    recipients = []
    if getattr(settings, 'ORDER_NOTIFICATION_EMAIL', None):
        recipients.append(settings.ORDER_NOTIFICATION_EMAIL)
    if seller and seller.email:
        recipients.append(seller.email)
    recipients = list(dict.fromkeys([r for r in recipients if r]))

    if recipients:
        try:
            send_mail(subject, message_body, settings.DEFAULT_FROM_EMAIL, recipients, html_message=html_message, fail_silently=False)
        except Exception:
            pass

    return redirect('order_complete', order_id=order.id)

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

@login_required
def my_conversations(request):
    """
    Показує список розмов, в яких учасник — поточний користувач.
    Не показує розмови, пов'язані з ордерами зі статусом 'closed'.
    """
    qs = (Conversation.objects
          .filter(participants=request.user)
          .exclude(order__status='closed')            # <-- виключаємо закриті ордери
          .select_related('order')
          .prefetch_related('participants')
          .order_by('-created_at'))
    return render(request, 'conversations_list.html', {'conversations': qs, 'title': 'Мої чати'})


@staff_member_required
def all_conversations(request):
    """
    Показує всі розмови для продавця/staff.
    Не показує розмови з ордерами, що мають status == 'closed'.
    """
    qs = (Conversation.objects
          .exclude(order__status='closed')            # <-- виключаємо закриті ордери
          .select_related('order')
          .prefetch_related('participants')
          .order_by('-created_at'))
    return render(request, 'conversations_list.html', {'conversations': qs, 'title': 'Всі чати (для продавця)'})

@staff_member_required
def confirm_payment(request, conv_id):
    """
    Staff-only action: підтверджує оплату для розмови/замовлення.
    Якщо замовлення існує — ставить payment_status='paid', створює message від продавця.
    Працює для AJAX (повертає JSON) або звичайного запиту (редірект в чат).
    """
    conv = get_object_or_404(Conversation, id=conv_id)
    order = getattr(conv, 'order', None)
    if not order:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': 'No order attached'}, status=400)
        return redirect('chat', conv_id=conv.id)

    # встановити статус і зберегти
    order.payment_status = 'paid'
    # якщо додаткові поля (payment_confirmed_by/at) присутні — заповнити їх
    try:
        # якщо поля є у моделі, присвоїмо їх без гарантії (атрибути створені опціонально)
        order.payment_confirmed_by = request.user
        order.payment_confirmed_at = timezone.now()
    except Exception:
        pass
    order.save()

    # створити системне повідомлення від продавця
    seller = get_user_model().objects.filter(username='VugriUa').first() or request.user
    sys_text = "Оплата отримана та підтверджена. Статус замовлення — Оплачено ✅"
    Message.objects.create(conversation=conv, sender=seller, text=sys_text)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'status': 'paid'})
    return redirect('chat', conv_id=conv.id)

@staff_member_required
def toggle_availability(request, product_id):
    """
    Staff-only (decorator). Additionally allow only username 'VugriUa' if you want exact user check.
    Accepts POST with optional 'set' parameter:
      set=1 -> mark in_stock True
      set=0 -> mark in_stock False
    If 'set' not provided -> toggle.
    Returns JSON for AJAX or redirect back to product page.
    """
    # Optional extra check: only allow specific username
    if not request.user.username == 'VugriUa':
        return HttpResponseForbidden("Only VugriUa can toggle availability")

    product = get_object_or_404(SeafoodProduct, pk=product_id)

    if request.method == 'POST':
        set_val = request.POST.get('set', None)
        if set_val is None:
            # toggle
            product.in_stock = not product.in_stock
        else:
            product.in_stock = bool(int(set_val))
        product.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'in_stock': product.in_stock, 'product_id': product.id})
        return redirect(reverse('product_details', args=[product.id]))

    # Reject GET
    return HttpResponseForbidden()

@require_POST
def add_to_cart(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({
                'ok': False,
                'error': 'login required',
                'login_url': reverse('login') + '?next=' + request.path
            }, status=401)

        product_id = request.POST.get('product_id')
        if not product_id:
            return JsonResponse({'ok': False, 'error': 'product_id required'}, status=400)

        product = get_object_or_404(SeafoodProduct, pk=int(product_id))

        # SERVER-SIDE AVAILABILITY CHECK
        if not product.in_stock:
            return JsonResponse({'ok': False, 'error': 'Товар тимчасово відсутній', 'in_stock': False}, status=400)

        # name (client may send, but fallback to DB)
        name = request.POST.get('name', product.name or 'Товар')

        # price_per_100g as Decimal (use product DB value; do not trust client price)
        try:
            price_per_100g = Decimal(str(product.price_per_100g)) if product.price_per_100g is not None else Decimal('0.00')
        except Exception:
            price_per_100g = Decimal('0.00')

        currency = request.POST.get('currency', 'UAH')

        try:
            q = int(float(request.POST.get('quantity', '1')))
        except Exception:
            q = 1
        quantity = max(1, q)

        image = request.POST.get('image', '')

        cart = _get_cart(request)  # ваш хелпер для сесійної корзини
        pid = str(product.id)

        # If product sold in packages
        if getattr(product, 'package_size_grams', None):
            package_size = int(product.package_size_grams)
            total_grams = package_size * quantity
            total_price = (price_per_100g * (Decimal(total_grams) / Decimal(100))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            item = {
                'name': name,
                'currency': currency,
                'unit': 'package',
                'package_size_grams': package_size,
                'quantity': quantity,               # number of packages
                'total_grams': total_grams,
                'unit_price_per_100g': str(price_per_100g),
                'total_price': str(total_price),
                'image': image,
            }

            if pid in cart:
                existing = cart[pid]
                existing_qty = int(existing.get('quantity', 0)) + quantity
                existing_total_grams = package_size * existing_qty
                existing_total_price = (price_per_100g * (Decimal(existing_total_grams) / Decimal(100))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                existing.update({
                    'quantity': existing_qty,
                    'total_grams': existing_total_grams,
                    'total_price': str(existing_total_price),
                })
                cart[pid] = existing
            else:
                cart[pid] = item

        else:
            # standard item (quantity = units)
            unit_price = price_per_100g.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if pid in cart:
                cart[pid]['quantity'] = int(cart[pid].get('quantity', 0)) + quantity
            else:
                cart[pid] = {
                    'name': name,
                    'price_per_100g': str(unit_price),
                    'currency': currency,
                    'unit': 'unit',
                    'quantity': quantity,
                    'image': image
                }

        request.session.modified = True
        return JsonResponse({'ok': True, 'cart_count': cart_count(request)})

    except Exception as e:
        # Лог у консоль/термінал для діагностики
        import traceback
        traceback.print_exc()
        # Повертаємо JSON з повідомленням (у DEBUG можна додати e)
        from django.conf import settings
        resp = {'ok': False, 'error': 'internal server error'}
        if settings.DEBUG:
            resp['debug'] = str(e)
        return JsonResponse(resp, status=500)

from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model

@staff_member_required
@require_POST
def close_order(request, conv_id):
    """
    Закриває ордер, пов'язаний з розмовою conv_id.
    Працює тільки для staff (VugriUa). Повертає JSON для AJAX або редірект назад.
    """
    conv = get_object_or_404(Conversation, id=conv_id)
    order = getattr(conv, 'order', None)
    if not order:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': 'No order attached'}, status=400)
        return redirect(request.META.get('HTTP_REFERER', reverse('my_conversations')))

    # mark closed
    order.status = 'closed'
    order.save()

    # system message from seller / current staff
    seller = get_user_model().objects.filter(username='VugriUa').first() or request.user
    sys_text = "Замовлення закрите. Розмова переміщена в архів."
    Message.objects.create(conversation=conv, sender=seller, text=sys_text)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'status': 'closed'})
    return redirect(request.META.get('HTTP_REFERER', reverse('my_conversations')))


@login_required
def archived_conversations(request):

    """
    Показує архівні розмови (order.status == 'closed').
    - staff бачить всі archived conversations
    - звичайний користувач бачить тільки свої archived conversations
    Використовує той самий шаблон conversations_list.html (title: 'Архів чатів').
    """
    if request.user.is_staff:
        qs = Conversation.objects.filter(order__status='closed').select_related('order').prefetch_related('participants').order_by('-created_at')
    else:
        qs = Conversation.objects.filter(participants=request.user, order__status='closed').select_related('order').prefetch_related('participants').order_by('-created_at')

    return render(request, 'conversations_list.html', {'conversations': qs, 'title': 'Архів чатів'})

@require_POST
@login_required
def delete_review(request, review_id):

    """
    Дозволяє видаляти Review лише користувачу з username == 'VugriUa'.
    Працює для звичайного POST (редірект назад на сторінку товару) і для AJAX (повертає JSON).
    """
    # Only the specific account is allowed
    if request.user.username != 'VugriUa':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)
        return HttpResponseForbidden("Only VugriUa can delete reviews")

    review = get_object_or_404(Review, pk=review_id)
    product_id = review.product_id
    review.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'review_id': review_id})
    # redirect back to product page
    return redirect('product_details', product_id=product_id)

def debug_session_cart(request):
    """
    Dev helper: повертає всі ключі сесії і значення cart (якщо є).
    Видалити після діагностики.
    """
    # Обережно — тут повертається весь вміст сесії. Використовувати лише у dev.
    data = {k: request.session.get(k) for k in request.session.keys()}
    return JsonResponse({
        'session_keys': list(request.session.keys()),
        'cart': request.session.get('cart'),
        'full': data
    }, json_dumps_params={'ensure_ascii': False})
