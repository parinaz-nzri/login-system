import random
from django.core.cache import cache


# Save OTP in Redis
def generate_otp(phone_number):
    """
    This function generates a 6-digit OTP and stores it in the cache (Redis).
    """
    code = str(random.randint(100000, 999999))
    cache.set(f"otp_{phone_number}", code, timeout=300)
    return code


# Verify the entered OTP code
def verify_otp(phone_number, code, ip):
    """
    This function compares the entered OTP code with the stored code in the cache (Redis).
    If the codes match, it deletes the stored OTP and returns True.
    """
    cached_code = cache.get(f"otp_{phone_number}")

    if cached_code == code:
        cache.delete(f"verify_attempts_user_{phone_number}")
        cache.delete(f"verify_attempts_ip_{ip}")
        cache.delete(f"otp_{phone_number}")
        cache.set(f"verified_{phone_number}", True, timeout=600)
        return True
    return False


# Get the client IP address from the HTTP request
def get_client_ip(request):
    """
    This function extracts the client's IP address from the HTTP request.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def incr_attempts(key, timeout=3600):
    """
    This function increments the number of failed attempts for a specific phone number
    or IP. If the key does not exist, it sets its value to 1 and the timeout to 1 hour (3600 seconds).
    """
    current_attempts = cache.get(key, 0)
    if current_attempts == 0:
        cache.set(key, 1, timeout=timeout)
    else:
        cache.incr(key)


def check_attempts(key, max_attempts=3):
    """
    This function checks whether the number of failed attempts for a specific key exceeds the allowed maximum.
    If the number of attempts exceeds the limit, it returns True.
    """
    attempts = cache.get(key, 0)
    if attempts >= max_attempts:
        return True
    return False


def is_blocked(ip, phone_number=None, prefix=None, max_attempts=3):
    """
    Checks if either the phone number or IP has exceeded the max allowed attempts.
    """
    ip_key = f"{prefix}_ip_{ip}"

    if phone_number:
        user_key = f"{prefix}_user_{phone_number}"
        if check_attempts(user_key, max_attempts=max_attempts):
            return True

    if check_attempts(ip_key, max_attempts=max_attempts):
        return True

    return False
