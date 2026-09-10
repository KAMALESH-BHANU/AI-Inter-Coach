import React, { useState, useEffect, useRef } from 'react';
import { interviewAPI } from '../services/api';
import { X, ShieldAlert, Video, AlertCircle } from 'lucide-react';

const VideoReplayModal = ({ sessionId, isOpen = true, onClose, onConsumed }) => {
  const [videoSrc, setVideoSrc] = useState(null);
  const [hasError, setHasError] = useState(false);
  const blobUrlRef = useRef(null);

  useEffect(() => {
    // 1. Prioritize client-side recorded blob for zero latency replay
    if (window.__INTERVIEW_VIDEO_BLOB__) {
      const url = URL.createObjectURL(window.__INTERVIEW_VIDEO_BLOB__);
      blobUrlRef.current = url;
      setVideoSrc(url);
    } else if (sessionId) {
      // 2. Fallback to backend streaming endpoint
      setVideoSrc(interviewAPI.getVideoUrl(sessionId));
    }

    return () => {
      // Clean up object URL on unmount
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
        blobUrlRef.current = null;
      }
    };
  }, [sessionId]);

  if (!isOpen) return null;

  const handleClose = async () => {
    // Clean up local recording blob
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current);
      blobUrlRef.current = null;
    }
    window.__INTERVIEW_VIDEO_BLOB__ = null;

    // Permanently purge on backend
    if (sessionId) {
      try {
        await interviewAPI.deleteVideo(sessionId);
      } catch (e) {
        console.warn('Backend video deletion error:', e);
      }
    }

    if (onConsumed) {
      onConsumed();
    }
    if (onClose) {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-3xl max-w-3xl w-full p-6 shadow-2xl space-y-4 relative">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-blue-600/20 text-blue-400 rounded-xl border border-blue-500/30">
              <Video className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">1-Time Temporary Interview Replay</h3>
              <p className="text-xs text-slate-400">Strict Privacy Policy: This recording is permanently deleted upon closing or playback finish.</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Video Player */}
        <div className="aspect-video bg-black rounded-2xl overflow-hidden flex items-center justify-center relative border border-slate-800 shadow-inner">
          {videoSrc && !hasError ? (
            <video
              controls
              autoPlay
              playsInline
              onEnded={handleClose}
              onError={() => setHasError(true)}
              className="w-full h-full object-contain"
            >
              <source src={videoSrc} type="video/webm" />
              Your browser does not support the video tag.
            </video>
          ) : (
            <div className="text-center p-6 space-y-2 text-slate-400">
              <AlertCircle className="w-8 h-8 text-amber-400 mx-auto" />
              <p className="text-sm font-medium">Temporary video recording has already been purged or is unavailable.</p>
            </div>
          )}
        </div>

        {/* Security Warning Notice */}
        <div className="flex items-center space-x-2 bg-amber-500/10 border border-amber-500/30 p-3.5 rounded-xl text-amber-300 text-xs">
          <ShieldAlert className="w-4 h-4 flex-shrink-0" />
          <span><b>Privacy Protection:</b> Once you close this player or video finishes playback, the temporary recording is permanently wiped from memory and the server.</span>
        </div>
      </div>
    </div>
  );
};

export default VideoReplayModal;
