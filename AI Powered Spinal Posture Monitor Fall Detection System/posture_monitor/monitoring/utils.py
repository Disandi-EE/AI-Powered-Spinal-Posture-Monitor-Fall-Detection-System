from twilio.rest import Client
from django.conf import settings
import asyncio

def send_emergency_call(phone_number, username):
    """Send emergency call using Twilio"""
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message_body = f"EMERGENCY ALERT: Fall detected for user {username}. Please check on them immediately."
        
        # Send SMS
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        # Make a call
        call = client.calls.create(
            twiml=f'<Response><Say>{message_body}</Say></Response>',
            to=phone_number,
            from_=settings.TWILIO_PHONE_NUMBER
        )
        
        return True
    except Exception as e:
        print(f"Error sending emergency alert: {e}")
        return False

def send_vibration_signal(device_id):
    """Send vibration signal to ESP32 device"""
    # This would be implemented based on your ESP32 communication protocol
    # For now, it's a placeholder
    pass