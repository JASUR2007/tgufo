import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ThumbsUp, ThumbsDown, Share2, Flag, Bell, Lock, UserPlus, Check, AlertCircle } from 'lucide-react';
import { Video } from '../types';
import { apiService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { VideoPlayer } from '../components/video/VideoPlayer';
import { VideoComments } from '../components/video/VideoComments';
import { ReportModal } from '../components/video/ReportModal';
import { VideoCard } from '../components/video/VideoCard';

export const WatchPage: React.FC = () => {
  const { videoId } = useParams<{ videoId: string }>();
  const { user, token, openAuthModal } = useAuth();

  const [video, setVideo] = useState<Video | null>(null);
  const [recommended, setRecommended] = useState<Video[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorStatus, setErrorStatus] = useState<{ status: number; message: string } | null>(null);

  const [likesCount, setLikesCount] = useState(0);
  const [dislikesCount, setDislikesCount] = useState(0);
  const [userReaction, setUserReaction] = useState<'like' | 'dislike' | null>(null);

  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscribersCount, setSubscribersCount] = useState(0);
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  const [mediaTicket, setMediaTicket] = useState<string>('');

  // Manage Grants modal state
  const [showGrants, setShowGrants] = useState(false);
  const [grants, setGrants] = useState<any[]>([]);
  const [grantInput, setGrantInput] = useState('');

  const loadVideo = async () => {
    if (!videoId) return;
    setIsLoading(true);
    setErrorStatus(null);
    try {
      const data = await apiService.getVideo(videoId);
      setVideo(data);
      setLikesCount(data.likes_count);
      setDislikesCount(data.dislikes_count);
      setUserReaction(data.user_reaction || null);
      if (data.channel) {
        setIsSubscribed(!!data.channel.is_subscribed);
        setSubscribersCount(data.channel.subscribers_count);
      }

      if (user) {
        apiService.getMediaTicket(videoId).then((t) => {
          if (t) setMediaTicket(t);
        });
      }

      // Load recommended videos
      const recRes = await apiService.getVideos({ page_size: 10 });
      setRecommended(recRes.items.filter((v: Video) => v.id !== videoId));
    } catch (err: any) {
      console.error("Watch load error:", err);
      setErrorStatus({
        status: err.response?.status || 500,
        message: err.response?.data?.detail || 'An error occurred loading the video.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadVideo();
  }, [videoId, user]);

  const handleReaction = async (type: 'like' | 'dislike') => {
    if (!user) {
      openAuthModal();
      return;
    }
    if (!videoId) return;
    try {
      const res = await apiService.toggleReaction(videoId, type);
      setUserReaction(res.user_reaction);
      setLikesCount(res.likes_count);
      setDislikesCount(res.dislikes_count);
    } catch (e) {
      console.error("Reaction failed:", e);
    }
  };

  const handleSubscribe = async () => {
    if (!user) {
      openAuthModal();
      return;
    }
    if (!video?.channel) return;
    try {
      const res = await apiService.toggleSubscribe(video.channel.id);
      setIsSubscribed(res.is_subscribed);
      setSubscribersCount(res.subscribers_count);
    } catch (e) {
      console.error("Subscribe toggle failed:", e);
    }
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const loadGrants = async () => {
    if (!videoId) return;
    try {
      const g = await apiService.getGrants(videoId);
      setGrants(g);
    } catch (e) {
      console.error("Failed to load grants:", e);
    }
  };

  const handleAddGrant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoId || !grantInput.trim()) return;
    try {
      await apiService.addGrant(videoId, grantInput.trim());
      setGrantInput('');
      loadGrants();
    } catch (e: any) {
      alert(e.response?.data?.detail || "Could not grant access");
    }
  };

  const handleRevokeGrant = async (targetUserId: string) => {
    if (!videoId) return;
    try {
      await apiService.revokeGrant(videoId, targetUserId);
      loadGrants();
    } catch (e) {
      console.error("Revoke failed:", e);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 p-6 flex flex-col items-center justify-center">
        <div className="w-12 h-12 border-4 border-red-600 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm text-zinc-400 mt-4">Loading video stream...</span>
      </div>
    );
  }

  if (errorStatus) {
    return (
      <div className="flex-1 p-10 flex flex-col items-center justify-center text-center">
        <div className="w-16 h-16 rounded-full bg-red-950/80 border border-red-500/50 flex items-center justify-center text-red-400 mb-4">
          <AlertCircle size={36} />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Video Unavailable</h2>
        <p className="text-sm text-zinc-400 max-w-md mb-6">{errorStatus.message}</p>
        {errorStatus.status === 401 && (
          <button
            onClick={openAuthModal}
            className="px-6 py-2.5 rounded-full bg-red-600 hover:bg-red-700 text-white font-semibold text-sm transition"
          >
            Sign in to check permissions
          </button>
        )}
      </div>
    );
  }

  if (!video) return null;

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 flex flex-col lg:flex-row gap-6">
      {/* Left/Main Column: Video & Metadata */}
      <div className="flex-1 max-w-[1280px]">
        {/* Player with scoped media-ticket authenticated streaming */}
        <VideoPlayer
          src={
            mediaTicket
              ? `${video.video_url}?ticket=${encodeURIComponent(mediaTicket)}`
              : video.video_url
          }
          poster={
            video.thumbnail_url
              ? mediaTicket
                ? `${video.thumbnail_url}?ticket=${encodeURIComponent(mediaTicket)}`
                : video.thumbnail_url
              : undefined
          }
        />

        {/* Video Title */}
        <h1 className="text-xl font-bold text-white mt-4">{video.title}</h1>

        {/* Action Bar & Channel Info */}
        <div className="flex flex-wrap items-center justify-between gap-4 mt-3 pb-3 border-b border-[#272727]">
          {/* Channel info */}
          <div className="flex items-center gap-3">
            {video.channel && (
              <Link to={`/channel/${video.channel.id}`} className="shrink-0">
                <img
                  src={video.channel.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${video.channel.name}`}
                  alt={video.channel.name}
                  className="w-10 h-10 rounded-full object-cover"
                />
              </Link>
            )}

            <div className="flex flex-col">
              {video.channel && (
                <Link to={`/channel/${video.channel.id}`} className="font-semibold text-sm text-white hover:text-zinc-300">
                  {video.channel.name}
                </Link>
              )}
              <span className="text-xs text-zinc-400">{subscribersCount} subscribers</span>
            </div>

            {/* Subscribe Button */}
            {video.channel && user?.id !== video.channel.user_id && (
              <button
                onClick={handleSubscribe}
                className={`ml-3 px-4 py-2 rounded-full text-sm font-semibold transition ${
                  isSubscribed
                    ? 'bg-[#272727] text-white hover:bg-[#383838]'
                    : 'bg-white text-black hover:bg-zinc-200'
                }`}
              >
                {isSubscribed ? 'Subscribed' : 'Subscribe'}
              </button>
            )}
          </div>

          {/* Action Buttons: Like, Dislike, Share, Report, Grants */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Like & Dislike Pills */}
            <div className="flex items-center bg-[#272727] rounded-full overflow-hidden">
              <button
                onClick={() => handleReaction('like')}
                className={`flex items-center gap-1.5 px-3.5 py-2 hover:bg-[#383838] text-sm font-medium transition ${
                  userReaction === 'like' ? 'text-blue-400' : 'text-white'
                }`}
              >
                <ThumbsUp size={16} className={userReaction === 'like' ? 'fill-blue-400' : ''} />
                <span>{likesCount}</span>
              </button>
              <div className="w-[1px] h-6 bg-zinc-600" />
              <button
                onClick={() => handleReaction('dislike')}
                className={`px-3.5 py-2 hover:bg-[#383838] text-sm font-medium transition ${
                  userReaction === 'dislike' ? 'text-red-400' : 'text-white'
                }`}
              >
                <ThumbsDown size={16} className={userReaction === 'dislike' ? 'fill-red-400' : ''} />
              </button>
            </div>

            {/* Share */}
            <button
              onClick={handleShare}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-full bg-[#272727] hover:bg-[#383838] text-white text-sm font-medium transition"
            >
              <Share2 size={16} />
              <span>{copiedLink ? 'Copied!' : 'Share'}</span>
            </button>

            {/* Private Video Grants Manager (for Owner / Admin) */}
            {video.is_owner && video.visibility === 'private' && (
              <button
                onClick={() => {
                  setShowGrants(!showGrants);
                  if (!showGrants) loadGrants();
                }}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-full bg-red-950/60 border border-red-600 text-red-200 hover:bg-red-900 text-sm font-medium transition"
              >
                <Lock size={15} />
                <span>Manage Grants</span>
              </button>
            )}

            {/* Report */}
            <button
              onClick={() => setIsReportModalOpen(true)}
              className="p-2 rounded-full bg-[#272727] hover:bg-[#383838] text-zinc-400 hover:text-red-400 transition"
              title="Report Video"
            >
              <Flag size={16} />
            </button>
          </div>
        </div>

        {/* Access Grants Panel if Owner Opened it */}
        {showGrants && (
          <div className="my-4 p-4 bg-[#181818] border border-red-800/50 rounded-xl space-y-3">
            <h3 className="text-sm font-bold text-red-400 uppercase tracking-wider flex items-center gap-2">
              <UserPlus size={16} />
              Private Video Access Grants
            </h3>
            <p className="text-xs text-zinc-400">
              Only users listed below can view this video. Add users by their username:
            </p>

            <form onSubmit={handleAddGrant} className="flex gap-2">
              <input
                type="text"
                value={grantInput}
                onChange={(e) => setGrantInput(e.target.value)}
                placeholder="Enter username (e.g. demo_viewer)"
                className="flex-1 bg-[#121212] border border-[#3f3f3f] rounded-lg px-3 py-1.5 text-sm text-white outline-none"
              />
              <button
                type="submit"
                className="px-4 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold transition"
              >
                Grant Access
              </button>
            </form>

            <div className="space-y-1.5 mt-2">
              {grants.length === 0 ? (
                <span className="text-xs text-zinc-500 italic">No external users granted yet. Only you can watch.</span>
              ) : (
                grants.map((g) => (
                  <div key={g.id} className="flex items-center justify-between p-2 rounded bg-zinc-900 border border-zinc-800 text-xs">
                    <span className="text-zinc-200 font-medium">@{g.user?.username || g.user_id}</span>
                    <button
                      onClick={() => handleRevokeGrant(g.user_id)}
                      className="text-red-400 hover:text-red-300 font-semibold"
                    >
                      Revoke
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Expandable Description Box */}
        <div
          onClick={() => setIsDescriptionExpanded(!isDescriptionExpanded)}
          className="mt-4 p-4 rounded-xl bg-[#272727] hover:bg-[#323232] cursor-pointer transition select-none"
        >
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <span>{video.views_count} views</span>
            <span>•</span>
            <span>{new Date(video.created_at).toLocaleDateString()}</span>
          </div>

          <p className={`text-sm text-zinc-200 mt-2 whitespace-pre-line ${
            isDescriptionExpanded ? '' : 'line-clamp-3'
          }`}>
            {video.description || 'No description provided.'}
          </p>

          <span className="text-xs font-semibold text-zinc-400 mt-2 block">
            {isDescriptionExpanded ? 'Show less' : 'Show more'}
          </span>
        </div>

        {/* Comments Section */}
        <VideoComments videoId={video.id} />
      </div>

      {/* Right Column: Recommended Videos */}
      <div className="w-full lg:w-[380px] shrink-0 flex flex-col gap-4">
        <h3 className="font-bold text-base text-white">Related videos</h3>
        {recommended.map((recVideo) => (
          <VideoCard key={recVideo.id} video={recVideo} />
        ))}
      </div>

      {/* Report Modal */}
      <ReportModal
        videoId={video.id}
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
      />
    </div>
  );
};
