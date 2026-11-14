import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Playlist, Video } from '../types';
import { apiService } from '../services/api';
import { ListVideo, Film } from 'lucide-react';

export const PlaylistsPage: React.FC = () => {
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadPlaylists = async () => {
      setIsLoading(true);
      try {
        // Fetch all videos, and if any channel has playlists, show them
        const vRes = await apiService.getVideos({ page_size: 20 });
        const channelIds: string[] = Array.from(new Set(vRes.items.map((v: Video) => v.channel_id)));
        const allPls: Playlist[] = [];
        for (const cid of channelIds) {
          try {
            const pls = await apiService.getChannelPlaylists(cid);
            allPls.push(...pls);
          } catch (e) {}
        }
        setPlaylists(allPls);
      } catch (e) {
        console.error("Failed to load playlists:", e);
      } finally {
        setIsLoading(false);
      }
    };
    loadPlaylists();
  }, []);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-2 mb-6">
        <ListVideo size={24} className="text-red-500" />
        <h1 className="text-xl font-bold text-white">Playlists</h1>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse aspect-video bg-zinc-800 rounded-xl" />
          ))}
        </div>
      ) : playlists.length === 0 ? (
        <div className="text-center py-20 text-zinc-500">
          <ListVideo size={48} className="mx-auto mb-3 text-zinc-600" />
          <p className="text-base font-semibold text-zinc-300">No playlists found</p>
          <p className="text-xs mt-1">Playlists created on channels will be displayed here.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {playlists.map((pl) => (
            <div
              key={pl.id}
              className="group bg-[#212121] border border-[#272727] rounded-2xl overflow-hidden hover:border-zinc-500 transition flex flex-col"
            >
              <div className="relative aspect-video bg-zinc-800 flex items-center justify-center text-zinc-400 group-hover:scale-[1.02] transition">
                <Film size={40} />
                <div className="absolute bottom-2 right-2 bg-black/80 px-2 py-0.5 rounded text-xs text-white font-medium flex items-center gap-1">
                  <ListVideo size={13} />
                  <span>{pl.items?.length || 0} videos</span>
                </div>
              </div>

              <div className="p-4 flex flex-col flex-1">
                <h3 className="font-bold text-base text-white group-hover:text-blue-400 transition">
                  {pl.title}
                </h3>
                <p className="text-xs text-zinc-400 mt-1 line-clamp-2">
                  {pl.description || 'Playlist collection.'}
                </p>

                {pl.items && pl.items.length > 0 && (
                  <Link
                    to={`/watch/${pl.items[0].video_id}`}
                    className="mt-4 px-4 py-2 rounded-lg bg-[#272727] hover:bg-[#323232] text-xs font-semibold text-white text-center transition"
                  >
                    Play All
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
