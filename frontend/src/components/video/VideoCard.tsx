import React from 'react';
import { Link } from 'react-router-dom';
import { Video } from '../../types';
import { Lock, Link2, Eye } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface VideoCardProps {
  video: Video;
}

export const VideoCard: React.FC<VideoCardProps> = ({ video }) => {
  const { user, token } = useAuth();

  const authenticatedThumbUrl = video.thumbnail_url
    ? (user && token ? `${video.thumbnail_url}?token=${encodeURIComponent(token)}` : video.thumbnail_url)
    : null;

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const formatViews = (views: number) => {
    if (views >= 1000000) return `${(views / 1000000).toFixed(1)}M views`;
    if (views >= 1000) return `${(views / 1000).toFixed(1)}K views`;
    return `${views} views`;
  };

  const formatRelativeDate = (dateString: string) => {
    const diffDays = Math.floor((new Date().getTime() - new Date(dateString).getTime()) / (1000 * 3600 * 24));
    if (diffDays <= 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    return `${diffDays} days ago`;
  };

  return (
    <div className="flex flex-col gap-3 group cursor-pointer">
      {/* Thumbnail Container */}
      <Link to={`/watch/${video.id}`} className="relative aspect-video w-full rounded-xl overflow-hidden bg-zinc-800">
        {authenticatedThumbUrl ? (
          <img
            src={authenticatedThumbUrl}
            alt={video.title}
            className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-zinc-900 text-zinc-600">
            <Eye size={36} />
          </div>
        )}

        {/* Duration Badge */}
        <div className="absolute bottom-2 right-2 bg-black/80 px-1.5 py-0.5 rounded text-[11px] font-semibold text-white">
          {formatDuration(video.duration)}
        </div>

        {/* Privacy Badges */}
        {video.visibility === 'private' && (
          <div className="absolute top-2 left-2 bg-red-950/90 border border-red-500/50 text-red-300 px-2 py-0.5 rounded text-[11px] font-medium flex items-center gap-1">
            <Lock size={12} />
            <span>Private</span>
          </div>
        )}
        {video.visibility === 'unlisted' && (
          <div className="absolute top-2 left-2 bg-amber-950/90 border border-amber-500/50 text-amber-300 px-2 py-0.5 rounded text-[11px] font-medium flex items-center gap-1">
            <Link2 size={12} />
            <span>Unlisted</span>
          </div>
        )}
      </Link>

      {/* Video Info Meta */}
      <div className="flex gap-3 px-0.5">
        {video.channel && (
          <Link to={`/channel/${video.channel.id}`} className="shrink-0 mt-0.5">
            {video.channel.avatar_url ? (
              <img
                src={video.channel.avatar_url}
                alt={video.channel.name}
                className="w-9 h-9 rounded-full object-cover"
              />
            ) : (
              <div className="w-9 h-9 rounded-full bg-red-600 flex items-center justify-center font-bold text-white text-sm">
                {video.channel.name[0].toUpperCase()}
              </div>
            )}
          </Link>
        )}

        <div className="flex flex-col">
          <Link
            to={`/watch/${video.id}`}
            className="font-semibold text-sm line-clamp-2 text-white group-hover:text-blue-400 transition"
            title={video.title}
          >
            {video.title}
          </Link>

          {video.channel && (
            <Link
              to={`/channel/${video.channel.id}`}
              className="text-xs text-zinc-400 hover:text-white transition mt-1"
            >
              {video.channel.name}
            </Link>
          )}

          <div className="flex items-center text-xs text-zinc-400 gap-1 mt-0.5">
            <span>{formatViews(video.views_count)}</span>
            <span>•</span>
            <span>{formatRelativeDate(video.created_at)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
