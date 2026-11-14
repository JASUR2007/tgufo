import React, { useState, useEffect } from 'react';
import { Comment } from '../../types';
import { apiService } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Trash2, MessageSquare } from 'lucide-react';

interface VideoCommentsProps {
  videoId: string;
}

export const VideoComments: React.FC<VideoCommentsProps> = ({ videoId }) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { user, openAuthModal } = useAuth();

  const loadComments = async () => {
    try {
      const data = await apiService.getComments(videoId);
      setComments(data);
    } catch (e) {
      console.error("Failed to load comments:", e);
    }
  };

  useEffect(() => {
    loadComments();
  }, [videoId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    if (!user) {
      openAuthModal();
      return;
    }

    setIsSubmitting(true);
    try {
      const created = await apiService.postComment(videoId, newComment.trim());
      setComments([created, ...comments]);
      setNewComment('');
    } catch (e) {
      console.error("Failed to post comment:", e);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (commentId: string) => {
    try {
      await apiService.deleteComment(commentId);
      setComments(comments.filter(c => c.id !== commentId));
    } catch (e) {
      console.error("Failed to delete comment:", e);
    }
  };

  return (
    <div className="mt-6 flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <h3 className="text-xl font-bold text-white">{comments.length} Comments</h3>
      </div>

      {/* Comment Input */}
      <div className="flex gap-4">
        {user ? (
          <img
            src={user.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${user.username}`}
            alt={user.username}
            className="w-10 h-10 rounded-full object-cover shrink-0"
          />
        ) : (
          <div className="w-10 h-10 rounded-full bg-zinc-700 flex items-center justify-center shrink-0 text-zinc-400">
            <MessageSquare size={20} />
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex-1 flex flex-col gap-2">
          <input
            type="text"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder={user ? "Add a comment..." : "Sign in to add a comment"}
            className="w-full bg-transparent border-b border-[#3f3f3f] focus:border-white outline-none py-1.5 text-sm text-white placeholder-zinc-500 transition"
          />
          {newComment && (
            <div className="flex justify-end gap-2 mt-1">
              <button
                type="button"
                onClick={() => setNewComment('')}
                className="px-3 py-1.5 rounded-full hover:bg-zinc-800 text-sm text-zinc-300"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-1.5 rounded-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold disabled:opacity-50 transition"
              >
                Comment
              </button>
            </div>
          )}
        </form>
      </div>

      {/* Comments List */}
      <div className="flex flex-col gap-5 mt-2">
        {comments.map((comment) => (
          <div key={comment.id} className="flex gap-4 group">
            <img
              src={comment.user?.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${comment.user?.username || 'user'}`}
              alt={comment.user?.username}
              className="w-10 h-10 rounded-full object-cover shrink-0"
            />
            <div className="flex-1 flex flex-col">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-white">
                  @{comment.user?.username || 'user'}
                </span>
                <span className="text-xs text-zinc-400">
                  {new Date(comment.created_at).toLocaleDateString()}
                </span>
              </div>

              <p className="text-sm text-zinc-200 mt-1 whitespace-pre-line">{comment.content}</p>
            </div>

            {comment.can_delete && (
              <button
                onClick={() => handleDelete(comment.id)}
                className="opacity-0 group-hover:opacity-100 p-2 text-zinc-500 hover:text-red-400 transition"
                title="Delete comment"
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
