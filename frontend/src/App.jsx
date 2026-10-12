import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './layouts/Layout';
import Dashboard from './pages/Dashboard';
import MicroZones from './pages/MicroZones';
import PredictionHistory from './pages/PredictionHistory';
import Reports from './pages/Reports';
import DatasetStatus from './pages/DatasetStatus';
import AuthorityAlerts from './pages/AuthorityAlerts';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="zones" element={<MicroZones />} />
          <Route path="predictions" element={<PredictionHistory />} />
          <Route path="alerts" element={<AuthorityAlerts />} />
          <Route path="reports" element={<Reports />} />
          <Route path="datasets" element={<DatasetStatus />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
