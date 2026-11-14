import React, { useState, useEffect } from 'react';
import { Video } from '../types';
import { apiService } from '../services/api';
import { VideoCard } from '../components/video/VideoCard';
import { Film } from 'lucide-react';

export const HomePage: React.FC = () => {
  const [videos, setVideos] = useState<Video[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState('All');

  const categories = [
    'All',
    'FastAPI',
    'Docker',
    'Python',
    'Architecture',
    'DevOps',
    'Web Development',
    'AI Engineering'
  ];

  const fetchVideos = async (filterText?: string) => {
    setIsLoading(true);
    try {
      const search = filterText && filterText !== 'All' ? filterText : undefined;
      const res = await apiService.getVideos({ search });
      setVideos(res.items);
    } catch (e) {
      console.error("Failed to load videos:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchVideos(activeCategory);
  }, [activeCategory]);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-4">
      {/* Categories Filter Bar */}
      <div className="flex items-center gap-3 overflow-x-auto pb-4 scrollbar-none select-none">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`px-3.5 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition ${
              activeCategory === cat
                ? 'bg-white text-black'
                : 'bg-[#272727] text-white hover:bg-[#383838]'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Videos Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-x-4 gap-y-8 mt-2">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="animate-pulse flex flex-col gap-3">
              <div className="aspect-video bg-zinc-800 rounded-xl" />
              <div className="flex gap-3">
                <div className="w-9 h-9 rounded-full bg-zinc-800 shrink-0" />
                <div className="flex-1 space-y-2 py-1">
                  <div className="h-4 bg-zinc-800 rounded w-3/4" />
                  <div className="h-3 bg-zinc-800 rounded w-1/2" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : videos.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center text-zinc-500">
          <Film size={54} className="mb-3 text-zinc-600" />
          <h3 className="text-lg font-semibold text-zinc-300">No videos found</h3>
          <p className="text-sm mt-1">Be the first to upload a video or click a demo account to seed content.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-x-4 gap-y-8 mt-2">
          {videos.map((video) => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>
      )}
    </div>
  );
};
