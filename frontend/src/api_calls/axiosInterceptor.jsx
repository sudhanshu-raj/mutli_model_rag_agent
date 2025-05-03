import axios from 'axios';
import {API_BASE_URL} from './apiConfig'; // Adjust the import path as necessary

const getSecretKey = () => {
  const userData = JSON.parse(localStorage.getItem('userData'));
  return userData?.value?.secret_key;
};

const api = axios.create({
  baseURL: API_BASE_URL, // Update to your actual Flask backend URL
});

// Request interceptor to add secret key to headers
api.interceptors.request.use((config) => {
  const secretKey = getSecretKey();
  const excludedPaths = ['/auth/validate'];

  // Skip adding the header if the URL is excluded
  if (secretKey && !excludedPaths.some(path => config.url.includes(path))) {
    config.headers['X-Secret-Key'] = secretKey;
  }

  return config;
}, (error) => {
  return Promise.reject(error);
});

export default api;
