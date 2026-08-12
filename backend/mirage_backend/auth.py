"""Authentication: password hashing, JWT issuance/verification, and the
signup/login world-state transitions. Replaces the frontend's old
always-succeeds demo gate (frontend/src/contexts/auth-context.tsx ignored
whatever email/password it was given) with real credential checking.

The FastAPI-wired `get_current_user` dependency itself lives in main.py
alongside get_db/get_ai_client — it needs `db: DBSession = Depends(get_db)`,
and get_db lives in main.py, so keeping it there avoids a circular import
between this module and main.py.
"""

from __future__ import annotations

import time

import bcrypt
import jwt
from sqlalchemy.orm import Session as DBSession

from .database import Organization, User, new_id

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_SECONDS = 60 * 60 * 24 * 7  # 7 days


class AuthenticationError(Exception):
    """Raised when credentials are missing, invalid, or a token doesn't
    verify — the caller isn't who they claim to be."""


class AuthorizationError(Exception):
    """Raised when the caller is authenticated but not allowed to act on
    the resource they asked for (e.g. another org's session)."""


class EmailAlreadyRegistered(Exception):
    """Raised by signup when the email is already in use."""


def hash_password(password: str) -> str:
    """hash_password: String -> String
    Purpose: a bcrypt hash of `password`, safe to store (never the
    plaintext itself).
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """verify_password: String String -> Boolean
    Purpose: does `password` match the bcrypt hash `hashed`? Never raises
    on a malformed hash — that's just "doesn't match."
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user: User, secret_key: str) -> str:
    """create_access_token: User String -> String
    Purpose: a signed JWT identifying `user` (subject, org, email, role),
    valid for JWT_EXPIRY_SECONDS.
    """
    now = int(time.time())
    payload = {
        "sub": user.user_id,
        "org_id": user.org_id,
        "email": user.email,
        "role": user.role,
        "iat": now,
        "exp": now + JWT_EXPIRY_SECONDS,
    }
    return jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> dict:
    """decode_access_token: String String -> dict
    Purpose: verify and decode `token`'s payload, or raise
    AuthenticationError if it's missing, expired, or doesn't verify.
    """
    try:
        return jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise AuthenticationError(f"invalid token: {exc}") from exc


def signup(db: DBSession, org_name: str, email: str, password: str) -> User:
    """signup: DBSession String String String -> User
    Purpose: create a brand-new Organization plus its first User (role
    "owner"). Raises EmailAlreadyRegistered if the email is already taken
    — email is globally unique across all organizations (see database.py's
    User.email unique constraint), not just within one org.
    """
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise EmailAlreadyRegistered(email)

    org = Organization(org_id=new_id(), name=org_name)
    db.add(org)
    db.flush()  # assign org.org_id before the User row references it

    user = User(
        user_id=new_id(),
        org_id=org.org_id,
        email=email,
        hashed_password=hash_password(password),
        role="owner",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: DBSession, email: str, password: str) -> User:
    """login: DBSession String String -> User
    Purpose: verify `email`/`password` against a stored User, or raise
    AuthenticationError. Deliberately doesn't distinguish "no such email"
    from "wrong password" in the exception message — that distinction is
    an enumeration oracle, not useful information for a legitimate caller.
    """
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(password, user.hashed_password):
        raise AuthenticationError("invalid email or password")
    return user
