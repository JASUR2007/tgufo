"""initial_schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-11-13 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('role', sa.Enum('USER', 'MODERATOR', 'ADMIN', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Channels
    op.create_table(
        'channels',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('handle', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('banner_url', sa.String(length=500), nullable=True),
        sa.Column('subscribers_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_channels_handle'), 'channels', ['handle'], unique=True)

    # Videos
    op.create_table(
        'videos',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('channel_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('video_filename', sa.String(length=255), nullable=False),
        sa.Column('thumbnail_filename', sa.String(length=255), nullable=True),
        sa.Column('duration', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('views_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('likes_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('dislikes_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('visibility', sa.Enum('PUBLIC', 'UNLISTED', 'PRIVATE', name='videovisibility'), nullable=False),
        sa.Column('processing_status', sa.Enum('UPLOADING', 'QUEUED', 'PROCESSING', 'READY', 'FAILED', name='videoprocessingstatus'), nullable=False),
        sa.Column('moderation_status', sa.Enum('PENDING', 'APPROVED', 'HIDDEN', name='videomoderationstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_videos_title'), 'videos', ['title'], unique=False)
    op.create_index(op.f('ix_videos_channel_id'), 'videos', ['channel_id'], unique=False)
    op.create_index(op.f('ix_videos_visibility'), 'videos', ['visibility'], unique=False)
    op.create_index(op.f('ix_videos_processing_status'), 'videos', ['processing_status'], unique=False)
    op.create_index(op.f('ix_videos_moderation_status'), 'videos', ['moderation_status'], unique=False)

    # Video Access Grants (Private Videos)
    op.create_table(
        'video_access_grants',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('video_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('video_id', 'user_id', name='uq_video_user_grant')
    )
    op.create_index(op.f('ix_video_access_grants_video_id'), 'video_access_grants', ['video_id'], unique=False)
    op.create_index(op.f('ix_video_access_grants_user_id'), 'video_access_grants', ['user_id'], unique=False)

    # Comments
    op.create_table(
        'comments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('video_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comments_video_id'), 'comments', ['video_id'], unique=False)
    op.create_index(op.f('ix_comments_user_id'), 'comments', ['user_id'], unique=False)

    # Video Reactions
    op.create_table(
        'video_reactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('video_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('reaction_type', sa.Enum('LIKE', 'DISLIKE', name='reactiontype'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('video_id', 'user_id', name='uq_video_user_reaction')
    )

    # Subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('channel_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'channel_id', name='uq_user_channel_subscription')
    )

    # Playlists
    op.create_table(
        'playlists',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('channel_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('visibility', sa.Enum('PUBLIC', 'UNLISTED', 'PRIVATE', name='videovisibility'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Playlist Items
    op.create_table(
        'playlist_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('playlist_id', sa.String(length=36), nullable=False),
        sa.Column('video_id', sa.String(length=36), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['playlist_id'], ['playlists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('playlist_id', 'video_id', name='uq_playlist_video')
    )

    # Reports
    op.create_table(
        'reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('video_id', sa.String(length=36), nullable=False),
        sa.Column('reporter_id', sa.String(length=36), nullable=False),
        sa.Column('reason', sa.String(length=100), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'REVIEWED', 'DISMISSED', name='reportstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_status'), 'reports', ['status'], unique=False)

    # Moderation Actions
    op.create_table(
        'moderation_actions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('moderator_id', sa.String(length=36), nullable=False),
        sa.Column('video_id', sa.String(length=36), nullable=False),
        sa.Column('action', sa.Enum('HIDE', 'RESTORE', 'DELETE', name='moderationactiontype'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['moderator_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('moderation_actions')
    op.drop_table('reports')
    op.drop_table('playlist_items')
    op.drop_table('playlists')
    op.drop_table('subscriptions')
    op.drop_table('video_reactions')
    op.drop_table('comments')
    op.drop_table('video_access_grants')
    op.drop_table('videos')
    op.drop_table('channels')
    op.drop_table('users')
