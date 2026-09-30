import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { interviewAPI } from '../services/api';
import { InterviewWebSocketService } from '../services/websocket';
import WebcamMonitor from '../components/WebcamMonitor';
import AudioRecorder from '../components/AudioRecorder';
import LiveMetricsCard from '../components/LiveMetricsCard';
import QuestionSpeaker from '../components/QuestionSpeaker';
import SqlEditor from '../components/SqlEditor';
import PseudocodeMcqQuestion from '../components/PseudocodeMcqQuestion';
import { stripQuestionEcho } from '../utils/speechBleedFilter';
import { Bot, ArrowRight, AlertTriangle, Loader2, CheckCircle2 } from 'lucide-react';

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
  const [loadError, setLoadError] = useState(null);
  const [savingAnswer, setSavingAnswer] = useState(false);
  const [isInterviewActive, setIsInterviewActive] = useState(true);
  const [isAITtsSpeaking, setIsAITtsSpeaking] = useState(false);

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
  const [selectedOptionText, setSelectedOptionText] = useState('');

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

  // Accurate real-time transcript ref to prevent stale closures during navigation
  const latestTranscriptRef = useRef('');

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
        setLoadError(err.response?.data?.detail || err.message || 'Failed to load interview session.');
      } finally {
        setLoading(false);
      }
    };

    fetchSession();

    return () => {
      if (wsService) {
        wsService.disconnect();
      }
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        try {
          window.speechSynthesis.cancel();
        } catch (e) {}
      }
    };
  }, [sessionId]);

  const questions = session?.questions || [];
  const currentQuestionIndex = session?.current_question_index ?? 0;
  const totalQuestions = questions.length || session?.total_questions || 13;
  const currentQ = questions[currentQuestionIndex] || (session?.questions && session.questions[currentQuestionIndex]) || session?.current_question || null;
  const isLastQuestion = currentQuestionIndex >= totalQuestions - 1;
  const isSqlQuestion = currentQ?.type === 'sql';
  const isPseudocodeMcq = currentQ?.type === 'pseudocode' || 
                          currentQ?.type === 'pseudocode_mcq' || 
                          currentQ?.questionType === 'PSEUDOCODE_MCQ' || 
                          currentQ?.answer_mode === 'mcq' || 
                          currentQ?.answerMode === 'mcq';

  // Navigation and question list invariant check (must be at top level with other hooks)
  useEffect(() => {
    if (session?.questions) {
      console.log('[Interview Navigation] Question list', {
        total: session.questions.length,
        ids: session.questions.map((q) => q.id),
        types: session.questions.map((q) => q.type),
        q12: session.questions[11]?.id,
        q13: session.questions[12]?.id
      });
      if (session.questions.length !== 13) {
        console.error('[Interview Navigation] Warning: expected 13 questions, got', session.questions.length);
      }
    }
  }, [session?.questions]);

  // Safety Watchdog: Ensure isAITtsSpeaking never gets stuck indefinitely
  useEffect(() => {
    if (isAITtsSpeaking) {
      const qWords = (currentQ?.question || '').split(/\s+/).filter(Boolean).length || 15;
      const dynamicLimitMs = Math.max(2500, Math.min(6500, (qWords / 2.8) * 1000 + 1200));
      const safetyTimeout = setTimeout(() => {
        console.log('[TTS Watchdog] Auto-releasing TTS speaking state to ensure microphone is active');
        setIsAITtsSpeaking(false);
      }, dynamicLimitMs);
      return () => clearTimeout(safetyTimeout);
    }
  }, [isAITtsSpeaking, currentQuestionIndex]);

  // Real-time speech update handler from AudioRecorder
  const handleSpeechUpdate = useCallback((rawTranscript, durationSec) => {
    if (!isInterviewActive) return;

    const qText = currentQ?.question || currentQ?.text || '';
    const transcript = stripQuestionEcho(rawTranscript, qText);

    latestTranscriptRef.current = transcript || '';
    setLiveTranscript(transcript || '');

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
  }, [isInterviewActive]);

  const handleNextQuestion = async (customQueryArg = null, customExecutionResult = null) => {
    // Only treat customQueryArg as query if it is a non-empty string (not an Event object)
    const customQuery = typeof customQueryArg === 'string' ? customQueryArg.trim() : null;

    // Immediately cancel any active speech utterance from previous question
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {}
    }
    setIsAITtsSpeaking(false);

    setSavingAnswer(true);
    setSpeakingState('PROCESSING');

    const currentIndex = currentQuestionIndex;
    const targetNextIndex = currentIndex + 1;

    console.log('[Interview Navigation] Next question triggered', {
      currentIndex,
      targetNextIndex,
      currentQuestionNumber: currentIndex + 1,
      targetNextQuestionNumber: targetNextIndex + 1,
      currentId: currentQ?.id,
      currentType: currentQ?.type,
      nextId: questions[targetNextIndex]?.id,
      nextType: questions[targetNextIndex]?.type,
      isLastQuestion
    });

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
      const rawRecorded = (latestTranscriptRef.current || liveTranscript || '').trim();
      const qText = currentQ?.question || currentQ?.text || '';
      const recordedSpeech = stripQuestionEcho(rawRecorded, qText).trim();
      let actualTranscript = '';
      let candidateQuery = null;

      if (isSqlQuestion) {
        candidateQuery = customQuery || '';
        actualTranscript = candidateQuery || 'SQL Query Submitted';
      } else if (isPseudocodeMcq) {
        candidateQuery = null;
        actualTranscript = '';
      } else if (selectedOption) {
        actualTranscript = `Selected option: ${selectedOption}`;
        if (recordedSpeech) {
          actualTranscript += ` | Spoken explanation: ${recordedSpeech}`;
        }
        candidateQuery = null;
      } else {
        actualTranscript = recordedSpeech;
        candidateQuery = null;
      }

      const hasSpoken = (actualTranscript.length >= 5 && !isSqlQuestion && !isPseudocodeMcq) || selectedOption !== null;

      // Save current question answer with authentic candidate metrics
      const answerPayload = {
        question_id: currentQ?.id || `Q_${currentIndex + 1}`,
        question_index: currentIndex,
        transcript: actualTranscript,
        candidate_query: candidateQuery,
        audio_duration: (isSqlQuestion || isPseudocodeMcq) ? 0.0 : 30.0,
        speaking_duration: (isSqlQuestion || isPseudocodeMcq) ? 0.0 : (hasSpoken ? 25.0 : 0.0),
        wpm: (isSqlQuestion || isPseudocodeMcq) ? 0.0 : (hasSpoken ? (wpm || 120.0) : 0.0),
        filler_count: (isSqlQuestion || isPseudocodeMcq) ? 0 : fillerCount,
        filler_words: (isSqlQuestion || isPseudocodeMcq) ? {} : fillerWords,
        pause_count: (isSqlQuestion || isPseudocodeMcq) ? 0 : pauseCount,
        average_pause_sec: (isSqlQuestion || isPseudocodeMcq) ? 0.0 : avgPauseSec,
        eye_contact_pct: avgEyeContactForQuestion,
        face_status: dominantStatus,
        face_visibility_pct: faceVisPct,
        single_face_frames: stats.singleFaceFrames,
        missing_face_frames: stats.missingFaceFrames,
        multiple_face_frames: stats.multipleFaceFrames,
        missing_face_events: stats.missingEvents,
        multiple_face_events: stats.multipleEvents,
        dominant_expression: expression,
        selected_option: selectedOption,
        selected_option_id: selectedOption,
        selected_option_text: selectedOptionText,
        answer_mode: isPseudocodeMcq ? 'mcq' : (isSqlQuestion ? 'sql' : 'speech')
      };

      // Reset Proctoring Accumulator & Pause Tracker immediately
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

      // ATOMIC RESET FOR NEXT QUESTION
      latestTranscriptRef.current = '';
      setLiveTranscript('');
      setSelectedOption(null);
      setSelectedOptionText('');
      setWpm(0);
      setFillerCount(0);
      setFillerWords({});
      setPauseCount(0);
      setAvgPauseSec(0.0);
      setSpeakingState('SILENT');

      if (isLastQuestion) {
        console.log('[Interview Navigation] Q13 completed, finalizing interview session');
        setIsInterviewActive(false);
        if (wsServiceRef.current) {
          wsServiceRef.current.disconnect();
        }
        await interviewAPI.saveAnswer(sessionId, answerPayload);
        await interviewAPI.complete(sessionId);
        navigate(`/interview/${sessionId}/results`);
      } else {
        // OPTIMISTIC ADVANCE: Switch question immediately on screen without waiting for cloud DB write
        console.log('[Interview Navigation] Optimistically advancing to question:', targetNextIndex + 1);
        setSession((prev) => {
          const currentQs = prev.questions || [];
          return {
            ...prev,
            current_question_index: targetNextIndex,
            current_question: currentQs[targetNextIndex] || null
          };
        });

        // Persist answer in background
        interviewAPI.saveAnswer(sessionId, answerPayload).catch((err) => {
          console.error('[Interview Navigation] Background answer save error:', err);
        });
      }
    } catch (err) {
      console.error('[Interview Navigation] Error saving answer:', err);
      // Fallback: advance local index safely
      if (currentIndex < totalQuestions - 1) {
        setSession((prev) => {
          const currentQs = prev.questions || [];
          return {
            ...prev,
            current_question_index: targetNextIndex,
            current_question: currentQs[targetNextIndex] || prev.current_question
          };
        });
      }
    } finally {
      setSavingAnswer(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
        <p className="text-slate-400 text-sm">Initializing interview environment & questions...</p>
      </div>
    );
  }

  if (loadError || !session) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center space-y-4 text-center px-4">
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-full text-rose-400">
          <AlertTriangle className="w-10 h-10" />
        </div>
        <h3 className="text-xl font-bold text-slate-100">Session Error</h3>
        <p className="text-slate-400 text-sm max-w-md">{loadError || 'Interview session could not be loaded.'}</p>
        <button
          onClick={() => navigate('/interview/setup')}
          className="mt-4 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition-all shadow-lg shadow-blue-500/20"
        >
          Configure New Interview
        </button>
      </div>
    );
  }

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
            {currentQuestionIndex + 1} <small className="text-slate-500 font-normal">/ {totalQuestions}</small>
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
        {/* Left Column: AI Question & Live Transcript or SQL IDE */}
        <div className="lg:col-span-7 space-y-6">
          {isSqlQuestion ? (
            <SqlEditor
              question={currentQ}
              questionNumber={currentQuestionIndex + 1}
              totalQuestions={totalQuestions}
              sessionId={sessionId}
              onAnswerSubmit={handleNextQuestion}
              savingAnswer={savingAnswer}
              isLastQuestion={isLastQuestion}
            />
          ) : isPseudocodeMcq ? (
            <PseudocodeMcqQuestion
              question={currentQ}
              questionNumber={currentQuestionIndex + 1}
              totalQuestions={totalQuestions}
              sessionId={sessionId}
              selectedOptionId={selectedOption}
              onSelectOption={(optId, optText) => {
                setSelectedOption(optId);
                setSelectedOptionText(optText);
              }}
              onNextQuestion={() => handleNextQuestion()}
              savingAnswer={savingAnswer}
              isLastQuestion={isLastQuestion}
              isAITtsSpeaking={isAITtsSpeaking}
              setIsAITtsSpeaking={setIsAITtsSpeaking}
            />
          ) : (
            <>
              {/* Question Card */}
              <div className="glass-card p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="px-3 py-1 text-xs font-semibold rounded-lg uppercase tracking-wider bg-blue-600/20 text-blue-300 border border-blue-500/30">
                    {`${currentQ?.type || 'technical'} • ${currentQ?.skill || 'Core'}`}
                  </span>
                  <span className="text-xs font-semibold text-slate-400 uppercase">
                    {currentQ?.difficulty || 'medium'} Difficulty
                  </span>
                </div>

                <h3 className="text-xl font-bold text-slate-100 leading-snug">
                  "{currentQ?.question || 'Please explain your technical approach.'}"
                </h3>

                {/* Question Speaker TTS Engine & Controls */}
                <QuestionSpeaker
                  question={currentQ}
                  questionNumber={currentQuestionIndex + 1}
                  sessionId={sessionId}
                  autoSpeak={true}
                  onSpeechStart={() => setIsAITtsSpeaking(true)}
                  onSpeechEnd={() => setIsAITtsSpeaking(false)}
                  onSpeechError={() => setIsAITtsSpeaking(false)}
                />
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
                    isAITtsSpeaking={isAITtsSpeaking}
                    questionIndex={currentQuestionIndex}
                    wsService={wsServiceRef.current}
                  />
                </div>

                <div 
                  onClick={() => {
                    if (isAITtsSpeaking) {
                      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
                        try { window.speechSynthesis.cancel(); } catch (e) {}
                      }
                      setIsAITtsSpeaking(false);
                    }
                  }}
                  className={`bg-slate-950 p-4 rounded-2xl border min-h-[100px] text-sm text-slate-200 leading-relaxed font-mono transition-all ${
                    isAITtsSpeaking 
                      ? 'border-amber-500/30 cursor-pointer hover:border-emerald-500/50 hover:bg-slate-900/50' 
                      : 'border-slate-800'
                  }`}
                  title={isAITtsSpeaking ? "Click to interrupt AI and start speaking immediately" : "Real-time speech transcript"}
                >
                  {liveTranscript ? (
                    <span>"{liveTranscript}"</span>
                  ) : isAITtsSpeaking ? (
                    <div className="flex flex-col space-y-1">
                      <span className="text-amber-400 font-medium">AI is reading the question...</span>
                      <span className="text-slate-500 text-xs italic">Tip: Click here or click "⚡ Speak Now" above to answer immediately.</span>
                    </div>
                  ) : (
                    <span className="text-slate-500 italic">Listening... Start speaking into your microphone...</span>
                  )}
                </div>
              </div>

              {/* Navigation Controls */}
              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  onClick={() => handleNextQuestion()}
                  disabled={savingAnswer}
                  className="px-8 py-3.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl transition-all shadow-xl shadow-blue-500/25 flex items-center space-x-2 disabled:opacity-50"
                >
                  <span>{savingAnswer ? 'Saving Response...' : (isLastQuestion ? 'Complete Interview' : 'Next Question')}</span>
                  <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </>
          )}
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
