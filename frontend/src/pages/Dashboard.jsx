import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  MapPin, AlertTriangle, ShieldCheck, Play, RefreshCw,
  Clock, Database, Cpu, ArrowUpRight, Filter, Radio, ArrowRight, Globe
} from 'lucide-react';
import apiService from '../services/api';
import MicroZoneMap from '../components/MicroZoneMap';
import WeatherTrendChart from '../components/WeatherTrendChart';
import RiskPieChart from '../components/RiskPieChart';
import RiskBadge from '../components/RiskBadge';
import FutureDisasterPrediction from '../components/FutureDisasterPrediction';

export default function Dashboard() {
  const [summaryData, setSummaryData] = useState(null);
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [runningBatch, setRunningBatch] = useState(false);
  const [error, setError] = useState(null);
  const [selectedZone, setSelectedZone] = useState(null);
  const [filterCategory, setFilterCategory] = useState('ALL');
  const [forecastRefreshKey, setForecastRefreshKey] = useState(0);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, zoneRes] = await Promise.all([
        apiService.getDashboardSummary(),
        apiService.getZones({ per_page: 100 })
      ]);
      setSummaryData(sumRes);
      setZones(zoneRes.zones || []);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data from backend server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunBatchInference = async () => {
    setRunningBatch(true);
    try {
      await apiService.runBatchPredictions();
      await fetchData();
      setForecastRefreshKey((k) => k + 1);
    } catch (err) {
      alert(`Inference failed: ${err.message}`);
    } finally {
      setRunningBatch(false);
    }
  };

  const handleSimulateScenario = async (scenarioName) => {
    setRunningBatch(true);
    try {
      await apiService.simulateScenario(scenarioName);
      await fetchData();
      setForecastRefreshKey((k) => k + 1);
    } catch (err) {
      alert(`Scenario simulation failed: ${err.message}`);
    } finally {
      setRunningBatch(false);
    }
  };

  const handleSyncLiveWeather = async () => {
    setRunningBatch(true);
    try {
      const res = await apiService.syncAllZonesLiveWeather();
      await apiService.runBatchPredictions();
      await fetchData();
      setForecastRefreshKey((k) => k + 1);
      alert(`🌐 Live Internet Weather Synchronized from Open-Meteo across ${res.results?.length || 5} micro-zones!\nAI risk predictions have been re-assessed using real-time atmospheric observations.`);
    } catch (err) {
      alert(`Live weather sync failed: ${err.message}`);
    } finally {
      setRunningBatch(false);
    }
  };

  if (loading) {
    return (
      <div className="h-96 flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="h-8 w-8 text-sky-400 animate-spin" />
        <p className="text-sm text-slate-400">Loading micro-zone disaster intelligence...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-950/40 border border-rose-800 rounded-2xl p-6 text-center max-w-lg mx-auto my-12">
        <AlertTriangle className="h-10 w-10 text-rose-400 mx-auto mb-3" />
        <h3 className="text-base font-bold text-white mb-1">Failed to Connect to Flask API</h3>
        <p className="text-xs text-rose-300 mb-4">{error}</p>
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold transition"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const summary = summaryData?.summary || {};
  const status = summaryData?.system_status || {};
  const weatherTrends = summaryData?.weather_trends || [];
  const latestPredictions = summaryData?.latest_predictions || [];

  const filteredPredictions = filterCategory === 'ALL'
    ? latestPredictions
    : latestPredictions.filter(p => p.risk_category === filterCategory);

  return (
    <div className="space-y-6">
      {/* Top Banner & Run Prediction Action */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-md">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight uppercase">
            MICRO-ZONE DISASTER PREDICTION SYSTEM
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time hydro-meteorological hazard forecasting &amp; multi-horizon future disaster prediction with TensorFlow Stacked LSTM
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Quick Scenario Simulators */}
          <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
            <span className="text-[11px] text-slate-400 font-semibold px-2">Scenario:</span>
            <button
              onClick={() => handleSimulateScenario('storm_surge')}
              disabled={runningBatch}
              className="px-2.5 py-1.5 bg-rose-950/80 hover:bg-rose-900 border border-rose-800 text-rose-200 rounded-lg text-xs font-semibold transition flex items-center gap-1 cursor-pointer"
              title="Simulate Severe Storm Surge (High & Medium Hazard Zones)"
            >
              <span>⚡ Severe Storm</span>
            </button>

            <button
              onClick={() => handleSimulateScenario('flash_flood')}
              disabled={runningBatch}
              className="px-2.5 py-1.5 bg-amber-950/80 hover:bg-amber-900 border border-amber-800 text-amber-200 rounded-lg text-xs font-semibold transition flex items-center gap-1 cursor-pointer"
              title="Simulate Flash Flood Hazard"
            >
              <span>🌊 Flash Flood</span>
            </button>

            <button
              onClick={() => handleSimulateScenario('calm')}
              disabled={runningBatch}
              className="px-2.5 py-1.5 bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-800 text-emerald-200 rounded-lg text-xs font-semibold transition flex items-center gap-1 cursor-pointer"
              title="Reset All Zones to Normal Weather"
            >
              <span>☀️ Normal</span>
            </button>

            <button
              onClick={handleSyncLiveWeather}
              disabled={runningBatch}
              className="px-2.5 py-1.5 bg-sky-950/80 hover:bg-sky-900 border border-sky-700/80 text-sky-200 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer shadow-sm shadow-sky-950"
              title="Fetch Real-Time Live Weather from Open-Meteo API for all zones"
            >
              <Globe className={`w-3.5 h-3.5 text-sky-400 ${runningBatch ? 'animate-spin' : ''}`} />
              <span>🌐 Live Weather</span>
            </button>
          </div>

          <button
            onClick={fetchData}
            disabled={loading}
            className="p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition border border-slate-700 text-xs"
            title="Refresh Data"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={handleRunBatchInference}
            disabled={runningBatch || !status.model_available}
            className="flex items-center gap-2 px-3.5 py-2.5 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-lg shadow-sky-950 transition cursor-pointer"
          >
            <Play className={`h-4 w-4 ${runningBatch ? 'animate-spin' : ''}`} />
            <span>{runningBatch ? 'Assessing...' : 'Re-assess Zones'}</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3.5">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Configured Zones</span>
            <MapPin className="h-4 w-4 text-sky-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">{summary.total_zones || 0}</div>
          <span className="text-[11px] text-slate-500">Active monitoring sectors</span>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Low Risk Zones</span>
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-400">{summary.low_risk_count || 0}</div>
          <span className="text-[11px] text-slate-500">Normal meteorological baseline</span>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Medium Risk</span>
            <span className="h-2 w-2 rounded-full bg-amber-500" />
          </div>
          <div className="text-2xl font-extrabold text-amber-400">{summary.medium_risk_count || 0}</div>
          <span className="text-[11px] text-slate-500">Elevated threshold advisory</span>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">High Risk</span>
            <span className="h-2 w-2 rounded-full bg-rose-500" />
          </div>
          <div className="text-2xl font-extrabold text-rose-400">{summary.high_risk_count || 0}</div>
          <span className="text-[11px] text-slate-500">Critical hazard signature</span>
        </div>

        <div className="col-span-2 lg:col-span-1 bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Active Model</span>
            <Cpu className="h-4 w-4 text-indigo-400" />
          </div>
          <div className="text-sm font-bold text-slate-200 truncate">{status.model_version || 'None'}</div>
          <span className="text-[11px] text-emerald-400 font-mono">
            {status.model_available ? 'Ready for Inference' : 'Model Missing'}
          </span>
        </div>
      </div>

      {/* Emergency Authority Signals Alert Banner */}
      {summary.high_risk_count > 0 && (
        <div className="bg-gradient-to-r from-rose-950/80 via-rose-900/40 to-slate-900 border border-rose-600/60 rounded-2xl p-4 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-fade-in">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-rose-600 text-white rounded-xl shadow-lg shadow-rose-950 shrink-0">
              <Radio className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-black text-white uppercase tracking-wider">
                  🚨 CRITICAL DISASTER SIGNALS TRANSMITTED TO AUTHORITIES
                </span>
                <span className="bg-rose-950 text-rose-300 border border-rose-800 text-[10px] font-mono px-2 py-0.5 rounded font-bold">
                  {summary.high_risk_count} ZONES IN HIGH HAZARD
                </span>
              </div>
              <p className="text-xs text-rose-200/90 mt-0.5">
                Automated early-warning alerts dispatched to DDMA, NDRF, and State Emergency Operations Center (SEOC).
              </p>
            </div>
          </div>
          <Link
            to="/alerts"
            className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-xl transition flex items-center gap-1.5 shrink-0 self-start sm:self-auto cursor-pointer shadow-md"
          >
            <span>View Transmitted Messages</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Future Disaster Prediction Engine (Multi-Horizon Forecast Based on Previous Data) */}
      <FutureDisasterPrediction
        key={forecastRefreshKey}
        zones={zones}
        initialZoneId={selectedZone?.id}
        onZoneChange={(zid) => {
          const matched = zones.find((z) => z.id === zid);
          if (matched) setSelectedZone(matched);
        }}
      />

      {/* Main Map & Risk Distribution Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <MapPin className="h-4 w-4 text-sky-400" />
              Micro-Zone Hazard Geography
            </h2>
            <span className="text-xs text-slate-400 font-mono">
              Last Assessed: {summary.latest_prediction_timestamp ? new Date(summary.latest_prediction_timestamp).toLocaleTimeString() : 'N/A'}
            </span>
          </div>
          <MicroZoneMap zones={zones} onSelectZone={(z) => setSelectedZone(z)} />
        </div>

        {/* Risk Distribution Donut */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-white mb-1">Risk Tier Distribution</h2>
            <p className="text-xs text-slate-400">Classification across all active micro-zones</p>
          </div>
          <RiskPieChart riskCounts={summary.risk_counts} />
          <div className="border-t border-slate-800 pt-3 text-[11px] text-slate-400 space-y-1">
            <div className="flex justify-between">
              <span>Threshold Low:</span>
              <span className="text-emerald-400 font-mono">&lt; 0.35</span>
            </div>
            <div className="flex justify-between">
              <span>Threshold High:</span>
              <span className="text-rose-400 font-mono">&ge; 0.70</span>
            </div>
          </div>
        </div>
      </div>

      {/* Weather Trends Chart */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-white">Historical Weather Observations Trend</h2>
            <p className="text-xs text-slate-400">Sequential multi-sensor observations (Rainfall, Wind Speed, Temperature)</p>
          </div>
          <div className="text-xs text-slate-400 font-mono bg-slate-950 px-2.5 py-1 rounded-md border border-slate-800">
            24-Hour Rolling Window
          </div>
        </div>
        <WeatherTrendChart data={weatherTrends} />
      </div>

      {/* Recent Predictions Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-base font-bold text-white">Recent Micro-Zone Predictions</h2>
            <p className="text-xs text-slate-400">Model output logs stored in Neon PostgreSQL</p>
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-sky-500"
            >
              <option value="ALL">All Categories</option>
              <option value="LOW">Low Risk</option>
              <option value="MEDIUM">Medium Risk</option>
              <option value="HIGH">High Risk</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Zone Code</th>
                <th className="py-2.5 px-3">Zone Name</th>
                <th className="py-2.5 px-3">Timestamp (UTC)</th>
                <th className="py-2.5 px-3">Horizon</th>
                <th className="py-2.5 px-3">Risk Score</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Rainfall</th>
                <th className="py-2.5 px-3">Wind</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredPredictions.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-6 text-center text-slate-500">
                    No predictions found matching current filter.
                  </td>
                </tr>
              ) : (
                filteredPredictions.map((pred) => {
                  const snap = pred.input_features_snapshot || {};
                  return (
                    <tr key={pred.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-2.5 px-3 font-mono font-semibold text-sky-400">
                        {pred.zone_code || `Zone #${pred.zone_id}`}
                      </td>
                      <td className="py-2.5 px-3 font-medium text-slate-200">
                        {pred.zone_name || 'N/A'}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px]">
                        {pred.assessment_timestamp ? new Date(pred.assessment_timestamp).toLocaleString() : 'N/A'}
                      </td>
                      <td className="py-2.5 px-3 text-slate-300">
                        {pred.prediction_horizon_hours}h ahead
                      </td>
                      <td className="py-2.5 px-3 font-mono font-semibold">
                        {(pred.risk_score * 100).toFixed(1)}%
                      </td>
                      <td className="py-2.5 px-3">
                        <RiskBadge category={pred.risk_category} score={pred.risk_score} showScore={false} size="sm" />
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">
                        {snap.rainfall_mm !== undefined ? `${snap.rainfall_mm} mm` : '-'}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">
                        {snap.wind_speed_kmh !== undefined ? `${snap.wind_speed_kmh} km/h` : '-'}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
