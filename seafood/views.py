import random
import requests
from types import SimpleNamespace

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import EmailVerification, Order, SeafoodProduct


SAMPLES = {
    1: {
        'name': 'Вугор',
        'description': 'Свіжий вугор — ідеальний для запікання, смаження та копчення.',
        'price_per_100g': '250.00',
        'image': '/static/images/png/vugor.png'
    },
    2: {
        'name': 'Натуральна ікра',
        'description': 'Солона натуральна ікра високої якості.',
        'price_per_100g': '1200.00',
        'image': '/static/images/png/ikra.png'
    },
    3: {
        'name': 'Раки / Краби',
        'description': 'Свіжі раки та краби для замовлення оптом.',
        'price_per_100g': '180.00',
        'image': '/static/images/png/redfish.png'
    }
}


def _product_from_db_or_sample(product_id):
    """
    Returns tuple: (product_obj_for_templates, db_product_or_none)
    product_obj_for_templates has: id, name, description, price_per_100g, image.url
    """
    prod = SeafoodProduct.objects.filter(id=product_id).first()
    if prod:
        img = None
        try:
            img = SimpleNamespace(url=prod.image.url)
        except Exception:
            img = None

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

    product_obj = SimpleNamespace(
        id=product_id,
        name=data['name'],
        description=data['description'],
        price_per_100g=data['price_per_100g'],
        image=SimpleNamespace(url=data['image']),
    )
    return product_obj, None


def homepage(request):
    products = SeafoodProduct.objects.all()
    return render(request, 'homepage.html', {'products': products})


def products(request):
    products = SeafoodProduct.objects.all()
    return render(request, 'products.html', {'products': products})


def product_details(request, product_id):
    product_obj, _db_prod = _product_from_db_or_sample(product_id)
    if not product_obj:
        return render(request, '404.html', status=404)
    return render(request, 'product_details.html', {'product': product_obj})


def order_form(request, product_id):
    product_obj, _db_prod = _product_from_db_or_sample(product_id)
    if not product_obj:
        return render(request, '404.html', status=404)
    return render(request, 'order_form.html', {'product': product_obj})


def submit_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    # product
    product_id = int(request.POST.get('product_id') or 0)
    product_obj, db_prod = _product_from_db_or_sample(product_id)
    if not product_obj:
        return render(request, '404.html', status=404)

    # delivery
    delivery_type = request.POST.get('delivery_type', '').strip()  # ukr_branch / nova_branch / nova_courier
    postal = request.POST.get('postal', '').strip()  # ukr / nova (hidden)
    region = request.POST.get('region', '').strip()
    city = request.POST.get('city', '').strip()
    branch = request.POST.get('branch', '').strip()
    address = request.POST.get('address', '').strip()

    # contact
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    middle_name = request.POST.get('middle_name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()

    full_name = f"{last_name} {first_name} {middle_name}".strip()

    # for courier: store address into branch field (so we don't change DB model now)
    if address:
        branch = address

    # quantity + price
    quantity = int(request.POST.get('quantity', 100))
    price_per_100g = Decimal(str(product_obj.price_per_100g))
    total_price = (Decimal(quantity) / Decimal(100)) * price_per_100g

    # validation
    if not (delivery_type and postal and region and city and branch and first_name and last_name and middle_name and email and phone):
        return render(request, 'order_form.html', {
            'product': product_obj,
            'error': "Заповніть всі поля (служба доставки, дані доставки, контактні дані)."
        })

    # If sample product -> create it in DB automatically to satisfy FK in Order
    if db_prod is None:
        db_prod = SeafoodProduct.objects.create(
            name=product_obj.name,
            description=product_obj.description,
            price_per_100g=price_per_100g,
        )

    order = Order.objects.create(
        product=db_prod,
        user=request.user if request.user.is_authenticated else None,
        full_name=full_name,
        phone=phone,
        region=region,
        city=city,
        postal=postal,      # ukr / nova
        branch=branch,      # branch number OR address for courier
        quantity_g=quantity,
        total_price=total_price,
        status='created',
    )

    return redirect('payment', order_id=order.id)


def payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # temporary fake payment
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
        # Registration
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

        # Login
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