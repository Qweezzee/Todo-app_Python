"""create categories table

Revision ID: d17b69959561
Revises: 57ed4e859a69
Create Date: 2026-11-08 19:02:17.583615

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d17b69959561"
down_revision: Union[str, Sequence[str], None] = "57ed4e859a69"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Keep tables created before Alembic; also supports offline SQL generation.
    op.create_table(
        "categories",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("categories")
