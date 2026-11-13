"""Add AI review, raw message and recruitment event metadata."""
from alembic import op
import sqlalchemy as sa

revision = "20261111_0004"
down_revision = "20261111_0003"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    additions = {
        "candidates": [("last_activity_at", sa.DateTime(timezone=True))],
        "recruitment_events": [("status_key", sa.String(40)), ("raw_expression", sa.Text()), ("event_time", sa.DateTime(timezone=True))],
        "raw_messages": [("filename", sa.String(255)), ("received_at", sa.DateTime(timezone=True)), ("parse_status", sa.String(30), "pending"), ("parse_error", sa.Text())],
        "ai_review_records": [("modified_json", sa.Text()), ("rejection_reason", sa.Text()), ("model", sa.String(100)), ("prompt_version", sa.String(50))],
    }
    for table, cols in additions.items():
        existing = {c["name"] for c in sa.inspect(bind).get_columns(table)}
        for item in cols:
            name, typ = item[:2]
            if name not in existing:
                kwargs = {"server_default": item[2]} if len(item) == 3 else {}
                op.add_column(table, sa.Column(name, typ, **kwargs))

def downgrade():
    pass
