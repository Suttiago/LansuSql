from typing import TypeVar, Generic, Type, Optional, Sequence, Any, Union, Dict
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession # Importante: usar AsyncSession
from pydantic import BaseModel
from .types import ModelType, PrimaryKeyType, UpdateDict
from .utils import build_filters

class AsyncBaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
        
    async def get_by_id(self, id: PrimaryKeyType) -> Optional[ModelType]:
        return await self.session.get(self.model, id)
    
    async def list_all(self) -> Sequence[ModelType]:
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by(self, **kwargs) -> Sequence[ModelType]:
        filters = build_filters(self.model, kwargs)
        stmt = select(self.model).where(*filters)        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def save(self, instance: ModelType, auto_commit: bool = False) -> ModelType:
        self.session.add(instance)
        if auto_commit:
            await self.session.commit()
            await self.session.refresh(instance)
        return instance
    
    async def create(self, obj_in: Union[BaseModel, Dict[str, Any]], auto_commit: bool = False) -> ModelType:
        if isinstance(obj_in, BaseModel):
            obj_data = obj_in.model_dump() 
        else:
            obj_data = obj_in
            
        db_obj = self.model(**obj_data) 
        
        return await self.save(db_obj, auto_commit)

    async def update(self, instance: ModelType, obj_in: Union[BaseModel, Dict[str, Any]], auto_commit: bool = False) -> ModelType:
        if isinstance(obj_in, BaseModel):
            update_data = obj_in.model_dump(exclude_unset=True) 
        else:
            update_data = obj_in

        for key, value in update_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
                
        return await self.save(instance, auto_commit)
    
    async def delete(self, instance: ModelType, auto_commit: bool = False) -> None:
        self.session.delete(instance)
        if auto_commit:
            await self.session.commit()