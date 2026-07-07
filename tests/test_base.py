import pytest
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
from lansuSql.BaseSync import BaseRepository


Base = declarative_base()
engine = create_engine("sqlite:///:memory:", echo=False)
TestingSessionLocal = sessionmaker(bind=engine)

class DummyUser(Base):
    __tablename__ = "dummy_users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    age = Column(Integer)
    is_active = Column(Boolean, default=True)

class DummyUserCreateDTO(BaseModel):
    name: str
    age: int
    is_active: bool = True

class DummyUserUpdateDTO(BaseModel):
    name: str | None = None
    age: int | None = None



@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def user_repo(db_session: Session):
    return BaseRepository[DummyUser](model=DummyUser, session=db_session)


def test_create_with_dict(user_repo: BaseRepository):
    data = {"name": "Alice", "age": 25}
    user = user_repo.create(data, auto_commit=True)

    assert user.id is not None
    assert user.name == "Alice"
    assert user.age == 25

def test_create_with_dto(user_repo: BaseRepository):
    dto = DummyUserCreateDTO(name="Bob", age=30)
    user = user_repo.create(dto, auto_commit=True)

    assert user.id is not None
    assert user.name == "Bob"

def test_get_by_id(user_repo: BaseRepository):
    created_user = user_repo.create({"name": "Charlie", "age": 40}, auto_commit=True)
    
    fetched_user = user_repo.get_by_id(created_user.id)
    
    assert fetched_user is not None
    assert fetched_user.name == "Charlie"

def test_list_all(user_repo: BaseRepository):
    user_repo.create({"name": "User 1", "age": 20}, auto_commit=True)
    user_repo.create({"name": "User 2", "age": 22}, auto_commit=True)

    users = user_repo.list_all()

    assert len(users) == 2

def test_find_by_dynamic_filters(user_repo: BaseRepository):
    user_repo.create({"name": "Adulto", "age": 30, "is_active": True}, auto_commit=True)
    user_repo.create({"name": "Jovem", "age": 15, "is_active": True}, auto_commit=True)
    user_repo.create({"name": "Inativo", "age": 40, "is_active": False}, auto_commit=True)

    results = user_repo.find_by(age__gt=18, is_active=True)

    assert len(results) == 1
    assert results[0].name == "Adulto"

def test_find_by_nin_like_and_ilike(user_repo: BaseRepository):
    user_repo.create({"name": "Alice", "age": 25}, auto_commit=True)
    user_repo.create({"name": "Bob", "age": 30}, auto_commit=True)
    user_repo.create({"name": "Alicia", "age": 35}, auto_commit=True)

    not_bob = user_repo.find_by(name__nin=["Bob"], order_by="age")
    matching_alias = user_repo.find_by(name__ilike="ali", order_by="-age")

    assert [user.name for user in not_bob] == ["Alice", "Alicia"]
    assert [user.name for user in matching_alias] == ["Alicia", "Alice"]

def test_find_by_invalid_field_raises(user_repo: BaseRepository):
    with pytest.raises(ValueError, match="Invalid filter field"):
        user_repo.find_by(nmae="Alice")

def test_find_by_invalid_operator_raises(user_repo: BaseRepository):
    with pytest.raises(ValueError, match="Invalid filter operator"):
        user_repo.find_by(age__between=[18, 30])

def test_find_by_non_strict_ignores_invalid_field(user_repo: BaseRepository):
    user_repo.create({"name": "Alice", "age": 25}, auto_commit=True)

    results = user_repo.find_by(strict=False, nmae="Alice")

    assert len(results) == 1

def test_list_all_with_limit_offset_and_order(user_repo: BaseRepository):
    user_repo.create({"name": "Young", "age": 18}, auto_commit=True)
    user_repo.create({"name": "Middle", "age": 30}, auto_commit=True)
    user_repo.create({"name": "Old", "age": 50}, auto_commit=True)

    users = user_repo.list_all(order_by="-age", limit=2, offset=1)

    assert [user.name for user in users] == ["Middle", "Young"]

def test_first_count_and_exists(user_repo: BaseRepository):
    user_repo.create({"name": "Alice", "age": 25}, auto_commit=True)
    user_repo.create({"name": "Bob", "age": 30}, auto_commit=True)

    first = user_repo.first_by(age__gt=20)

    assert first is not None
    assert user_repo.count(age__gt=20) == 2
    assert user_repo.exists(name="Bob") is True
    assert user_repo.exists(name="Nobody") is False

def test_update_with_dto_exclude_unset(user_repo: BaseRepository):
    user = user_repo.create({"name": "João", "age": 20}, auto_commit=True)
    
    update_dto = DummyUserUpdateDTO(age=21)
    updated_user = user_repo.update(user, update_dto, auto_commit=True)

    assert updated_user.age == 21
    assert updated_user.name == "João" 

def test_update_invalid_field_raises(user_repo: BaseRepository):
    user = user_repo.create({"name": "Alice", "age": 20}, auto_commit=True)

    with pytest.raises(ValueError, match="Invalid update field"):
        user_repo.update(user, {"unknown": "value"})

def test_update_non_strict_ignores_invalid_field(user_repo: BaseRepository):
    user = user_repo.create({"name": "Alice", "age": 20}, auto_commit=True)

    updated_user = user_repo.update(user, {"unknown": "value"}, strict=False)

    assert updated_user.name == "Alice"
    assert not hasattr(updated_user, "unknown")

def test_delete(user_repo: BaseRepository, db_session: Session):
    user = user_repo.create({"name": "Deletado", "age": 99}, auto_commit=True)
    
    user_repo.delete(user, auto_commit=True)
    
    deleted_user = user_repo.get_by_id(user.id)
    assert deleted_user is None
