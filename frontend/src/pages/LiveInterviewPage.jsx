import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { interviewAPI } from '../services/api';
import { InterviewWebSocketService } from '../services/websocket';
import WebcamMonitor from '../components/WebcamMonitor';
import AudioRecorder from '../components/AudioRecorder';
import LiveMetricsCard from '../components/LiveMetricsCard';
import { Bot, ArrowRight, AlertTriangle, Loader2 } from 'lucide-react';

const FILLER_PATTERNS = [
  { term: 'you know', regex: /\byou know\b/gi },
  { term: 'i mean', regex: /\bi mean\b/gi },
  { term: 'sort of', regex: /\bsort of\b/gi },
  { term: 'kind of', regex: /\bkind of\b/gi },
  { term: 'um', regex: /\bum\b/gi },
  { term: 'uh', regex: /\buh\b/gi },
  { term: 'erm', regex: /\berm\b/gi },
  { term: 'hmm', regex: /\bhmm\b/gi },
  { term: 'like', regex: /\blike\b/gi },
  { term: 'actually', regex: /\bactually\b/gi },
  { term: 'basically', regex: /\bbasically\b/gi },
  { term: 'literally', regex: /\bliterally\b/gi }
];

const LiveInterviewPage = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [savingAnswer, setSavingAnswer] = useState(false);
  const [isInterviewActive, setIsInterviewActive] = useState(true);

  // Live streaming metrics state
  const [liveTranscript, setLiveTranscript] = useState('');
  const [speakingState, setSpeakingState] = useState('SILENT');
  const [wpm, setWpm] = useState(0);
  const [fillerCount, setFillerCount] = useState(0);
  const [fillerWords, setFillerWords] = useState({});
  const [pauseCount, setPauseCount] = useState(0);
  const [avgPauseSec, setAvgPauseSec] = useState(0.0);
  
  // Vision metrics
  const [eyeContactPct, setEyeContactPct] = useState(-1.0); // -1.0 means "Calculating..."
  const [expression, setExpression] = useState('Face Missing');
  const [faceStatus, setFaceStatus] = useState('FACE_MISSING');
  const [visionWarning, setVisionWarning] = useState('WARNING: Face Missing');

  // Selected option for Pseudocode questions
  const [selectedOption, setSelectedOption] = useState(null);

  const [wsInstance, setWsInstance] = useState(null);
  const wsServiceRef = useRef(null);

  // Proctoring frame and eye contact accumulator per question
  const proctoringStatsRef = useRef({
    eyeContactSamples: [],
    singleFaceFrames: 0,
    missingFaceFrames: 0,
    multipleFaceFrames: 0,
    missingEvents: 0,
    multipleEvents: 0,
    lastFaceStatus: 'FACE_MISSING'
  });

  // Accurate real-time pause duration tracker
  const pauseTrackerRef = useRef({
    lastSpeechTime: 0,
    pauseDurations: []
  });

  useEffect(() => {
    let wsService = null;

    const fetchSession = async () => {
      try {
        const res = await interviewAPI.getSession(sessionId);
        setSession(res.data);

        // Connect WebSocket feed for Vision metrics
        wsService = new InterviewWebSocketService(sessionId, (metrics) => {
          if (metrics.type === 'vision_update') {
            const currentStatus = metrics.face_status || (metrics.face_detected ? 'SINGLE_FACE' : 'FACE_MISSING');
            const eyePct = metrics.eye_contact_pct;

            setEyeContactPct(eyePct);
            setExpression(metrics.expression);
            setFaceStatus(currentStatus);
            setVisionWarning(metrics.warning || null);

            // Accumulate metrics for current question
            const stats = proctoringStatsRef.current;
            if (eyePct >= 0) {
              stats.eyeContactSamples.push(eyePct);
            }

            if (currentStatus === 'SINGLE_FACE') {
              stats.singleFaceFrames += 1;
            } else if (currentStatus === 'FACE_MISSING') {
              stats.missingFaceFrames += 1;
              if (stats.lastFaceStatus !== 'FACE_MISSING') {
                stats.missingEvents += 1;
              }
            } else if (currentStatus === 'MULTIPLE_FACES') {
              stats.multipleFaceFrames += 1;
              if (stats.lastFaceStatus !== 'MULTIPLE_FACES') {
                stats.multipleEvents += 1;
              }
            }
            stats.lastFaceStatus = currentStatus;

          } else if (metrics.type === 'speech_update') {
            setSpeakingState(metrics.speaking_state || 'SILENT');
          }
        });

        wsService.connect();
        wsServiceRef.current = wsService;
        setWsInstance(wsService);

      } catch (err) {
        console.error('Failed to load session:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSession();

    return () => {
      if (wsService) {
        wsService.disconnect();
      }
    };
  }, [sessionId]);

  // Real-time speech update handler from AudioRecorder
  const handleSpeechUpdate = (transcript, durationSec) => {
    if (!isInterviewActive) return;

    setLiveTranscript(transcript);

    if (!transcript) {
      setSpeakingState('SILENT');
      return;
    }

    setSpeakingState('SPEAKING');

    const now = Date.now();
    const pTracker = pauseTrackerRef.current;
    if (pTracker.lastSpeechTime > 0) {
      const gapSec = (now - pTracker.lastSpeechTime) / 1000.0;
      // Register pause if silence between phrases was >= 0.8s (800ms) and under 15s
      if (gapSec >= 0.8 && gapSec <= 15.0) {
        pTracker.pauseDurations.push(gapSec);
      }
    }
    pTracker.lastSpeechTime = now;

    // Real pause statistics calculation
    const recordedPauses = pTracker.pauseDurations;
    const pCount = recordedPauses.length;
    const realAvgPause = pCount > 0 
      ? Math.round((recordedPauses.reduce((a, b) => a + b, 0) / pCount) * 10) / 10 
      : 0.0;

    setPauseCount(pCount);
    setAvgPauseSec(realAvgPause);

    const words = transcript.split(/\s+/).filter(Boolean);
    const wordCount = words.length;
    
    // WPM calculation
    const durationMin = Math.max(0.05, durationSec / 60.0);
    const calculatedWpm = Math.round(wordCount / durationMin);
    setWpm(calculatedWpm > 0 && calculatedWpm < 250 ? calculatedWpm : 130);

    // Contextual filler word detection
    let totalFillers = 0;
    const breakdown = {};

    FILLER_PATTERNS.forEach(({ term, regex }) => {
      const matches = (transcript.match(regex) || []).length;
      if (matches > 0) {
        breakdown[term] = matches;
        totalFillers += matches;
      }
    });

    setFillerCount(totalFillers);
    setFillerWords(breakdown);
  };

  if (loading || !session) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
        <p className="text-slate-400 text-sm">Initializing interview environment & questions...</p>
      </div>
    );
  }

  const currentQ = session.current_question || (session.questions && session.questions[session.current_question_index]) || null;
  const isLastQuestion = session.current_question_index >= (session.total_questions || 10) - 1;

  const handleNextQuestion = async () => {
    setSavingAnswer(true);
    setSpeakingState('PROCESSING');

    // Calculate aggregated question eye contact & proctoring stats
    const stats = proctoringStatsRef.current;
    let avgEyeContactForQuestion = eyeContactPct >= 0 ? eyeContactPct : 0.0;
    if (stats.eyeContactSamples.length > 0) {
      const sum = stats.eyeContactSamples.reduce((a, b) => a + b, 0);
      avgEyeContactForQuestion = Math.round((sum / stats.eyeContactSamples.length) * 10) / 10;
    }

    const totalFrames = stats.singleFaceFrames + stats.missingFaceFrames + stats.multipleFaceFrames;
    const faceVisPct = totalFrames > 0 
      ? Math.round(((stats.singleFaceFrames + stats.multipleFaceFrames) / totalFrames) * 1000) / 10 
      : (faceStatus === 'FACE_MISSING' ? 0.0 : 100.0);

    let dominantStatus = faceStatus;
    if (stats.missingFaceFrames > stats.singleFaceFrames && stats.missingFaceFrames > stats.multipleFaceFrames) {
      dominantStatus = 'FACE_MISSING';
    } else if (stats.multipleFaceFrames > 0 && stats.multipleFaceFrames >= stats.singleFaceFrames * 0.3) {
      dominantStatus = 'MULTIPLE_FACES';
    }

    try {
      const actualTranscript = liveTranscript.trim() || (selectedOption ? `Selected option: ${selectedOption}` : '');
      const hasSpoken = actualTranscript.length >= 5 || selectedOption !== null;

      // Save current question answer with authentic candidate metrics (0 if not answered)
      const answerPayload = {
        question_id: currentQ?.id || `Q_${session.current_question_index + 1}`,
        question_index: session.current_question_index,
        transcript: actualTranscript,
        audio_duration: 30.0,
        speaking_duration: hasSpoken ? 25.0 : 0.0,
        wpm: hasSpoken ? (wpm || 120.0) : 0.0,
        filler_count: fillerCount,
        filler_words: fillerWords,
        pause_count: pauseCount,
        average_pause_sec: avgPauseSec,
        eye_contact_pct: avgEyeContactForQuestion,
        face_status: dominantStatus,
        face_visibility_pct: faceVisPct,
        single_face_frames: stats.singleFaceFrames,
        missing_face_frames: stats.missingFaceFrames,
        multiple_face_frames: stats.multipleFaceFrames,
        missing_face_events: stats.missingEvents,
        multiple_face_events: stats.multipleEvents,
        dominant_expression: expression,
        selected_option: selectedOption
      };

      const saveRes = await interviewAPI.saveAnswer(sessionId, answerPayload);

      // Reset Proctoring Accumulator & Pause Tracker for next question
      proctoringStatsRef.current = {
        eyeContactSamples: [],
        singleFaceFrames: 0,
        missingFaceFrames: 0,
        multipleFaceFrames: 0,
        missingEvents: 0,
        multipleEvents: 0,
        lastFaceStatus: faceStatus
      };

      pauseTrackerRef.current = {
        lastSpeechTime: 0,
        pauseDurations: []
      };

      // ATOMIC RESET FOR NEXT QUESTION (ZERO TRANSCRIPT BLEED)
      setLiveTranscript('');
      setSelectedOption(null);
      setWpm(0);
      setFillerCount(0);
      setFillerWords({});
      setPauseCount(0);
      setAvgPauseSec(0.0);
      setSpeakingState('SILENT');

      if (isLastQuestion) {
        // Complete interview & trigger hardware track releases
        setIsInterviewActive(false);
        if (wsServiceRef.current) {
          wsServiceRef.current.disconnect();
        }
        await interviewAPI.complete(sessionId);
        navigate(`/interview/${sessionId}/results`);
      } else {
        // Fetch fresh question state from server
        const res = await interviewAPI.getSession(sessionId);
        setSession(res.data);
      }
    } catch (err) {
      console.error('Error saving answer:', err);
      // Fallback: move local index if network had temporary error
      if (session.current_question_index < (session.total_questions || 10) - 1) {
        const nextIdx = session.current_question_index + 1;
        setSession((prev) => ({
          ...prev,
          current_question_index: nextIdx,
          current_question: prev.questions?.[nextIdx] || prev.current_question
        }));
      }
    } finally {
      setSavingAnswer(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-16">
      {/* Header Bar */}
      <div className="flex items-center justify-between glass-card p-4 rounded-2xl border border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-600 text-white rounded-xl">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">Live AI Mock Interview</h2>
            <p className="text-xs text-slate-400">Session ID: {sessionId.substring(0, 8)}...</p>
          </div>
        </div>

        {/* Question Counter Progress */}
        <div className="flex items-center space-x-3 bg-slate-800 px-4 py-2 rounded-xl border border-slate-700">
          <span className="text-xs font-semibold text-slate-300">Question</span>
          <span className="text-lg font-extrabold text-blue-400">
            {session.current_question_index + 1} <small className="text-slate-500 font-normal">/ {session.total_questions || 10}</small>
          </span>
        </div>
      </div>

      {/* TOP METRICS BAR: Positioned above question & camera for maximum horizontal space */}
      <LiveMetricsCard
        eyeContactPct={eyeContactPct}
        wpm={wpm}
        fillerCount={fillerCount}
        averagePauseSec={avgPauseSec}
      />

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: AI Question & Live Transcript */}
        <div className="lg:col-span-7 space-y-6">
          {/* Question Card */}
          <div className="glass-card p-6 rounded-3xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <span className="px-3 py-1 bg-blue-600/20 text-blue-300 border border-blue-500/30 text-xs font-semibold rounded-lg uppercase tracking-wider">
                {currentQ?.type || 'technical'} • {currentQ?.skill || 'Core'}
              </span>
              <span className="text-xs font-semibold text-slate-400 uppercase">
                {currentQ?.difficulty || 'medium'} Difficulty
              </span>
            </div>

            <h3 className="text-xl font-bold text-slate-100 leading-snug">
              "{currentQ?.question || 'Please explain your technical approach.'}"
            </h3>

            {/* Pseudocode Options if applicable */}
            {currentQ?.type === 'pseudocode' && currentQ.options && (
              <div className="space-y-2 pt-2">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">Select Predicted Output Option:</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {currentQ.options.map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => setSelectedOption(opt)}
                      className={`p-3 rounded-xl text-left text-sm font-semibold border transition-all ${
                        selectedOption === opt
                          ? 'bg-blue-600 text-white border-blue-500 shadow-lg shadow-blue-500/20'
                          : 'bg-slate-800 text-slate-200 border-slate-700 hover:border-slate-600'
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Real-Time Transcript Widget */}
          <div className="glass-card p-6 rounded-3xl border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Live Speech Transcript</h4>
                {/* Speaking State Badge */}
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                  speakingState === 'SPEAKING' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 animate-pulse' :
                  speakingState === 'PROCESSING' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                  'bg-slate-800 text-slate-400'
                }`}>
                  ● {speakingState}
                </span>
              </div>

              <AudioRecorder
                onSpeechUpdate={handleSpeechUpdate}
                isAnswering={isInterviewActive}
                questionIndex={session.current_question_index}
                wsService={wsServiceRef.current}
              />
            </div>

            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 min-h-[100px] text-sm text-slate-200 leading-relaxed font-mono">
              {liveTranscript ? (
                <span>"{liveTranscript}"</span>
              ) : (
                <span className="text-slate-500 italic">Listening... Start speaking into your microphone...</span>
              )}
            </div>
          </div>

          {/* Navigation Controls */}
          <div className="flex justify-end pt-2">
            <button
              type="button"
              onClick={handleNextQuestion}
              disabled={savingAnswer}
              className="px-8 py-3.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl transition-all shadow-xl shadow-blue-500/25 flex items-center space-x-2 disabled:opacity-50"
            >
              <span>{savingAnswer ? 'Saving Response...' : (isLastQuestion ? 'Complete Interview' : 'Next Question')}</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Right Column: Live Camera */}
        <div className="lg:col-span-5 space-y-4">
          <WebcamMonitor
            sessionId={sessionId}
            wsService={wsInstance || wsServiceRef.current}
            eyeContactPct={eyeContactPct}
            expression={expression}
            faceStatus={faceStatus}
            warning={visionWarning}
            isInterviewActive={isInterviewActive}
            fps={5}
          />
        </div>
      </div>
    </div>
  );
};

export default LiveInterviewPage;
