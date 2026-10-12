import React, { useState, useEffect } from 'react';
import {
  MapPin, Play, RefreshCw, Mountain, Users,
  History, CloudRain, Wind, AlertCircle, X, ChevronRight, Globe,
  Plus, Sparkles, Building
} from 'lucide-react';
import apiService from '../services/api';
import RiskBadge from '../components/RiskBadge';
import WeatherTrendChart from '../components/WeatherTrendChart';

const PRESET_LOCATIONS = [
  {
    name: 'Pune Western Ghats Basin',
    state: 'Maharashtra',
    latitude: '18.5204',
    longitude: '73.8567',
    elevation_m: '560',
    population_estimate: '3124000',
    topography: 'Hilly Plateau / River Basin',
    description: 'Western Ghats rain shadow zone susceptible to flash urban floods and landslides.'
  },
  {
    name: 'Hyderabad Musi River Corridor',
    state: 'Telangana',
    latitude: '17.3850',
    longitude: '78.4867',
    elevation_m: '542',
    population_estimate: '6800000',
    topography: 'Deccan Plateau',
    description: 'Central Deccan urban zone with monsoon inundation and heatwave vulnerability.'
  },
  {
    name: 'Jaipur Aravalli Foothills Sector',
    state: 'Rajasthan',
    latitude: '26.9124',
    longitude: '75.7873',
    elevation_m: '431',
    population_estimate: '3073000',
    topography: 'Semi-Arid Basin',
    description: 'Western semi-arid zone susceptible to intense flash storms and extreme summer heat.'
  },
  {
    name: 'Bhubaneswar Mahanadi Coastal Belt',
    state: 'Odisha',
    latitude: '20.2961',
    longitude: '85.8245',
    elevation_m: '45',
    population_estimate: '838000',
    topography: 'Coastal Delta',
    description: 'Eastern coastal belt prone to severe cyclonic storms and deltaic river surges.'
  },
  {
    name: 'Shimla Ridge & Valley Slopes',
    state: 'Himachal Pradesh',
    latitude: '31.1048',
    longitude: '77.1734',
    elevation_m: '2205',
    population_estimate: '170000',
    topography: 'Steep Mountainous Slope',
    description: 'Himalayan slope micro-zone prone to cloudbursts, soil erosion, and severe winter freezes.'
  },
];

export default function MicroZones() {
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeZoneModal, setActiveZoneModal] = useState(null);
  const [zoneHistory, setZoneHistory] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [predictingZoneId, setPredictingZoneId] = useState(null);
  const [syncingZoneId, setSyncingZoneId] = useState(null);

  // Pan-India & Custom Location modal states
  const [isAddLocationModalOpen, setIsAddLocationModalOpen] = useState(false);
  const [isSeedingPanIndia, setIsSeedingPanIndia] = useState(false);
  const [addingCustomLocation, setAddingCustomLocation] = useState(false);
  const [customForm, setCustomForm] = useState(PRESET_LOCATIONS[0]);

  const fetchZones = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.getZones({ per_page: 50 });
      setZones(res.zones || []);
    } catch (err) {
      setError(err.message || 'Failed to fetch zones.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchZones();
  }, []);

  const handleInspectHistory = async (zone) => {
    setActiveZoneModal(zone);
    setLoadingHistory(true);
    try {
      const res = await apiService.getZoneHistory(zone.id, { limit: 48 });
      setZoneHistory(res);
    } catch (err) {
      alert(`Failed to load history for zone: ${err.message}`);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleRunSinglePrediction = async (zoneId) => {
    setPredictingZoneId(zoneId);
    try {
      const res = await apiService.runPrediction(zoneId, 24);
      await fetchZones();
      if (activeZoneModal && activeZoneModal.id === zoneId) {
        handleInspectHistory(activeZoneModal);
      }
      if (res?.prediction?.risk_category === 'HIGH') {
        const scorePct = Math.round((res.prediction.risk_score || 0) * 100);
        alert(`🚨 HIGH RISK DETECTED (${scorePct}%)!\nEmergency signal messages have been automatically transmitted to DDMA, SEOC, NDRF, and GCC-ICCC.\nCheck the 'Authority Signals' tab to view dispatched logs.`);
      }
    } catch (err) {
      alert(`Prediction failed: ${err.message}`);
    } finally {
      setPredictingZoneId(null);
    }
  };

  const handleSyncLiveZone = async (zoneId) => {
    setSyncingZoneId(zoneId);
    try {
      const res = await apiService.syncZoneLiveWeather(zoneId);
      const cond = res.sync_details?.latest_live_conditions || {};
      alert(`🌐 Live Internet Weather Synchronized from Open-Meteo for ${res.sync_details?.zone_code}!\nTemp: ${cond.temperature_c}°C | Rain: ${cond.rainfall_mm}mm | Wind: ${cond.wind_speed_kmh}km/h | Pressure: ${cond.pressure_hpa}hPa\nObservations recorded in database.`);
      await fetchZones();
      if (activeZoneModal && activeZoneModal.id === zoneId) {
        handleInspectHistory(activeZoneModal);
      }
    } catch (err) {
      alert(`Live sync failed: ${err.message}`);
    } finally {
      setSyncingZoneId(null);
    }
  };

  const handleSeedPanIndia = async () => {
    setIsSeedingPanIndia(true);
    try {
      const res = await apiService.seedPanIndiaZones();
      alert(`🇮🇳 Pan-India micro-zones synchronized!\n${res.message}\nTotal active zones in database: ${res.total_zones}`);
      await fetchZones();
    } catch (err) {
      alert(`Seeding failed: ${err.message}`);
    } finally {
      setIsSeedingPanIndia(false);
    }
  };

  const handleAddCustomLocation = async (e) => {
    e?.preventDefault();
    setAddingCustomLocation(true);
    try {
      const payload = {
        name: customForm.name,
        state: customForm.state,
        latitude: parseFloat(customForm.latitude),
        longitude: parseFloat(customForm.longitude),
        elevation_m: parseFloat(customForm.elevation_m || 20),
        population_estimate: parseInt(customForm.population_estimate || 100000, 10),
        topography: customForm.topography,
        description: customForm.description
      };
      const res = await apiService.addCustomLocation(payload);
      alert(`✅ New India Location Added: ${res.zone?.zone_code} - ${res.zone?.name}!\nLive Open-Meteo weather synced and LSTM AI hazard prediction calculated (${res.prediction?.risk_category} risk).`);
      setIsAddLocationModalOpen(false);
      await fetchZones();
    } catch (err) {
      alert(`Failed to add location: ${err.message}`);
    } finally {
      setAddingCustomLocation(false);
    }
  };

  if (loading) {
    return (
      <div className="h-96 flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="h-8 w-8 text-sky-400 animate-spin" />
        <p className="text-sm text-slate-400">Loading configured micro-zones...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-white tracking-tight">Pan-India Micro-Zone Sectors</h1>
            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
              {zones.length} Active Across India
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Geographic demarcations, topographic attributes, and localized disaster susceptibility covering all regions of India
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleSeedPanIndia}
            disabled={isSeedingPanIndia}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition cursor-pointer"
            title="Seed / Refresh 15 Major Disaster Zones Across India"
          >
            <Sparkles className={`h-3.5 w-3.5 text-amber-400 ${isSeedingPanIndia ? 'animate-spin' : ''}`} />
            <span>{isSeedingPanIndia ? 'Seeding...' : '🇮🇳 Seed Pan-India Zones'}</span>
          </button>

          <button
            onClick={() => setIsAddLocationModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md transition cursor-pointer"
            title="Add any custom city or coordinate across India"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add India Location</span>
          </button>

          <button
            onClick={fetchZones}
            className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-slate-700 transition cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Grid of Micro-Zone Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {zones.map((zone) => {
          const category = zone.latest_prediction?.risk_category || 'LOW';
          const score = zone.latest_prediction?.risk_score;
          const isPredicting = predictingZoneId === zone.id;

          return (
            <div
              key={zone.id}
              className="bg-slate-900/60 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 transition flex flex-col justify-between shadow-lg"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div>
                    <span className="text-[10px] font-mono text-sky-400 bg-sky-950 px-2 py-0.5 rounded border border-sky-800">
                      {zone.zone_code}
                    </span>
                    <h3 className="text-base font-bold text-white mt-1.5">{zone.name}</h3>
                  </div>
                  <RiskBadge category={category} score={score} size="sm" />
                </div>

                <p className="text-xs text-slate-400 mb-4 line-clamp-2">
                  {zone.description || 'Continuous monitoring micro-zone sector.'}
                </p>

                <div className="grid grid-cols-2 gap-2 text-xs text-slate-300 mb-4 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                  <div className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-sky-400" />
                    <span>{zone.latitude.toFixed(3)}, {zone.longitude.toFixed(3)}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Mountain className="w-3.5 h-3.5 text-emerald-400" />
                    <span>{zone.elevation_m}m elv</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Users className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{(zone.population_estimate / 1000).toFixed(0)}k pop</span>
                  </div>
                  <div className="flex items-center gap-1.5 truncate">
                    <span className="text-[11px] text-slate-400 font-medium">{zone.topography}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-3 border-t border-slate-800">
                <button
                  onClick={() => handleInspectHistory(zone)}
                  className="py-2 px-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition flex items-center justify-center gap-1.5"
                  title="Inspect Historical Time Series"
                >
                  <History className="w-3.5 h-3.5 text-sky-400" />
                  <span>History</span>
                </button>

                <button
                  onClick={() => handleSyncLiveZone(zone.id)}
                  disabled={syncingZoneId === zone.id}
                  className="py-2 px-2.5 bg-sky-950/80 hover:bg-sky-900 border border-sky-800/80 text-sky-300 text-xs font-semibold rounded-xl transition flex items-center justify-center gap-1.5 cursor-pointer"
                  title="Fetch Real-Time Live Weather from Open-Meteo API for this zone"
                >
                  <Globe className={`w-3.5 h-3.5 text-sky-400 ${syncingZoneId === zone.id ? 'animate-spin' : ''}`} />
                  <span>Live Sync</span>
                </button>

                <button
                  onClick={() => handleRunSinglePrediction(zone.id)}
                  disabled={isPredicting}
                  className="flex-1 py-2 px-2.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl transition flex items-center justify-center gap-1.5 shadow-md shadow-sky-950 cursor-pointer"
                  title="Run Single Zone AI Risk Assessment"
                >
                  <Play className={`w-3.5 h-3.5 ${isPredicting ? 'animate-spin' : ''}`} />
                  <span>{isPredicting ? 'Assessing...' : 'Assess Risk'}</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Zone Detail Modal */}
      {activeZoneModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-4xl bg-slate-900 border border-slate-700 rounded-2xl p-6 shadow-2xl text-slate-200 max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => { setActiveZoneModal(null); setZoneHistory(null); }}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 border-b border-slate-800 pb-3 mb-4">
              <span className="text-xs font-mono bg-sky-950 text-sky-400 border border-sky-800 px-2 py-0.5 rounded">
                {activeZoneModal.zone_code}
              </span>
              <h2 className="text-xl font-bold text-white">{activeZoneModal.name} History & Analysis</h2>
            </div>

            {loadingHistory ? (
              <div className="h-64 flex flex-col items-center justify-center space-y-2">
                <RefreshCw className="h-6 w-6 text-sky-400 animate-spin" />
                <p className="text-xs text-slate-400">Loading historical observations & event logs...</p>
              </div>
            ) : zoneHistory ? (
              <div className="space-y-6">
                {/* Weather Chart */}
                <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
                  <h3 className="text-sm font-bold text-white mb-3">Hydro-Meteorological Time Series</h3>
                  <WeatherTrendChart
                    data={zoneHistory.weather_history.map(obs => ({
                      timestamp: new Date(obs.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                      rainfall_mm: obs.rainfall_mm,
                      temperature_c: obs.temperature_c,
                      humidity_pct: obs.humidity_pct,
                      wind_speed_kmh: obs.wind_speed_kmh
                    }))}
                  />
                </div>

                {/* Past Disaster Ground Truth Events */}
                <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
                  <h3 className="text-sm font-bold text-white mb-2">Ground Truth Hazard Records</h3>
                  {zoneHistory.disaster_events.length === 0 ? (
                    <p className="text-xs text-slate-500 py-2">No historical disaster ground truth recorded for this sector.</p>
                  ) : (
                    <div className="space-y-2">
                      {zoneHistory.disaster_events.slice(0, 5).map((evt) => (
                        <div key={evt.id} className="text-xs bg-slate-900 border border-slate-800 p-2.5 rounded-lg flex items-center justify-between">
                          <div>
                            <span className="font-semibold text-rose-300 mr-2">{evt.disaster_type}</span>
                            <span className="text-slate-400">{evt.description}</span>
                          </div>
                          <span className="text-[11px] font-mono text-slate-500">
                            {new Date(evt.timestamp).toLocaleDateString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
      {/* Add Custom Location Across India Modal */}
      {isAddLocationModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div className="relative w-full max-w-xl bg-slate-900 border border-slate-700/80 rounded-2xl p-6 shadow-2xl text-slate-200 max-h-[90vh] overflow-y-auto space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-sky-950 rounded-xl border border-sky-800 text-sky-400">
                  <MapPin className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Add Micro-Zone Across India</h3>
                  <p className="text-xs text-slate-400">Deploy AI risk prediction to any coordinate in India</p>
                </div>
              </div>
              <button
                onClick={() => setIsAddLocationModalOpen(false)}
                className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Quick Preset Selector */}
            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
              <label className="text-[11px] font-semibold text-sky-400 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Quick Preset Indian Cities / Vulnerability Hotspots:</span>
              </label>
              <select
                onChange={(e) => {
                  const idx = parseInt(e.target.value, 10);
                  if (idx >= 0 && PRESET_LOCATIONS[idx]) {
                    setCustomForm(PRESET_LOCATIONS[idx]);
                  }
                }}
                className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500"
              >
                {PRESET_LOCATIONS.map((preset, i) => (
                  <option key={i} value={i}>
                    {preset.name} ({preset.state}) - [{preset.latitude}, {preset.longitude}]
                  </option>
                ))}
              </select>
            </div>

            <form onSubmit={handleAddCustomLocation} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Location / Sector Name:</label>
                  <input
                    type="text"
                    required
                    value={customForm.name}
                    onChange={(e) => setCustomForm({ ...customForm, name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500 text-xs"
                    placeholder="e.g. Pune Western Ghats Basin"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">State / Region:</label>
                  <input
                    type="text"
                    required
                    value={customForm.state}
                    onChange={(e) => setCustomForm({ ...customForm, state: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500 text-xs"
                    placeholder="e.g. Maharashtra"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Latitude (°N):</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={customForm.latitude}
                    onChange={(e) => setCustomForm({ ...customForm, latitude: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500 font-mono text-xs"
                    placeholder="18.5204"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Longitude (°E):</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={customForm.longitude}
                    onChange={(e) => setCustomForm({ ...customForm, longitude: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500 font-mono text-xs"
                    placeholder="73.8567"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Elevation (Meters):</label>
                  <input
                    type="number"
                    value={customForm.elevation_m}
                    onChange={(e) => setCustomForm({ ...customForm, elevation_m: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500 font-mono text-xs"
                    placeholder="560"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Population Estimate:</label>
                  <input
                    type="number"
                    value={customForm.population_estimate}
                    onChange={(e) => setCustomForm({ ...customForm, population_estimate: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500 font-mono text-xs"
                    placeholder="3124000"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Topography Classification:</label>
                <input
                  type="text"
                  value={customForm.topography}
                  onChange={(e) => setCustomForm({ ...customForm, topography: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500 text-xs"
                  placeholder="e.g. Hilly Plateau / Coastal Strip / Mountain Basin"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Vulnerability & Description:</label>
                <textarea
                  rows="2"
                  value={customForm.description}
                  onChange={(e) => setCustomForm({ ...customForm, description: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500 text-xs"
                  placeholder="Susceptible hazards, river proximity, or flood vulnerability..."
                />
              </div>

              <div className="bg-sky-950/30 border border-sky-800/40 p-3 rounded-xl text-[11px] text-sky-300">
                ⚡ <strong>Instant AI Deployment:</strong> Adding this location will automatically fetch live weather from Open-Meteo, generate 24h baseline time-series, and execute an initial LSTM hazard prediction.
              </div>

              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddLocationModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addingCustomLocation}
                  className="px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-md transition flex items-center gap-1.5"
                >
                  <MapPin className={`w-3.5 h-3.5 ${addingCustomLocation ? 'animate-spin' : ''}`} />
                  <span>{addingCustomLocation ? 'Adding & Predicting...' : 'Add Location & Predict'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
