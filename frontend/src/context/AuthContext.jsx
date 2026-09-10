import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      if (token) {
        try {
          const res = await authAPI.getMe();
          setUser(res.data);
        } catch (err) {
          console.error('Failed to fetch user profile:', err);
          logout();
        }
      }
      setLoading(false);
    };
    fetchUser();
  }, [token]);

  const login = async (email, password) => {
    const res = await authAPI.login({ email, password });
    const { access_token, user_id, full_name } = res.data;
    localStorage.setItem('token', access_token);
    setToken(access_token);
    setUser({ id: user_id, email, full_name, skills: [] });
    return res.data;
  };

  const register = async (email, full_name, password, skills) => {
    const res = await authAPI.register({ email, full_name, password, skills });
    const { access_token, user_id } = res.data;
    localStorage.setItem('token', access_token);
    setToken(access_token);
    setUser({ id: user_id, email, full_name, skills });
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
