import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const register    = (data)    => api.post('/auth/register', data);
export const login       = (data)    => api.post('/auth/login', data);
export const getMe       = ()        => api.get('/auth/me');

export const getInsuranceTypes    = ()           => api.get('/insurance-types');
export const getRules             = (type)       => api.get(`/rules/${type}`);
export const getClaims            = ()           => api.get('/claims');
export const createClaim          = (data)       => api.post('/claims', data);
export const updateClaim          = (id, data)   => api.put(`/claims/${id}`, data);
export const validateClaim        = (id)         => api.post(`/claims/${id}/validate`);
export const getClaimReport       = (id)         => api.get(`/claims/${id}/report`);
export const getClaimQR           = (id)         => api.get(`/claims/${id}/qr`);
export const getInsuranceCompanies= (type)       => api.get(`/insurance-companies?type=${type || ''}`);
export const submitToInsurer      = (id, data)   => api.post(`/claims/${id}/submit`, data);
export const getApprovedNetwork   = (type, city, claimId) => api.get(`/network/${type}?city=${city||''}&claim_id=${claimId||''}`);
export const analyzeDocuments     = (id)         => api.post(`/claims/${id}/analyze`);
export const downloadPackage      = (id)         => `http://localhost:5000/api/claims/${id}/package`;
export const getClaimStatus       = (id)         => api.get(`/claims/${id}/status`);
export const updateClaimStatus    = (id, data)   => api.put(`/claims/${id}/status`, data);

export default api;
