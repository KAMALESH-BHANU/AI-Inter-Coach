import React, { useEffect, useRef, useState } from 'react';
import { Mic, MicOff } from 'lucide-react';

const AudioRecorder = ({ onSpeechUpdate, isAnswering = true, questionIndex = 0, wsService = null }) => {
  const [recording, setRecording] = useState(false);
  const [micError, setMicError] = useState(null);
  const recognitionRef = useRef(null);
  const micStreamRef = useRef(null);
  const audioContextRef = useRef(null);

  const stopMicrophoneStream = () => {
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((track) => {
        track.stop();
        console.log(`Microphone track ${track.label} state: ${track.readyState}`);
      });
      micStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      try { audioContextRef.current.close(); } catch (e) {}
    }
    setRecording(false);
  };

  useEffect(() => {
    let active = true;

    if (!isAnswering) {
      stopMicrophoneStream();
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
        recognitionRef.current = null;
      }
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
      try {
        // Destroy existing instance to guarantee zero question-bleed
        if (recognitionRef.current) {
          try { recognitionRef.current.stop(); } catch (e) {}
          recognitionRef.current = null;
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        const startTime = Date.now();

        recognition.onresult = (event) => {
          if (!active) return;
          let currentTranscript = '';
          for (let i = 0; i < event.results.length; i++) {
            currentTranscript += event.results[i][0].transcript + ' ';
          }

          const trimmed = currentTranscript.trim();
          const durationSec = Math.max(0.1, (Date.now() - startTime) / 1000.0);
          
          if (onSpeechUpdate) {
            onSpeechUpdate(trimmed, durationSec);
          }
        };

        recognition.onerror = (err) => {
          console.warn('Speech recognition notice:', err.error);
        };

        recognition.onend = () => {
          if (active && isAnswering && recognitionRef.current) {
            try { recognition.start(); } catch (e) {}
          }
        };

        recognition.start();
        recognitionRef.current = recognition;
        setRecording(true);
        setMicError(null);
      } catch (err) {
        console.error('Speech recognition setup error:', err);
      }
    } else {
      // Microphone MediaRecorder stream fallback
      const startMediaRecorder = async () => {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          micStreamRef.current = stream;
          setRecording(true);
        } catch (err) {
          setMicError('Microphone permission denied.');
          setRecording(false);
        }
      };
      startMediaRecorder();
    }

    return () => {
      active = false;
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
        recognitionRef.current = null;
      }
      stopMicrophoneStream();
    };
  }, [isAnswering, questionIndex]);

  return (
    <div className="flex items-center space-x-3 bg-slate-800/80 border border-slate-700 px-4 py-2 rounded-xl text-xs font-medium">
      {micError ? (
        <>
          <MicOff className="w-4 h-4 text-rose-400" />
          <span className="text-rose-400">{micError}</span>
        </>
      ) : (
        <>
          <div className="relative flex items-center">
            <Mic className={`w-4 h-4 ${recording ? 'text-emerald-400' : 'text-slate-400'}`} />
            {recording && <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>}
          </div>
          <span className="text-slate-300">
            {recording ? 'Microphone Active (Real-Time)' : 'Microphone Stopped'}
          </span>
        </>
      )}
    </div>
  );
};

export default AudioRecorder;
