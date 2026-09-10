import React from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Mail, Code, ShieldCheck } from 'lucide-react';

const ProfilePage = () => {
  const { user } = useAuth();

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      <div className="flex items-center space-x-3">
        <div className="p-3 bg-blue-600/20 text-blue-400 rounded-2xl">
          <User className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Candidate Profile</h1>
          <p className="text-xs text-slate-400">Account settings and technical preferences</p>
        </div>
      </div>

      <div className="glass-card p-8 rounded-3xl border border-slate-800 space-y-6">
        <div className="flex items-center space-x-4 border-b border-slate-800 pb-6">
          <div className="w-16 h-16 rounded-2xl bg-blue-600/30 border border-blue-500/40 flex items-center justify-center text-blue-400 text-2xl font-bold">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-100">{user?.full_name}</h2>
            <p className="text-sm text-slate-400 flex items-center space-x-1.5 mt-0.5">
              <Mail className="w-4 h-4 text-slate-500" />
              <span>{user?.email}</span>
            </p>
          </div>
        </div>

        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
            <Code className="w-4 h-4 text-blue-400" />
            <span>Primary Technical Skills</span>
          </h3>
          <div className="flex flex-wrap gap-2">
            {user?.skills?.length > 0 ? (
              user.skills.map((skill) => (
                <span key={skill} className="px-3 py-1 bg-blue-600/20 text-blue-300 text-xs font-medium rounded-lg border border-blue-500/30">
                  {skill}
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-400 italic">No skills selected yet.</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
