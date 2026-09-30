import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
};

export const resumeAPI = {
  upload: (formData) => api.post('/resume/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
};

export const questionAPI = {
  getSkills: (search) => api.get('/questions/skills', { params: { search } }),
  getCategories: () => api.get('/questions/skills/categories'),
};

export const interviewAPI = {
  create: (data) => api.post('/interview/create', data),
  getSession: (id) => api.get(`/interview/${id}`),
  saveAnswer: (id, data) => api.post(`/interview/${id}/answer`, data),
  complete: (id) => api.post(`/interview/${id}/complete`),
  runSql: (sessionId, questionId, query) => api.post('/interview/sql/run', {
    session_id: sessionId,
    question_id: questionId,
    query: query
  }),
  getResults: (id) => api.get(`/interview/${id}/results`),
  getSuggestions: (id) => api.get(`/interview/${id}/suggestions`),
  generateSuggestions: (id, force = false) => api.post(`/interview/${id}/suggestions`, { force_regenerate: force }),
  uploadVideo: (id, formData) => api.post(`/interview/${id}/upload-video`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deleteVideo: (id) => api.post(`/interview/${id}/delete-video`),
  getVideoUrl: (id) => `http://localhost:8000/api/interview/${id}/video`,
  getUserHistory: () => api.get('/interview/history/user'),
  downloadPDF: (id) => api.get(`/interview/${id}/pdf`, { responseType: 'blob' }),
  getPDFUrl: (id) => `http://localhost:8000/api/interview/${id}/pdf`,
};

export default api;
