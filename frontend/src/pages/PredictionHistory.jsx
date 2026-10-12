import React, { useState, useEffect } from 'react';
import {
  History, Filter, Download, ChevronLeft, ChevronRight,
  Eye, RefreshCw, X, ShieldAlert, Cpu
} from 'lucide-react';
import apiService from '../services/api';
import RiskBadge from '../components/RiskBadge';

export default function PredictionHistory() {
  const [predictions, setPredictions] = useState([]);
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedZoneId, setSelectedZoneId] = useState('');
  const [selectedRiskCategory, setSelectedRiskCategory] = useState('');
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState({ total: 0, pages: 1 });
  const [detailModal, setDetailModal] = useState(null);

  const fetchPredictions = async () => {
    setLoading(true);
    try {
      const params = { page, per_page: 15 };
      if (selectedZoneId) params.zone_id = selectedZoneId;
      if (selectedRiskCategory) params.risk_category = selectedRiskCategory;

      const [predRes, zonesRes] = await Promise.all([
        apiService.getPredictions(params),
        apiService.getZones({ per_page: 100 })
      ]);

      setPredictions(predRes.predictions || []);
      setPagination(predRes.pagination || { total: 0, pages: 1 });
      setZones(zonesRes.zones || []);
    } catch (err) {
      alert(`Error loading predictions: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, [page, selectedZoneId, selectedRiskCategory]);

  const handleExportCsv = () => {
    const params = {};
    if (selectedZoneId) params.zone_id = selectedZoneId;
    if (selectedRiskCategory) params.risk_category = selectedRiskCategory;
    const url = apiService.getExportCsvUrl(params);
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-md">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Prediction History</h1>
          <p className="text-xs text-slate-400 mt-1">
            Historical audit log of model predictions stored in Neon PostgreSQL
          </p>
        </div>

        <button
          onClick={handleExportCsv}
          className="flex items-center gap-2 px-4 py-2.5 bg-emerald-700 hover:bg-emerald-600 text-white rounded-xl text-xs font-semibold shadow-lg shadow-emerald-950 transition cursor-pointer"
        >
          <Download className="h-4 w-4" />
          <span>Export History to CSV</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-300">Filter Records:</span>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400">Zone:</label>
          <select
            value={selectedZoneId}
            onChange={(e) => { setSelectedZoneId(e.target.value); setPage(1); }}
            className="bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-sky-500"
          >
            <option value="">All Zones</option>
            {zones.map((z) => (
              <option key={z.id} value={z.id}>
                {z.zone_code} - {z.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400">Hazard Tier:</label>
          <select
            value={selectedRiskCategory}
            onChange={(e) => { setSelectedRiskCategory(e.target.value); setPage(1); }}
            className="bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-sky-500"
          >
            <option value="">All Tiers</option>
            <option value="LOW">Low Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="HIGH">High Risk</option>
          </select>
        </div>

        <button
          onClick={fetchPredictions}
          className="ml-auto text-xs text-slate-400 hover:text-white flex items-center gap-1.5"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Predictions Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/70 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">ID</th>
                <th className="py-3 px-4">Zone Code</th>
                <th className="py-3 px-4">Zone Name</th>
                <th className="py-3 px-4">Assessment Timestamp (UTC)</th>
                <th className="py-3 px-4">Horizon</th>
                <th className="py-3 px-4">Risk Probability</th>
                <th className="py-3 px-4">Tier Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan="8" className="py-8 text-center text-slate-400">
                    <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-sky-400" />
                    Loading prediction records...
                  </td>
                </tr>
              ) : predictions.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-8 text-center text-slate-500">
                    No prediction entries found.
                  </td>
                </tr>
              ) : (
                predictions.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono text-slate-500">#{p.id}</td>
                    <td className="py-3 px-4 font-mono font-bold text-sky-400">
                      {p.zone_code || `Zone #${p.zone_id}`}
                    </td>
                    <td className="py-3 px-4 text-slate-200 font-medium">
                      {p.zone_name || 'N/A'}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                      {p.assessment_timestamp ? new Date(p.assessment_timestamp).toLocaleString() : '-'}
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      {p.prediction_horizon_hours} Hours
                    </td>
                    <td className="py-3 px-4 font-mono font-semibold">
                      {(p.risk_score * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4">
                      <RiskBadge category={p.risk_category} score={p.risk_score} showScore={false} size="sm" />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setDetailModal(p)}
                        className="p-1.5 bg-slate-800 hover:bg-slate-700 text-sky-400 rounded-lg transition inline-flex items-center gap-1 text-[11px]"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-slate-800 text-xs text-slate-400">
          <div>
            Showing Page <span className="font-semibold text-slate-200">{page}</span> of{' '}
            <span className="font-semibold text-slate-200">{pagination.pages || 1}</span> (
            {pagination.total} records total)
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
              disabled={page <= 1}
              className="p-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 rounded-lg transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage((prev) => Math.min(prev + 1, pagination.pages || 1))}
              disabled={page >= (pagination.pages || 1)}
              className="p-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 rounded-lg transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Prediction Details Modal */}
      {detailModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-lg bg-slate-900 border border-slate-700 rounded-2xl p-6 shadow-2xl text-slate-200">
            <button
              onClick={() => setDetailModal(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2.5 border-b border-slate-800 pb-3 mb-4">
              <History className="w-5 h-5 text-sky-400" />
              <h2 className="text-lg font-bold text-white">Prediction Details #{detailModal.id}</h2>
            </div>

            <div className="space-y-4 text-xs">
              <div className="flex items-center justify-between bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div>
                  <div className="text-slate-400 text-[10px] uppercase font-bold">Zone Sector</div>
                  <div className="text-sm font-bold text-white mt-0.5">
                    {detailModal.zone_name} ({detailModal.zone_code})
                  </div>
                </div>
                <RiskBadge category={detailModal.risk_category} score={detailModal.risk_score} size="md" />
              </div>

              <div>
                <div className="text-slate-400 text-[11px] font-semibold mb-2">
                  Input Meteorological Feature Snapshot:
                </div>
                <div className="grid grid-cols-2 gap-2 bg-slate-950 p-3 rounded-xl border border-slate-800 font-mono">
                  {Object.entries(detailModal.input_features_snapshot || {}).map(([key, val]) => (
                    <div key={key} className="flex justify-between text-[11px]">
                      <span className="text-slate-400">{key}:</span>
                      <span className="text-sky-300 font-semibold">{val}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="text-[11px] text-slate-400 space-y-1">
                <div>Target Hazard: <span className="text-slate-200">{detailModal.prediction_target}</span></div>
                <div>Model Engine: <span className="text-slate-200">{detailModal.model_tag}</span></div>
                <div>Horizon: <span className="text-slate-200">{detailModal.prediction_horizon_hours} Hours Forward</span></div>
              </div>

              <div className="bg-sky-950/40 border border-sky-900/40 p-3 rounded-xl text-[11px] text-sky-200">
                <ShieldAlert className="w-4 h-4 text-sky-400 inline mr-1.5" />
                <span>{detailModal.limitations_notes}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
