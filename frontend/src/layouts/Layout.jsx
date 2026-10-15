import React, { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  Activity, MapPin, History, BarChart3, Database,
  ShieldCheck, HelpCircle, AlertOctagon, Terminal, Radio, Mail
} from 'lucide-react';
import apiService from '../services/api';
import DisclaimerModal from '../components/DisclaimerModal';

export default function Layout() {
  const [health, setHealth] = useState({ status: 'CHECKING', database: 'UNKNOWN' });
  const [alertsCount, setAlertsCount] = useState(0);
  const [isDisclaimerOpen, setIsDisclaimerOpen] = useState(false);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const [healthRes, alertsRes] = await Promise.all([
          apiService.getHealth(),
          apiService.getAlertsSummary()
        ]);
        setHealth({
          status: healthRes.status,
          database: healthRes.dependencies?.database?.status || 'CONNECTED'
        });
        setAlertsCount(alertsRes.critical_high_count || alertsRes.total_dispatched || 0);
      } catch (err) {
        setHealth({ status: 'OFFLINE', database: 'DISCONNECTED' });
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { to: '/', label: 'Dashboard', icon: Activity },
    { to: '/zones', label: 'Micro-Zones', icon: MapPin },
    { to: '/predictions', label: 'Prediction History', icon: History },
    { to: '/alerts', label: 'Email Alerts & Awareness', icon: Mail, count: alertsCount },
    { to: '/reports', label: 'Risk Reports', icon: BarChart3 },
    { to: '/datasets', label: 'Dataset Status', icon: Database },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 bg-slate-900/80 backdrop-blur-md border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-sky-600 via-indigo-600 to-cyan-400 p-0.5 shadow-lg shadow-sky-900/30">
              <div className="h-full w-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <AlertOctagon className="h-5 w-5 text-sky-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-sm md:text-base tracking-tight bg-gradient-to-r from-sky-400 via-cyan-300 to-indigo-300 bg-clip-text text-transparent uppercase">
                  MICRO-ZONE DISASTER PREDICTION SYSTEM
                </span>
                <span className="hidden sm:inline-flex text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800/60 font-medium">
                  LSTM Engine
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Real-Time Hydro-Meteorological Hazard &amp; Future Forecasting
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                      isActive
                        ? 'bg-sky-600/20 text-sky-300 border border-sky-500/30 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                    }`
                  }
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                  {item.count !== undefined && item.count > 0 && (
                    <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-rose-600 text-white font-bold leading-none animate-pulse">
                      {item.count}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>

          {/* Right Status Badges & Disclaimer Button */}
          <div className="flex items-center gap-3">
            {/* Live System Status Indicator */}
            <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs">
              <span
                className={`h-2 w-2 rounded-full ${
                  health.status === 'HEALTHY'
                    ? 'bg-emerald-500 shadow-sm shadow-emerald-500'
                    : health.status === 'DEGRADED'
                    ? 'bg-amber-500'
                    : 'bg-rose-500'
                } animate-pulse`}
              />
              <span className="text-[11px] text-slate-300 font-medium">
                {health.status === 'HEALTHY' ? 'SYSTEM LIVE' : health.status}
              </span>
            </div>

            <button
              onClick={() => setIsDisclaimerOpen(true)}
              className="flex items-center gap-1 text-xs text-slate-400 hover:text-sky-300 hover:bg-slate-800/80 px-2 py-1 rounded-md transition"
              title="View Scientific Scope & Disclaimers"
            >
              <HelpCircle className="h-4 w-4 text-sky-400" />
              <span className="hidden lg:inline text-[11px]">Notice</span>
            </button>
          </div>
        </div>

        {/* Mobile Navigation Bar */}
        <div className="md:hidden border-t border-slate-800/80 px-4 py-2 flex items-center justify-around bg-slate-950/90 overflow-x-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex flex-col items-center gap-1 px-2 py-1 text-[10px] font-medium ${
                    isActive ? 'text-sky-400' : 'text-slate-400'
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </div>
      </header>

      {/* Scientific Notice Banner */}
      <div className="bg-sky-950/40 border-b border-sky-900/30 px-4 py-1.5 text-center text-[11px] text-sky-300 flex items-center justify-center gap-2">
        <ShieldCheck className="h-3.5 w-3.5 text-sky-400 shrink-0" />
        <span>
          Academic Decision-Support System: Predictive inference is generated from verified historical hydro-meteorological observations.
        </span>
        <button
          onClick={() => setIsDisclaimerOpen(true)}
          className="underline font-semibold hover:text-white ml-1 cursor-pointer"
        >
          Read Disclaimers
        </button>
      </div>

      {/* Main Page Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/90 text-slate-500 text-xs py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 text-center space-y-1">
          <p className="font-medium text-slate-400">
            Human Behavior Aware Micro-Zone Disaster Prediction System Using AI
          </p>
          <p className="text-[11px]">
            Final-Year AIML Project • Powered by TensorFlow LSTM & Neon PostgreSQL • Academic Decision-Support System
          </p>
        </div>
      </footer>

      {/* Scientific Framework Modal */}
      <DisclaimerModal
        isOpen={isDisclaimerOpen}
        onClose={() => setIsDisclaimerOpen(false)}
      />
    </div>
  );
}
