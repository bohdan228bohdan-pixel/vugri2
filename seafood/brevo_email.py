"""
Brevo (SendinBlue) email integration utility module.
Provides functions to send emails via Brevo Transactional Email API.
No SDK dependency - uses requests library directly.
"""

from django.conf import settings
import logging
import json
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Brevo API endpoint for sending transactional emails
BREVO_API_URL = 'https://api.brevo.com/v3/smtp/email'


def send_email_via_brevo(
    subject: str,
    recipient_email: str,
    recipient_name: str = '',
    html_content: Optional[str] = None,
    text_content: Optional[str] = None,
    sender_email: Optional[str] = None,
    sender_name: Optional[str] = None,
    reply_to: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
) -> bool:
    """
    Send an email via Brevo Transactional Email API using requests.
    
    Args:
        subject: Email subject
        recipient_email: Recipient's email address
        recipient_name: Recipient's name (optional)
        html_content: HTML version of the email body
        text_content: Plain text version of the email body
        sender_email: Sender's email (defaults to BREVO_SENDER_EMAIL)
        sender_name: Sender's name (defaults to BREVO_SENDER_NAME)
        reply_to: Reply-to email address
        cc: List of CC email addresses
        bcc: List of BCC email addresses
        tags: List of tags for email categorization
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    
    api_key = getattr(settings, 'BREVO_API_KEY', '')
    if not api_key:
        logger.error('Brevo API key is not configured')
        return False
    
    sender_email = sender_email or getattr(settings, 'BREVO_SENDER_EMAIL', '')
    sender_name = sender_name or getattr(settings, 'BREVO_SENDER_NAME', 'VugriUkraine')
    
    if not sender_email:
        logger.error('Brevo sender email is not configured')
        return False
    
    if not html_content and not text_content:
        logger.error('Either html_content or text_content must be provided')
        return False
    
    # Default to text_content if html_content is not provided
    if not html_content and text_content:
        html_content = text_content.replace('\n', '<br>')
    
    try:
        # Build email payload for Brevo API
        payload = {
            'subject': subject,
            'sender': {
                'name': sender_name,
                'email': sender_email,
            },
            'to': [{
                'name': recipient_name or recipient_email,
                'email': recipient_email,
            }],
        }
        
        # Add content
        if html_content:
            payload['htmlContent'] = html_content
        if text_content:
            payload['textContent'] = text_content
        
        # Add optional fields
        if reply_to:
            payload['replyTo'] = {
                'email': reply_to,
            }
        
        if cc:
            payload['cc'] = [{'email': email} for email in cc]
        
        if bcc:
            payload['bcc'] = [{'email': email} for email in bcc]
        
        if tags:
            payload['tags'] = tags
        
        # Set up headers with API key
        headers = {
            'api-key': api_key,
            'Content-Type': 'application/json',
        }
        
        # Send email via Brevo API
        response = requests.post(
            BREVO_API_URL,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        # Check response status
        if response.status_code in (200, 201):
            response_data = response.json()
            message_id = response_data.get('messageId', 'N/A')
            logger.info(f'Email sent successfully to {recipient_email}. Message ID: {message_id}')
            return True
        else:
            error_msg = response.text
            logger.error(f'Brevo API error {response.status_code}: {error_msg}')
            return False
        
    except requests.exceptions.RequestException as e:
        logger.error(f'Network error sending email via Brevo: {str(e)}')
        return False
    except Exception as e:
        logger.error(f'Error sending email via Brevo: {str(e)}')
        return False


def send_verification_email(email: str, code: str) -> bool:
    """
    Send email verification code via Brevo.
    
    Args:
        email: Recipient's email address
        code: 6-digit verification code
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    subject = 'Підтвердження email — VugriUkraine'
    
    text_content = f'Ваш код підтвердження: {code}'
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                <h2 style="color: #333; margin-top: 0;">Підтвердження email</h2>
                <p style="color: #555; font-size: 16px; line-height: 1.6;">
                    Вітаємо на VugriUkraine!
                </p>
                <p style="color: #555; font-size: 16px; line-height: 1.6;">
                    Ваш код підтвердження:
                </p>
                <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; color: #007bff; letter-spacing: 5px;">{code}</span>
                </div>
                <p style="color: #999; font-size: 14px;">
                    Цей код дійсний протягом 24 годин.
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    Якщо ви не створювали цей акаунт, будь ласка, ігноруйте цей лист.
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email_via_brevo(
        subject=subject,
        recipient_email=email,
        html_content=html_content,
        text_content=text_content,
        tags=['verification', 'registration']
    )


def send_order_notification_email(
    email: str,
    full_name: str,
    order_id: int,
    order_details: Dict = None,
) -> bool:
    """
    Send order notification email via Brevo.
    
    Args:
        email: Recipient's email address
        full_name: Customer's full name
        order_id: Order ID
        order_details: Dictionary with order details (product name, total, etc.)
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    if order_details is None:
        order_details = {}
    
    subject = f'Ваше замовлення #{order_id} на VugriUkraine'
    
    product_name = order_details.get('product_name', 'Товари')
    total_price = order_details.get('total_price', 'N/A')
    
    text_content = f"""Привіт {full_name}!

Ваше замовлення #{order_id} було успішно створено.

Товар: {product_name}
Вартість: {total_price}

Спасибо, що обрали VugriUkraine!
"""
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                <h2 style="color: #333; margin-top: 0;">Ваше замовлення №{order_id}</h2>
                <p style="color: #555; font-size: 16px; line-height: 1.6;">
                    Привіт, {full_name}!
                </p>
                <p style="color: #555; font-size: 16px; line-height: 1.6;">
                    Ваше замовлення було успішно створено.
                </p>
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Товар:</strong> {product_name}</p>
                    <p><strong>Вартість:</strong> {total_price}</p>
                </div>
                <p style="color: #555; font-size: 16px; line-height: 1.6;">
                    Спасибо, що обрали VugriUkraine! Ми контактуватимемо з вами для підтвердження замовлення.
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    Якщо у вас виникли запитання, зв'яжіться з нами.
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email_via_brevo(
        subject=subject,
        recipient_email=email,
        recipient_name=full_name,
        html_content=html_content,
        text_content=text_content,
        tags=['order', 'notification']
    )


def send_callback_request_notification_email(
    admin_email: str,
    callback_id: int,
    caller_name: str,
    caller_phone: str,
    product_name: str = '',
    preferred_time: str = '',
    message: str = '',
) -> bool:
    """
    Send callback request notification email to admin via Brevo.
    
    Args:
        admin_email: Admin's email address
        callback_id: Callback request ID
        caller_name: Caller's name
        caller_phone: Caller's phone
        product_name: Product name (optional)
        preferred_time: Preferred callback time (optional)
        message: Caller's message (optional)
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    subject = f"Новий запит зворотного зв'язку #{callback_id}"
    
    text_content = f"""Новий запит зворотного зв'язку #{callback_id}

Телефон: {caller_phone}
Ім'я: {caller_name}
Продукт: {product_name}
Час: {preferred_time}

Повідомлення:
{message}
"""
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                <h2 style="color: #333; margin-top: 0;">Новий запит зворотного зв'язку №{callback_id}</h2>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Ім'я:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{caller_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Телефон:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><a href="tel:{caller_phone}">{caller_phone}</a></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Продукт:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{product_name or 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;"><strong>Час:</strong></td>
                        <td style="padding: 8px;">{preferred_time or 'N/A'}</td>
                    </tr>
                </table>
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Повідомлення:</strong></p>
                    <p style="margin: 0; white-space: pre-wrap; color: #555;">{message}</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    return send_email_via_brevo(
        subject=subject,
        recipient_email=admin_email,
        html_content=html_content,
        text_content=text_content,
        tags=['callback', 'admin-notification']
    )
