import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Channel, Video, Playlist } from '../types';
import { apiService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { VideoCard } from '../components/video/VideoCard';
import { Video as VideoIcon, ListVideo, Info } from 'lucide-react';

export const ChannelPage: React.FC = () => {
  const { channelId } = useParams<{ channelId: string }>();
  const { user, openAuthModal } = useAuth();

  const [channel, setChannel] = useState<Channel | null>(null);
  const [videos, setVideos] = useState<Video[]>([]);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [activeTab, setActiveTab] = useState<'videos' | 'playlists' | 'about'>('videos');
  const [isLoading, setIsLoading] = useState(true);

  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscribersCount, setSubscribersCount] = useState(0);

  const loadChannelData = async () => {
    if (!channelId) return;
    setIsLoading(true);
    try {
      const ch = await apiService.getChannel(channelId);
      setChannel(ch);
      setIsSubscribed(!!ch.is_subscribed);
      setSubscribersCount(ch.subscribers_count);

      const vList = await apiService.getChannelVideos(channelId);
      setVideos(vList);

      const pList = await apiService.getChannelPlaylists(channelId);
      setPlaylists(pList);
    } catch (e) {
      console.error("Failed to load channel:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadChannelData();
  }, [channelId]);

  const handleSubscribe = async () => {
    if (!user) {
      openAuthModal();
      return;
    }
    if (!channel) return;
    try {
      const res = await apiService.toggleSubscribe(channel.id);
      setIsSubscribed(res.is_subscribed);
      setSubscribersCount(res.subscribers_count);
    } catch (e) {
      console.error("Failed subscribe:", e);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 p-6 flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-red-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!channel) {
    return (
      <div className="flex-1 p-10 text-center text-zinc-400">
        Channel not found.
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Banner */}
      <div className="w-full h-36 sm:h-52 md:h-64 bg-zinc-800 overflow-hidden relative">
        {channel.banner_url ? (
          <img
            src={channel.banner_url}
            alt={channel.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-r from-red-900 to-zinc-900" />
        )}
      </div>

      {/* Channel Header Meta */}
      <div className="max-w-7xl mx-auto px-6 py-6 border-b border-[#272727]">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <img
              src={channel.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${channel.name}`}
              alt={channel.name}
              className="w-20 h-20 sm:w-28 sm:h-28 rounded-full object-cover border-4 border-[#0f0f0f]"
            />
            <div className="flex flex-col">
              <h1 className="text-2xl font-bold text-white">{channel.name}</h1>
              <div className="flex items-center gap-2 text-sm text-zinc-400 mt-1">
                <span>{channel.handle}</span>
                <span>•</span>
                <span>{subscribersCount} subscribers</span>
                <span>•</span>
                <span>{videos.length} videos</span>
              </div>
              <p className="text-sm text-zinc-300 mt-2 max-w-2xl line-clamp-2">
                {channel.description || 'Welcome to this channel!'}
              </p>
            </div>
          </div>

          {user?.id !== channel.user_id && (
            <button
              onClick={handleSubscribe}
              className={`px-6 py-2.5 rounded-full font-semibold text-sm transition ${
                isSubscribed
                  ? 'bg-[#272727] text-white hover:bg-[#383838]'
                  : 'bg-white text-black hover:bg-zinc-200'
              }`}
            >
              {isSubscribed ? 'Subscribed' : 'Subscribe'}
            </button>
          )}
        </div>

        {/* Channel Tabs */}
        <div className="flex gap-8 mt-6">
          <button
            onClick={() => setActiveTab('videos')}
            className={`pb-3 font-semibold text-sm flex items-center gap-2 border-b-2 transition ${
              activeTab === 'videos'
                ? 'border-white text-white'
                : 'border-transparent text-zinc-400 hover:text-white'
            }`}
          >
            <VideoIcon size={18} />
            <span>Videos ({videos.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('playlists')}
            className={`pb-3 font-semibold text-sm flex items-center gap-2 border-b-2 transition ${
              activeTab === 'playlists'
                ? 'border-white text-white'
                : 'border-transparent text-zinc-400 hover:text-white'
            }`}
          >
            <ListVideo size={18} />
            <span>Playlists ({playlists.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('about')}
            className={`pb-3 font-semibold text-sm flex items-center gap-2 border-b-2 transition ${
              activeTab === 'about'
                ? 'border-white text-white'
                : 'border-transparent text-zinc-400 hover:text-white'
            }`}
          >
            <Info size={18} />
            <span>About</span>
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        {activeTab === 'videos' && (
          videos.length === 0 ? (
            <div className="text-center py-16 text-zinc-500">
              No videos uploaded yet on this channel.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-x-4 gap-y-8">
              {videos.map((v) => (
                <VideoCard key={v.id} video={v} />
              ))}
            </div>
          )
        )}

        {activeTab === 'playlists' && (
          playlists.length === 0 ? (
            <div className="text-center py-16 text-zinc-500">
              No public playlists available.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {playlists.map((pl) => (
                <div key={pl.id} className="p-4 rounded-xl bg-[#212121] border border-[#272727] flex flex-col gap-2">
                  <div className="aspect-video bg-zinc-800 rounded-lg flex items-center justify-center text-zinc-500">
                    <ListVideo size={36} />
                  </div>
                  <h3 className="font-bold text-white text-base mt-1">{pl.title}</h3>
                  <p className="text-xs text-zinc-400 line-clamp-2">{pl.description || 'Playlist'}</p>
                </div>
              ))}
            </div>
          )
        )}

        {activeTab === 'about' && (
          <div className="max-w-2xl bg-[#212121] p-6 rounded-2xl border border-[#272727] space-y-4">
            <h3 className="text-lg font-bold text-white">About {channel.name}</h3>
            <p className="text-sm text-zinc-300 whitespace-pre-line leading-relaxed">
              {channel.description || 'No detailed description provided.'}
            </p>
            <div className="border-t border-[#303030] pt-4 text-xs text-zinc-400 space-y-1">
              <p>Joined: {new Date(channel.created_at).toLocaleDateString()}</p>
              <p>Total subscribers: {subscribersCount}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
