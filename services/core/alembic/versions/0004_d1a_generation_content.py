"""D1a additive project lifecycle; generation/content additions share this revision.

Legacy projects receive the conservative INTERNAL classification. Existing
history is never rewritten or deleted. Restore a pre-upgrade backup instead of
a lossy downgrade.
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    if connection.exec_driver_sql("PRAGMA foreign_key_check").fetchone() is not None:
        raise RuntimeError("Legacy relationship audit failed")
    # Existing duplicate versions are an audit failure, never silently renumbered.
    if connection.exec_driver_sql("SELECT 1 FROM context_packages GROUP BY project_id,version HAVING count(*)>1 LIMIT 1").fetchone():
        raise RuntimeError("Legacy context version audit failed")
    # Audit logical references before the first schema mutation. Legacy NULL
    # generation is preserved, but dangling references are never repaired here.
    import json
    checks=[
        "SELECT 1 FROM tasks t LEFT JOIN context_packages c ON c.id=t.context_package_id WHERE t.context_package_id IS NOT NULL AND (c.id IS NULL OR c.project_id<>t.project_id) LIMIT 1",
        "SELECT 1 FROM runs r LEFT JOIN tasks t ON t.id=r.task_id LEFT JOIN context_packages c ON c.id=r.context_package_id WHERE t.id IS NULL OR c.id IS NULL OR c.project_id<>t.project_id LIMIT 1",
        "SELECT 1 FROM artifacts a LEFT JOIN tasks t ON t.id=a.task_id WHERE a.task_id IS NOT NULL AND (t.id IS NULL OR t.project_id<>a.project_id) LIMIT 1",
        "SELECT 1 FROM artifacts a LEFT JOIN runs r ON r.id=a.run_id LEFT JOIN tasks t ON t.id=r.task_id WHERE a.run_id IS NOT NULL AND (r.id IS NULL OR t.project_id<>a.project_id) LIMIT 1",
        "SELECT 1 FROM evidence e LEFT JOIN runs r ON r.id=e.run_id WHERE r.id IS NULL OR r.task_id<>e.task_id LIMIT 1",
        "SELECT 1 FROM findings f LEFT JOIN runs r ON r.id=f.run_id WHERE r.id IS NULL OR r.task_id<>f.task_id LIMIT 1",
    ]
    if any(connection.exec_driver_sql(query).fetchone() for query in checks):
        raise RuntimeError('Legacy logical relationship audit failed')
    for project_id,raw in connection.exec_driver_sql('SELECT project_id,artifact_refs FROM context_packages'):
        try:references=json.loads(raw)
        except (ValueError,TypeError):raise RuntimeError('Legacy content reference audit failed') from None
        if not isinstance(references,list) or any(not isinstance(v,str) for v in references) or len(references)!=len(set(references)):
            raise RuntimeError('Legacy content reference audit failed')
        for reference in references:
            if not isinstance(reference,str) or connection.execute(sa.text('SELECT 1 FROM artifacts WHERE id=:id AND project_id=:p'),{'id':reference,'p':project_id}).fetchone() is None:
                raise RuntimeError('Legacy content reference audit failed')
    op.add_column("projects", sa.Column("classification", sa.String(32), nullable=False, server_default="INTERNAL"))
    op.add_column("projects", sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.text("0")))

    for table in ("tasks", "context_packages", "artifacts"):
        op.add_column(table, sa.Column("classification", sa.String(32), nullable=False, server_default="INTERNAL"))
    op.create_index("uq_context_project_version", "context_packages", ["project_id", "version"], unique=True)
    for table in ("context_packages", "artifacts"):
        op.execute(f"CREATE TRIGGER {table}_immutable BEFORE UPDATE ON {table} BEGIN SELECT RAISE(ABORT, 'Content metadata is immutable'); END")
        op.execute(f"CREATE TRIGGER {table}_retained BEFORE DELETE ON {table} BEGIN SELECT RAISE(ABORT, 'Content references are retained'); END")

    op.create_table("prepared_inputs",sa.Column("id",sa.String(80),primary_key=True),sa.Column("task_id",sa.String(64),sa.ForeignKey("tasks.id"),nullable=False),sa.Column("record",sa.Text(),nullable=False),sa.Column("inputs",sa.Text(),nullable=False))
    op.execute("CREATE TRIGGER prepared_inputs_immutable BEFORE UPDATE ON prepared_inputs BEGIN SELECT RAISE(ABORT, 'Prepared inputs are immutable'); END")
    op.create_table("generation_counters",
        sa.Column("task_id", sa.String(64), sa.ForeignKey("tasks.id"), primary_key=True),
        sa.Column("revision", sa.Integer(), nullable=False), sa.CheckConstraint("revision >= 0"))
    op.create_table("work_generations",
        sa.Column("task_id", sa.String(64), sa.ForeignKey("tasks.id"), primary_key=True),
        sa.Column("revision", sa.Integer(), primary_key=True),
        sa.Column("inputs", sa.Text(), nullable=False),
        sa.Column("predecessor", sa.Integer(), nullable=True),
        sa.Column("control_revision", sa.Integer(), nullable=False),
        sa.Column("aborted", sa.Boolean(), nullable=False),
        sa.Column("closed", sa.Boolean(), nullable=False),
        sa.Column("ownership_unknown", sa.Boolean(), nullable=False),
        sa.CheckConstraint("revision > 0 AND control_revision >= 0"),
        sa.ForeignKeyConstraint(["task_id", "predecessor"], ["work_generations.task_id", "work_generations.revision"]))
    op.add_column("runs", sa.Column("generation_revision", sa.Integer(), nullable=True))
    op.add_column("runs", sa.Column("generation_parent_run_id", sa.String(64), nullable=True))
    op.execute("CREATE TRIGGER run_generation_immutable BEFORE UPDATE OF generation_revision,generation_parent_run_id,task_id,context_package_id ON runs WHEN NEW.generation_revision IS NOT OLD.generation_revision OR NEW.generation_parent_run_id IS NOT OLD.generation_parent_run_id OR NEW.task_id IS NOT OLD.task_id OR NEW.context_package_id IS NOT OLD.context_package_id BEGIN SELECT RAISE(ABORT, 'Run generation is immutable'); END")
    op.execute("CREATE TRIGGER run_generation_scope BEFORE INSERT ON runs WHEN NEW.generation_revision IS NOT NULL AND NOT EXISTS (SELECT 1 FROM work_generations g WHERE g.task_id=NEW.task_id AND g.revision=NEW.generation_revision AND json_extract(g.inputs,'$.context_package_id')=NEW.context_package_id) BEGIN SELECT RAISE(ABORT, 'Run generation scope mismatch'); END")
    op.create_table("workspace_scopes",sa.Column("scope_id",sa.String(128),primary_key=True),sa.Column("fence",sa.Integer(),nullable=False),sa.Column("run_id",sa.String(64),nullable=True),sa.Column("released",sa.Boolean(),nullable=False))
    op.create_table("generation_events",sa.Column("event_id",sa.String(64),primary_key=True),sa.Column("task_id",sa.String(64),nullable=False),sa.Column("revision",sa.Integer(),nullable=False),sa.Column("control_revision",sa.Integer(),nullable=False),sa.Column("kind",sa.String(64),nullable=False),sa.Column("command_id",sa.String(128),nullable=True),sa.Column("occurred_at",sa.String(64),nullable=False),sa.Column("details",sa.Text(),nullable=False),sa.ForeignKeyConstraint(["task_id","revision"],["work_generations.task_id","work_generations.revision"]))
    op.create_table("generation_workspaces",sa.Column("task_id",sa.String(64),primary_key=True),sa.Column("revision",sa.Integer(),primary_key=True),sa.Column("run_id",sa.String(64),sa.ForeignKey("runs.id"),nullable=False),sa.Column("fence",sa.Integer(),nullable=False),sa.Column("workspace_id",sa.String(64),nullable=False),sa.Column("identity",sa.Text(),nullable=False),sa.Column("git_observation",sa.Text(),nullable=False),sa.Column("ownership",sa.Text(),nullable=False),sa.Column("recoverability",sa.Text(),nullable=False),sa.ForeignKeyConstraint(["task_id","revision"],["work_generations.task_id","work_generations.revision"]))
    op.create_table("generation_commands",
        sa.Column("principal", sa.String(128), primary_key=True),
        sa.Column("command_id", sa.String(128), primary_key=True),
        sa.Column("payload_digest", sa.String(64), nullable=False),
        sa.Column("response", sa.Text(), nullable=False))
    op.create_table("generation_writer_claims",
        sa.Column("task_id", sa.String(64), primary_key=True),
        sa.Column("revision", sa.Integer(), primary_key=True),
        sa.Column("lineage", sa.String(128), nullable=False),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("fence", sa.Integer(), nullable=False),
        sa.Column("released", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["task_id", "revision"], ["work_generations.task_id", "work_generations.revision"]),
        sa.CheckConstraint("fence > 0"))
    op.execute("CREATE TRIGGER generation_inputs_immutable BEFORE UPDATE OF task_id,revision,inputs,predecessor ON work_generations BEGIN SELECT RAISE(ABORT, 'Generation inputs are immutable'); END")
    op.execute("CREATE TRIGGER generation_lineage_immutable BEFORE UPDATE OF task_id,revision,lineage,run_id ON generation_writer_claims BEGIN SELECT RAISE(ABORT, 'Writer lineage is immutable'); END")
    op.execute("CREATE TRIGGER generation_lineage_retained BEFORE DELETE ON generation_writer_claims BEGIN SELECT RAISE(ABORT, 'Writer lineage is retained'); END")


def downgrade():
    raise RuntimeError("D1a downgrade is not lossless; restore the verified pre-upgrade backup")
