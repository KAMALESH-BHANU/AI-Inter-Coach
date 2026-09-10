import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Bot, Cpu, Eye, Sparkles, FileText, CheckCircle2, ArrowRight, ShieldCheck } from 'lucide-react';

const LandingPage = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-24 pb-20">
      {/* Hero Section */}
      <section className="relative pt-16 text-center space-y-8 max-w-4xl mx-auto px-4">
        <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-blue-600/10 border border-blue-500/30 text-blue-400 text-sm font-medium">
          <Sparkles className="w-4 h-4" />
          <span>Real-Time AI Mock Interviews & Analytics</span>
        </div>

        <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight leading-tight">
          Master Tech Interviews with <br />
          <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
            Real-Time AI Vision & Speech Analysis
          </span>
        </h1>

        <p className="text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Simulate realistic software engineering interviews. Practice coding, system design, and technical project questions with instant AI feedback on speech fluency, eye contact, and technical depth.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          {user ? (
            <>
              <Link
                to="/dashboard"
                className="w-full sm:w-auto px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-2xl transition-all shadow-xl shadow-blue-500/25 flex items-center justify-center space-x-2"
              >
                <span>Go to Dashboard</span>
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to="/interview/setup"
                className="w-full sm:w-auto px-8 py-4 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-2xl transition-all border border-slate-700"
              >
                Start New Interview
              </Link>
            </>
          ) : (
            <>
              <Link
                to="/register"
                className="w-full sm:w-auto px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-2xl transition-all shadow-xl shadow-blue-500/25 flex items-center justify-center space-x-2"
              >
                <span>Start Free Mock Interview</span>
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to="/login"
                className="w-full sm:w-auto px-8 py-4 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-2xl transition-all border border-slate-700"
              >
                Sign In to Account
              </Link>
            </>
          )}
        </div>
      </section>

      {/* Feature Grid */}
      <section className="max-w-7xl mx-auto px-4 grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="glass-card glass-card-hover p-8 rounded-3xl space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Cpu className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-slate-100">10-Question Structured Mock</h3>
          <p className="text-slate-400 text-sm leading-relaxed">
            Strict distribution of 3 project architecture questions, 5 technical concept questions, and 2 code output prediction questions tailored to your skills.
          </p>
        </div>

        <div className="glass-card glass-card-hover p-8 rounded-3xl space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Eye className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-slate-100">Real-Time Camera & Audio</h3>
          <p className="text-slate-400 text-sm leading-relaxed">
            Measures Eye Contact %, filler word rate (um, uh, like), Words-Per-Minute, and facial posture in real-time at controlled 5–10 FPS.
          </p>
        </div>

        <div className="glass-card glass-card-hover p-8 rounded-3xl space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-purple-600/20 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <FileText className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-slate-100">Gemini LLM Feedback & PDF</h3>
          <p className="text-slate-400 text-sm leading-relaxed">
            Receive personalized qualitative strengths and weakness breakdowns powered by Gemini, plus downloadable evaluation PDF reports.
          </p>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
