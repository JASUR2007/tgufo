import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Compass, PlaySquare, Clock, ThumbsUp, ShieldAlert, ListVideo, FileText, User } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  isOpen: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen }) => {
  const { user } = useAuth();

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-5 px-3 py-2.5 rounded-xl text-sm transition ${
      isActive
        ? 'bg-[#272727] text-white font-semibold'
        : 'text-zinc-300 hover:bg-[#222222]'
    }`;

  if (!isOpen) {
    // Collapsed compact sidebar
    return (
      <aside className="w-18 bg-[#0f0f0f] border-r border-[#272727] flex flex-col items-center py-3 gap-6 select-none hidden sm:flex">
        <NavLink to="/" className="flex flex-col items-center gap-1 text-[10px] text-zinc-300 hover:text-white">
          <Home size={22} />
          <span>Home</span>
        </NavLink>
        <NavLink to="/playlists" className="flex flex-col items-center gap-1 text-[10px] text-zinc-300 hover:text-white">
          <ListVideo size={22} />
          <span>Playlists</span>
        </NavLink>
        {user && (user.role === 'moderator' || user.role === 'admin') && (
          <NavLink to="/moderation" className="flex flex-col items-center gap-1 text-[10px] text-purple-400 hover:text-white">
            <ShieldAlert size={22} />
            <span>Mod</span>
          </NavLink>
        )}
      </aside>
    );
  }

  return (
    <aside className="w-60 bg-[#0f0f0f] border-r border-[#272727] flex flex-col p-3 overflow-y-auto select-none shrink-0 h-[calc(100vh-56px)]">
      <div className="space-y-1">
        <NavLink to="/" end className={navLinkClass}>
          <Home size={20} />
          <span>Home</span>
        </NavLink>
        <NavLink to="/playlists" className={navLinkClass}>
          <ListVideo size={20} />
          <span>Playlists</span>
        </NavLink>
      </div>

      <div className="my-3 border-t border-[#272727]" />

      <div className="space-y-1">
        <h4 className="px-3 py-1 text-xs font-semibold text-zinc-400 uppercase tracking-wider">You</h4>
        {user ? (
          <NavLink to={`/channel/${user.id}`} className={navLinkClass}>
            <User size={20} />
            <span>Your Channel</span>
          </NavLink>
        ) : null}
        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-5 px-3 py-2.5 rounded-xl text-sm text-zinc-300 hover:bg-[#222222] transition"
        >
          <FileText size={20} className="text-emerald-400" />
          <span>API Swagger Docs</span>
        </a>
      </div>

      {user && (user.role === 'moderator' || user.role === 'admin') && (
        <>
          <div className="my-3 border-t border-[#272727]" />
          <div className="space-y-1">
            <h4 className="px-3 py-1 text-xs font-semibold text-purple-400 uppercase tracking-wider">Moderation</h4>
            <NavLink to="/moderation" className={navLinkClass}>
              <ShieldAlert size={20} className="text-purple-400" />
              <span>Review Reports</span>
            </NavLink>
          </div>
        </>
      )}

      <div className="mt-auto pt-6 text-[11px] text-zinc-500 px-3">
        <p>© 2026 YouTube Clone</p>
        <p className="mt-1">FastAPI • PostgreSQL • MinIO</p>
      </div>
    </aside>
  );
};
