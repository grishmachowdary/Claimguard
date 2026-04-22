import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000, // 30s timeout
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Global response interceptor — handle 401 and errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // JWT expired or invalid — clear and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('claim_id');
      localStorage.removeItem('insurance_type');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const register    = (data)    => api.post('/auth/register', data);
export const login       = (data)    => api.post('/auth/login', data);
export const getMe       = ()        => api.get('/auth/me');

export const getInsuranceTypes    = ()           => api.get('/insurance-types');
export const getRules             = (type)       => api.get(`/rules/${type}`);
export const getClaims            = (page=1)     => api.get(`/claims?page=${page}`);
export const createClaim          = (data)       => api.post('/claims', data);
export const updateClaim          = (id, data)   => api.put(`/claims/${id}`, data);
export const validateClaim        = (id)         => api.post(`/claims/${id}/validate`);
export const getClaimReport       = (id)         => api.get(`/claims/${id}/report`);
export const getClaimQR           = (id)         => api.get(`/claims/${id}/qr`);
export const getInsuranceCompanies= (type)       => api.get(`/insurance-companies?type=${type || ''}`);
export const submitToInsurer      = (id, data)   => api.post(`/claims/${id}/submit`, data);
export const getApprovedNetwork   = (type, city, claimId) => api.get(`/network/${type}?city=${city||''}&claim_id=${claimId||''}`);
export const analyzeDocuments     = (id)         => api.post(`/claims/${id}/analyze`);
export const downloadPackage      = (id)         => `${API_BASE_URL}/claims/${id}/package`;
export const getClaimStatus       = (id)         => api.get(`/claims/${id}/status`);
export const updateClaimStatus    = (id, data)   => api.put(`/claims/${id}/status`, data);
export const getClaimDeadline     = (id)         => api.get(`/claims/${id}/deadline`);
export const getClaimComparison   = (id)         => api.get(`/claims/${id}/comparison`);

export default api;
