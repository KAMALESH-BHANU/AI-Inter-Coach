import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Bot, User, LogOut, LayoutDashboard, History, PlayCircle } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';
  const showAuthenticatedMenu = user && !isAuthPage;
  const isActive = (path) => location.pathname === path;

  return (
    <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-3">
            <div className="p-2 bg-blue-600 rounded-xl text-white shadow-lg shadow-blue-500/20">
              <Bot className="w-6 h-6" />
            </div>
            <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-blue-400 to-indigo-300 bg-clip-text text-transparent">
              AI INTERVIEW COACH
            </span>
          </Link>

          {showAuthenticatedMenu ? (
            <div className="flex items-center space-x-6">
              <Link
                to="/dashboard"
                className={`flex items-center space-x-2 text-sm font-medium transition-colors ${
                  isActive('/dashboard') ? 'text-blue-400' : 'text-slate-300 hover:text-white'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </Link>
              <Link
                to="/interview/setup"
                className={`flex items-center space-x-2 text-sm font-medium transition-colors ${
                  isActive('/interview/setup') ? 'text-blue-400' : 'text-slate-300 hover:text-white'
                }`}
              >
                <PlayCircle className="w-4 h-4" />
                <span>Start Interview</span>
              </Link>
              <Link
                to="/history"
                className={`flex items-center space-x-2 text-sm font-medium transition-colors ${
                  isActive('/history') ? 'text-blue-400' : 'text-slate-300 hover:text-white'
                }`}
              >
                <History className="w-4 h-4" />
                <span>History</span>
              </Link>
              
              <div className="flex items-center space-x-3 pl-4 border-l border-slate-800">
                <div className="flex items-center space-x-2 text-sm font-medium text-slate-200">
                  <div className="w-8 h-8 rounded-full bg-blue-600/30 border border-blue-500/40 flex items-center justify-center text-blue-400">
                    <User className="w-4 h-4" />
                  </div>
                  <span>{user.full_name}</span>
                </div>
                <button
                  onClick={() => { logout(); navigate('/login'); }}
                  className="p-2 text-slate-400 hover:text-rose-400 transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center space-x-4">
              {location.pathname !== '/login' && (
                <Link
                  to="/login"
                  className="text-sm font-medium text-slate-300 hover:text-white transition-colors"
                >
                  Sign In
                </Link>
              )}
              {location.pathname !== '/register' && (
                <Link
                  to="/register"
                  className="text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl transition-all shadow-lg shadow-blue-500/20"
                >
                  Get Started
                </Link>
              )}
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
