#!/usr/bin/env python
"""
Debug script to check email configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vugri.settings')
django.setup()

from django.conf import settings

print('=' * 60)
print('EMAIL CONFIGURATION DEBUG')
print('=' * 60)

print('\n📧 DJANGO EMAIL SETTINGS:')
print(f'  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
print(f'  EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
print(f'  EMAIL_HOST: {settings.EMAIL_HOST}')
print(f'  EMAIL_PORT: {settings.EMAIL_PORT}')
print(f'  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
print(f'  EMAIL_HOST_PASSWORD: {"*" * 10 if settings.EMAIL_HOST_PASSWORD else "NOT SET"}')
print(f'  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
print(f'  EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}')

print('\n🔑 BREVO CONFIGURATION:')
api_key = settings.BREVO_API_KEY
print(f'  BREVO_API_KEY: {"SET" if api_key else "❌ NOT SET"}')
if api_key:
    print(f'    (First 10 chars: {api_key[:10]}...)')
print(f'  BREVO_SENDER_EMAIL: {settings.BREVO_SENDER_EMAIL}')
print(f'  BREVO_SENDER_NAME: {settings.BREVO_SENDER_NAME}')

print('\n📬 ORDER NOTIFICATIONS:')
print(f'  ORDER_NOTIFICATION_EMAIL: {settings.ORDER_NOTIFICATION_EMAIL}')
print(f'  ADMIN_EMAIL: {settings.ADMIN_EMAIL}')

print('\n' + '=' * 60)

# Test Django send_mail
print('\n🧪 TESTING DJANGO SEND_MAIL:')
from django.core.mail import send_mail

try:
    result = send_mail(
        subject='Test Email - Django',
        message='This is a test email from Django send_mail',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['bohdan228bohdan@gmail.com'],
        fail_silently=False,
    )
    print(f'✅ Django send_mail SUCCESS (result: {result})')
except Exception as e:
    print(f'❌ Django send_mail FAILED: {str(e)}')

print('\n' + '=' * 60)
