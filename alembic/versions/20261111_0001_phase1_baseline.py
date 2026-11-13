"""Phase 1 baseline; preserves existing V1 candidates."""
from alembic import op
import sqlalchemy as sa
from hireflow.models import Base
revision = "20261111_0001"
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("candidates"):
        cols = {c["name"] for c in inspector.get_columns("candidates")}
        if "status_key" not in cols: op.add_column("candidates", sa.Column("status_key", sa.String(40), nullable=True))
        if "status_raw" not in cols: op.add_column("candidates", sa.Column("status_raw", sa.String(100), nullable=True))
        for table in Base.metadata.sorted_tables:
            if table.name != "candidates" and not sa.inspect(bind).has_table(table.name): table.create(bind)
    else:
        Base.metadata.create_all(bind)
    bind.execute(sa.text("UPDATE candidates SET status_key = CASE status WHEN 'new' THEN 'invited' WHEN 'screening' THEN 'screening_passed' WHEN 'interview' THEN 'first_round_passed' WHEN 'hired' THEN 'hired' ELSE NULL END WHERE status_key IS NULL"))
def downgrade():
    pass
