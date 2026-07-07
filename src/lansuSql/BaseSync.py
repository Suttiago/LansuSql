from collections.abc import Sequence as SequenceABC
from typing import Generic, Type, Optional, Sequence, Any, Union, Dict

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .types import ModelType, PrimaryKeyType
from .utils import build_filters

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: Session):
        self.model = model
        self.session = session
        
        
    def get_by_id(self, id: PrimaryKeyType) -> Optional[ModelType]:
        return self.session.get(self.model, id)
    
    def list_all(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[Any] = None,
    ) -> Sequence[ModelType]:
        stmt = select(self.model)
        stmt = self._apply_query_options(
            stmt,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
        return self.session.execute(stmt).scalars().all()

    def find_by(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[Any] = None,
        strict: bool = True,
        **kwargs,
    ) -> Sequence[ModelType]:
        filters = build_filters(self.model, kwargs, strict=strict)
        stmt = select(self.model).where(*filters)
        stmt = self._apply_query_options(
            stmt,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
        return self.session.execute(stmt).scalars().all()

    def first_by(self, *, strict: bool = True, **kwargs) -> Optional[ModelType]:
        filters = build_filters(self.model, kwargs, strict=strict)
        stmt = select(self.model).where(*filters).limit(1)
        return self.session.execute(stmt).scalars().first()

    def count(self, *, strict: bool = True, **kwargs) -> int:
        filters = build_filters(self.model, kwargs, strict=strict)
        stmt = select(func.count()).select_from(self.model).where(*filters)
        return self.session.execute(stmt).scalar_one()

    def exists(self, *, strict: bool = True, **kwargs) -> bool:
        return self.count(strict=strict, **kwargs) > 0

    def save(self, instance: ModelType, auto_commit: bool = False) -> ModelType:
        self.session.add(instance)
        if auto_commit:
            try:
                self.session.commit()
                self.session.refresh(instance)
            except SQLAlchemyError:
                self.session.rollback()
                raise
        return instance
    
    def create(self, obj_in: Union[BaseModel, Dict[str, Any]], auto_commit: bool = False) -> ModelType:

        if isinstance(obj_in, BaseModel):
            obj_data = obj_in.model_dump() 
        else:
            obj_data = obj_in
            
        db_obj = self.model(**obj_data) 
        
        return self.save(db_obj, auto_commit)

    def update(
        self,
        instance: ModelType,
        obj_in: Union[BaseModel, Dict[str, Any]],
        auto_commit: bool = False,
        *,
        strict: bool = True,
    ) -> ModelType:

        if isinstance(obj_in, BaseModel):
            update_data = obj_in.model_dump(exclude_unset=True) 
        else:
            update_data = obj_in

        for key, value in update_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
            elif strict:
                raise ValueError(
                    f"Invalid update field '{key}' for model '{self.model.__name__}'."
                )
                
        return self.save(instance, auto_commit)
    
    def delete(self, instance: ModelType, auto_commit: bool = False) -> None:
        self.session.delete(instance)
        if auto_commit:
            try:
                self.session.commit()
            except SQLAlchemyError:
                self.session.rollback()
                raise

    def _apply_query_options(
        self,
        stmt: Any,
        *,
        limit: Optional[int],
        offset: Optional[int],
        order_by: Optional[Any],
    ) -> Any:
        for clause in self._resolve_order_by(order_by):
            stmt = stmt.order_by(clause)

        if offset is not None:
            self._validate_non_negative_int("offset", offset)
            stmt = stmt.offset(offset)

        if limit is not None:
            self._validate_non_negative_int("limit", limit)
            stmt = stmt.limit(limit)

        return stmt

    def _resolve_order_by(self, order_by: Optional[Any]) -> list[Any]:
        if order_by is None:
            return []

        if isinstance(order_by, SequenceABC) and not isinstance(order_by, (str, bytes)):
            order_items = list(order_by)
        else:
            order_items = [order_by]

        clauses = []
        for item in order_items:
            if isinstance(item, str):
                descending = item.startswith("-")
                field_name = item[1:] if descending else item
                column = getattr(self.model, field_name, None)
                if column is None:
                    raise ValueError(
                        f"Invalid order_by field '{field_name}' for model "
                        f"'{self.model.__name__}'."
                    )
                clauses.append(column.desc() if descending else column.asc())
            else:
                clauses.append(item)

        return clauses

    @staticmethod
    def _validate_non_negative_int(name: str, value: int) -> None:
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"'{name}' must be a non-negative integer.")
