import os
import hashlib
import binascii
from typing import Optional

from app.dal.user_dal import UserDAL
from app.service.database_service import database_service
from app.security import jwt as jwt_util


PBKDF2_ROUNDS = int(os.getenv("PWD_ROUNDS", "100_000"))


class AuthService:

    def _hash_password(self, password: str, salt: bytes | None = None) -> tuple[str, bytes]:
        if salt is None:
            salt = hashlib.sha256(os.urandom(16)).digest()

        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
        hashed = binascii.hexlify(dk).decode("ascii")
        return hashed, salt

    def _verify_password(self, password: str, hashed: str, salt: bytes) -> bool:
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
        return binascii.hexlify(dk).decode("ascii") == hashed

    def create_user(self, email: str, password: str, role: str = "user"):
        db = database_service.create_session()
        try:
            user_dal = UserDAL(db)
            existing = user_dal.get_by_email(email)
            if existing is not None:
                raise ValueError("Email already exists")

            hashed, salt = self._hash_password(password)
            salt_hex = binascii.hexlify(salt).decode("ascii")
            stored = f"{salt_hex}${hashed}"

            user = user_dal.insert({
                "email": email,
                "hashed_password": stored,
                "role": role,
            })
            db.commit()
            return user
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def authenticate_user(self, email: str, password: str):
        db = database_service.create_session()
        try:
            user_dal = UserDAL(db)
            user = user_dal.get_by_email(email)
            if user is None:
                return None
            try:
                salt_hex, hashed = user.hashed_password.split("$", 1)
                salt = binascii.unhexlify(salt_hex.encode("ascii"))
            except Exception:
                return None

            if not self._verify_password(password, hashed, salt):
                return None

            return user
        finally:
            db.close()

    def create_token_for_user(self, user_id: int, email: str):
        payload = {"sub": email, "user_id": user_id}
        return jwt_util.create_access_token(payload)

    def get_user_from_token(self, token: str):
        if not token:
            return None

        normalized_token = token
        if normalized_token.lower().startswith("bearer "):
            normalized_token = normalized_token.split(None, 1)[1]

        decoded = jwt_util.decode_access_token(normalized_token)
        if not decoded:
            return None

        email = decoded.get("sub")
        if not email:
            return None

        db = database_service.create_session()
        try:
            user_dal = UserDAL(db)
            return user_dal.get_by_email(email)
        finally:
            db.close()


auth_service = AuthService()
