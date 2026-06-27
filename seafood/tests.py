from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import EmailVerification
from django.contrib.auth.models import User


class RegistrationVerificationFlowTests(TestCase):
    @override_settings(SECURE_SSL_REDIRECT=False)
    @patch('seafood.views.send_verification_email', return_value=False)
    def test_registration_redirects_to_verification_page_when_email_fails(self, mock_send_email):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newuser123',
                'email': 'user@example.com',
                'password1': 'Qwerty123!',
                'password2': 'Qwerty123!',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('verify_email'))
        self.assertTrue(User.objects.filter(username='newuser123').exists())
        self.assertTrue(EmailVerification.objects.filter(user__username='newuser123').exists())
        self.assertContains(response, 'Акаунт створено, але лист з кодом не надійшов')
        mock_send_email.assert_called_once()
