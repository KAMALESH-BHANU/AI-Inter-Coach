import React, { useEffect, useRef, useState } from 'react';
import { Mic, MicOff, RefreshCw } from 'lucide-react';

const AudioRecorder = ({ 
  onSpeechUpdate, 
  isAnswering = true, 
  isAITtsSpeaking = false,
  questionIndex = 0, 
  wsService = null 
}) => {
  const [recording, setRecording] = useState(false);
  const [micError, setMicError] = useState(null);
  const [micToggled, setMicToggled] = useState(0);

  const recognitionRef = useRef(null);
  const accumulatedTranscriptRef = useRef('');
  const startTimeRef = useRef(Date.now());
  const isAnsweringRef = useRef(isAnswering);
  const isAITtsSpeakingRef = useRef(isAITtsSpeaking);
  const onSpeechUpdateRef = useRef(onSpeechUpdate);
  const restartTimerRef = useRef(null);

  // Keep live refs updated on every render without triggering effects
  useEffect(() => {
    isAnsweringRef.current = isAnswering;
    isAITtsSpeakingRef.current = isAITtsSpeaking;
    onSpeechUpdateRef.current = onSpeechUpdate;
  });

  // Reset accumulated transcript ONLY when questionIndex changes
  useEffect(() => {
    accumulatedTranscriptRef.current = '';
    startTimeRef.current = Date.now();
    if (onSpeechUpdateRef.current) {
      onSpeechUpdateRef.current('', 0.1);
    }
  }, [questionIndex]);

  // Main Recognition Lifecycle Effect
  useEffect(() => {
    let unmounted = false;

    // Clear any pending restart timer
    if (restartTimerRef.current) {
      clearTimeout(restartTimerRef.current);
      restartTimerRef.current = null;
    }

    // If AI is currently speaking or interview is inactive, stop recognition gently
    if (isAITtsSpeaking || !isAnswering) {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (e) {}
        recognitionRef.current = null;
      }
      setRecording(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMicError('Speech recognition not supported in this browser. Please use Google Chrome or Microsoft Edge.');
      setRecording(false);
      return;
    }

    const startListening = () => {
      if (unmounted || isAITtsSpeakingRef.current || !isAnsweringRef.current) return;

      try {
        if (recognitionRef.current) {
          try { recognitionRef.current.abort(); } catch (e) {}
          recognitionRef.current = null;
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
          if (unmounted) return;
          setRecording(true);
          setMicError(null);
          console.log('[AudioRecorder] Microphone listening active');
        };

        recognition.onresult = (event) => {
          if (unmounted || isAITtsSpeakingRef.current) return;

          let interim = '';
          let newlyFinalized = '';

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcriptChunk = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              newlyFinalized += transcriptChunk + ' ';
            } else {
              interim += transcriptChunk;
            }
          }

          if (newlyFinalized) {
            accumulatedTranscriptRef.current = (accumulatedTranscriptRef.current + ' ' + newlyFinalized).trim();
          }

          const currentTotalText = (accumulatedTranscriptRef.current + (interim ? ' ' + interim : '')).trim();
          const durationSec = Math.max(0.1, (Date.now() - startTimeRef.current) / 1000.0);

          if (onSpeechUpdateRef.current) {
            onSpeechUpdateRef.current(currentTotalText, durationSec);
          }
        };

        recognition.onerror = (event) => {
          if (unmounted) return;
          const err = event.error;

          if (err === 'no-speech') {
            // Normal pause between words, recognition will auto-restart in onend
            return;
          }
          if (err === 'not-allowed') {
            setMicError('Microphone permission blocked. Please allow mic access in your browser.');
            setRecording(false);
            return;
          }
          if (err === 'aborted') {
            // Normal abort during question transition or TTS
            return;
          }
          console.warn('[AudioRecorder] Speech recognition error:', err);
        };

        recognition.onend = () => {
          if (unmounted) return;
          setRecording(false);

          // If interview is still active and AI is not speaking, automatically restart
          if (!isAITtsSpeakingRef.current && isAnsweringRef.current && !unmounted) {
            restartTimerRef.current = setTimeout(() => {
              if (!unmounted && !isAITtsSpeakingRef.current && isAnsweringRef.current) {
                try {
                  startListening();
                } catch (e) {
                  console.warn('[AudioRecorder] Auto-restart error:', e);
                }
              }
            }, 20);
          }
        };

        recognition.start();
        recognitionRef.current = recognition;
        setRecording(true);
        setMicError(null);

      } catch (err) {
        console.warn('[AudioRecorder] Failed to start SpeechRecognition:', err);
        setRecording(false);
        // Try to recover quickly after 100ms
        restartTimerRef.current = setTimeout(() => {
          if (!unmounted && !isAITtsSpeakingRef.current && isAnsweringRef.current) {
            startListening();
          }
        }, 100);
      }
    };

    // Immediate start when AI stops speaking
    startListening();

    return () => {
      unmounted = true;
      if (restartTimerRef.current) {
        clearTimeout(restartTimerRef.current);
      }
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (e) {}
        recognitionRef.current = null;
      }
      setRecording(false);
    };
  }, [isAnswering, isAITtsSpeaking, questionIndex, micToggled]);

  const handleManualRestart = () => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {}
    }
    setMicError(null);
    setMicToggled(prev => prev + 1);
  };

  return (
    <div className="flex items-center space-x-3 bg-slate-900/90 border border-slate-700/80 px-4 py-2 rounded-2xl text-xs font-medium shadow-sm">
      {micError ? (
        <div className="flex items-center space-x-2">
          <MicOff className="w-4 h-4 text-rose-400 animate-pulse" />
          <span className="text-rose-400 font-semibold">{micError}</span>
          <button 
            onClick={handleManualRestart}
            className="ml-2 px-2.5 py-1 bg-rose-600/30 hover:bg-rose-600/50 text-rose-200 border border-rose-500/50 rounded-lg flex items-center space-x-1 transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Retry</span>
          </button>
        </div>
      ) : isAITtsSpeaking ? (
        <div className="flex items-center space-x-3">
          <div className="relative flex items-center">
            <Mic className="w-4 h-4 text-amber-400 animate-pulse" />
          </div>
          <span className="text-amber-300 font-medium">
            AI Speaking...
          </span>
          <button
            type="button"
            onClick={handleManualRestart}
            className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg flex items-center space-x-1 font-bold shadow-sm transition-all active:scale-95 cursor-pointer"
            title="Interrupt AI and speak answer now"
          >
            <span>⚡ Speak Now</span>
          </button>
        </div>
      ) : (
        <div className="flex items-center space-x-3">
          <div className="relative flex items-center">
            <Mic className={`w-4 h-4 ${recording ? 'text-emerald-400' : 'text-slate-400'}`} />
            {recording && (
              <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            )}
          </div>

          <div className="flex items-center space-x-2">
            <span className={`font-medium ${recording ? 'text-emerald-300' : 'text-slate-300'}`}>
              {recording ? '● Microphone Listening (Speak your answer)' : 'Microphone Ready'}
            </span>
          </div>

          {!recording && (
            <button
              onClick={handleManualRestart}
              className="px-2.5 py-1 bg-blue-600/30 hover:bg-blue-600/50 text-blue-200 border border-blue-500/40 rounded-lg flex items-center space-x-1 transition-colors"
            >
              <Mic className="w-3 h-3" />
              <span>Start Mic</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default AudioRecorder;

