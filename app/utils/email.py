import resend
from app.config import settings

resend.api_key = settings.resend_api_key

FROM = "MyApp <noreply@abdulazeez-akande.com.ng>"   # use your real app name
REPLY_TO = "support@abdulazeez-akande.com.ng"       # an inbox you actually check


def _send(to: str, subject: str, html: str, text: str) -> None:
    resend.Emails.send({
        "from": FROM,
        "to": [to],
        "reply_to": REPLY_TO,
        "subject": subject,
        "html": html,
        "text": text,
    })


def send_otp_email(email: str, otp: str):
    _send(
        email,
        f"{otp} is your MyApp verification code",
        f"<p>Your verification code is <b>{otp}</b>.</p>"
        "<p>It expires in 10 minutes. If you didn't request it, ignore this email.</p>",
        f"Your verification code is {otp}. It expires in 10 minutes. "
        "If you didn't request it, ignore this email.",
    )


def send_verify_email(email: str):
    _send(
        email,
        "Your MyApp account is verified",
        "<p>Your account has been verified successfully.</p>",
        "Your account has been verified successfully.",
    )