import random
def create_otp():
    otp_code = str(random.randint(100000, 999999))
    return otp_code
def verify_otp(user_otp: str, otp_code: str) -> bool:
    return user_otp == otp_code