import React, { useState } from 'react';
import { X, LogIn, UserPlus } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const AuthModal: React.FC = () => {
  const { isAuthModalOpen, closeAuthModal, login, register, switchDemoAccount } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setIsLoading(true);

    try {
      if (isRegister) {
        await register({
          email,
          username,
          password,
          full_name: fullName || username,
        });
      } else {
        await login(email, password);
      }
    } catch (err: any) {
      console.error("Auth error:", err);
      setErrorMsg(err.response?.data?.detail || 'Authentication failed. Check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-md bg-[#212121] border border-[#3f3f3f] rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#3f3f3f]">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            {isRegister ? <UserPlus size={18} className="text-red-500" /> : <LogIn size={18} className="text-red-500" />}
            {isRegister ? 'Create your Account' : 'Sign in to YouTube'}
          </h2>
          <button onClick={closeAuthModal} className="text-zinc-400 hover:text-white">
            <X size={18} />
          </button>
        </div>

        {/* 1-Click Demo Logins Section */}
        <div className="p-6 pb-2">
          <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-xl space-y-2">
            <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">
              ⚡ 1-Click Examiner Demo Logins:
            </span>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => switchDemoAccount('admin')}
                className="p-2 bg-red-950/60 hover:bg-red-900 border border-red-700/60 text-red-200 rounded-lg text-left font-medium transition"
              >
                <div className="font-bold">Admin</div>
                <div className="text-[10px] text-red-300">admin@youtube.local</div>
              </button>
              <button
                type="button"
                onClick={() => switchDemoAccount('moderator')}
                className="p-2 bg-purple-950/60 hover:bg-purple-900 border border-purple-700/60 text-purple-200 rounded-lg text-left font-medium transition"
              >
                <div className="font-bold">Moderator</div>
                <div className="text-[10px] text-purple-300">moderator@youtube.local</div>
              </button>
              <button
                type="button"
                onClick={() => switchDemoAccount('creator')}
                className="p-2 bg-blue-950/60 hover:bg-blue-900 border border-blue-700/60 text-blue-200 rounded-lg text-left font-medium transition"
              >
                <div className="font-bold">Creator</div>
                <div className="text-[10px] text-blue-300">creator@youtube.local</div>
              </button>
              <button
                type="button"
                onClick={() => switchDemoAccount('viewer')}
                className="p-2 bg-emerald-950/60 hover:bg-emerald-900 border border-emerald-700/60 text-emerald-200 rounded-lg text-left font-medium transition"
              >
                <div className="font-bold">Viewer</div>
                <div className="text-[10px] text-emerald-300">viewer@youtube.local</div>
              </button>
            </div>
          </div>
        </div>

        <div className="px-6 flex items-center gap-3">
          <div className="flex-1 border-t border-zinc-800" />
          <span className="text-[11px] text-zinc-500 uppercase">or use form</span>
          <div className="flex-1 border-t border-zinc-800" />
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 pt-3 space-y-4">
          {errorMsg && (
            <div className="p-3 bg-red-950/80 border border-red-500 rounded-lg text-xs text-red-200">
              {errorMsg}
            </div>
          )}

          {isRegister && (
            <>
              <div>
                <label className="block text-xs font-semibold text-zinc-400 mb-1">Username *</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="cool_creator"
                  required
                  className="w-full bg-[#121212] border border-[#3f3f3f] focus:border-red-500 rounded-lg px-3 py-2 text-sm text-white outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-400 mb-1">Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="John Doe"
                  className="w-full bg-[#121212] border border-[#3f3f3f] focus:border-red-500 rounded-lg px-3 py-2 text-sm text-white outline-none"
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-semibold text-zinc-400 mb-1">Email *</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              required
              className="w-full bg-[#121212] border border-[#3f3f3f] focus:border-red-500 rounded-lg px-3 py-2 text-sm text-white outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-400 mb-1">Password *</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full bg-[#121212] border border-[#3f3f3f] focus:border-red-500 rounded-lg px-3 py-2 text-sm text-white outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold text-sm transition disabled:opacity-50"
          >
            {isLoading ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
          </button>

          <div className="text-center pt-2">
            <button
              type="button"
              onClick={() => {
                setIsRegister(!isRegister);
                setErrorMsg('');
              }}
              className="text-xs text-blue-400 hover:underline"
            >
              {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Register"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
