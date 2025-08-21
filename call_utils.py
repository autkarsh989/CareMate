from twilio.rest import Client
from config import TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

def make_call(to_number: str, message: str):
    try:
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            twiml=f"<Response><Say>{message}</Say></Response>"
        )
        print(f"📞 Call placed to {to_number}, Call SID: {call.sid}")
    except Exception as e:
        print(f"❌ Call failed: {e}")
