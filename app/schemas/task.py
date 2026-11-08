from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    completed: bool


class TaskCreate(BaseModel):
    title: NonEmptyString


class TaskUpdate(BaseModel):
    completed: bool | None = None
    title: NonEmptyString | None = None
