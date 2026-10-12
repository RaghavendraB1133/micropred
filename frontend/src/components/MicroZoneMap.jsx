import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import RiskBadge from './RiskBadge';
import { Navigation, CloudRain, Wind, Mountain, Users } from 'lucide-react';

export default function MicroZoneMap({ zones = [], onSelectZone }) {
  // Center map around geographic center of India
  const defaultCenter = [22.500, 78.900];
  const defaultZoom = 5;

  const getColor = (category) => {
    switch ((category || '').toUpperCase()) {
      case 'HIGH':
        return '#ef4444';
      case 'MEDIUM':
        return '#f59e0b';
      case 'LOW':
      default:
        return '#10b981';
    }
  };

  return (
    <div className="relative w-full h-[450px] rounded-xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-950">
      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        scrollWheelZoom={true}
        className="w-full h-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {zones.map((zone) => {
          const category = (zone.latest_prediction?.risk_category || 'LOW').toUpperCase();
          const score = zone.latest_prediction?.risk_score;
          const color = getColor(category);
          const snap = zone.latest_prediction?.input_features_snapshot || {};
          const isHigh = category === 'HIGH';
          const isMedium = category === 'MEDIUM';

          const markerRadius = isHigh ? 22 : (isMedium ? 18 : 14);
          const strokeWidth = isHigh ? 4 : (isMedium ? 3 : 2);
          const fillOpacity = isHigh ? 0.75 : (isMedium ? 0.60 : 0.45);

          return (
            <React.Fragment key={zone.id}>
              {/* Outer pulsing alert ring for High Hazard zones */}
              {isHigh && (
                <CircleMarker
                  center={[zone.latitude, zone.longitude]}
                  radius={32}
                  pathOptions={{
                    color: '#ef4444',
                    fillColor: '#ef4444',
                    fillOpacity: 0.18,
                    weight: 1.5,
                    dashArray: '4, 4'
                  }}
                />
              )}

              <CircleMarker
                center={[zone.latitude, zone.longitude]}
                radius={markerRadius}
                pathOptions={{
                  color: isHigh ? '#ffffff' : color,
                  fillColor: color,
                  fillOpacity: fillOpacity,
                  weight: strokeWidth,
                }}
              >
                <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
                  <div className="text-xs font-bold text-slate-900">
                    {zone.name} • <span style={{ color: color }}>{category} RISK</span>
                  </div>
                </Tooltip>

              <Popup className="custom-popup">
                <div className="p-1 min-w-[220px] text-slate-800">
                  <div className="flex items-center justify-between gap-2 border-b pb-1.5 mb-2">
                    <span className="font-bold text-sm text-slate-900">{zone.name}</span>
                    <span className="text-[10px] font-mono bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
                      {zone.zone_code}
                    </span>
                  </div>

                  <div className="mb-2">
                    <RiskBadge category={category} score={score} size="sm" />
                  </div>

                  <div className="grid grid-cols-2 gap-1.5 text-[11px] text-slate-600 mb-3">
                    <div className="flex items-center gap-1">
                      <CloudRain className="w-3 h-3 text-sky-600" />
                      <span>{snap.rainfall_mm !== undefined ? `${snap.rainfall_mm} mm` : '0 mm'}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Wind className="w-3 h-3 text-cyan-600" />
                      <span>{snap.wind_speed_kmh !== undefined ? `${snap.wind_speed_kmh} km/h` : '12 km/h'}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Mountain className="w-3 h-3 text-emerald-600" />
                      <span>{zone.elevation_m}m elv</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="w-3 h-3 text-indigo-600" />
                      <span>{(zone.population_estimate / 1000).toFixed(0)}k pop</span>
                    </div>
                  </div>

                  {onSelectZone && (
                    <button
                      onClick={() => onSelectZone(zone)}
                      className="w-full py-1 text-xs font-medium text-white bg-sky-600 hover:bg-sky-500 rounded transition text-center"
                    >
                      Inspect Zone History
                    </button>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          </React.Fragment>
          );
        })}
      </MapContainer>

      {/* Map Floating Legend */}
      <div className="absolute bottom-3 right-3 z-[1000] bg-slate-900/90 backdrop-blur-md border border-slate-700/60 rounded-lg p-2.5 shadow-xl text-xs space-y-1.5">
        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Hazard Tier</div>
        <div className="flex items-center gap-2 text-slate-200">
          <span className="w-3 h-3 rounded-full bg-emerald-500 border border-emerald-400" />
          <span>Low Hazard (&lt; 35%)</span>
        </div>
        <div className="flex items-center gap-2 text-slate-200">
          <span className="w-3 h-3 rounded-full bg-amber-500 border border-amber-400" />
          <span>Medium Hazard (35% - 70%)</span>
        </div>
        <div className="flex items-center gap-2 text-slate-200">
          <span className="w-3 h-3 rounded-full bg-rose-500 border border-rose-400" />
          <span>High Hazard (&ge; 70%)</span>
        </div>
      </div>
    </div>
  );
}
