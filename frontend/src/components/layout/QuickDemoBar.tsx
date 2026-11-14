import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { ShieldAlert, ShieldCheck, Video, UserCheck, LogOut } from 'lucide-react';

export const QuickDemoBar: React.FC = () => {
  const { user, switchDemoAccount, logout, openAuthModal } = useAuth();

  return (
    <div className="bg-[#18181b] border-b border-[#27272a] px-4 py-1.5 flex flex-wrap items-center justify-between text-xs text-zinc-300">
      <div className="flex items-center gap-2">
        <span className="font-semibold text-zinc-400">⚡ Quick Demo Role:</span>
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => switchDemoAccount('admin')}
            className={`px-2.5 py-1 rounded flex items-center gap-1 transition ${
              user?.role === 'admin'
                ? 'bg-red-600 text-white font-medium ring-1 ring-red-400'
                : 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300'
            }`}
          >
            <ShieldAlert size={13} />
            <span>Admin</span>
          </button>

          <button
            onClick={() => switchDemoAccount('moderator')}
            className={`px-2.5 py-1 rounded flex items-center gap-1 transition ${
              user?.role === 'moderator'
                ? 'bg-purple-600 text-white font-medium ring-1 ring-purple-400'
                : 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300'
            }`}
          >
            <ShieldCheck size={13} />
            <span>Moderator</span>
          </button>

          <button
            onClick={() => switchDemoAccount('creator')}
            className={`px-2.5 py-1 rounded flex items-center gap-1 transition ${
              user?.username === 'tech_guru'
                ? 'bg-blue-600 text-white font-medium ring-1 ring-blue-400'
                : 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300'
            }`}
          >
            <Video size={13} />
            <span>Creator (@tech_guru)</span>
          </button>

          <button
            onClick={() => switchDemoAccount('viewer')}
            className={`px-2.5 py-1 rounded flex items-center gap-1 transition ${
              user?.username === 'demo_viewer'
                ? 'bg-emerald-600 text-white font-medium ring-1 ring-emerald-400'
                : 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300'
            }`}
          >
            <UserCheck size={13} />
            <span>Viewer (@demo_viewer)</span>
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {user ? (
          <div className="flex items-center gap-2">
            <span className="text-zinc-400">
              Active: <strong className="text-white">{user.username}</strong> ({user.role})
            </span>
            <button
              onClick={logout}
              className="hover:text-red-400 p-1 flex items-center gap-1 transition"
              title="Logout"
            >
              <LogOut size={13} />
              <span>Exit</span>
            </button>
          </div>
        ) : (
          <button
            onClick={openAuthModal}
            className="text-blue-400 hover:underline"
          >
            Not logged in (Click to Login)
          </button>
        )}
      </div>
    </div>
  );
};
