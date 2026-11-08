from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Category(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class CategoryCreate(BaseModel):
    name: NonEmptyString


class CategoryUpdate(BaseModel):
    name: NonEmptyString | None = None
