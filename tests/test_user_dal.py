from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.dal.user_dal import UserDAL
from app.models.base import Base


def setup_module():
    global engine, SessionLocal
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def test_user_dal_crud():
    db = SessionLocal()
    dal = UserDAL(db)

    user = dal.insert({"email": "user@example.com", "hashed_password": "salt$hash"})
    assert user.id == 1
    assert user.email == "user@example.com"

    found = dal.get_by_id(user.id)
    assert found is not None and found.email == "user@example.com"

    by_email = dal.get_by_email("user@example.com")
    assert by_email is not None and by_email.id == user.id

    all_users = dal.get_all()
    assert len(all_users) == 1

    deleted = dal.delete(user.id)
    assert deleted is True
    assert dal.get_by_id(user.id) is None
    db.close()
