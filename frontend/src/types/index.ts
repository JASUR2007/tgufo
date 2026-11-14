export type UserRole = 'user' | 'moderator' | 'admin';
export type VideoVisibility = 'public' | 'unlisted' | 'private';
export type VideoProcessingStatus = 'uploading' | 'queued' | 'processing' | 'ready' | 'failed';
export type VideoModerationStatus = 'pending' | 'approved' | 'hidden';

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  avatar_url: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface Channel {
  id: string;
  user_id: string;
  handle: string;
  name: string;
  description: string;
  avatar_url: string | null;
  banner_url: string | null;
  subscribers_count: number;
  created_at: string;
  is_subscribed?: boolean;
}

export interface Video {
  id: string;
  channel_id: string;
  title: string;
  description: string;
  video_url: string;
  thumbnail_url: string | null;
  duration: number;
  views_count: number;
  likes_count: number;
  dislikes_count: number;
  visibility: VideoVisibility;
  processing_status: VideoProcessingStatus;
  moderation_status: VideoModerationStatus;
  created_at: string;
  channel?: Channel;
  user_reaction?: 'like' | 'dislike' | null;
  is_owner?: boolean;
}

export interface VideoAccessGrant {
  id: string;
  video_id: string;
  user_id: string;
  user?: User;
  created_at: string;
}

export interface Comment {
  id: string;
  video_id: string;
  user_id: string;
  content: string;
  created_at: string;
  user?: User;
  can_delete?: boolean;
}

export interface Playlist {
  id: string;
  channel_id: string;
  title: string;
  description: string;
  visibility: VideoVisibility;
  created_at: string;
  items?: PlaylistItem[];
}

export interface PlaylistItem {
  id: string;
  playlist_id: string;
  video_id: string;
  position: number;
  added_at: string;
  video?: Video;
}

export interface Report {
  id: string;
  video_id: string;
  reporter_id: string;
  reason: string;
  details: string;
  status: 'pending' | 'reviewed' | 'dismissed';
  created_at: string;
  reporter?: User;
  video?: Video;
}

export interface ModerationAction {
  id: string;
  moderator_id: string;
  video_id: string;
  action: 'hide' | 'restore' | 'delete';
  reason: string;
  created_at: string;
  moderator?: User;
}
