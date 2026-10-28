from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.category import CategoryORM
from app.repositories.category import CategoryRepository
from app.schemas.category import Category, CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.category_repository = CategoryRepository(db)

    def list_category(self) -> list[Category]:
        return [
            Category.model_validate(item)
            for item in self.category_repository.get_all()
        ]

    def _get_or_404(self, category_id: str) -> CategoryORM:
        item = self.category_repository.get_by_id(category_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
            )
        return item

    def create_category(self, payload: CategoryCreate) -> Category:
        item = self.category_repository.create(name=payload.name)
        self.db.commit()
        self.db.refresh(item)
        return Category.model_validate(item)

    def update_category(self, category_id: str, payload: CategoryUpdate) -> Category:
        item = self._get_or_404(category_id)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return Category.model_validate(item)

    def delete_category(self, category_id: str) -> None:
        item = self._get_or_404(category_id)
        self.category_repository.delete(item)
        self.db.commit()
