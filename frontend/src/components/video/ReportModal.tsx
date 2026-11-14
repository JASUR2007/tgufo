import React, { useState } from 'react';
import { X, Flag, AlertTriangle } from 'lucide-react';
import { apiService } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

interface ReportModalProps {
  videoId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const ReportModal: React.FC<ReportModalProps> = ({ videoId, isOpen, onClose, onSuccess }) => {
  const { user, openAuthModal } = useAuth();
  const [reason, setReason] = useState('Misleading or Clickbait');
  const [details, setDetails] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  if (!isOpen) return null;

  const reasons = [
    'Misleading or Clickbait',
    'Copyright Infringement',
    'Spam or Scams',
    'Harassment or Bullying',
    'Violent or Dangerous Content',
    'Other Guideline Violation'
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      onClose();
      openAuthModal();
      return;
    }

    setIsSubmitting(true);
    try {
      await apiService.reportVideo({
        video_id: videoId,
        reason,
        details
      });
      setIsSuccess(true);
      setTimeout(() => {
        setIsSuccess(false);
        onClose();
        if (onSuccess) onSuccess();
      }, 1500);
    } catch (e) {
      console.error("Report failed:", e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-md bg-[#212121] border border-[#3f3f3f] rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#3f3f3f]">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Flag size={18} className="text-red-500" />
            Report Video
          </h2>
          <button onClick={onClose} className="text-zinc-400 hover:text-white">
            <X size={18} />
          </button>
        </div>

        {isSuccess ? (
          <div className="p-8 flex flex-col items-center justify-center text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-950/80 border border-emerald-500 flex items-center justify-center text-emerald-400">
              ✓
            </div>
            <h3 className="text-base font-bold text-white">Report Submitted</h3>
            <p className="text-xs text-zinc-400">Thank you. Our moderation team will review this video.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <p className="text-xs text-zinc-400">
              Help keep the community safe. Select the primary reason for your report:
            </p>

            <div className="space-y-2">
              {reasons.map((r) => (
                <label key={r} className="flex items-center gap-3 p-2 rounded-lg hover:bg-zinc-800 cursor-pointer text-sm text-zinc-200">
                  <input
                    type="radio"
                    name="reason"
                    checked={reason === r}
                    onChange={() => setReason(r)}
                    className="accent-red-600"
                  />
                  <span>{r}</span>
                </label>
              ))}
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-400 mb-1">
                Additional Details (Optional)
              </label>
              <textarea
                rows={2}
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                placeholder="Provide timestamps or specific information..."
                className="w-full bg-[#121212] border border-[#3f3f3f] rounded-lg p-2.5 text-xs text-white outline-none"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-[#3f3f3f]">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-lg hover:bg-zinc-800 text-xs text-zinc-300 font-medium"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-5 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-semibold transition"
              >
                {isSubmitting ? 'Submitting...' : 'Submit Report'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
