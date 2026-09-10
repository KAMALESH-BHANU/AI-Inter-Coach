import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { interviewAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { PlayCircle, Award, MessageSquare, Code, TrendingUp, Calendar, ChevronRight } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

const DashboardPage = () => {
  const { user } = useAuth();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await interviewAPI.getUserHistory();
        setHistory(res.data);
      } catch (err) {
        console.error('Failed to load interview history:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const totalInterviews = history.length;
  const avgOverall = totalInterviews > 0
    ? Math.round(history.reduce((acc, curr) => acc + curr.overall_score, 0) / totalInterviews)
    : 0;
  const avgTech = totalInterviews > 0
    ? Math.round(history.reduce((acc, curr) => acc + curr.technical_score, 0) / totalInterviews)
    : 0;
  const avgComm = totalInterviews > 0
    ? Math.round(history.reduce((acc, curr) => acc + curr.communication_score, 0) / totalInterviews)
    : 0;

  const chartData = history.slice(0, 7).reverse().map((item, idx) => ({
    name: `Session ${idx + 1}`,
    Overall: item.overall_score,
    Technical: item.technical_score,
    Communication: item.communication_score,
  }));

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-16">
      {/* Header Banner */}
      <div className="glass-card p-8 rounded-3xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold text-slate-100">
            Welcome back, <span className="text-blue-400">{user?.full_name}</span> 👋
          </h1>
          <p className="text-slate-400 text-sm">
            Track your interview performance metrics, technical score trends, and speech fluency.
          </p>
        </div>
        <Link
          to="/interview/setup"
          className="inline-flex items-center space-x-2 px-6 py-3.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-2xl transition-all shadow-lg shadow-blue-500/25 flex-shrink-0"
        >
          <PlayCircle className="w-5 h-5" />
          <span>Start New Interview</span>
        </Link>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Total Mock Sessions</span>
            <Calendar className="w-5 h-5 text-blue-400" />
          </div>
          <span className="text-3xl font-extrabold text-slate-100">{totalInterviews}</span>
        </div>

        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Avg Overall Score</span>
            <Award className="w-5 h-5 text-amber-400" />
          </div>
          <span className="text-3xl font-extrabold text-blue-400">{avgOverall}<small className="text-sm font-normal text-slate-400">/100</small></span>
        </div>

        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Avg Technical Score</span>
            <Code className="w-5 h-5 text-emerald-400" />
          </div>
          <span className="text-3xl font-extrabold text-emerald-400">{avgTech}<small className="text-sm font-normal text-slate-400">/100</small></span>
        </div>

        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Avg Communication</span>
            <MessageSquare className="w-5 h-5 text-indigo-400" />
          </div>
          <span className="text-3xl font-extrabold text-indigo-400">{avgComm}<small className="text-sm font-normal text-slate-400">/100</small></span>
        </div>
      </div>

      {/* Score Trend Chart */}
      {chartData.length > 0 && (
        <div className="glass-card p-6 rounded-3xl border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-bold text-slate-100">Score Improvement Trend</h3>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis domain={[0, 100]} stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }} />
                <Bar dataKey="Overall" fill="#3b82f6" radius={[6, 6, 0, 0]} />
                <Bar dataKey="Technical" fill="#10b981" radius={[6, 6, 0, 0]} />
                <Bar dataKey="Communication" fill="#818cf8" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Recent Interviews Table */}
      <div className="glass-card p-6 rounded-3xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-100">Recent Interview Sessions</h3>
          <Link to="/history" className="text-xs font-semibold text-blue-400 hover:underline flex items-center space-x-1">
            <span>View All History</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>

        {loading ? (
          <div className="text-center py-8 text-slate-400 text-sm">Loading interview history...</div>
        ) : history.length === 0 ? (
          <div className="text-center py-12 space-y-3">
            <p className="text-slate-400 text-sm">You haven't completed any mock interviews yet.</p>
            <Link
              to="/interview/setup"
              className="inline-block px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl"
            >
              Start First Mock Interview
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {history.slice(0, 5).map((session) => (
              <div key={session.session_id} className="py-4 flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-semibold text-slate-200">
                      Session #{session.session_id.substring(0, 8)}
                    </span>
                    <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-600/20 text-blue-300 border border-blue-500/30">
                      {session.state}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Skills: {session.skills?.join(', ') || 'General'}
                  </p>
                </div>

                <div className="flex items-center space-x-6">
                  <div className="text-right">
                    <span className="text-xs text-slate-400 block">Overall Score</span>
                    <span className="text-base font-bold text-blue-400">{session.overall_score}/100</span>
                  </div>
                  <Link
                    to={`/interview/${session.session_id}/results`}
                    className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold transition-colors"
                  >
                    View Report
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

export default DashboardPage;
