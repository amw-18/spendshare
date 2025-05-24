from typing import Type, TypeVar, Optional
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, select

ModelType = TypeVar("ModelType", bound=SQLModel)

async def get_object_or_404(
    session: AsyncSession, model_class: Type[ModelType], object_id: int
) -> ModelType:
    """
    Fetches an object by its ID from the database.
    Raises HTTPException with status_code 404 if the object is not found.
    """
    obj = await session.get(model_class, object_id)
    if not obj:
        raise HTTPException(
            status_code=404, detail=f"{model_class.__name__} with id {object_id} not found"
        )
    return obj

async def get_object_by_attribute_or_404(
    session: AsyncSession, model_class: Type[ModelType], attribute_name: str, attribute_value: any
) -> ModelType:
    """
    Fetches an object by a specific attribute from the database.
    Raises HTTPException with status_code 404 if the object is not found.
    """
    statement = select(model_class).where(getattr(model_class, attribute_name) == attribute_value)
    result = await session.exec(statement)
    obj = result.first()
    if not obj:
        raise HTTPException(
            status_code=404, detail=f"{model_class.__name__} with {attribute_name} {attribute_value} not found"
        )
    return obj

async def get_optional_object_by_attribute(
    session: AsyncSession, model_class: Type[ModelType], attribute_name: str, attribute_value: any
) -> Optional[ModelType]:
    """
    Fetches an object by a specific attribute from the database.
    Returns None if the object is not found.
    """
    statement = select(model_class).where(getattr(model_class, attribute_name) == attribute_value)
    result = await session.exec(statement)
    return result.first()
