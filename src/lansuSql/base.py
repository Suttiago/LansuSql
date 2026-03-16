from typing import TypeVar, Generic, Type, Optional, Sequence, Any
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session

    def get_by_id(self, id: Any) -> Optional[T]:
        return self.session.get(self.model, id)

    def list_all(self) -> Sequence[T]:
        stmt = select(self.model)
        return self.session.execute(stmt).scalars().all()

    def find_by(self, **kwargs) -> Sequence[T]:
        stmt = select(self.model).filter_by(**kwargs)
        return self.session.execute(stmt).scalars().all()

    def save(self, instance: T, commit: bool = True) -> T:
        self.session.add(instance)
        if commit:
            self.session.commit()
            self.session.refresh(instance)
        return instance

    def delete(self, instance: T, commit: bool = True) -> None:
        self.session.delete(instance)
        if commit:
            self.session.commit()