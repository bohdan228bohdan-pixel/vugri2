from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views

# Primary app providing product/order views
from seafood import views as seafood_views

# Try to import cart endpoints from 'main' app; if not available, try to use same names from 'seafood'
# so this urls.py works in both setups.
try:
    from main import views as main_views
except Exception:
    main_views = None

# Choose cart view callables: prefer main_views if it defines them, otherwise fallback to seafood_views
def _choose(view_name):
    if main_views and hasattr(main_views, view_name):
        return getattr(main_views, view_name)
    if hasattr(seafood_views, view_name):
        return getattr(seafood_views, view_name)
    raise ImportError(f"Не знайдено view '{view_name}' у main.views або seafood.views. Додай реалізацію або імпорт у urls.py.")

add_to_cart_view = _choose('add_to_cart')
cart_view = _choose('cart_view') if hasattr(seafood_views, 'cart_view') or (main_views and hasattr(main_views, 'cart_view')) else _choose('cart')
update_cart_item_view = _choose('update_cart_item')
checkout_session_view = _choose('checkout_session')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Site pages / product flow (from seafood app)
    path('', seafood_views.homepage, name='homepage'),
    path('products/', seafood_views.products, name='products'),
    path('product/<int:product_id>/', seafood_views.product_details, name='product_details'),
    path('order/<int:product_id>/', seafood_views.order_form, name='order_form'),
    path('submit_order/', seafood_views.submit_order, name='submit_order'),
    path('fetch_branches/', seafood_views.fetch_postal_branches, name='fetch_branches'),

    # Auth / registration / profile
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='homepage'), name='logout'),
    path('register/', seafood_views.register, name='register'),
    path('verify_email/', seafood_views.verify_email, name='verify_email'),
    path('profile/', seafood_views.profile, name='profile'),

    # About / contact / payment
    path('about/', seafood_views.about, name='about'),
    path('contact/', seafood_views.contacts, name='contact'),
    path('payment/<int:order_id>/', seafood_views.payment, name='payment'),

    # Cart endpoints (selected implementations)
    path('cart/add/', add_to_cart_view, name='add_to_cart'),
    path('cart/', cart_view, name='cart'),
    path('cart/update/', update_cart_item_view, name='update_cart_item'),
    path('cart/checkout/', checkout_session_view, name='cart_checkout'),
]