from django.contrib import admin
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from seafood import views as seafood_views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", seafood_views.homepage, name="homepage"),

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

    # Chat / conversations
    path('chat/<int:conv_id>/', seafood_views.chat_view, name='chat'),
    path('conversations/', seafood_views.my_conversations, name='my_conversations'),
    path('conversations/all/', seafood_views.all_conversations, name='all_conversations'),
    path('chat/<int:conv_id>/confirm_payment/', seafood_views.confirm_payment, name='confirm_payment'),
    path('product/<int:product_id>/toggle_availability/', seafood_views.toggle_availability, name='toggle_availability'),
    path('chat/<int:conv_id>/close_order/', seafood_views.close_order, name='close_order'),
    path('conversations/archived/', seafood_views.archived_conversations, name='archived_conversations'),
    path('review/<int:review_id>/delete/', seafood_views.delete_review, name='delete_review'),
    path('debug/session-cart/', seafood_views.debug_session_cart, name='debug_session_cart'),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Password change (user must be logged in)
urlpatterns += [
    path(
        'password_change/',
        auth_views.PasswordChangeView.as_view(
            template_name='registration/password_change_form.html',
            success_url=reverse_lazy('password_change_done')
        ),
        name='password_change'
    ),
    path(
        'password_change/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='registration/password_change_done.html'
        ),
        name='password_change_done'
    ),
]

# Password reset (forgot password) flow
urlpatterns += [
    path(
        'password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done')
        ),
        name='password_reset'
    ),
    path(
        'password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete')
        ),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]

# Temporarily serve media files in production for debugging.
# NOTE: This is a temporary convenience only. Do NOT rely on Django to serve media long-term in production.
# Remove this once you have S3 or a persistent disk + proper static hosting.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
