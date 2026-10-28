from pydantic import BaseModel, ConfigDict


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    completed: bool


class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    completed: bool | None = None
    title: str | None = None
