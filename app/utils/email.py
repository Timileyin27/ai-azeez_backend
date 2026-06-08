import resend
from app.config import settings
resend.api_key= settings.resend_api_key
def send_otp_email(email: str, otp: str):
    resend.Emails.send({
        "from": "Your App <onboarding@resend.dev>",
        "to": [email],
        "subject": "Your OTP Code",
        "html": f"""
            <h2>Your OTP Code</h2>
            <p><b>{otp}</b></p>
            <p>This code expires in 10 minutes.</p>
        """
    })

def send_welcome_email(email: str):
    resend.Emails.send({
        "from": "Your App <onboarding@resend.dev>",
        "to": [email],
        "subject": "Welcome!",
        "html": """
            <h2>Welcome Back</h2>
            <p>Your account has logged in back .</p>
        """
    })
def send_verify_email(email: str):
    resend.Emails.send({
        "from": "Your App <onboarding@resend.dev>",
        "to": [email],
        "subject": "Welcome!",
        "html": """
            <h2>Welcome</h2>
            <p>Your account has been verified successfully.</p>
        """
    })