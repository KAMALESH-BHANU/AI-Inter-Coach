import React, { useEffect, useState, useRef, useCallback } from 'react';
import { 
  Volume2, 
  VolumeX, 
  Play, 
  Pause, 
  Square, 
  RotateCcw, 
  Settings2, 
  AlertCircle, 
  CheckCircle2, 
  Sparkles,
  Headphones,
  User,
  Bug
} from 'lucide-react';
import {
  isTtsSupported,
  getReadableQuestionText,
  speakQuestion,
  cancelSpeech,
  pauseSpeech,
  resumeSpeech,
  subscribeToVoices,
  findBestFemaleVoice,
  getTtsDebugInfo
} from '../utils/tts';

export const TTS_STATES = {
  IDLE: 'QUESTION_IDLE',
  SPEAKING: 'QUESTION_SPEAKING',
  PAUSED: 'QUESTION_PAUSED',
  FINISHED: 'QUESTION_FINISHED',
  ERROR: 'QUESTION_ERROR'
};

const VOICE_STORAGE_KEY = 'ai_interview_coach_tts_voice_uri';

const QuestionSpeaker = ({
  question,
  questionNumber = 1,
  sessionId = '',
  autoSpeak = true,
  onSpeechStart = () => {},
  onSpeechEnd = () => {},
  onSpeechError = () => {}
}) => {
  const [ttsState, setTtsState] = useState(TTS_STATES.IDLE);
  const [voices, setVoices] = useState([]);
  const [selectedVoiceUri, setSelectedVoiceUri] = useState(() => {
    try {
      return sessionStorage.getItem(VOICE_STORAGE_KEY) || '';
    } catch (e) {
      return '';
    }
  });
  const [speechRate, setSpeechRate] = useState(1.05);
  const [pitch, setPitch] = useState(1.0);
  const [volume, setVolume] = useState(1.0);
  const [showSettings, setShowSettings] = useState(false);
  const [showDebug, setShowDebug] = useState(false);
  const [debugInfo, setDebugInfo] = useState({});
  const [errorMessage, setErrorMessage] = useState('');

  const readableText = getReadableQuestionText(question);
  const questionId = question?.id || `q_${questionNumber}`;
  const speechKey = `${sessionId || 'session'}_${questionId}_${questionNumber}`;

  // Stable refs to prevent stale callbacks and render-loop cancels
  const spokenKeysSetRef = useRef(new Set());
  const currentKeyRef = useRef(speechKey);
  const onSpeechStartRef = useRef(onSpeechStart);
  const onSpeechEndRef = useRef(onSpeechEnd);
  const onSpeechErrorRef = useRef(onSpeechError);

  useEffect(() => {
    onSpeechStartRef.current = onSpeechStart;
    onSpeechEndRef.current = onSpeechEnd;
    onSpeechErrorRef.current = onSpeechError;
  }, [onSpeechStart, onSpeechEnd, onSpeechError]);

  // Update debug info periodically when speaking or in debug mode
  useEffect(() => {
    const updateDebug = () => {
      setDebugInfo(getTtsDebugInfo());
    };
    updateDebug();
    const interval = setInterval(updateDebug, 1000);
    return () => clearInterval(interval);
  }, []);

  // Voice subscription handling (asynchronous voice loading)
  useEffect(() => {
    if (!isTtsSupported()) {
      setTtsState(TTS_STATES.ERROR);
      setErrorMessage('Voice reading is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    const unsubscribe = subscribeToVoices((availableVoices) => {
      setVoices(availableVoices);
      if (availableVoices.length > 0) {
        const savedUri = sessionStorage.getItem(VOICE_STORAGE_KEY);
        let match = null;
        if (savedUri) {
          match = availableVoices.find(v => v.voiceURI === savedUri);
        }
        if (!match) {
          match = findBestFemaleVoice(availableVoices);
          if (match) {
            try { sessionStorage.setItem(VOICE_STORAGE_KEY, match.voiceURI); } catch(e) {}
          }
        }
        if (match) {
          setSelectedVoiceUri(match.voiceURI);
        }
      }
    });

    return unsubscribe;
  }, []);

  // Core speak trigger
  const triggerSpeech = useCallback((overrideText = null) => {
    const textToSpeak = overrideText || readableText;
    if (!textToSpeak) {
      console.warn('[TTS] No text available to speak');
      return;
    }

    speakQuestion(textToSpeak, {
      voiceUri: selectedVoiceUri,
      rate: speechRate,
      pitch: pitch,
      volume: volume,
      onStart: () => {
        setTtsState(TTS_STATES.SPEAKING);
        setErrorMessage('');
        spokenKeysSetRef.current.add(speechKey);
        onSpeechStartRef.current();
        setDebugInfo(getTtsDebugInfo());
      },
      onEnd: () => {
        setTtsState(TTS_STATES.FINISHED);
        if (onSpeechEndRef.current) onSpeechEndRef.current();
        setDebugInfo(getTtsDebugInfo());
      },
      onError: (err) => {
        console.error('[TTS] Speech error callback triggered:', err);
        setTtsState(TTS_STATES.ERROR);
        setErrorMessage(
          err === 'not-allowed'
            ? 'Audio autoplay blocked. Click Read Question to hear question.'
            : 'Voice playback encountered an issue. Click Read Question to retry.'
        );
        if (onSpeechErrorRef.current) onSpeechErrorRef.current(err);
        if (onSpeechEndRef.current) onSpeechEndRef.current();
        setDebugInfo(getTtsDebugInfo());
      }
    });
  }, [readableText, selectedVoiceUri, speechRate, pitch, volume, speechKey]);

  // Handle Question Changes & Auto-Speak Trigger
  useEffect(() => {
    if (!readableText) return;

    if (speechKey !== currentKeyRef.current) {
      currentKeyRef.current = speechKey;
      setTtsState(TTS_STATES.IDLE);
      setErrorMessage('');
    }

    if (autoSpeak && !spokenKeysSetRef.current.has(speechKey)) {
      // Transition buffer so question state and DOM have mounted
      const timer = setTimeout(() => {
        if (!spokenKeysSetRef.current.has(speechKey)) {
          triggerSpeech();
        }
      }, 150);

      return () => clearTimeout(timer);
    }
  }, [speechKey, readableText, autoSpeak, triggerSpeech]);

  // Read Question Button Handler (Direct Real User Gesture)
  const handleReadQuestion = () => {
    console.log('[TTS] Read Question clicked', { speechKey, readableText });
    triggerSpeech();
  };

  const handlePause = () => {
    pauseSpeech();
    setTtsState(TTS_STATES.PAUSED);
  };

  const handleResume = () => {
    resumeSpeech();
    setTtsState(TTS_STATES.SPEAKING);
  };

  const handleStop = () => {
    cancelSpeech();
    setTtsState(TTS_STATES.FINISHED);
    onSpeechEndRef.current();
  };

  const handleVoiceChange = (uri) => {
    setSelectedVoiceUri(uri);
    try {
      sessionStorage.setItem(VOICE_STORAGE_KEY, uri);
    } catch (e) {}
  };

  const englishVoices = voices.filter(v => v.lang && v.lang.toLowerCase().startsWith('en'));
  const otherVoices = voices.filter(v => !v.lang || !v.lang.toLowerCase().startsWith('en'));
  const activeVoice = voices.find(v => v.voiceURI === selectedVoiceUri);

  if (!isTtsSupported()) {
    return (
      <div className="bg-amber-950/30 border border-amber-800/40 p-3 rounded-2xl text-xs text-amber-300 flex items-center space-x-2">
        <AlertCircle className="w-4 h-4 flex-shrink-0" />
        <span>Text-to-speech is not supported in this browser. Please use Chrome or Edge for voice question reading.</span>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Main TTS Status Banner & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/90 border border-slate-800 px-4 py-2.5 rounded-2xl">
        <div className="flex items-center space-x-2.5">
          {ttsState === TTS_STATES.SPEAKING && (
            <div className="flex items-center space-x-2 bg-blue-500/20 text-blue-300 border border-blue-500/40 px-3 py-1 rounded-full text-xs font-bold animate-pulse">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
              <span>🔊 AI Interviewer Speaking...</span>
            </div>
          )}

          {ttsState === TTS_STATES.PAUSED && (
            <div className="flex items-center space-x-2 bg-amber-500/20 text-amber-300 border border-amber-500/40 px-3 py-1 rounded-full text-xs font-bold">
              <Pause className="w-3.5 h-3.5" />
              <span>⏸ Question Paused</span>
            </div>
          )}

          {ttsState === TTS_STATES.FINISHED && (
            <div className="flex items-center space-x-2 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 px-3 py-1 rounded-full text-xs font-bold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>✓ Question Finished • 🎤 You can answer now</span>
            </div>
          )}

          {ttsState === TTS_STATES.IDLE && (
            <div className="flex items-center space-x-2 bg-slate-800 text-slate-300 border border-slate-700 px-3 py-1 rounded-full text-xs font-medium">
              <Volume2 className="w-3.5 h-3.5 text-slate-400" />
              <span>Ready</span>
            </div>
          )}

          {ttsState === TTS_STATES.ERROR && (
            <div className="flex items-center space-x-2 bg-rose-500/20 text-rose-300 border border-rose-500/40 px-3 py-1 rounded-full text-xs font-medium">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>{errorMessage || 'Voice playback notice'}</span>
            </div>
          )}

          {/* Female Voice Indicator Badge */}
          {activeVoice && (
            <div className="hidden md:flex items-center space-x-1 text-[11px] text-slate-400 bg-slate-800/60 px-2.5 py-0.5 rounded-lg border border-slate-700/60">
              <User className="w-3 h-3 text-pink-400" />
              <span className="truncate max-w-[140px]" title={activeVoice.name}>
                {activeVoice.name.replace(/Microsoft |Desktop |Online \(Natural\)|Google /gi, '').trim() || 'Female Voice'}
              </span>
            </div>
          )}

          {/* Headphone isolation recommendation */}
          <div className="hidden sm:flex items-center space-x-1 text-[11px] text-slate-400 pl-1">
            <Headphones className="w-3.5 h-3.5 text-blue-400" />
            <span>Headphones recommended</span>
          </div>
        </div>

        {/* Audio Control Action Buttons */}
        <div className="flex items-center space-x-1.5">
          {/* Read / Replay Button */}
          {ttsState !== TTS_STATES.SPEAKING && (
            <button
              type="button"
              onClick={handleReadQuestion}
              aria-label="Read question aloud"
              title="Read question aloud"
              className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-blue-600/25 cursor-pointer active:scale-95"
            >
              {ttsState === TTS_STATES.FINISHED ? (
                <>
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Replay</span>
                </>
              ) : (
                <>
                  <Volume2 className="w-3.5 h-3.5" />
                  <span>Read Question</span>
                </>
              )}
            </button>
          )}

          {/* Skip AI & Speak Now Button */}
          {ttsState === TTS_STATES.SPEAKING && (
            <button
              type="button"
              onClick={handleStop}
              aria-label="Skip AI voice and speak now"
              title="Skip AI voice and start answering immediately"
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-emerald-600/25 cursor-pointer active:scale-95"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>⚡ Answer Now</span>
            </button>
          )}

          {/* Pause Button */}
          {ttsState === TTS_STATES.SPEAKING && (
            <button
              type="button"
              onClick={handlePause}
              aria-label="Pause speech"
              title="Pause speech"
              className="flex items-center space-x-1 px-3 py-1.5 bg-amber-600/80 hover:bg-amber-600 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-amber-600/20 cursor-pointer"
            >
              <Pause className="w-3.5 h-3.5" />
              <span>Pause</span>
            </button>
          )}

          {/* Resume Button */}
          {ttsState === TTS_STATES.PAUSED && (
            <button
              type="button"
              onClick={handleResume}
              aria-label="Resume speech"
              title="Resume speech"
              className="flex items-center space-x-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition-all cursor-pointer"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Resume</span>
            </button>
          )}

          {/* Stop Button */}
          {(ttsState === TTS_STATES.SPEAKING || ttsState === TTS_STATES.PAUSED) && (
            <button
              type="button"
              onClick={handleStop}
              aria-label="Stop speech"
              title="Stop speech"
              className="flex items-center space-x-1 px-2.5 py-1.5 bg-slate-800 hover:bg-rose-600/80 text-slate-300 hover:text-white border border-slate-700 hover:border-rose-500 rounded-xl text-xs font-semibold transition-all cursor-pointer"
            >
              <Square className="w-3 h-3" />
              <span>Stop</span>
            </button>
          )}

          {/* TTS Voice Settings Drawer Toggle */}
          <button
            type="button"
            onClick={() => setShowSettings(!showSettings)}
            aria-label="Voice settings"
            title="Configure TTS Voice & Speed"
            className={`p-1.5 rounded-xl border transition-all text-xs cursor-pointer ${
              showSettings 
                ? 'bg-blue-600/20 text-blue-300 border-blue-500/40' 
                : 'bg-slate-800/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border-slate-700'
            }`}
          >
            <Settings2 className="w-4 h-4" />
          </button>

          {/* TTS Debug Toggle */}
          <button
            type="button"
            onClick={() => setShowDebug(!showDebug)}
            aria-label="TTS diagnostics"
            title="TTS Diagnostics"
            className={`p-1.5 rounded-xl border transition-all text-xs cursor-pointer ${
              showDebug
                ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/40'
                : 'bg-slate-800/80 hover:bg-slate-800 text-slate-500 hover:text-slate-300 border-slate-700'
            }`}
          >
            <Bug className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Voice Settings Panel */}
      {showSettings && (
        <div className="bg-slate-900/95 border border-slate-800 p-4 rounded-2xl space-y-3 text-xs animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between pb-1 border-b border-slate-800">
            <span className="font-bold text-slate-200 flex items-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              <span>Text-to-Speech Settings (Female Voice Prioritized)</span>
            </span>
            <span className="text-[11px] text-slate-400">Web Speech API (Native)</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Voice Dropdown */}
            <div className="space-y-1 md:col-span-1">
              <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Interviewer Voice
              </label>
              <select
                value={selectedVoiceUri}
                onChange={(e) => handleVoiceChange(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-2.5 py-1.5 text-slate-200 text-xs focus:outline-none focus:border-blue-500"
              >
                {voices.length === 0 && <option value="">Default System Voice</option>}
                {englishVoices.length > 0 && (
                  <optgroup label="English Voices">
                    {englishVoices.map((v) => (
                      <option key={v.voiceURI} value={v.voiceURI}>
                        {v.name} ({v.lang})
                      </option>
                    ))}
                  </optgroup>
                )}
                {otherVoices.length > 0 && (
                  <optgroup label="Other Voices">
                    {otherVoices.map((v) => (
                      <option key={v.voiceURI} value={v.voiceURI}>
                        {v.name} ({v.lang})
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>
            </div>

            {/* Speech Rate Slider */}
            <div className="space-y-1">
              <div className="flex justify-between text-[11px]">
                <span className="text-slate-400 font-semibold uppercase tracking-wider">Speed Rate</span>
                <span className="text-blue-400 font-mono font-bold">{speechRate.toFixed(2)}x</span>
              </div>
              <input
                type="range"
                min="0.6"
                max="1.4"
                step="0.05"
                value={speechRate}
                onChange={(e) => setSpeechRate(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <div className="flex justify-between text-[10px] text-slate-500">
                <span>0.6x (Slower)</span>
                <span>0.95x (Default)</span>
                <span>1.4x (Faster)</span>
              </div>
            </div>

            {/* Pitch & Volume Sliders */}
            <div className="space-y-1">
              <div className="flex justify-between text-[11px]">
                <span className="text-slate-400 font-semibold uppercase tracking-wider">Pitch & Volume</span>
                <span className="text-blue-400 font-mono font-bold">{pitch.toFixed(1)}p / {Math.round(volume * 100)}%</span>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="range"
                  min="0.7"
                  max="1.3"
                  step="0.1"
                  value={pitch}
                  onChange={(e) => setPitch(parseFloat(e.target.value))}
                  title="Pitch"
                  className="w-1/2 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
                <input
                  type="range"
                  min="0.2"
                  max="1.0"
                  step="0.1"
                  value={volume}
                  onChange={(e) => setVolume(parseFloat(e.target.value))}
                  title="Volume"
                  className="w-1/2 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-500">
                <span>Pitch: {pitch.toFixed(1)}</span>
                <span>Vol: {Math.round(volume * 100)}%</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TTS Diagnostics Panel (Visible when toggled or in debug mode) */}
      {showDebug && (
        <div className="bg-slate-950/90 border border-slate-800/80 p-3 rounded-xl font-mono text-[11px] text-slate-300 space-y-1">
          <div className="flex items-center justify-between text-indigo-400 font-bold">
            <span>[TTS Diagnostic Status]</span>
            <span>Voices: {debugInfo.availableVoiceCount || voices.length}</span>
          </div>
          <div><span className="text-slate-500">TTS Supported:</span> <span className="text-emerald-400">{debugInfo.isSupported ? 'Yes' : 'No'}</span></div>
          <div><span className="text-slate-500">Question Text:</span> <span className="text-slate-200">"{readableText.substring(0, 70)}..."</span></div>
          <div><span className="text-slate-500">Selected Voice:</span> <span className="text-pink-300">{activeVoice?.name || debugInfo.voiceName || 'None'}</span></div>
          <div><span className="text-slate-500">Speaking Status:</span> <span className={debugInfo.speaking || ttsState === TTS_STATES.SPEAKING ? 'text-blue-400 font-bold' : 'text-slate-400'}>{ttsState} (Synthesis Speaking: {String(debugInfo.speaking)})</span></div>
          <div><span className="text-slate-500">Last Start:</span> <span>{debugInfo.startedAt || 'N/A'}</span> | <span className="text-slate-500">Last End:</span> <span>{debugInfo.completedAt || 'N/A'}</span></div>
          {debugInfo.lastError && (
            <div><span className="text-rose-400">Last Error:</span> <span className="text-rose-300">{debugInfo.lastError}</span></div>
          )}
        </div>
      )}
    </div>
  );
};

export default QuestionSpeaker;
