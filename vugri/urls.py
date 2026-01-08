from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from seafood import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage, name='homepage'),
    path('products/', views.products, name='products'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='homepage'), name='logout'),
    path('verify_email/', views.verify_email, name='verify_email'),
    path('profile/', views.profile, name='profile'),
    path('product/<int:product_id>/', views.product_details, name='product_details'),
    path('order/<int:product_id>/', views.order_form, name='order_form'),
    path('submit_order/', views.submit_order, name='submit_order'),
    path('fetch_branches/', views.fetch_postal_branches, name='fetch_branches'),
    path('register/', views.register, name='register'),
    path('about/', views.about, name='about'),
    path('payment/<int:order_id>/', views.payment, name='payment'), 
    path('contact/', views.contacts, name='contact'),
]
 