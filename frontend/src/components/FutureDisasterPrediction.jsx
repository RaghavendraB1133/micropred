import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  AreaChart, Area, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend, ReferenceLine
} from 'recharts';
import {
  Sparkles, Clock, AlertTriangle, ShieldCheck, ShieldAlert,
  Droplets, Wind, Gauge, Compass, RefreshCw, ArrowRight,
  TrendingUp, Calendar, AlertOctagon, CheckCircle2
} from 'lucide-react';
import apiService from '../services/api';
import RiskBadge from './RiskBadge';

export default function FutureDisasterPrediction({ zones = [], initialZoneId = null, onZoneChange = null }) {
  const [selectedZoneId, setSelectedZoneId] = useState(initialZoneId || (zones[0]?.id || 1));
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeHorizonTab, setActiveHorizonTab] = useState('ALL'); // 'ALL' or specific hours like 24, 48, 72

  // Sync when initialZoneId changes externally (e.g. from map click)
  useEffect(() => {
    if (initialZoneId && initialZoneId !== selectedZoneId) {
      setSelectedZoneId(initialZoneId);
    }
  }, [initialZoneId]);

  const loadForecast = async (zoneIdToLoad) => {
    const zid = zoneIdToLoad || selectedZoneId;
    if (!zid) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.getFutureDisasterForecast(zid);
      setForecastData(res);
    } catch (err) {
      setError(err.message || 'Failed to generate future disaster prediction.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedZoneId) {
      loadForecast(selectedZoneId);
    }
  }, [selectedZoneId]);

  const handleSelectZone = (e) => {
    const newId = parseInt(e.target.value, 10);
    setSelectedZoneId(newId);
    if (onZoneChange) onZoneChange(newId);
  };

  const zone = forecastData?.zone || {};
  const histSummary = forecastData?.historical_summary || {};
  const triggers = forecastData?.trigger_factors || [];
  const forecasts = forecastData?.future_forecasts || [];
  const timeline = forecastData?.combined_timeline || [];
  const peakWindow = forecastData?.peak_hazard_window || 'N/A';
  const overallTier = forecastData?.overall_future_tier || 'LOW';

  const filteredForecasts = activeHorizonTab === 'ALL'
    ? forecasts
    : forecasts.filter(f => f.horizon_hours <= parseInt(activeHorizonTab, 10));

  const CustomTimelineTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;
    const point = payload[0]?.payload || {};
    const isFuture = point.is_future;

    return (
      <div className="bg-slate-900 border border-slate-700/80 rounded-xl p-3 shadow-2xl text-xs space-y-1.5 max-w-xs backdrop-blur-md">
        <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-1.5">
          <span className="font-bold text-white flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-sky-400" />
            {point.label}
          </span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
            isFuture ? 'bg-indigo-950 text-indigo-300 border border-indigo-700/60' : 'bg-slate-800 text-slate-300'
          }`}>
            {isFuture ? '🔮 Future Forecast' : '📜 Historical Observed'}
          </span>
        </div>

        {point.future_risk_pct !== undefined && point.future_risk_pct !== null && (
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Forecasted Risk:</span>
            <span className={`font-mono font-black ${
              point.future_risk_pct >= 70 ? 'text-rose-400' : point.future_risk_pct >= 35 ? 'text-amber-400' : 'text-emerald-400'
            }`}>
              {point.future_risk_pct}%
            </span>
          </div>
        )}

        {point.risk_score_pct !== undefined && point.risk_score_pct !== null && !isFuture && (
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Historical Risk:</span>
            <span className="font-mono font-bold text-sky-300">
              {point.risk_score_pct}%
            </span>
          </div>
        )}

        {point.predicted_disaster && (
          <div className="text-[11px] font-medium text-slate-200">
            {point.predicted_disaster}
          </div>
        )}

        <div className="grid grid-cols-2 gap-x-3 gap-y-1 pt-1 border-t border-slate-800 text-[11px] text-slate-400">
          <div>Rain: <span className="text-sky-300 font-mono font-medium">{point.rainfall_mm} mm</span></div>
          <div>Wind: <span className="text-amber-300 font-mono font-medium">{point.wind_speed_kmh} km/h</span></div>
          <div>Pressure: <span className="text-slate-300 font-mono">{point.pressure_hpa} hPa</span></div>
          <div>Soil: <span className="text-emerald-300 font-mono">{point.soil_moisture_pct}%</span></div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-gradient-to-b from-slate-900/90 via-slate-900/60 to-slate-950 border border-sky-900/40 rounded-2xl p-5 shadow-2xl space-y-6">
      {/* Header & Controls Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-gradient-to-tr from-sky-600 to-indigo-600 rounded-xl text-white shadow-md shadow-sky-950">
              <Sparkles className="w-5 h-5 text-sky-200 animate-pulse" />
            </div>
            <div>
              <h2 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
                FUTURE DISASTER PREDICTION ENGINE
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-700/60">
                  Sequential LSTM Trajectory
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Multi-horizon disaster risk forecasting projected from sequential historical observation data
              </p>
            </div>
          </div>
        </div>

        {/* Controls: Zone Selector & Re-forecast Action */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs">
            <span className="text-slate-400 font-medium">Zone:</span>
            <select
              value={selectedZoneId}
              onChange={handleSelectZone}
              className="bg-transparent text-slate-200 font-semibold focus:outline-none cursor-pointer"
            >
              {zones.map((z) => (
                <option key={z.id} value={z.id} className="bg-slate-900 text-slate-200">
                  {z.zone_code} - {z.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-xl p-1 text-xs">
            <button
              onClick={() => setActiveHorizonTab('ALL')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition cursor-pointer ${
                activeHorizonTab === 'ALL'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              72h Outlook
            </button>
            <button
              onClick={() => setActiveHorizonTab('24')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition cursor-pointer ${
                activeHorizonTab === '24'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              24h Peak
            </button>
          </div>

          <button
            onClick={() => loadForecast(selectedZoneId)}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition shadow-md shadow-sky-950 cursor-pointer"
            title="Recalculate future disaster probabilities from latest observation sequence"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Forecast Now</span>
          </button>
        </div>
      </div>

      {loading && (
        <div className="h-64 flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="h-8 w-8 text-sky-400 animate-spin" />
          <p className="text-xs text-slate-400">Computing sequential LSTM multi-horizon disaster predictions...</p>
        </div>
      )}

      {error && !loading && (
        <div className="bg-rose-950/40 border border-rose-800 rounded-xl p-4 text-center">
          <AlertTriangle className="h-6 w-6 text-rose-400 mx-auto mb-1" />
          <p className="text-xs text-rose-300">{error}</p>
          <button
            onClick={() => loadForecast(selectedZoneId)}
            className="mt-2 text-xs text-sky-400 underline font-semibold hover:text-sky-300 cursor-pointer"
          >
            Retry Forecasting
          </button>
        </div>
      )}

      {!loading && !error && forecastData && (
        <>
          {/* Top Diagnostic Banner: Previous Data Foundation & Trigger Factors */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Historical Previous Data Basis */}
            <div className="lg:col-span-2 bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-300 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-sky-400" />
                  Historical Foundation (Previous Observations Analyzed)
                </span>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800">
                  {histSummary.observation_window_label || 'Sequential Time Series'}
                </span>
              </div>

              {/* Previous Data Metrics Strip */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="bg-slate-900/80 border border-slate-800/80 rounded-lg p-2.5">
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span>Prev Total Rain</span>
                    <Droplets className="w-3.5 h-3.5 text-sky-400" />
                  </div>
                  <div className="text-base font-black text-white mt-1">
                    {histSummary.total_rainfall_mm} <span className="text-xs font-normal text-slate-400">mm</span>
                  </div>
                </div>

                <div className="bg-slate-900/80 border border-slate-800/80 rounded-lg p-2.5">
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span>Avg Wind Gust</span>
                    <Wind className="w-3.5 h-3.5 text-amber-400" />
                  </div>
                  <div className="text-base font-black text-white mt-1">
                    {histSummary.average_wind_kmh} <span className="text-xs font-normal text-slate-400">km/h</span>
                  </div>
                </div>

                <div className="bg-slate-900/80 border border-slate-800/80 rounded-lg p-2.5">
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span>Pressure Momentum</span>
                    <Gauge className="w-3.5 h-3.5 text-indigo-400" />
                  </div>
                  <div className="text-base font-black text-white mt-1">
                    {histSummary.latest_pressure_hpa} <span className="text-xs font-normal text-slate-400">hPa</span>
                  </div>
                </div>

                <div className="bg-slate-900/80 border border-slate-800/80 rounded-lg p-2.5">
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span>Soil Saturation</span>
                    <Compass className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                  <div className="text-base font-black text-emerald-300 mt-1">
                    {histSummary.soil_saturation_pct}%
                  </div>
                </div>
              </div>

              {/* Detected Trigger Factors in Previous Data */}
              <div className="space-y-1.5 pt-1">
                <span className="text-[11px] font-semibold text-slate-400">
                  Key Hazard Precursors Identified in Previous Data:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {triggers.map((trig, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-1.5 text-[11px] bg-slate-900 border border-slate-800 text-slate-300 px-2.5 py-1 rounded-lg"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                      <span>{trig}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Peak Future Hazard Status Card */}
            <div className={`border rounded-xl p-4 flex flex-col justify-between ${
              overallTier === 'HIGH'
                ? 'bg-rose-950/40 border-rose-800/80'
                : overallTier === 'MEDIUM'
                ? 'bg-amber-950/40 border-amber-800/80'
                : 'bg-emerald-950/30 border-emerald-800/60'
            }`}>
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-300">Overall Future Outlook</span>
                  <RiskBadge category={overallTier} size="sm" />
                </div>

                <div className="mt-3">
                  <div className="text-[11px] text-slate-400">Peak Projected Impact:</div>
                  <div className={`text-base font-black mt-0.5 ${
                    overallTier === 'HIGH' ? 'text-rose-400' : overallTier === 'MEDIUM' ? 'text-amber-400' : 'text-emerald-400'
                  }`}>
                    {peakWindow}
                  </div>
                </div>

                <div className="mt-2 text-xs text-slate-300 leading-relaxed">
                  {overallTier === 'HIGH' ? (
                    <span>⚠️ Extreme disaster vulnerability projected based on the previous rainfall gradient. Actionable disaster mitigation protocols recommended.</span>
                  ) : overallTier === 'MEDIUM' ? (
                    <span>⚡ Moderate inundation hazard expected. Catchment channels should be monitored for overflow.</span>
                  ) : (
                    <span>✅ Calm hydro-meteorological trajectory. All projected future parameters remain within safe baseline bounds.</span>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800/60 mt-3 flex items-center justify-between">
                <span className="text-[11px] text-slate-400 font-mono">
                  Zone: <strong className="text-white">{zone.zone_code}</strong>
                </span>
                <Link
                  to="/alerts"
                  className="text-xs font-bold text-sky-400 hover:text-sky-300 flex items-center gap-1 cursor-pointer"
                >
                  <span>Dispatch Alerts</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          </div>

          {/* Interactive Trajectory Visualization Chart */}
          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-sky-400" />
                  Sequential Disaster Trajectory: Previous Data → Future Projected Risk Curve
                </h3>
                <p className="text-xs text-slate-400">
                  Left side illustrates previous sequential observations; right side projects future disaster likelihood calculated by TensorFlow Stacked LSTM
                </p>
              </div>

              <div className="flex items-center gap-3 text-[11px]">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-sky-500/80 inline-block" />
                  <span className="text-slate-300">Previous Observed Risk</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-rose-500 inline-block shadow-sm shadow-rose-500" />
                  <span className="text-rose-300 font-semibold">Future Forecasted Risk</span>
                </div>
              </div>
            </div>

            <div className="h-72 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timeline} margin={{ top: 15, right: 15, left: -15, bottom: 5 }}>
                  <defs>
                    <linearGradient id="histRiskGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0284c7" stopOpacity={0.6}/>
                      <stop offset="95%" stopColor="#0284c7" stopOpacity={0.0}/>
                    </linearGradient>
                    <linearGradient id="futureRiskGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.7}/>
                      <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.05}/>
                    </linearGradient>
                  </defs>

                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="label" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis
                    stroke="#64748b"
                    tick={{ fontSize: 11 }}
                    domain={[0, 100]}
                    tickFormatter={(v) => `${v}%`}
                  />
                  <Tooltip content={<CustomTimelineTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />

                  {/* Vertical Dividing Reference Line at NOW (T0) */}
                  <ReferenceLine
                    x="NOW (T0)"
                    stroke="#f59e0b"
                    strokeDasharray="4 4"
                    strokeWidth={2}
                    label={{
                      value: '⚡ Present / Observation Cutoff',
                      position: 'top',
                      fill: '#f59e0b',
                      fontSize: 10,
                      fontWeight: 'bold'
                    }}
                  />

                  {/* Historical Risk Curve */}
                  <Area
                    type="monotone"
                    dataKey="risk_score_pct"
                    name="Previous Data Observed Hazard (%)"
                    stroke="#0284c7"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#histRiskGradient)"
                  />

                  {/* Future Forecasted Risk Curve */}
                  <Area
                    type="monotone"
                    dataKey="future_risk_pct"
                    name="Future Projected Disaster Risk (%)"
                    stroke="#f43f5e"
                    strokeWidth={3}
                    strokeDasharray="5 5"
                    fillOpacity={1}
                    fill="url(#futureRiskGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Multi-Horizon Future Outlook Grid Cards */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Clock className="w-4 h-4 text-indigo-400" />
                Multi-Horizon Future Outlook Cards (T+6h to T+72h)
              </h3>
              <span className="text-[11px] text-slate-400">
                Inference computed from sequential atmospheric physics & LSTM
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
              {filteredForecasts.map((f, i) => {
                const isHigh = f.risk_category === 'HIGH';
                const isMed = f.risk_category === 'MEDIUM';

                return (
                  <div
                    key={f.horizon_hours}
                    className={`rounded-xl p-3.5 border transition hover:translate-y-[-2px] flex flex-col justify-between space-y-3 ${
                      isHigh
                        ? 'bg-gradient-to-b from-rose-950/70 to-slate-900 border-rose-700/70 shadow-lg shadow-rose-950/40'
                        : isMed
                        ? 'bg-gradient-to-b from-amber-950/50 to-slate-900 border-amber-700/60'
                        : 'bg-gradient-to-b from-slate-900/90 to-slate-950 border-slate-800'
                    }`}
                  >
                    <div>
                      {/* Card Header: Horizon & Risk Category */}
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono text-xs font-black px-2 py-0.5 rounded bg-slate-950 text-sky-400 border border-slate-800">
                          {f.time_label} Ahead
                        </span>
                        <RiskBadge category={f.risk_category} score={f.risk_score} showScore={false} size="sm" />
                      </div>

                      {/* Predicted Disaster Title */}
                      <div className="text-xs font-bold text-white line-clamp-2 min-h-[32px]">
                        {f.predicted_disaster}
                      </div>

                      {/* Probability Score Big Number */}
                      <div className="mt-2 flex items-baseline gap-2">
                        <span className={`text-2xl font-black font-mono ${
                          isHigh ? 'text-rose-400' : isMed ? 'text-amber-400' : 'text-emerald-400'
                        }`}>
                          {(f.risk_score * 100).toFixed(1)}%
                        </span>
                        <span className="text-[11px] text-slate-400">Disaster Probability</span>
                      </div>

                      {/* Projected Weather Indicators */}
                      <div className="grid grid-cols-2 gap-1.5 mt-2.5 pt-2.5 border-t border-slate-800/80 text-[11px] text-slate-400 font-mono">
                        <div>Rain: <span className="text-sky-300 font-semibold">{f.projected_rainfall_mm} mm</span></div>
                        <div>Wind: <span className="text-amber-300 font-semibold">{f.projected_wind_kmh} km/h</span></div>
                        <div>Press: <span className="text-slate-300">{f.projected_pressure_hpa} hPa</span></div>
                        <div>Soil: <span className="text-emerald-300">{f.projected_soil_moisture_pct}%</span></div>
                      </div>
                    </div>

                    {/* Actionable Decision-Support Advisory */}
                    <div className="text-[11px] text-slate-300/90 bg-slate-950/70 p-2 rounded-lg border border-slate-800/60 leading-tight">
                      <strong className="text-slate-400 block text-[10px] uppercase tracking-wider mb-0.5">Advisory:</strong>
                      {f.early_warning_advisory}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
