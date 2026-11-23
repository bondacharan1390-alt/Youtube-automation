"""Merge the existing Phase 5 and Higgsfield migration heads."""

from typing import Sequence, Union


revision: str = "a1b2c3d4e5f6"
down_revision: Union[tuple[str, str], None] = ("9b4e2c1a7d33", "8e4f6b7c1d22")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
