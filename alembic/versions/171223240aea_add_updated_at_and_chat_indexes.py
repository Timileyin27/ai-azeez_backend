"""add updated_at and chat indexes

Revision ID: 171223240aea
Revises: 0955890a7c93
Create Date: 2026-10-19 20:23:11.378901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '171223240aea'
down_revision: Union[str, None] = '0955890a7c93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE conversations
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_conversations_user_id ON conversations (user_id)")
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_messages_conversation_created
        ON messages (conversation_id, created_at)
    """)

def downgrade() -> None:
   
    op.execute("DROP INDEX IF EXISTS ix_messages_conversation_created")
    op.execute("DROP INDEX IF EXISTS ix_conversations_user_id")
    op.execute("ALTER TABLE conversations DROP COLUMN IF EXISTS updated_at")
