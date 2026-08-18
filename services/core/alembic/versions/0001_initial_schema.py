"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("project_id", sa.String(64), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("workflow_id", sa.String(128), nullable=False),
        sa.Column("workflow_version", sa.Integer, nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("context_package_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "context_packages",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("project_id", sa.String(64), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("instructions", sa.Text, nullable=False, server_default="[]"),
        sa.Column("constraints", sa.Text, nullable=False, server_default="[]"),
        sa.Column("project_facts", sa.Text, nullable=False, server_default="{}"),
        sa.Column("artifact_refs", sa.Text, nullable=False, server_default="[]"),
        sa.Column("prior_decision_refs", sa.Text, nullable=False, server_default="[]"),
        sa.Column("memory_refs", sa.Text, nullable=False, server_default="[]"),
        sa.Column("source_refs", sa.Text, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "runs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("task_id", sa.String(64), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("workflow_id", sa.String(128), nullable=False),
        sa.Column("workflow_version", sa.Integer, nullable=False),
        sa.Column("context_package_id", sa.String(64), nullable=False),
        sa.Column("execution_target", sa.String(32), nullable=False),
        sa.Column("resume_mode", sa.String(32), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("runtime_ref", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("result_status", sa.String(32), nullable=True),
        sa.Column("result_summary", sa.Text, nullable=True),
        sa.Column("result_finding_ids", sa.Text, nullable=False, server_default="[]"),
        sa.Column("result_evidence_ids", sa.Text, nullable=False, server_default="[]"),
        sa.Column("result_artifact_ids", sa.Text, nullable=False, server_default="[]"),
    )

    op.create_table(
        "run_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("from_state", sa.String(32), nullable=False),
        sa.Column("to_state", sa.String(32), nullable=False),
        sa.Column("occurred_at", sa.DateTime, nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
    )

    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("project_id", sa.String(64), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("artifact_type", sa.String(32), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("storage_ref", sa.String(512), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size", sa.Integer, nullable=False, server_default="0"),
        sa.Column("task_id", sa.String(64), nullable=True),
        sa.Column("run_id", sa.String(64), nullable=True),
    )

    op.create_table(
        "findings",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("task_id", sa.String(64), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("evidence_refs", sa.Text, nullable=False, server_default="[]"),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "evidence",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("task_id", sa.String(64), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.String(64), nullable=False),
        sa.Column("source", sa.String(256), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("artifact_refs", sa.Text, nullable=False, server_default="[]"),
        sa.Column("metadata_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column("observed_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("evidence")
    op.drop_table("findings")
    op.drop_table("artifacts")
    op.drop_table("run_events")
    op.drop_table("runs")
    op.drop_table("context_packages")
    op.drop_table("tasks")
    op.drop_table("projects")
