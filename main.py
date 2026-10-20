from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column, Session

DATABASE_URL = 'postgresql+psycopg://postgres:admin@127.0.0.1:15432/postgres'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))

class TaskORM(Base):
    __tablename__ = "tasks"

    title: Mapped[str]
    completed: Mapped[bool] = mapped_column(default=False)

class CategoryORM(Base):
    __tablename__ = "categories"

    name: Mapped[str]

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def task_to_model(task_orm: TaskORM) ->TaskSchema:
    return TaskSchema(id=task_orm.id, title=task_orm.title, completed=task_orm.completed)

def category_to_model(category_orm: CategoryORM) -> Category:
    return Category(id=category_orm.id, name=category_orm.name)

@app.post("/book")
def set_book(payload: BookSchema):
    global book
    book = payload.book
    return {"message": "Книга сохранена"}

@app.get("/book")
def get_book():
    return f'Favourite book: {book}'

@app.get('/tasks')
def read_tasks(db: Session = Depends(get_db)) -> list[TaskSchema]:
    tasks_from_db = db.scalars(select(TaskORM)).all()
    return [task_to_model(task) for task in tasks_from_db]


@app.post('/tasks',status_code = status.HTTP_201_CREATED)
def create_task(payload: TaskCreateSchema, db: Session = Depends(get_db)) -> TaskSchema:
    new_task = TaskORM(title=payload.title, completed=False)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return task_to_model(new_task)


@app.patch('/tasks/{task_id}')
def update_task(task_id: str, payload: TaskUpdateSchema, db: Session = Depends(get_db)) -> TaskSchema:
    task = db.get(TaskORM, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if payload.title is not None:
        task.title = payload.title
    if payload.completed is not None:
        task.completed = payload.completed
    db.commit()
    db.refresh(task)
    return task_to_model(task)


@app.delete('/tasks/{task_id}',status_code = status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(TaskORM, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.delete(task)
    db.commit()


@app.get("/categories")
def read_categories(db: Session = Depends(get_db)) -> list[Category]:
    categories_from_db = db.scalars(select(CategoryORM)).all()
    return [category_to_model(category) for category in categories_from_db]


@app.post("/categories", status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> Category:
    new_category = CategoryORM(name=payload.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return category_to_model(new_category)


@app.patch("/categories/{category_id}")
def update_category(category_id: str, payload: CategoryUpdate, db: Session = Depends(get_db)) -> Category:
    category = db.get(CategoryORM, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    if payload.name is not None:
        category.name = payload.name
    db.commit()
    db.refresh(category)
    return category_to_model(category)


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: str, db: Session = Depends(get_db)):
    category = db.get(CategoryORM, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    db.delete(category)
    db.commit()



