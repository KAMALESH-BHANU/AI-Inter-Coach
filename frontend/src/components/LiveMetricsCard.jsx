import React from 'react';
import { Eye, Gauge, MessageSquareX, PauseCircle } from 'lucide-react';

const LiveMetricsCard = ({ 
  eyeContactPct = -1, 
  wpm = 0, 
  fillerCount = 0, 
  averagePauseSec = 0.0 
}) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full">
      {/* 1. Eye Contact Card */}
      <div className="glass-card p-4 rounded-2xl border border-slate-800/90 bg-slate-900/60 shadow-lg hover:border-slate-700 transition-all flex items-center space-x-3.5">
        <div className="p-3 bg-blue-500/15 text-blue-400 rounded-xl border border-blue-500/25 flex-shrink-0">
          <Eye className="w-5 h-5" />
        </div>
        <div className="min-w-0 flex-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block truncate">
            Eye Contact
          </span>
          <div className="text-xl font-extrabold text-slate-100 leading-tight">
            {eyeContactPct < 0 ? (
              <span className="text-xs font-semibold text-slate-400 animate-pulse">Calculating...</span>
            ) : (
              `${eyeContactPct}%`
            )}
          </div>
          <span className="text-[10px] text-blue-400 font-medium block truncate">
            {eyeContactPct >= 75 ? '● Optimal' : eyeContactPct >= 50 ? '● Moderate' : '● Focus Camera'}
          </span>
        </div>
      </div>

      {/* 2. Speaking Rate (Pacing) Card */}
      <div className="glass-card p-4 rounded-2xl border border-slate-800/90 bg-slate-900/60 shadow-lg hover:border-slate-700 transition-all flex items-center space-x-3.5">
        <div className="p-3 bg-indigo-500/15 text-indigo-400 rounded-xl border border-indigo-500/25 flex-shrink-0">
          <Gauge className="w-5 h-5" />
        </div>
        <div className="min-w-0 flex-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block truncate">
            Speaking Rate
          </span>
          <div className="text-xl font-extrabold text-slate-100 leading-tight flex items-baseline space-x-1">
            <span>{wpm || 0}</span>
            <span className="text-xs font-normal text-slate-400">WPM</span>
          </div>
          <span className="text-[10px] text-indigo-400 font-medium block truncate">
            {wpm >= 110 && wpm <= 160 ? '● Ideal Pace' : wpm > 160 ? '● Fast Pace' : '● Steady Pace'}
          </span>
        </div>
      </div>

      {/* 3. Filler Words Card */}
      <div className="glass-card p-4 rounded-2xl border border-slate-800/90 bg-slate-900/60 shadow-lg hover:border-slate-700 transition-all flex items-center space-x-3.5">
        <div className="p-3 bg-amber-500/15 text-amber-400 rounded-xl border border-amber-500/25 flex-shrink-0">
          <MessageSquareX className="w-5 h-5" />
        </div>
        <div className="min-w-0 flex-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block truncate">
            Filler Words
          </span>
          <div className="text-xl font-extrabold text-slate-100 leading-tight">
            {fillerCount}
          </div>
          <span className="text-[10px] text-amber-400 font-medium block truncate">
            {fillerCount === 0 ? '● Clean' : fillerCount <= 3 ? '● Low' : '● Frequent'}
          </span>
        </div>
      </div>

      {/* 4. Avg Pause Card */}
      <div className="glass-card p-4 rounded-2xl border border-slate-800/90 bg-slate-900/60 shadow-lg hover:border-slate-700 transition-all flex items-center space-x-3.5">
        <div className="p-3 bg-emerald-500/15 text-emerald-400 rounded-xl border border-emerald-500/25 flex-shrink-0">
          <PauseCircle className="w-5 h-5" />
        </div>
        <div className="min-w-0 flex-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block truncate">
            Avg Pause
          </span>
          <div className="text-xl font-extrabold text-slate-100 leading-tight flex items-baseline space-x-1">
            <span>{typeof averagePauseSec === 'number' ? averagePauseSec.toFixed(1) : averagePauseSec}</span>
            <span className="text-xs font-normal text-slate-400">s</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-medium block truncate">
            {averagePauseSec > 0 && averagePauseSec <= 2.5 ? '● Natural' : averagePauseSec > 2.5 ? '● Long' : '● Active Flow'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default LiveMetricsCard;
