"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-07-22 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_locations_name", "locations", ["name"])

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_categories_name", "categories", ["name"])

    op.create_table(
        "test_modules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_index", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_test_modules_name", "test_modules", ["name"])
    op.create_index("ix_test_modules_sort_index", "test_modules", ["sort_index"])

    op.create_table(
        "pcs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_pcs_name", "pcs", ["name"])
    op.create_index("ix_pcs_location_id", "pcs", ["location_id"])

    op.create_table(
        "dongles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dongle_id", sa.String(length=255), nullable=False),
        sa.Column("pc_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["pc_id"], ["pcs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dongle_id"),
    )
    op.create_index("ix_dongles_dongle_id", "dongles", ["dongle_id"])
    op.create_index("ix_dongles_pc_id", "dongles", ["pc_id"])

    op.create_table(
        "category_test_modules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("test_module_id", sa.Integer(), nullable=False),
        sa.Column("sort_index", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_module_id"], ["test_modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", "test_module_id", name="uq_category_test_module"),
    )
    op.create_index("ix_category_test_modules_category_id", "category_test_modules", ["category_id"])
    op.create_index("ix_category_test_modules_test_module_id", "category_test_modules", ["test_module_id"])

    op.create_table(
        "dongle_test_modules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dongle_id", sa.Integer(), nullable=False),
        sa.Column("test_module_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["dongle_id"], ["dongles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_module_id"], ["test_modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dongle_id", "test_module_id", name="uq_dongle_test_module"),
    )
    op.create_index("ix_dongle_test_modules_dongle_id", "dongle_test_modules", ["dongle_id"])
    op.create_index("ix_dongle_test_modules_test_module_id", "dongle_test_modules", ["test_module_id"])


def downgrade() -> None:
    op.drop_table("dongle_test_modules")
    op.drop_table("category_test_modules")
    op.drop_table("dongles")
    op.drop_table("pcs")
    op.drop_table("test_modules")
    op.drop_table("categories")
    op.drop_table("locations")
