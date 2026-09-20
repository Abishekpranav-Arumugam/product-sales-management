import os
import hashlib
import binascii
from typing import Any
from app.utils.logger import get_logger
logger = get_logger(__name__)
from app.dal.user_dal import UserDAL
from app.service.database_service import database_service
from app.security import jwt as jwt_util


PBKDF2_ROUNDS = int(os.getenv("PWD_ROUNDS", "100_000"))

class StatelessUser:
    def __init__(self, user_id: int, email: str, role: str):
        self.id = user_id
        self.email = email
        self.role = role

class AuthService:

    def _hash_password(
        self, password: str, salt: bytes | None = None
    ) -> tuple[str, bytes]:
        if salt is None:
            salt = hashlib.sha256(os.urandom(16)).digest()

        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
        hashed = binascii.hexlify(dk).decode("ascii")
        return hashed, salt

    def _verify_password(
        self, password: str, hashed: str, salt: bytes
    ) -> bool:
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
        return binascii.hexlify(dk).decode("ascii") == hashed

    def create_user(
        self, email: str, password: str, role: str = "user"
    ) -> Any:
        db = database_service.create_session()
        try:
            user_dal = UserDAL(db)
            existing = user_dal.get_by_email(email)
            if existing is not None:
                logger.warning(
                    "Registration failed: Email already exists",
                    extra={"email": email}
                )
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
            logger.info(
                "New user registered",
                extra={"user_id": user.id}
            )
            return user

        except ValueError as e:
            db.rollback()
            logger.warning(
                "Registration failed due to business logic validation",
                extra={"email": email, "error": str(e)}
            )
            raise

        except Exception as e:
            db.rollback()
            logger.error(
                "Registration failed due to database or system error",
                extra={"email": email, "error": str(e)}
            )
            raise

        finally:
            db.close()

    def authenticate_user(self, email: str, password: str) -> Any:
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

            logger.info(
                "User authenticated successfully",
                extra={"user_id": user.id}
            )
            return user

        except ValueError as e:
            logger.warning(
                "Authentication failed",
                extra={"email": email, "error": str(e)}
            )
            return None
        
        finally:
            db.close()

    def create_token_for_user(
        self, user_id: int, email: str, role: str = "user"
    ) -> str:
        payload = {"sub": email, "user_id": user_id, "role": role}
        return jwt_util.create_access_token(payload)

    def get_user_from_token(self, token: str) -> Any:
        if not token:
            return None

        normalized_token = token
        if normalized_token.lower().startswith("bearer "):
            normalized_token = normalized_token.split(None, 1)[1]

        decoded = jwt_util.decode_access_token(normalized_token)
        if not decoded:
            return None

        email = decoded.get("sub")
        user_id = decoded.get("user_id")
        role = decoded.get("role", "user")

        if not email or not user_id:
            return None

        return StatelessUser(user_id=user_id, email=email, role=role)

        # Bypassing the sessions
        # db = database_service.create_session()
        # try:
        #     user_dal = UserDAL(db)
        #     return user_dal.get_by_email(email)
        # finally:
        #     db.close()


auth_service = AuthService()