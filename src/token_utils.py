"""
JWT token creation and validation utilities using PyJWT.
"""

import os
import time
import jwt

DEFAULT_EXPIRATION = 3600  # 1 hour
ALGORITHM = "HS256"


def get_secret():
    """Retrieve the JWT signing secret from environment variables."""
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise ValueError("JWT_SECRET environment variable is not set")
    return secret


def create_token(sub, email, role="user", expiration=None):
    """
    Create a signed JWT token.

    Args:
        sub: Subject identifier (user ID).
        email: User email address.
        role: User role, defaults to "user".
        expiration: Token lifetime in seconds, defaults to 1 hour.

    Returns:
        Encoded JWT string.
    """
    secret = get_secret()
    now = int(time.time())
    exp = expiration or DEFAULT_EXPIRATION

    payload = {
        "sub": sub,
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + exp,
    }

    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token):
    """
    Decode and validate a JWT token.

    Args:
        token: The encoded JWT string.

    Returns:
        Decoded token payload as a dictionary.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is malformed or invalid.
    """
    secret = get_secret()

    return jwt.decode(
        token,
        secret,
        algorithms=[ALGORITHM],
        options={"require": ["sub", "email", "exp", "iat"]},
    )
