import axios from 'axios';
import { User, Channel, Video, Comment, Playlist, Report, ModerationAction, VideoAccessGrant } from '../types';

const api = axios.create({
  baseURL: '/api/v1',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('yt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const apiService = {
  // Auth
  async register(data: any) {
    const res = await api.post('/auth/register', data);
    return res.data;
  },
  async login(email: string, password: string) {
    const res = await api.post('/auth/login', { email, password });
    return res.data;
  },
  async getMe(): Promise<User> {
    const res = await api.get('/auth/me');
    return res.data;
  },

  // Videos
  async getVideos(params?: { search?: string; page?: number; page_size?: number }) {
    const res = await api.get('/videos', { params });
    return res.data;
  },
  async searchVideos(q: string) {
    const res = await api.get('/videos/search', { params: { q } });
    return res.data;
  },
  async getVideo(id: string): Promise<Video> {
    const res = await api.get(`/videos/${id}`);
    return res.data;
  },
  async uploadVideo(formData: FormData) {
    const res = await api.post('/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  async updateVideo(id: string, data: any) {
    const res = await api.patch(`/videos/${id}`, data);
    return res.data;
  },
  async deleteVideo(id: string) {
    await api.delete(`/videos/${id}`);
  },

  // Private Video Grants
  async getGrants(videoId: string): Promise<VideoAccessGrant[]> {
    const res = await api.get(`/videos/${videoId}/grants`);
    return res.data;
  },
  async addGrant(videoId: string, userIdentifier: string) {
    const res = await api.post(`/videos/${videoId}/grants`, { user_identifier: userIdentifier });
    return res.data;
  },
  async revokeGrant(videoId: string, userId: string) {
    await api.delete(`/videos/${videoId}/grants/${userId}`);
  },

  // Reactions
  async toggleReaction(videoId: string, reactionType: 'like' | 'dislike') {
    const res = await api.post(`/videos/${videoId}/reactions`, { reaction_type: reactionType });
    return res.data;
  },

  // Comments
  async getComments(videoId: string): Promise<Comment[]> {
    const res = await api.get(`/videos/${videoId}/comments`);
    return res.data;
  },
  async postComment(videoId: string, content: string): Promise<Comment> {
    const res = await api.post(`/videos/${videoId}/comments`, { content });
    return res.data;
  },
  async deleteComment(commentId: string) {
    await api.delete(`/comments/${commentId}`);
  },

  // Channels & Subscriptions
  async getChannel(channelId: string): Promise<Channel> {
    const res = await api.get(`/channels/${channelId}`);
    return res.data;
  },
  async getChannelVideos(channelId: string): Promise<Video[]> {
    const res = await api.get(`/channels/${channelId}/videos`);
    return res.data;
  },
  async toggleSubscribe(channelId: string) {
    const res = await api.post(`/channels/${channelId}/subscribe`);
    return res.data;
  },

  // Playlists
  async getChannelPlaylists(channelId: string): Promise<Playlist[]> {
    const res = await api.get(`/playlists/channel/${channelId}`);
    return res.data;
  },
  async createPlaylist(data: { title: string; description?: string; visibility?: string }): Promise<Playlist> {
    const res = await api.post('/playlists', data);
    return res.data;
  },
  async getPlaylist(playlistId: string): Promise<Playlist> {
    const res = await api.get(`/playlists/${playlistId}`);
    return res.data;
  },
  async addPlaylistItem(playlistId: string, videoId: string) {
    const res = await api.post(`/playlists/${playlistId}/items`, { video_id: videoId });
    return res.data;
  },

  // Moderation
  async reportVideo(data: { video_id: string; reason: string; details?: string }): Promise<Report> {
    const res = await api.post('/moderation/reports', data);
    return res.data;
  },
  async getReports(): Promise<Report[]> {
    const res = await api.get('/moderation/reports');
    return res.data;
  },
  async hideVideo(videoId: string, reason: string): Promise<ModerationAction> {
    const res = await api.post(`/moderation/videos/${videoId}/hide`, { action: 'hide', reason });
    return res.data;
  },
  async restoreVideo(videoId: string, reason: string): Promise<ModerationAction> {
    const res = await api.post(`/moderation/videos/${videoId}/restore`, { action: 'restore', reason });
    return res.data;
  },
  async getModerationActions(): Promise<ModerationAction[]> {
    const res = await api.get('/moderation/actions');
    return res.data;
  },

  // Users
  async searchUsers(search?: string): Promise<User[]> {
    const res = await api.get('/users', { params: { search } });
    return res.data;
  }
};
