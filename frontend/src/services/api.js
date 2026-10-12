import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const customError = {
      message: error.response?.data?.error || error.message || 'An unexpected network error occurred',
      status: error.response?.status,
      data: error.response?.data,
    };
    return Promise.reject(customError);
  }
);

export const apiService = {
  // Health
  getHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  // Dashboard
  getDashboardSummary: async () => {
    const res = await apiClient.get('/dashboard/summary');
    return res.data;
  },

  // Micro-Zones
  getZones: async (params = {}) => {
    const res = await apiClient.get('/zones', { params });
    return res.data;
  },

  getZoneById: async (zoneId) => {
    const res = await apiClient.get(`/zones/${zoneId}`);
    return res.data;
  },

  getZoneHistory: async (zoneId, params = {}) => {
    const res = await apiClient.get(`/zones/${zoneId}/history`, { params });
    return res.data;
  },

  syncZoneLiveWeather: async (zoneId) => {
    const res = await apiClient.post(`/zones/${zoneId}/sync-live`, {});
    return res.data;
  },

  syncAllZonesLiveWeather: async () => {
    const res = await apiClient.post('/zones/sync-live-all', {});
    return res.data;
  },

  // Predictions
  getPredictions: async (params = {}) => {
    const res = await apiClient.get('/predictions', { params });
    return res.data;
  },

  getPredictionById: async (predictionId) => {
    const res = await apiClient.get(`/predictions/${predictionId}`);
    return res.data;
  },

  runPrediction: async (zoneId, horizonHours = 24) => {
    const res = await apiClient.post('/predictions/run', {
      zone_id: zoneId,
      horizon_hours: horizonHours,
    });
    return res.data;
  },

  runBatchPredictions: async () => {
    const res = await apiClient.post('/predictions/batch');
    return res.data;
  },

  simulateScenario: async (scenario = 'storm_surge') => {
    const res = await apiClient.post('/predictions/simulate-scenario', { scenario });
    return res.data;
  },

  // Datasets
  getDatasetStatus: async () => {
    const res = await apiClient.get('/datasets/status');
    return res.data;
  },

  validateDataset: async (formData) => {
    const res = await apiClient.post('/datasets/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  importDataset: async (formData) => {
    const res = await apiClient.post('/datasets/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  // Reports
  getReportsSummary: async (params = {}) => {
    const res = await apiClient.get('/reports/summary', { params });
    return res.data;
  },

  getExportCsvUrl: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return `${API_BASE_URL}/reports/export${query ? `?${query}` : ''}`;
  },

  // Authority Alerts
  getAlerts: async (params = {}) => {
    const res = await apiClient.get('/alerts', { params });
    return res.data;
  },

  getAuthorities: async () => {
    const res = await apiClient.get('/alerts/authorities');
    return res.data;
  },

  getAlertsSummary: async () => {
    const res = await apiClient.get('/alerts/summary');
    return res.data;
  },

  broadcastDrill: async (zoneId, authorityCode = null) => {
    const res = await apiClient.post('/alerts/broadcast', {
      zone_id: zoneId,
      authority_code: authorityCode,
    });
    return res.data;
  },

  sendEmailAlert: async (zoneId, recipientEmail) => {
    const res = await apiClient.post('/alerts/send-email', {
      zone_id: zoneId,
      recipient_email: recipientEmail,
    });
    return res.data;
  },

  getEmailPreview: async (zoneId) => {
    const res = await apiClient.get('/alerts/email-preview', {
      params: { zone_id: zoneId }
    });
    return res.data;
  },

  // SMTP Configuration
  getSmtpConfig: async () => {
    const res = await apiClient.get('/alerts/smtp-config');
    return res.data;
  },

  saveSmtpConfig: async (config) => {
    const res = await apiClient.post('/alerts/smtp-config', config);
    return res.data;
  },

  testSmtpConnection: async (data) => {
    const res = await apiClient.post('/alerts/test-smtp', data);
    return res.data;
  },

  // Pan-India Geo-Locations
  seedPanIndiaZones: async () => {
    const res = await apiClient.post('/zones/seed-pan-india', {});
    return res.data;
  },

  addCustomLocation: async (locationData) => {
    const res = await apiClient.post('/zones/add-custom', locationData);
    return res.data;
  },
};

export default apiService;
