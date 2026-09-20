from app.service.auth_service import AuthService


class DummyDB:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


def test_hash_and_verify_password_round_trip() -> None:
    service = AuthService()  # Arrange
    hashed, salt = service._hash_password("secret123")  # act
    assert service._verify_password(
        "secret123", hashed, salt) is True  # assertion
    assert service._verify_password(
        "wrongpass", hashed, salt) is False  # assertion


def test_create_user_rejects_duplicate_email(monkeypatch) -> None:
    service = AuthService()

    class FakeUserDAL:
        def __init__(self, db):
            self.db = db

        def get_by_email(self, email):
            return object()

        def insert(self, user_data):
            raise AssertionError(
                "insert should not be called for duplicate email")

    monkeypatch.setattr("app.service.auth_service.UserDAL", FakeUserDAL)

    try:
        service.create_user("dup@example.com", "secret123")
        assert False, "Expected ValueError for duplicate email"
    except ValueError as exc:
        assert str(exc) == "Email already exists"


def test_authenticate_user_success_and_failure(monkeypatch) -> None:
    service = AuthService()
    email = "auth@example.com"
    pwd = "secret123"
    hashed, salt = service._hash_password(pwd)
    stored = f"{salt.hex()}${hashed}"

    class FakeUserDAL:
        def __init__(self, db):
            self.db = db

        def get_by_email(self, value):
            if value == email:
                class User:
                    id = 1  # Added mock id attribute to satisfy the logger
                    hashed_password = stored
                return User()
            return None

    monkeypatch.setattr("app.service.auth_service.UserDAL", FakeUserDAL)

    user = service.authenticate_user(email, pwd)
    assert user is not None
    assert service.authenticate_user(email, "wrongpass") is None
    assert service.authenticate_user("missing@example.com", pwd) is None


def test_create_token_and_get_user_from_token(monkeypatch) -> None:
    service = AuthService()
    payload = {"sub": "jwt@example.com", "user_id": 7}

    class FakeDecode:
        @staticmethod
        def decode(token):
            return payload

    monkeypatch.setattr(
        "app.service.auth_service.jwt_util.decode_access_token",
        lambda token: payload
    )

    class FakeUserDAL:
        def __init__(self, db):
            self.db = db

        def get_by_email(self, email):
            if email == payload["sub"]:
                class User:
                    email = payload["sub"]
                    id = payload["user_id"]
                return User()
            return None

    monkeypatch.setattr("app.service.auth_service.UserDAL", FakeUserDAL)

    token = service.create_token_for_user(payload["user_id"], payload["sub"])
    assert token
    user = service.get_user_from_token(token)
    assert user is not None
    assert user.email == payload["sub"]
