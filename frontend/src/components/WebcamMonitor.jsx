import React, { useRef, useEffect, useState } from 'react';
import { CameraOff, Eye, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';
import { interviewAPI } from '../services/api';

const WebcamMonitor = ({
  sessionId,
  wsService,
  eyeContactPct = -1.0,
  expression = "Face Missing",
  faceStatus = "FACE_MISSING",
  warning = "WARNING: Face Missing",
  isInterviewActive = true,
  fps = 5
}) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const wsServiceRef = useRef(wsService);
  const mediaRecorderRef = useRef(null);
  const recordedChunksRef = useRef([]);

  const [streamActive, setStreamActive] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isInitializing, setIsInitializing] = useState(true);

  // Keep wsService ref updated without triggering camera restarts
  useEffect(() => {
    wsServiceRef.current = wsService;
  }, [wsService]);

  // Stop camera MediaStream tracks explicitly & finalize video recording
  const stopCameraStream = () => {
    // 1. Stop MediaRecorder if running
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {
        console.warn('Error stopping MediaRecorder:', e);
      }
    }

    // 2. Stop camera tracks
    if (streamRef.current) {
      const tracks = streamRef.current.getTracks();
      tracks.forEach((track) => {
        try { track.stop(); } catch (e) {}
      });
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setStreamActive(false);
    setIsInitializing(false);
  };

  // 1. Camera Stream Lifecycle & Video Recording
  useEffect(() => {
    let isMounted = true;

    if (!isInterviewActive) {
      stopCameraStream();
      return;
    }

    const startWebcam = async () => {
      setIsInitializing(true);
      setErrorMsg(null);

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { 
            width: { ideal: 640 }, 
            height: { ideal: 480 }, 
            frameRate: { ideal: 15, max: 20 } 
          },
          audio: true
        });

        if (!isMounted) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }

        streamRef.current = stream;

        // Initialize MediaRecorder for 1-Time Replay
        try {
          recordedChunksRef.current = [];
          const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp8,opus')
            ? 'video/webm;codecs=vp8,opus'
            : (MediaRecorder.isTypeSupported('video/webm') ? 'video/webm' : '');
          
          const options = mimeType ? { mimeType } : undefined;
          const recorder = new MediaRecorder(stream, options);
          
          recorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
              recordedChunksRef.current.push(event.data);
            }
          };

          recorder.onstop = async () => {
            if (recordedChunksRef.current.length > 0) {
              const videoBlob = new Blob(recordedChunksRef.current, { type: 'video/webm' });
              // Save in memory for instant local replay
              window.__INTERVIEW_VIDEO_BLOB__ = videoBlob;

              // Upload to backend
              if (sessionId) {
                try {
                  const formData = new FormData();
                  formData.append('file', videoBlob, `${sessionId}.webm`);
                  await interviewAPI.uploadVideo(sessionId, formData);
                } catch (uploadErr) {
                  console.warn('Backend video upload failed, local blob available:', uploadErr);
                }
              }
            }
          };

          recorder.start(1000); // 1-second timeslices
          mediaRecorderRef.current = recorder;
        } catch (recErr) {
          console.warn('MediaRecorder not available or failed to initialize:', recErr);
        }

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.onloadedmetadata = async () => {
            try {
              await videoRef.current.play();
            } catch (playErr) {
              console.warn('Video play prevented:', playErr);
            }
            if (isMounted) {
              setStreamActive(true);
              setIsInitializing(false);
              setErrorMsg(null);
            }
          };
        } else {
          setStreamActive(true);
          setIsInitializing(false);
        }

      } catch (err) {
        console.error('Camera permission denied or camera missing:', err);
        if (isMounted) {
          setErrorMsg('Webcam access was denied or no camera device found. Please check browser permissions.');
          setStreamActive(false);
          setIsInitializing(false);
        }
      }
    };

    startWebcam();

    return () => {
      isMounted = false;
      stopCameraStream();
    };
  }, [isInterviewActive, sessionId]);

  // 2. Sampling Frame Interval: Sends frames at controlled FPS without restarting camera
  useEffect(() => {
    if (!isInterviewActive) return;

    const sampleIntervalMs = Math.round(1000 / fps);
    const intervalId = setInterval(() => {
      if (canvasRef.current && videoRef.current && wsServiceRef.current && isInterviewActive && streamActive) {
        const canvas = canvasRef.current;
        const video = videoRef.current;
        if (video.readyState >= 2 && video.videoWidth > 0) {
          const ctx = canvas.getContext('2d');
          canvas.width = 480;
          canvas.height = 360;
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          const b64Image = canvas.toDataURL('image/jpeg', 0.65);
          wsServiceRef.current.sendFrame(b64Image);
        }
      }
    }, sampleIntervalMs);

    return () => {
      clearInterval(intervalId);
    };
  }, [fps, isInterviewActive, streamActive]);

  return (
    <div className="relative rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 aspect-video flex items-center justify-center shadow-2xl">
      <canvas ref={canvasRef} className="hidden" />

      {/* Video is ALWAYS rendered so ref is never null during getUserMedia */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className={`w-full h-full object-cover transform -scale-x-100 ${streamActive ? 'block' : 'hidden'}`}
      />

      {/* Loading State */}
      {isInitializing && !errorMsg && (
        <div className="text-center p-6 space-y-3 z-10">
          <RefreshCw className="w-10 h-10 text-blue-500 animate-spin mx-auto" />
          <p className="text-slate-400 text-sm font-medium">Connecting camera feed...</p>
        </div>
      )}

      {/* Error or Stopped Overlay */}
      {(!streamActive && !isInitializing) && (
        <div className="text-center p-6 space-y-3 z-10">
          <CameraOff className="w-12 h-12 text-slate-500 mx-auto" />
          <p className="text-slate-400 text-sm font-medium">
            {errorMsg || "Camera Stopped / Interview Complete"}
          </p>
        </div>
      )}

      {/* Active Camera Overlays */}
      {streamActive && (
        <>
          {/* 3-State Face Status Banner */}
          {faceStatus === "MULTIPLE_FACES" && (
            <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-amber-500 text-slate-950 font-extrabold text-xs px-4 py-1.5 rounded-full shadow-lg flex items-center space-x-1.5 animate-pulse z-20">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>WARNING: Multiple Faces Detected</span>
            </div>
          )}

          {faceStatus === "FACE_MISSING" && (
            <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-rose-600 text-white font-extrabold text-xs px-4 py-1.5 rounded-full shadow-lg flex items-center space-x-1.5 animate-pulse z-20">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>WARNING: Face Missing</span>
            </div>
          )}

          {faceStatus === "SINGLE_FACE" && (
            <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-emerald-600 text-white font-semibold text-xs px-3.5 py-1 rounded-full shadow-md flex items-center space-x-1.5 z-20">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Single Face Detected</span>
            </div>
          )}

          {/* Dynamic Eye Contact Overlay Badge */}
          <div className="absolute bottom-4 left-4 flex items-center space-x-2 bg-slate-900/80 backdrop-blur-md border border-slate-700/80 px-3 py-1.5 rounded-full text-xs font-semibold text-slate-200 shadow-lg">
            <Eye className={`w-3.5 h-3.5 ${eyeContactPct >= 75 ? 'text-emerald-400' : 'text-amber-400'}`} />
            <span>
              Eye Contact:{' '}
              <strong className="text-blue-400">
                {eyeContactPct < 0 ? 'Calculating...' : `${eyeContactPct}%`}
              </strong>
            </span>
          </div>

          {/* Expression Badge */}
          <div className="absolute bottom-4 right-4 bg-slate-900/80 backdrop-blur-md border border-slate-700/80 px-3 py-1.5 rounded-full text-xs font-semibold text-slate-300">
            <span>Expression: <strong>{expression}</strong></span>
          </div>
        </>
      )}
    </div>
  );
};

export default WebcamMonitor;
