from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from fastapi import FastAPI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
)

book = ""

class BookSchema(BaseModel):
    book: str

class TaskSchema(BaseModel):
    id: str
    title: str
    completed: bool


class TaskCreateSchema(BaseModel):
    title: str

tasks: list[TaskSchema] = []


@app.post("/book")
def set_book(payload: BookSchema):
    global book
    book = payload.book
    return {"message": "Книга сохранена"}

@app.get("/book")
def get_book():
    return f'Favourite book: {book}'

@app.get('/tasks')
def read_tasks():
    return tasks


@app.post('/tasks')
def create_task(payload: TaskCreateSchema) -> TaskSchema:
    new_task = TaskSchema(id=str(uuid4()),title=payload.title,completed=False)

    tasks.append(new_task)
    return new_task


