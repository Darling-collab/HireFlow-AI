"""Correct ambiguous V1 status mappings without changing legacy values."""
from alembic import op
import sqlalchemy as sa

revision = "20261111_0003"
down_revision = "20261111_0002"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    bind.execute(sa.text("INSERT INTO status_dictionary (code, label, is_active) SELECT 'pending_confirmation', '待确认', 1 WHERE NOT EXISTS (SELECT 1 FROM status_dictionary WHERE code = 'pending_confirmation')"))
    # Keep V1 status as-is; only correct the derived canonical key.
    bind.execute(sa.text("UPDATE candidates SET status_key = 'pending_confirmation', status_raw = status WHERE status IN ('screening', 'interview', 'offer')"))

def downgrade():
    # Do not revert derived status fields automatically; historical raw values remain intact.
    pass
