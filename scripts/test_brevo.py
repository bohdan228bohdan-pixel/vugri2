#!/usr/bin/env python
"""
Test script to verify Brevo email integration with VugriUkraine.

Usage:
    python scripts/test_brevo.py
"""

import os
import sys
import django

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vugri.settings')
django.setup()

from django.conf import settings
from seafood.brevo_email import (
    send_verification_email,
    send_callback_request_notification_email,
    send_email_via_brevo
)


def test_brevo_config():
    """Test if Brevo is properly configured."""
    print("=" * 60)
    print("BREVO CONFIGURATION TEST")
    print("=" * 60)
    
    api_key = getattr(settings, 'BREVO_API_KEY', '')
    sender_email = getattr(settings, 'BREVO_SENDER_EMAIL', '')
    sender_name = getattr(settings, 'BREVO_SENDER_NAME', '')
    
    print(f"\n✓ BREVO_API_KEY: {'**set**' if api_key else '❌ NOT SET'}")
    print(f"✓ BREVO_SENDER_EMAIL: {sender_email if sender_email else '❌ NOT SET'}")
    print(f"✓ BREVO_SENDER_NAME: {sender_name if sender_name else '❌ NOT SET'}")
    
    if not api_key:
        print("\n❌ ERROR: BREVO_API_KEY not configured")
        print("   Please set BREVO_API_KEY in your .env file")
        return False
    
    if not sender_email:
        print("\n❌ ERROR: BREVO_SENDER_EMAIL not configured")
        print("   Please set BREVO_SENDER_EMAIL in your .env file")
        return False
    
    print("\n✅ Basic configuration looks good!")
    return True


def test_verification_email(test_email):
    """Test sending a verification email."""
    print("\n" + "=" * 60)
    print("TEST 1: VERIFICATION EMAIL")
    print("=" * 60)
    
    print(f"\nAttempting to send verification email to: {test_email}")
    
    try:
        result = send_verification_email(test_email, '123456')
        
        if result:
            print("✅ SUCCESS: Verification email sent!")
            print(f"   Check your email at {test_email}")
        else:
            print("❌ FAILED: Could not send verification email")
            print("   Check the Brevo API key and configuration")
            
        return result
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_callback_email(admin_email):
    """Test sending a callback notification email."""
    print("\n" + "=" * 60)
    print("TEST 2: CALLBACK NOTIFICATION EMAIL")
    print("=" * 60)
    
    print(f"\nAttempting to send callback notification to: {admin_email}")
    
    try:
        result = send_callback_request_notification_email(
            admin_email=admin_email,
            callback_id=999,
            caller_name='Тест Користувач',
            caller_phone='+38 (095) 123-45-67',
            product_name='Вугор',
            preferred_time='13:00',
            message='Це тестовий запит зворотного зв\'язку'
        )
        
        if result:
            print("✅ SUCCESS: Callback notification sent!")
            print(f"   Check your email at {admin_email}")
        else:
            print("❌ FAILED: Could not send callback notification")
            
        return result
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_generic_email(recipient_email):
    """Test sending a generic email."""
    print("\n" + "=" * 60)
    print("TEST 3: GENERIC EMAIL")
    print("=" * 60)
    
    print(f"\nAttempting to send generic email to: {recipient_email}")
    
    try:
        html_content = """
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Тест Brevo</h2>
                <p>Це тестовий лист для перевірки Brevo інтеграції.</p>
                <p style="color: green;">✅ Якщо ви отримали цей лист, все працює правильно!</p>
            </body>
        </html>
        """
        
        result = send_email_via_brevo(
            subject='Тест Brevo інтеграції',
            recipient_email=recipient_email,
            html_content=html_content,
            text_content='Тест Brevo'
        )
        
        if result:
            print("✅ SUCCESS: Generic email sent!")
            print(f"   Check your email at {recipient_email}")
        else:
            print("❌ FAILED: Could not send generic email")
            
        return result
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  BREVO EMAIL INTEGRATION TEST SCRIPT".center(58) + "║")
    print("║" + "  VugriUkraine".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Test configuration
    if not test_brevo_config():
        print("\n❌ Configuration test failed. Exiting.")
        sys.exit(1)
    
    # Get test email
    test_email = input("\n📧 Enter your email address for testing: ").strip()
    if not test_email or '@' not in test_email:
        print("❌ Invalid email address")
        sys.exit(1)
    
    # Run tests
    results = {
        'config': True,
        'verification': test_verification_email(test_email),
        'callback': test_callback_email(test_email),
        'generic': test_generic_email(test_email),
    }
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nYour Brevo integration is working correctly.")
        print("You can now register and verify emails on the site.")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease check your Brevo configuration and try again.")
        print("\nFor help, see: BREVO_SETUP.md")
    
    print("=" * 60 + "\n")
    
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
