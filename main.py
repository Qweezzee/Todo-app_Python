from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from fastapi import FastAPI, HTTPException, status


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

class TaskUpdateSchema(BaseModel):
    completed: bool | None = None
    title: str | None = None


class Category(BaseModel):
    id: str
    name: str


class CategoryCreate(BaseModel):
    name: str


class CategoryUpdate(BaseModel):
    name: str | None = None


tasks: list[TaskSchema] = []
categories: list[Category] = []


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


@app.post('/tasks',status_code = status.HTTP_201_CREATED)
def create_task(payload: TaskCreateSchema) -> TaskSchema:
    new_task = TaskSchema(id=str(uuid4()),title=payload.title,completed=False)

    tasks.append(new_task)
    return new_task


@app.patch('/tasks/{task_id}')
def update_task(task_id: str,payload: TaskUpdateSchema):
    for task in tasks:
        if task.id == task_id:
            if payload.title:
                task.title = payload.title
            if payload.completed is not None:
                task.completed = payload.completed

            return task


@app.delete('/tasks/{task_id}',status_code = status.HTTP_204_NO_CONTENT)
def delete_task(task_id):
    for task in tasks:
        if task.id == task_id:
            tasks.remove(task)


@app.get("/categories")
def read_categories() -> list[Category]:
    return categories


@app.post("/categories", status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate) -> Category:
    new_category = Category(id=str(uuid4()), name=payload.name)
    categories.append(new_category)
    return new_category


@app.patch("/categories/{category_id}")
def update_category(category_id: str, payload: CategoryUpdate) -> Category:
    for category in categories:
        if category.id == category_id:
            if payload.name is not None:
                category.name = payload.name
            return category

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Category not found",
    )


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: str):
    for category in categories:
        if category.id == category_id:
            categories.remove(category)
            return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Category not found",
    )
