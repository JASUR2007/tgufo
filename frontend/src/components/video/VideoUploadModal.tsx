import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Upload, Film, Image as ImageIcon, Lock, Globe, EyeOff, UserPlus, Check } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiService } from '../../services/api';
import { VideoVisibility } from '../../types';

export const VideoUploadModal: React.FC = () => {
  const { isUploadModalOpen, closeUploadModal } = useAuth();
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [visibility, setVisibility] = useState<VideoVisibility>('public');
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [thumbnailFile, setThumbnailFile] = useState<File | null>(null);
  const [grantedUser, setGrantedUser] = useState('');
  const [grantedUsersList, setGrantedUsersList] = useState<string[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isUploadModalOpen) return null;

  const handleAddGrant = (e: React.FormEvent) => {
    e.preventDefault();
    if (grantedUser.trim() && !grantedUsersList.includes(grantedUser.trim())) {
      setGrantedUsersList([...grantedUsersList, grantedUser.trim()]);
      setGrantedUser('');
    }
  };

  const handleRemoveGrant = (username: string) => {
    setGrantedUsersList(grantedUsersList.filter(u => u !== username));
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoFile) {
      setErrorMsg('Please select a video file.');
      return;
    }
    if (!title.trim()) {
      setErrorMsg('Please enter a video title.');
      return;
    }

    setIsUploading(true);
    setErrorMsg('');
    setUploadProgress(15);

    try {
      const formData = new FormData();
      formData.append('title', title.trim());
      formData.append('description', description.trim());
      formData.append('visibility', visibility);
      formData.append('video_file', videoFile);
      if (thumbnailFile) {
        formData.append('thumbnail_file', thumbnailFile);
      }

      setUploadProgress(60);
      const video = await apiService.uploadVideo(formData);
      setUploadProgress(85);

      // If private and granted users specified, add grants
      if (visibility === 'private' && grantedUsersList.length > 0) {
        for (const u of grantedUsersList) {
          try {
            await apiService.addGrant(video.id, u);
          } catch (err) {
            console.error(`Failed to grant access to ${u}:`, err);
          }
        }
      }

      setUploadProgress(100);
      closeUploadModal();
      navigate(`/watch/${video.id}`);
    } catch (err: any) {
      console.error("Upload error:", err);
      setErrorMsg(err.response?.data?.detail || 'Failed to upload video.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-2xl bg-[#212121] border border-[#3f3f3f] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#3f3f3f]">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Upload size={20} className="text-red-500" />
            Upload Video
          </h2>
          <button
            onClick={closeUploadModal}
            className="p-1 text-zinc-400 hover:text-white rounded-full hover:bg-zinc-800 transition"
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleUpload} className="p-6 overflow-y-auto space-y-5">
          {errorMsg && (
            <div className="p-3 bg-red-950/80 border border-red-500 rounded-lg text-sm text-red-200">
              {errorMsg}
            </div>
          )}

          {/* Video File Picker */}
          <div>
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
              Video File (MP4, WebM, MKV) *
            </label>
            <label className="flex flex-col items-center justify-center border-2 border-dashed border-[#444] hover:border-red-500 rounded-xl p-6 cursor-pointer bg-[#181818] transition">
              <Film size={36} className="text-zinc-400 mb-2" />
              <span className="text-sm font-medium text-white">
                {videoFile ? videoFile.name : 'Select video file to upload'}
              </span>
              <span className="text-xs text-zinc-500 mt-1">Up to 500MB supported</span>
              <input
                type="file"
                accept="video/*"
                className="hidden"
                onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
              />
            </label>
          </div>

          {/* Title */}
          <div>
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1">
              Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Give your video a catchy title"
              required
              className="w-full bg-[#121212] border border-[#3f3f3f] focus:border-red-500 rounded-lg px-4 py-2 text-sm text-white outline-none"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1">
              Description
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Tell viewers what your video is about"
              className="w-full bg-[#121212] border border-[#3f3f3f] focus:border-red-500 rounded-lg p-3 text-sm text-white outline-none"
            />
          </div>

          {/* Thumbnail (Optional) */}
          <div>
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
              Thumbnail (Optional - auto-generated if left blank)
            </label>
            <label className="flex items-center gap-3 border border-[#3f3f3f] rounded-lg p-3 cursor-pointer bg-[#181818] hover:border-zinc-500 transition">
              <ImageIcon size={22} className="text-zinc-400" />
              <span className="text-sm text-zinc-300 truncate">
                {thumbnailFile ? thumbnailFile.name : 'Upload custom thumbnail image'}
              </span>
              <input
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => setThumbnailFile(e.target.files?.[0] || null)}
              />
            </label>
          </div>

          {/* Visibility Selector */}
          <div>
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
              Visibility
            </label>
            <div className="grid grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setVisibility('public')}
                className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border text-sm transition ${
                  visibility === 'public'
                    ? 'border-blue-500 bg-blue-950/30 text-white'
                    : 'border-[#3f3f3f] bg-[#181818] text-zinc-400 hover:border-zinc-500'
                }`}
              >
                <Globe size={18} />
                <span className="font-semibold">Public</span>
                <span className="text-[11px] text-zinc-500 text-center">Everyone can watch</span>
              </button>

              <button
                type="button"
                onClick={() => setVisibility('unlisted')}
                className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border text-sm transition ${
                  visibility === 'unlisted'
                    ? 'border-blue-500 bg-blue-950/30 text-white'
                    : 'border-[#3f3f3f] bg-[#181818] text-zinc-400 hover:border-zinc-500'
                }`}
              >
                <EyeOff size={18} />
                <span className="font-semibold">Unlisted</span>
                <span className="text-[11px] text-zinc-500 text-center">Anyone with link</span>
              </button>

              <button
                type="button"
                onClick={() => setVisibility('private')}
                className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border text-sm transition ${
                  visibility === 'private'
                    ? 'border-red-500 bg-red-950/30 text-white'
                    : 'border-[#3f3f3f] bg-[#181818] text-zinc-400 hover:border-zinc-500'
                }`}
              >
                <Lock size={18} />
                <span className="font-semibold">Private</span>
                <span className="text-[11px] text-zinc-500 text-center">Only granted users</span>
              </button>
            </div>
          </div>

          {/* Private Video Access Grants */}
          {visibility === 'private' && (
            <div className="p-4 bg-[#181818] border border-red-900/40 rounded-xl space-y-3">
              <h4 className="text-xs font-bold text-red-400 uppercase tracking-wider flex items-center gap-1.5">
                <UserPlus size={14} />
                Grant Access to Users
              </h4>
              <p className="text-xs text-zinc-400">
                Enter username or email of users who should have permission to watch this private video:
              </p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={grantedUser}
                  onChange={(e) => setGrantedUser(e.target.value)}
                  placeholder="e.g. demo_viewer"
                  className="flex-1 bg-[#121212] border border-[#3f3f3f] rounded-lg px-3 py-1.5 text-sm text-white outline-none"
                />
                <button
                  type="button"
                  onClick={handleAddGrant}
                  className="px-4 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium transition"
                >
                  Add
                </button>
              </div>

              {grantedUsersList.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {grantedUsersList.map((u) => (
                    <span
                      key={u}
                      className="px-2.5 py-1 rounded-full bg-red-950/60 border border-red-500/50 text-red-200 text-xs flex items-center gap-1.5"
                    >
                      <span>@{u}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveGrant(u)}
                        className="hover:text-white"
                      >
                        <X size={12} />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Upload Progress Bar */}
          {isUploading && (
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-zinc-400">
                <span>Uploading and processing...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full h-2 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-600 transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Footer actions */}
          <div className="flex justify-end gap-3 pt-3 border-t border-[#3f3f3f]">
            <button
              type="button"
              onClick={closeUploadModal}
              disabled={isUploading}
              className="px-4 py-2 rounded-lg hover:bg-zinc-800 text-sm text-zinc-300 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isUploading}
              className="px-6 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-semibold disabled:opacity-50 transition flex items-center gap-2"
            >
              {isUploading ? 'Publishing...' : 'Publish'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
