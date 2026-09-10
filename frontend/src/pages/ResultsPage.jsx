import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { interviewAPI } from '../services/api';
import VideoReplayModal from '../components/VideoReplayModal';
import {
  Award, CheckCircle2, AlertTriangle, Download, RefreshCw, Play, ShieldCheck, FileText, ChevronDown, ChevronUp
} from 'lucide-react';

const ResultsPage = () => {
  const { sessionId } = useParams();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [showVideoModal, setShowVideoModal] = useState(false);
  const [expandedQuestion, setExpandedQuestion] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const res = await interviewAPI.getResults(sessionId);
        setResults(res.data);
      } catch (err) {
        console.error('Failed to fetch results:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, [sessionId]);

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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card p-5 rounded-2xl border border-blue-500/30 bg-blue-950/20 text-center space-y-1">
          <span className="text-xs font-semibold text-blue-300 uppercase">Overall Score</span>
          <p className="text-3xl font-black text-blue-400">{scores.overall_score}/100</p>
        </div>
        <div className="glass-card p-5 rounded-2xl border border-slate-800 text-center space-y-1">
          <span className="text-xs font-semibold text-slate-400 uppercase">Technical Knowledge</span>
          <p className="text-3xl font-black text-slate-100">{scores.technical_knowledge}/100</p>
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

      {/* AI Qualitative Feedback Card */}
      {feedback && (
        <div className="glass-card p-8 rounded-3xl border border-slate-800 space-y-6">
          <div className="flex items-center space-x-3">
            <Award className="w-6 h-6 text-blue-400" />
            <h3 className="text-lg font-bold text-slate-100">AI Qualitative Feedback & Coaching</h3>
          </div>

          <p className="text-sm text-slate-300 leading-relaxed bg-slate-900/60 p-4 rounded-2xl border border-slate-800">
            {feedback.overall_summary}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4" />
                <span>Key Strengths</span>
              </h4>
              <ul className="space-y-2">
                {feedback.strengths?.map((st, i) => (
                  <li key={i} className="text-xs text-slate-300 bg-slate-900/40 p-2.5 rounded-xl border border-slate-800">
                    • {st}
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
                {feedback.areas_to_improve?.map((imp, i) => (
                  <li key={i} className="text-xs text-slate-300 bg-slate-900/40 p-2.5 rounded-xl border border-slate-800">
                    • {imp}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

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
                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs text-slate-300 font-mono">
                      <strong>Candidate Answer Transcript:</strong>
                      <p className="mt-1">{ans?.transcript || 'No response recorded'}</p>
                    </div>
                    {q.ideal_answer && (
                      <div className="bg-blue-950/20 p-3 rounded-xl border border-blue-900/40 text-xs text-blue-200">
                        <strong>Expected Concepts & Ideal Answer:</strong>
                        <p className="mt-1">{q.ideal_answer}</p>
                      </div>
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
