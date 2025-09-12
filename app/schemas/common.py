from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

DataT = TypeVar('DataT')


class ResponseModel(BaseModel, Generic[DataT]):
    success: bool
    data: Optional[DataT] = None
    error: Optional[str] = None
    message: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[DataT]):
    items: list[DataT]
    total: int
    page: int
    size: int
    pages: int


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: Optional[str] = None
    details: Optional[Any] = None
