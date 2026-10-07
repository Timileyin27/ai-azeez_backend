import resend
from app.config import settings
resend.api_key= settings.resend_api_key
def send_otp_email(email: str, otp: str):
    resend.Emails.send({
        "from": "Your App <noreply@abdulazeez-akande.com.ng>",
        "to": [email],
        "subject": "Your OTP Code",
        "html": f"""
            <h2>Your OTP Code</h2>
            "{otp} is your MyApp verification code",
        f"<p>Your verification code is <b>{otp}</b>.</p>"
        "<p>It expires in 10 minutes. If you didn't request it, ignore this email.</p>",
        f"Your verification code is {otp}. It expires in 10 minutes. "
        "If you didn't request it, ignore this email.
        """
    })

def send_welcome_email(email: str):
    resend.Emails.send({
        "from": "Your App <noreply@abdulazeez-akande.com.ng>",
        "to": [email],
        "subject": "Welcome!",
        "html": """
            <h2>Welcome Back</h2>
            <p>Your account has logged in back .</p>
        """
    })
def send_verify_email(email: str):
    resend.Emails.send({
        "from": "Your App <noreply@abdulazeez-akande.com.ng>",
        "to": [email],
        "subject": "Welcome!",
        "html": """
            <h2>Welcome</h2>
            <p>Your account has been verified successfully.</p>
            "Your account has been verified successfully."
        """
    })