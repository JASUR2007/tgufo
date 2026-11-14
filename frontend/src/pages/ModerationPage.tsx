import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ShieldCheck, Eye, EyeOff, CheckCircle2, History, AlertTriangle } from 'lucide-react';
import { Report, ModerationAction } from '../types';
import { apiService } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const ModerationPage: React.FC = () => {
  const { user, switchDemoAccount } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [actions, setActions] = useState<ModerationAction[]>([]);
  const [activeTab, setActiveTab] = useState<'reports' | 'audit'>('reports');
  const [isLoading, setIsLoading] = useState(true);

  const [hideReason, setHideReason] = useState('');
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);

  const isPrivileged = user && (user.role === 'moderator' || user.role === 'admin');

  const loadData = async () => {
    if (!isPrivileged) return;
    setIsLoading(true);
    try {
      const rep = await apiService.getReports();
      setReports(rep);
      const act = await apiService.getModerationActions();
      setActions(act);
    } catch (e) {
      console.error("Moderation load failed:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user]);

  const handleHideVideo = async (videoId: string) => {
    const reason = prompt("Enter moderation reason for hiding this video:", "Violates community guidelines.");
    if (!reason) return;

    try {
      await apiService.hideVideo(videoId, reason);
      loadData();
    } catch (e: any) {
      alert(e.response?.data?.detail || "Action failed");
    }
  };

  const handleRestoreVideo = async (videoId: string) => {
    const reason = prompt("Enter moderation reason for restoring this video:", "Appeal accepted / false positive.");
    if (!reason) return;

    try {
      await apiService.restoreVideo(videoId, reason);
      loadData();
    } catch (e: any) {
      alert(e.response?.data?.detail || "Action failed");
    }
  };

  if (!isPrivileged) {
    return (
      <div className="flex-1 p-10 flex flex-col items-center justify-center text-center max-w-lg mx-auto">
        <div className="w-16 h-16 rounded-full bg-purple-950/80 border border-purple-500/50 flex items-center justify-center text-purple-400 mb-4">
          <ShieldAlert size={36} />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Moderation Access Required</h2>
        <p className="text-sm text-zinc-400 mb-6">
          You need Moderator or Administrator privileges to review user complaints and manage content visibility.
        </p>
        <div className="flex gap-3">
          <button
            onClick={() => switchDemoAccount('moderator')}
            className="px-5 py-2.5 rounded-full bg-purple-600 hover:bg-purple-700 text-white font-semibold text-xs transition"
          >
            Switch to Moderator Account
          </button>
          <button
            onClick={() => switchDemoAccount('admin')}
            className="px-5 py-2.5 rounded-full bg-red-600 hover:bg-red-700 text-white font-semibold text-xs transition"
          >
            Switch to Admin Account
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-[#272727]">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-purple-950/60 border border-purple-600 text-purple-400">
            <ShieldCheck size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Trust & Safety Moderation Desk</h1>
            <p className="text-xs text-zinc-400">Review reported videos, enforce guidelines, and inspect audit logs.</p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex gap-2 bg-[#212121] p-1 rounded-xl border border-[#272727]">
          <button
            onClick={() => setActiveTab('reports')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'reports' ? 'bg-purple-600 text-white' : 'text-zinc-400 hover:text-white'
            }`}
          >
            Pending Reports ({reports.filter(r => r.status === 'pending').length})
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
              activeTab === 'audit' ? 'bg-purple-600 text-white' : 'text-zinc-400 hover:text-white'
            }`}
          >
            <History size={14} />
            <span>Audit Trail ({actions.length})</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="mt-6">
        {isLoading ? (
          <div className="text-center py-16 text-zinc-400">Loading moderation records...</div>
        ) : activeTab === 'reports' ? (
          reports.length === 0 ? (
            <div className="text-center py-20 text-zinc-500">
              <CheckCircle2 size={48} className="mx-auto mb-3 text-emerald-500" />
              <p className="text-lg font-semibold text-zinc-300">All caught up!</p>
              <p className="text-xs mt-1">There are no pending user reports requiring review.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {reports.map((report) => (
                <div
                  key={report.id}
                  className="p-5 bg-[#212121] border border-[#272727] rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6"
                >
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded text-[11px] font-semibold bg-red-950/80 border border-red-700/60 text-red-300">
                        {report.reason}
                      </span>
                      <span className="text-xs text-zinc-400">
                        Reported by: <strong className="text-white">@{report.reporter?.username || report.reporter_id}</strong>
                      </span>
                      <span className="text-xs text-zinc-500">• {new Date(report.created_at).toLocaleString()}</span>
                    </div>

                    <h3 className="font-bold text-base text-white">
                      Target: {report.video?.title || `Video ID: ${report.video_id}`}
                    </h3>

                    {report.details && (
                      <p className="text-xs text-zinc-300 bg-zinc-900/60 p-2.5 rounded-lg border border-zinc-800">
                        "{report.details}"
                      </p>
                    )}

                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-zinc-400">Video Status:</span>
                      <span className={`font-semibold ${
                        report.video?.moderation_status === 'hidden' ? 'text-red-400' : 'text-emerald-400'
                      }`}>
                        {report.video?.moderation_status?.toUpperCase() || 'UNKNOWN'}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <Link
                      to={`/watch/${report.video_id}`}
                      target="_blank"
                      className="px-3.5 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-zinc-200 flex items-center gap-1.5 transition"
                    >
                      <Eye size={14} />
                      <span>Preview</span>
                    </Link>

                    {report.video?.moderation_status === 'hidden' ? (
                      <button
                        onClick={() => handleRestoreVideo(report.video_id)}
                        className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-xs font-semibold text-white flex items-center gap-1.5 transition"
                      >
                        <Eye size={14} />
                        <span>Restore Video</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => handleHideVideo(report.video_id)}
                        className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-xs font-semibold text-white flex items-center gap-1.5 transition"
                      >
                        <EyeOff size={14} />
                        <span>Hide Video</span>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )
        ) : (
          /* Audit Log */
          actions.length === 0 ? (
            <div className="text-center py-20 text-zinc-500">No moderation actions recorded yet.</div>
          ) : (
            <div className="bg-[#212121] border border-[#272727] rounded-2xl overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#181818] border-b border-[#272727] text-zinc-400 uppercase font-semibold">
                  <tr>
                    <th className="p-3.5">Timestamp</th>
                    <th className="p-3.5">Moderator</th>
                    <th className="p-3.5">Action</th>
                    <th className="p-3.5">Video ID</th>
                    <th className="p-3.5">Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#272727] text-zinc-300">
                  {actions.map((act) => (
                    <tr key={act.id} className="hover:bg-[#282828] transition">
                      <td className="p-3.5 whitespace-nowrap text-zinc-400">
                        {new Date(act.created_at).toLocaleString()}
                      </td>
                      <td className="p-3.5 font-medium text-white">
                        @{act.moderator?.username || act.moderator_id}
                      </td>
                      <td className="p-3.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          act.action === 'hide' ? 'bg-red-950 text-red-300 border border-red-800' : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                        }`}>
                          {act.action}
                        </span>
                      </td>
                      <td className="p-3.5 font-mono text-zinc-400">{act.video_id.slice(0, 8)}...</td>
                      <td className="p-3.5">{act.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}
      </div>
    </div>
  );
};
