import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { interviewAPI } from '../services/api';
import VideoReplayModal from '../components/VideoReplayModal';
import {
  Award, CheckCircle2, AlertTriangle, Download, RefreshCw, Play, ShieldCheck, FileText, ChevronDown, ChevronUp, Database, Code, Check, X,
  Sparkles, Calendar, BookOpen, Target, MessageSquare, Cpu, ArrowRight
} from 'lucide-react';

const ResultsPage = () => {
  const { sessionId } = useParams();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [showVideoModal, setShowVideoModal] = useState(false);
  const [expandedQuestion, setExpandedQuestion] = useState(null);

  // Gemini AI Suggestions State
  const [suggestions, setSuggestions] = useState(null);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [suggestionsError, setSuggestionsError] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const res = await interviewAPI.getResults(sessionId);
        setResults(res.data);
        if (res.data.suggestions) {
          setSuggestions(res.data.suggestions);
        } else {
          // Trigger asynchronous generation if not yet generated
          fetchOrGenerateSuggestions(sessionId);
        }
      } catch (err) {
        console.error('Failed to fetch results:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, [sessionId]);

  const fetchOrGenerateSuggestions = async (id, force = false) => {
    setSuggestionsLoading(true);
    setSuggestionsError(null);
    try {
      const res = await interviewAPI.generateSuggestions(id, force);
      if (res.data && res.data.suggestions) {
        setSuggestions(res.data.suggestions);
      }
    } catch (err) {
      console.warn('Unable to generate AI suggestions, falling back to local review:', err);
      setSuggestionsError(err.response?.data?.detail || 'AI suggestions temporarily unavailable.');
    } finally {
      setSuggestionsLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    setDownloadingPdf(true);
    try {
      const response = await interviewAPI.downloadPDF(sessionId);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `AI_Interview_Report_${sessionId.substring(0, 8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading PDF report:', err);
      alert('Unable to generate report. Please try again.');
    } finally {
      setDownloadingPdf(false);
    }
  };

  if (loading || !results) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <div className="text-center space-y-3">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto" />
          <p className="text-slate-400 text-sm">Generating your personalized AI Feedback Report...</p>
        </div>
      </div>
    );
  }

  const scores = results.scores || {};
  const feedback = results.gemini_feedback || {};
  const speech = results.speech_metrics || {};
  const vision = results.vision_metrics || {};
  const faceMonitoring = vision.face_monitoring || {};

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {/* Header Summary */}
      <div className="glass-card p-8 rounded-3xl border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-2 text-center md:text-left">
          <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold rounded-lg uppercase">
            Interview Completed
          </span>
          <h1 className="text-3xl font-extrabold text-slate-100">Performance Assessment</h1>
          <p className="text-sm text-slate-400">
            Skills Evaluated: <span className="text-blue-400 font-medium">{results.skills?.join(', ')}</span>
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-3">
          {results.video_available && (
            <button
              type="button"
              onClick={() => setShowVideoModal(true)}
              className="px-5 py-3 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-xl text-sm border border-slate-700 flex items-center space-x-2 transition-all shadow-lg cursor-pointer"
            >
              <Play className="w-4 h-4 text-emerald-400" />
              <span>Replay Interview (1-Time)</span>
            </button>
          )}

          <button
            type="button"
            onClick={handleDownloadPDF}
            disabled={downloadingPdf}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl text-sm flex items-center space-x-2 transition-all shadow-lg shadow-blue-500/25 disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            <span>{downloadingPdf ? 'Generating PDF...' : 'Download PDF Report'}</span>
          </button>
        </div>
      </div>

      {/* Score Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="glass-card p-5 rounded-2xl border border-blue-500/30 bg-blue-950/20 text-center space-y-1">
          <span className="text-xs font-semibold text-blue-300 uppercase">Overall Score</span>
          <p className="text-3xl font-black text-blue-400">{scores.overall_score}/100</p>
        </div>
        <div className="glass-card p-5 rounded-2xl border border-slate-800 text-center space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase">Technical Knowledge</span>
          <p className="text-3xl font-black text-slate-100">{scores.technical_knowledge}/100</p>
        </div>
        <div className="glass-card p-5 rounded-2xl border border-indigo-500/30 bg-indigo-950/20 text-center space-y-1">
          <span className="text-xs font-semibold text-indigo-300 uppercase flex items-center justify-center space-x-1">
            <Database className="w-3.5 h-3.5 mr-1" /> SQL Coding (Q12-13)
          </span>
          <p className="text-3xl font-black text-indigo-400">{scores.sql_score ?? 0}%</p>
        </div>
        <div className="glass-card p-5 rounded-2xl border border-slate-800 text-center space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase">Communication</span>
          <p className="text-3xl font-black text-slate-100">{scores.communication}/100</p>
        </div>
        <div className="glass-card p-5 rounded-2xl border border-slate-800 text-center space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase">Eye Contact & Gaze</span>
          <p className="text-3xl font-black text-slate-100">{scores.eye_contact}%</p>
        </div>
      </div>

      {/* Face Monitoring Integrity Card */}
      <div className="glass-card p-6 rounded-3xl border border-amber-500/30 bg-amber-950/10 space-y-4">
        <div className="flex items-center space-x-2 text-amber-400">
          <ShieldCheck className="w-5 h-5" />
          <h3 className="text-base font-bold text-slate-100">Face Proctoring & Integrity Monitoring</h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span className="text-xs text-slate-400 block">Single Face Presence</span>
            <strong className="text-lg text-emerald-400">{faceMonitoring.single_face_percentage || 100}%</strong>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span className="text-xs text-slate-400 block">Missing Face Events</span>
            <strong className="text-lg text-amber-400">{faceMonitoring.missing_face_events || 0} ({faceMonitoring.missing_face_percentage || 0}%)</strong>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span className="text-xs text-slate-400 block">Multiple Face Events</span>
            <strong className="text-lg text-rose-400">{faceMonitoring.multiple_face_events || 0} ({faceMonitoring.multiple_face_percentage || 0}%)</strong>
          </div>
          <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
            <span className="text-xs text-slate-400 block">Speaking Rate</span>
            <strong className="text-lg text-blue-400">{speech.average_wpm || 0} WPM</strong>
          </div>
        </div>
      </div>

      {/* AI Interview Suggestions & Coaching Section */}
      <div className="glass-card p-8 rounded-3xl border border-slate-800 space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
                <span>AI Interview Suggestions & Coaching</span>
              </h3>
              <p className="text-xs text-slate-400">
                Personalized communication diagnostics, technical reviews, and 5-day study roadmap
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {suggestions && (
              <span className={`px-3 py-1 rounded-lg text-xs font-semibold uppercase tracking-wider flex items-center space-x-1.5 ${
                suggestions.isFallback
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
              }`}>
                {suggestions.isFallback ? <AlertTriangle className="w-3.5 h-3.5 mr-1" /> : <Sparkles className="w-3.5 h-3.5 mr-1" />}
                {suggestions.isFallback ? 'Deterministic Coaching' : 'Gemini AI Coaching'}
              </span>
            )}

            <button
              type="button"
              onClick={() => fetchOrGenerateSuggestions(sessionId, true)}
              disabled={suggestionsLoading}
              className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold rounded-xl border border-slate-700 flex items-center space-x-1.5 transition-all disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${suggestionsLoading ? 'animate-spin' : ''}`} />
              <span>{suggestionsLoading ? 'Analyzing...' : 'Regenerate'}</span>
            </button>
          </div>
        </div>

        {/* Fallback Notice Banner */}
        {suggestions?.isFallback && (
          <div className="bg-amber-950/20 border border-amber-500/30 p-4 rounded-2xl flex items-start space-x-3 text-xs text-amber-200">
            <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="block font-semibold text-amber-300 mb-0.5">Offline Fallback Coaching Active</strong>
              <p className="text-amber-200/90 leading-relaxed">
                {suggestions.fallbackReason || 'Gemini API was temporarily unreachable. The coaching points below were deterministically derived from your objective interview metrics.'}
              </p>
            </div>
          </div>
        )}

        {suggestionsLoading ? (
          <div className="py-12 text-center space-y-4">
            <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto" />
            <div className="space-y-1">
              <p className="text-slate-200 text-sm font-semibold">Gemini AI is analyzing your interview results...</p>
              <p className="text-slate-400 text-xs">Reviewing transcripts, pace, pause ratios, SQL syntax, and logic tracing.</p>
            </div>
          </div>
        ) : suggestions ? (
          <div className="space-y-8">
            {/* 1. Executive Summary */}
            <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 space-y-2">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                <Award className="w-4 h-4 text-blue-400" />
                <span>Executive Summary</span>
              </h4>
              <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                {suggestions.overallSummary || suggestions.overall_summary || feedback?.overall_summary}
              </p>
            </div>

            {/* 2. Key Strengths & Growth Areas */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Key Strengths</span>
                </h4>
                <ul className="space-y-2">
                  {(suggestions.strengths || feedback?.strengths || []).map((st, i) => (
                    <li key={i} className="text-xs text-slate-300 bg-slate-900/40 p-3 rounded-xl border border-slate-800/80 flex items-start space-x-2">
                      <span className="text-emerald-400 font-bold">•</span>
                      <span>{st}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-amber-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <AlertTriangle className="w-4 h-4" />
                  <span>Areas to Improve</span>
                </h4>
                <ul className="space-y-2">
                  {(suggestions.improvementAreas || suggestions.areas_to_improve || feedback?.areas_to_improve || []).map((imp, i) => (
                    <li key={i} className="text-xs text-slate-300 bg-slate-900/40 p-3 rounded-xl border border-slate-800/80 flex items-start space-x-2">
                      <span className="text-amber-400 font-bold">•</span>
                      <span>{imp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* 3. Communication Feedback Breakdown */}
            {suggestions.communicationFeedback && (
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <MessageSquare className="w-4 h-4 text-indigo-400" />
                  <span>Communication & Behavioral Diagnostics</span>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  <div className="bg-slate-900/40 p-3.5 rounded-xl border border-slate-800 space-y-1">
                    <span className="text-[11px] font-semibold text-blue-400 block uppercase">Camera & Eye Contact</span>
                    <p className="text-xs text-slate-300">{suggestions.communicationFeedback.eyeContact}</p>
                  </div>
                  <div className="bg-slate-900/40 p-3.5 rounded-xl border border-slate-800 space-y-1">
                    <span className="text-[11px] font-semibold text-indigo-400 block uppercase">Speaking Rate & Pace</span>
                    <p className="text-xs text-slate-300">{suggestions.communicationFeedback.speakingPace}</p>
                  </div>
                  <div className="bg-slate-900/40 p-3.5 rounded-xl border border-slate-800 space-y-1">
                    <span className="text-[11px] font-semibold text-amber-400 block uppercase">Filler Word Control</span>
                    <p className="text-xs text-slate-300">{suggestions.communicationFeedback.fillerWords}</p>
                  </div>
                  <div className="bg-slate-900/40 p-3.5 rounded-xl border border-slate-800 space-y-1">
                    <span className="text-[11px] font-semibold text-purple-400 block uppercase">Pauses & Cadence</span>
                    <p className="text-xs text-slate-300">{suggestions.communicationFeedback.pauses}</p>
                  </div>
                  <div className="bg-slate-900/40 p-3.5 rounded-xl border border-slate-800 space-y-1 sm:col-span-2 lg:col-span-2">
                    <span className="text-[11px] font-semibold text-emerald-400 block uppercase">Articulation & Clarity</span>
                    <p className="text-xs text-slate-300">{suggestions.communicationFeedback.clarity}</p>
                  </div>
                </div>
              </div>
            )}

            {/* 4. Technical Feedback Items */}
            {suggestions.technicalFeedback && suggestions.technicalFeedback.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <Cpu className="w-4 h-4 text-cyan-400" />
                  <span>Technical Concepts & Architecture Feedback</span>
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {suggestions.technicalFeedback.map((item, idx) => (
                    <div key={idx} className="bg-slate-900/40 p-4 rounded-2xl border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-cyan-400 px-2.5 py-0.5 rounded-md bg-cyan-950/40 border border-cyan-800/40">
                          {item.topic}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        <strong className="text-slate-400">Observation: </strong>{item.observation}
                      </p>
                      <p className="text-xs text-emerald-300 bg-emerald-950/20 p-2 rounded-lg border border-emerald-900/30">
                        <strong className="text-emerald-400">Action: </strong>{item.recommendation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 5. Recommended Study Topics */}
            {suggestions.recommendedTopics && suggestions.recommendedTopics.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <BookOpen className="w-4 h-4 text-emerald-400" />
                  <span>Recommended Topics to Master</span>
                </h4>
                <div className="flex flex-wrap gap-2">
                  {suggestions.recommendedTopics.map((top, idx) => (
                    <span key={idx} className="px-3 py-1.5 rounded-xl bg-slate-900 text-xs font-medium text-slate-200 border border-slate-800 flex items-center space-x-1.5 shadow-sm">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                      <span>{top}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 6. 5-Day Structured Practice Plan */}
            {suggestions.practicePlan && suggestions.practicePlan.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <Calendar className="w-4 h-4 text-purple-400" />
                  <span>5-Day Structured Practice Roadmap</span>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                  {suggestions.practicePlan.map((dayItem) => (
                    <div key={dayItem.day} className="bg-slate-900/50 p-3.5 rounded-2xl border border-slate-800 space-y-2 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                            Day {dayItem.day}
                          </span>
                        </div>
                        <h5 className="text-xs font-semibold text-slate-200 line-clamp-2 mb-2">{dayItem.focus}</h5>
                        <ul className="space-y-1.5 text-[11px] text-slate-400">
                          {dayItem.tasks?.map((task, tIdx) => (
                            <li key={tIdx} className="flex items-start space-x-1.5">
                              <span className="text-purple-400 mt-0.5">›</span>
                              <span className="leading-tight">{task}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 7. Next Interview Goals */}
            {suggestions.nextInterviewGoals && suggestions.nextInterviewGoals.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <Target className="w-4 h-4 text-rose-400" />
                  <span>Goals for Your Next Mock Interview</span>
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {suggestions.nextInterviewGoals.map((goal, idx) => (
                    <div key={idx} className="bg-slate-900/40 p-3 rounded-xl border border-slate-800 flex items-start space-x-2 text-xs text-slate-300">
                      <ArrowRight className="w-3.5 h-3.5 text-rose-400 flex-shrink-0 mt-0.5" />
                      <span>{goal}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-6 text-center space-y-3 bg-slate-900/40 rounded-2xl border border-slate-800">
            <p className="text-xs text-slate-400">No suggestions generated yet for this session.</p>
            <button
              type="button"
              onClick={() => fetchOrGenerateSuggestions(sessionId, true)}
              disabled={suggestionsLoading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-500/25"
            >
              Generate AI Coaching Suggestions
            </button>
          </div>
        )}
      </div>

      {/* Question Breakdown */}
      <div className="glass-card p-8 rounded-3xl border border-slate-800 space-y-4">
        <h3 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
          <FileText className="w-5 h-5 text-blue-400" />
          <span>Question-by-Question Detailed Analysis</span>
        </h3>

        <div className="space-y-3">
          {results.questions?.map((q, i) => {
            const ans = results.answers?.[i];
            const isExpanded = expandedQuestion === i;
            return (
              <div key={q.id} className="bg-slate-900/60 rounded-2xl border border-slate-800 overflow-hidden">
                <button
                  type="button"
                  onClick={() => setExpandedQuestion(isExpanded ? null : i)}
                  className="w-full p-4 text-left flex items-center justify-between hover:bg-slate-800/40 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <span className="w-7 h-7 rounded-lg bg-blue-600/20 text-blue-300 font-bold text-xs flex items-center justify-center">
                      {i + 1}
                    </span>
                    <div>
                      <span className="text-xs font-semibold text-slate-400 uppercase mr-2">[{q.type}] {q.skill}</span>
                      <h4 className="text-sm font-semibold text-slate-200 line-clamp-1">{q.question}</h4>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-bold text-blue-400">{ans ? `${ans.technical_score}/100` : 'N/A'}</span>
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                  </div>
                </button>

                {isExpanded && (
                  <div className="p-4 pt-0 border-t border-slate-800/60 space-y-3">
                    {q.type === 'sql' ? (
                      <div className="space-y-3 pt-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                            <Database className="w-4 h-4 text-indigo-400" />
                            <span>SQL Query Submission</span>
                          </span>
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider flex items-center space-x-1 ${
                            ans?.is_correct 
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' 
                              : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                          }`}>
                            {ans?.is_correct ? <Check className="w-3.5 h-3.5 mr-1" /> : <X className="w-3.5 h-3.5 mr-1" />}
                            {ans?.is_correct ? 'Correct Solution' : 'Incorrect Solution'}
                          </span>
                        </div>

                        {/* Candidate Query */}
                        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs font-mono">
                          <strong className="text-slate-400 block mb-1">Your Submitted SQL:</strong>
                          <pre className="text-indigo-300 whitespace-pre-wrap overflow-x-auto">
                            {ans?.candidate_query || (ans?.transcript && !ans.transcript.includes('SQL Query Submitted') ? ans.transcript : '') || 'No query submitted'}
                          </pre>
                        </div>

                        {/* Expected Query */}
                        {q.expected_query && (
                          <div className="bg-slate-950 p-3 rounded-xl border border-blue-900/40 text-xs font-mono">
                            <strong className="text-blue-400 block mb-1">Expected Reference Query:</strong>
                            <pre className="text-blue-200 whitespace-pre-wrap overflow-x-auto">
                              {q.expected_query}
                            </pre>
                          </div>
                        )}

                        {/* Explanation */}
                        {q.explanation && (
                          <div className="bg-blue-950/20 p-3 rounded-xl border border-blue-900/40 text-xs text-blue-200">
                            <strong>Solution Explanation:</strong>
                            <p className="mt-1">{q.explanation}</p>
                          </div>
                        )}
                      </div>
                    ) : (q.type === 'pseudocode' || q.type === 'pseudocode_mcq' || q.questionType === 'PSEUDOCODE_MCQ' || q.answer_mode === 'mcq') ? (
                      <div className="space-y-3">
                        {/* Result Header Badge */}
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                            <Code className="w-4 h-4 text-purple-400" />
                            <span>Pseudocode MCQ Result</span>
                          </span>
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider flex items-center space-x-1 ${
                            ans?.is_correct 
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' 
                              : (!ans?.selected_option && !ans?.selected_option_id)
                                ? 'bg-slate-800 text-slate-400 border border-slate-700'
                                : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                          }`}>
                            {ans?.is_correct ? <Check className="w-3.5 h-3.5 mr-1" /> : <X className="w-3.5 h-3.5 mr-1" />}
                            {ans?.is_correct ? 'Correct (1/1)' : (!ans?.selected_option && !ans?.selected_option_id) ? 'Not Answered (0/1)' : 'Incorrect (0/1)'}
                          </span>
                        </div>

                        {/* Displayed Pseudocode */}
                        {(q.pseudocode || q.code_snippet) && (
                          <div className="bg-slate-950 p-3 rounded-xl border border-purple-950/60 text-xs font-mono text-purple-200">
                            <strong className="text-slate-400 block mb-1">Pseudocode:</strong>
                            <pre className="whitespace-pre-wrap overflow-x-auto leading-relaxed">
                              {q.pseudocode || q.code_snippet}
                            </pre>
                          </div>
                        )}

                        {/* Displayed Input */}
                        {(q.input || q.input_description) && (
                          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs font-mono">
                            <strong className="text-slate-400 block mb-0.5">Input:</strong>
                            <p className="text-slate-200">{q.input || q.input_description}</p>
                          </div>
                        )}

                        {/* Options List */}
                        {q.options && Array.isArray(q.options) && (
                          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs font-mono space-y-1.5">
                            <strong className="text-slate-400 block mb-1">Options:</strong>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                              {q.options.map((opt) => {
                                const optId = typeof opt === 'object' ? opt.id : opt;
                                const optText = typeof opt === 'object' ? opt.text : opt;
                                const corrOpt = q.correctOptionId || q.correct_option_id || q.correct_answer;
                                const isCorr = String(optId).toLowerCase() === String(corrOpt).toLowerCase();
                                const isUserSel = String(optId).toLowerCase() === String(ans?.selected_option || ans?.selected_option_id).toLowerCase();

                                return (
                                  <div
                                    key={optId}
                                    className={`p-2 rounded-lg border flex items-center justify-between text-xs ${
                                      isCorr
                                        ? 'bg-emerald-950/30 border-emerald-500/50 text-emerald-300 font-semibold'
                                        : isUserSel && !isCorr
                                        ? 'bg-rose-950/30 border-rose-500/50 text-rose-300'
                                        : 'bg-slate-900/60 border-slate-800 text-slate-400'
                                    }`}
                                  >
                                    <span>
                                      <strong>{optId}.</strong> {optText}
                                    </span>
                                    <div className="flex items-center space-x-1">
                                      {isUserSel && (
                                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                                          Your Choice
                                        </span>
                                      )}
                                      {isCorr && (
                                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                          Correct
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* Selected vs Correct Summary */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                          <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                            <span className="text-slate-400 block text-[10px] uppercase font-bold">Candidate Selected:</span>
                            <span className={`font-mono font-medium ${ans?.is_correct ? 'text-emerald-400' : ans?.selected_option ? 'text-rose-400' : 'text-slate-400 italic'}`}>
                              {ans?.selected_option || ans?.selected_option_id 
                                ? `${ans?.selected_option || ans?.selected_option_id}${ans?.selected_option_text ? ` (${ans.selected_option_text})` : ''}` 
                                : 'Not answered'}
                            </span>
                          </div>
                          <div className="bg-slate-950 p-2.5 rounded-xl border border-emerald-900/40">
                            <span className="text-emerald-400 block text-[10px] uppercase font-bold">Correct Answer:</span>
                            <span className="font-mono text-emerald-300 font-medium">
                              {q.correctOptionId || q.correct_option_id || q.correct_answer || 'N/A'}
                            </span>
                          </div>
                        </div>

                        {/* Explanation */}
                        {q.explanation && (
                          <div className="bg-purple-950/20 p-3 rounded-xl border border-purple-900/40 text-xs text-purple-200">
                            <strong>Explanation:</strong>
                            <p className="mt-1 leading-relaxed">{q.explanation}</p>
                          </div>
                        )}
                      </div>
                    ) : (
                      <>
                        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs text-slate-300 font-mono">
                          <strong className="text-slate-400 block mb-1">
                            Candidate Answer Transcript:
                          </strong>
                          <p className="mt-1 whitespace-pre-wrap leading-relaxed">
                            {ans?.transcript && ans.transcript.trim() && !ans.transcript.startsWith('-- Write your MySQL query')
                              ? ans.transcript
                              : 'No response recorded'}
                          </p>
                        </div>
                        {q.ideal_answer && (
                          <div className="bg-blue-950/20 p-3 rounded-xl border border-blue-900/40 text-xs text-blue-200">
                            <strong>Expected Concepts & Ideal Answer:</strong>
                            <p className="mt-1">{q.ideal_answer}</p>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Video Modal */}
      {showVideoModal && (
        <VideoReplayModal
          sessionId={sessionId}
          isOpen={true}
          onClose={() => setShowVideoModal(false)}
          onConsumed={() => setResults((prev) => ({ ...prev, video_available: false }))}
        />
      )}
    </div>
  );
};

export default ResultsPage;
