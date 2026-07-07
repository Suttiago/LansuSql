from collections.abc import Sequence as SequenceABC
from typing import Generic, Type, Optional, Sequence, Any, Union, Dict

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from .types import ModelType, PrimaryKeyType
from .utils import build_filters

class AsyncBaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
        
    async def get_by_id(self, id: PrimaryKeyType) -> Optional[ModelType]:
        return await self.session.get(self.model, id)
    
    async def list_all(
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
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by(
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
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def first_by(self, *, strict: bool = True, **kwargs) -> Optional[ModelType]:
        filters = build_filters(self.model, kwargs, strict=strict)
        stmt = select(self.model).where(*filters).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def count(self, *, strict: bool = True, **kwargs) -> int:
        filters = build_filters(self.model, kwargs, strict=strict)
        stmt = select(func.count()).select_from(self.model).where(*filters)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists(self, *, strict: bool = True, **kwargs) -> bool:
        return (await self.count(strict=strict, **kwargs)) > 0

    async def save(self, instance: ModelType, auto_commit: bool = False) -> ModelType:
        self.session.add(instance)
        if auto_commit:
            try:
                await self.session.commit()
                await self.session.refresh(instance)
            except SQLAlchemyError:
                await self.session.rollback()
                raise
        return instance
    
    async def create(self, obj_in: Union[BaseModel, Dict[str, Any]], auto_commit: bool = False) -> ModelType:
        if isinstance(obj_in, BaseModel):
            obj_data = obj_in.model_dump() 
        else:
            obj_data = obj_in
            
        db_obj = self.model(**obj_data) 
        
        return await self.save(db_obj, auto_commit)

    async def update(
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
                
        return await self.save(instance, auto_commit)
    
    async def delete(self, instance: ModelType, auto_commit: bool = False) -> None:
        await self.session.delete(instance)
        if auto_commit:
            try:
                await self.session.commit()
            except SQLAlchemyError:
                await self.session.rollback()
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
