import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { interviewAPI } from '../services/api';
import { History, Calendar, ChevronRight, Award } from 'lucide-react';

const HistoryPage = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await interviewAPI.getUserHistory();
        setHistory(res.data);
      } catch (err) {
        console.error('Failed to fetch history:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      <div className="flex items-center space-x-3">
        <div className="p-3 bg-blue-600/20 text-blue-400 rounded-2xl">
          <History className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Interview History & Evaluation Logs</h1>
          <p className="text-xs text-slate-400">Review all your previous mock interview sessions and scores</p>
        </div>
      </div>

      <div className="glass-card p-6 rounded-3xl border border-slate-800">
        {loading ? (
          <div className="text-center py-12 text-slate-400 text-sm">Loading interview history logs...</div>
        ) : history.length === 0 ? (
          <div className="text-center py-16 space-y-4">
            <p className="text-slate-400 text-sm">No interview records found.</p>
            <Link
              to="/interview/setup"
              className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl text-xs"
            >
              Start First Interview
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {history.map((session) => (
              <div key={session.session_id} className="py-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-3">
                    <span className="text-base font-bold text-slate-100">
                      Session #{session.session_id.substring(0, 8)}
                    </span>
                    <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-blue-600/20 text-blue-300 border border-blue-500/30">
                      {session.state}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 flex items-center space-x-2">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{new Date(session.date).toLocaleDateString()}</span>
                    <span>•</span>
                    <span>Skills: {session.skills?.join(', ')}</span>
                  </p>
                </div>

                <div className="flex items-center space-x-6">
                  <div className="text-right">
                    <span className="text-xs text-slate-400 block">Overall Score</span>
                    <span className="text-lg font-bold text-blue-400">{session.overall_score}/100</span>
                  </div>
                  <Link
                    to={`/interview/${session.session_id}/results`}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold transition-all flex items-center space-x-1"
                  >
                    <span>View Report</span>
                    <ChevronRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryPage;
