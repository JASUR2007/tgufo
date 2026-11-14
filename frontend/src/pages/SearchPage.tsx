import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Video } from '../types';
import { apiService } from '../services/api';
import { Search, Eye } from 'lucide-react';

export const SearchPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const [videos, setVideos] = useState<Video[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const doSearch = async () => {
      setIsLoading(true);
      try {
        const res = await apiService.searchVideos(query);
        setVideos(res.items);
      } catch (e) {
        console.error("Search failed:", e);
      } finally {
        setIsLoading(false);
      }
    };
    if (query) {
      doSearch();
    }
  }, [query]);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-2 mb-6 text-sm text-zinc-400">
        <Search size={18} />
        <span>Search results for: <strong className="text-white">"{query}"</strong></span>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse flex flex-col sm:flex-row gap-4">
              <div className="w-full sm:w-80 aspect-video bg-zinc-800 rounded-xl shrink-0" />
              <div className="flex-1 space-y-2 py-2">
                <div className="h-5 bg-zinc-800 rounded w-2/3" />
                <div className="h-4 bg-zinc-800 rounded w-1/3" />
                <div className="h-10 bg-zinc-800 rounded w-full mt-2" />
              </div>
            </div>
          ))}
        </div>
      ) : videos.length === 0 ? (
        <div className="text-center py-20 text-zinc-500">
          <p className="text-lg">No results found matching "{query}"</p>
          <p className="text-sm mt-1">Try different keywords or check spelling.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-5">
          {videos.map((video) => (
            <div key={video.id} className="flex flex-col sm:flex-row gap-4 group cursor-pointer">
              {/* Thumbnail */}
              <Link to={`/watch/${video.id}`} className="relative w-full sm:w-80 aspect-video rounded-xl overflow-hidden bg-zinc-800 shrink-0">
                {video.thumbnail_url ? (
                  <img
                    src={video.thumbnail_url}
                    alt={video.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-zinc-900 text-zinc-600">
                    <Eye size={36} />
                  </div>
                )}
                <div className="absolute bottom-2 right-2 bg-black/80 px-1.5 py-0.5 rounded text-[11px] font-semibold text-white">
                  {Math.floor(video.duration / 60)}:{Math.floor(video.duration % 60) < 10 ? '0' : ''}{Math.floor(video.duration % 60)}
                </div>
              </Link>

              {/* Meta */}
              <div className="flex-1 flex flex-col py-1">
                <Link
                  to={`/watch/${video.id}`}
                  className="font-bold text-base text-white group-hover:text-blue-400 transition line-clamp-2"
                >
                  {video.title}
                </Link>

                <div className="flex items-center gap-2 text-xs text-zinc-400 mt-1">
                  <span>{video.views_count} views</span>
                  <span>•</span>
                  <span>{new Date(video.created_at).toLocaleDateString()}</span>
                </div>

                {video.channel && (
                  <Link
                    to={`/channel/${video.channel.id}`}
                    className="flex items-center gap-2 mt-3 hover:text-white transition"
                  >
                    <img
                      src={video.channel.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${video.channel.name}`}
                      alt={video.channel.name}
                      className="w-6 h-6 rounded-full object-cover"
                    />
                    <span className="text-xs text-zinc-300">{video.channel.name}</span>
                  </Link>
                )}

                <p className="text-xs text-zinc-400 mt-2 line-clamp-2">
                  {video.description || 'No description available.'}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
