"""Add candidate query indexes and canonical status dictionary."""
from alembic import op
import sqlalchemy as sa

revision = "20261111_0002"
down_revision = "20261111_0001"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {idx["name"] for idx in inspector.get_indexes("candidates")} if inspector.has_table("candidates") else set()
    if "ix_candidates_status" not in existing:
        op.create_index("ix_candidates_status", "candidates", ["status"])
    if "ix_candidates_follow_up_date" not in existing:
        op.create_index("ix_candidates_follow_up_date", "candidates", ["follow_up_date"])
    statuses = [("invited", "已邀约"), ("screening_passed", "初筛通过"), ("first_round_passed", "一面通过"), ("second_round_passed", "二面通过"), ("final_round_passed", "终面通过"), ("offer_sent", "Offer 已发"), ("offer_accepted", "Offer 已接受"), ("hired", "已入职"), ("withdrawn", "已放弃"), ("rejected", "已淘汰"), ("talent_pool", "人才池储备")]
    for code, label in statuses:
        bind.execute(sa.text("INSERT INTO status_dictionary (code, label, is_active) SELECT :code, :label, 1 WHERE NOT EXISTS (SELECT 1 FROM status_dictionary WHERE code = :code)"), {"code": code, "label": label})

def downgrade():
    pass
