import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Menu, Search, Upload, Bell, User as UserIcon, ShieldAlert, LogIn } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface HeaderProps {
  toggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({ toggleSidebar }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const { user, openAuthModal, openUploadModal } = useAuth();
  const navigate = useNavigate();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between px-4 h-14 bg-[#0f0f0f] border-b border-[#272727]">
      {/* Left: Menu & Brand */}
      <div className="flex items-center gap-4">
        <button
          onClick={toggleSidebar}
          className="p-2 hover:bg-[#272727] rounded-full transition text-white"
          title="Toggle Navigation"
        >
          <Menu size={22} />
        </button>

        <Link to="/" className="flex items-center gap-1">
          <div className="w-8 h-6 bg-[#ff0000] rounded-lg flex items-center justify-center text-white">
            <div className="w-0 h-0 border-y-[5px] border-y-transparent border-l-[9px] border-l-white ml-0.5" />
          </div>
          <span className="font-bold text-lg tracking-tighter text-white">YouTube</span>
          <span className="text-[10px] text-zinc-400 font-semibold self-start ml-0.5">RU</span>
        </Link>
      </div>

      {/* Middle: Search Box */}
      <form onSubmit={handleSearch} className="flex items-center max-w-[640px] w-full mx-4">
        <div className="flex items-center w-full border border-[#303030] bg-[#121212] rounded-l-full px-4 py-1.5 focus-within:border-blue-500">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search videos..."
            className="w-full bg-transparent outline-none text-sm text-white placeholder-zinc-500"
          />
        </div>
        <button
          type="submit"
          className="bg-[#222222] hover:bg-[#272727] border border-l-0 border-[#303030] rounded-r-full px-5 py-2 text-zinc-300 transition"
          title="Search"
        >
          <Search size={18} />
        </button>
      </form>

      {/* Right: Actions & User */}
      <div className="flex items-center gap-2">
        {/* Upload Button */}
        <button
          onClick={openUploadModal}
          className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#272727] hover:bg-[#383838] text-white text-sm font-medium transition"
        >
          <Upload size={18} />
          <span className="hidden sm:inline">Upload</span>
        </button>

        {/* Moderation Link for Mod / Admin */}
        {user && (user.role === 'moderator' || user.role === 'admin') && (
          <Link
            to="/moderation"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-purple-950/60 hover:bg-purple-900 border border-purple-600 text-purple-200 text-sm font-medium transition"
          >
            <ShieldAlert size={16} />
            <span className="hidden md:inline">Moderation</span>
          </Link>
        )}

        {/* User Profile / Login */}
        {user ? (
          <Link
            to={`/channel/${user.id}`}
            className="flex items-center gap-2 p-1 hover:bg-[#272727] rounded-full transition"
            title={user.username}
          >
            {user.avatar_url ? (
              <img
                src={user.avatar_url}
                alt={user.username}
                className="w-8 h-8 rounded-full object-cover border border-zinc-700"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-red-600 flex items-center justify-center font-bold text-white text-sm">
                {user.username[0].toUpperCase()}
              </div>
            )}
          </Link>
        ) : (
          <button
            onClick={openAuthModal}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-blue-500 text-blue-400 hover:bg-blue-950/40 text-sm font-medium transition"
          >
            <LogIn size={18} />
            <span>Sign in</span>
          </button>
        )}
      </div>
    </header>
  );
};
