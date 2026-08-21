"""
Rate limiting configuration using SlowAPI.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Default client IP-based rate limiter
limiter = Limiter(key_func=get_remote_address)
