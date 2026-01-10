# E:\soft\vugri\vugri\urls.py  (замініть повністю або онови маршрути)
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views

from seafood import views as seafood_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Site / products
    path('', seafood_views.homepage, name='homepage'),
    path('products/', seafood_views.products, name='products'),
    path('product/<int:product_id>/', seafood_views.product_details, name='product_details'),
    path('product/<int:product_id>/review/', seafood_views.submit_review, name='submit_review'),
    path('order/<int:product_id>/', seafood_views.order_form, name='order_form'),
    path('submit_order/', seafood_views.submit_order, name='submit_order'),
    path('fetch_branches/', seafood_views.fetch_postal_branches, name='fetch_branches'),
    path('product/1/', seafood_views.product_details, kwargs={'product_id': 1}, name='product_1'),
    path('product/2/', seafood_views.product_details, kwargs={'product_id': 2}, name='product_2'),
    path('product/3/', seafood_views.product_details, kwargs={'product_id': 3}, name='product_3'),
    path('product/4/', seafood_views.product_details, kwargs={'product_id': 4}, name='product_4'),
    path('product/5/', seafood_views.product_details, kwargs={'product_id': 5}, name='product_5'),
    path('product/6/', seafood_views.product_details, kwargs={'product_id': 6}, name='product_6'),
    path('product/7/', seafood_views.product_details, kwargs={'product_id': 7}, name='product_7'),
    path('product/8/', seafood_views.product_details, kwargs={'product_id': 8}, name='product_8'),
    path('product/9/', seafood_views.product_details, kwargs={'product_id': 9}, name='product_9'),
    path('product/10/', seafood_views.product_details, kwargs={'product_id': 10}, name='product_10'),
    path('product/11/', seafood_views.product_details, kwargs={'product_id': 11}, name='product_11'),
    path('product/12/', seafood_views.product_details, kwargs={'product_id': 12}, name='product_12'),

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

    # Cart endpoints
    path('cart/add/', seafood_views.add_to_cart, name='add_to_cart'),
    path('cart/', seafood_views.cart_view, name='cart'),
    path('cart/update/', seafood_views.update_cart_item, name='update_cart_item'),
    path('cart/checkout/', seafood_views.checkout_session, name='cart_checkout'),
    path('cart/clear/', seafood_views.clear_cart, name='clear_cart'),

    # Favorites
    path('favorites/', seafood_views.favorites_view, name='favorites'),
    path('favorites/toggle/', seafood_views.toggle_favorite, name='toggle_favorite'),
    path('products/', seafood_views.products_list, name='products_list'),
    path('order/complete/<int:order_id>/', seafood_views.order_complete, name='order_complete'),
    path('chat/<int:conv_id>/', seafood_views.chat_view, name='chat'),

]