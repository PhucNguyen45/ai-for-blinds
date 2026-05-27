"""
Initial database schema for SgBe Vision.

Creates all core tables:
- users (student profiles & preferences)
- learning_sessions (study session tracking)
- learning_moments (Persistent Visual Memory with vector embeddings)
- voice_notes (recorded voice memos with transcription)
- textbook_contents (SGK content chunks for RAG)
- feedbacks (user ratings for AI outputs)

Enables pgvector extension for vector similarity search.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── users ─────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("display_name", sa.String(128), nullable=True),
        sa.Column("device_id", sa.String(256), unique=True, nullable=True),
        sa.Column("tts_speed", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("tts_pitch", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("tts_volume", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("prefers_dark_mode", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── textbook_contents ─────────────────────────────────────
    op.create_table(
        "textbook_contents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("grade", sa.Integer(), nullable=True),
        sa.Column("subject", sa.String(64), nullable=True),
        sa.Column("chapter", sa.String(128), nullable=True),
        sa.Column("chapter_number", sa.Integer(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_textbook_grade_subject", "textbook_contents", ["grade", "subject"])
    op.create_index("idx_textbook_content_hash", "textbook_contents", ["content_hash"])

    # ── learning_sessions ─────────────────────────────────────
    op.create_table(
        "learning_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_type", sa.String(32), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("items_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_session_user_type", "learning_sessions", ["user_id", "session_type"])

    # ── learning_moments ──────────────────────────────────────
    op.create_table(
        "learning_moments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(32), nullable=False, server_default="text"),
        sa.Column("file_path", sa.String(512), nullable=True),
        sa.Column("file_type", sa.String(16), nullable=True),
        sa.Column("textbook_id", sa.String(36), sa.ForeignKey("textbook_contents.id"), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("chapter", sa.String(128), nullable=True),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_moments_user_created", "learning_moments", ["user_id", "created_at"])

    # ── voice_notes ─────────────────────────────────────────────
    op.create_table(
        "voice_notes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("transcription", sa.Text(), nullable=True),
        sa.Column("is_transcribed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_voice_notes_user", "voice_notes", ["user_id"])

    # ── feedbacks ──────────────────────────────────────────────
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("learning_moment_id", sa.String(36), sa.ForeignKey("learning_moments.id"), nullable=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("learning_sessions.id"), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("helpful", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("feedback_type", sa.String(32), nullable=False, server_default="general"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("feedbacks")
    op.drop_table("voice_notes")
    op.drop_table("learning_moments")
    op.drop_table("learning_sessions")
    op.drop_table("textbook_contents")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
