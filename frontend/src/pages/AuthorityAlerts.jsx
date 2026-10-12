import React, { useState, useEffect } from 'react';
import {
  Radio, Send, ShieldAlert, CheckCircle2, Phone,
  Clock, AlertTriangle, RefreshCw, Filter, Building2,
  ChevronLeft, ChevronRight, MessageSquareText,
  Mail, Eye, BookOpen, HeartHandshake, ShieldCheck, X,
  Settings, Key, Check
} from 'lucide-react';
import apiService from '../services/api';

export default function AuthorityAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [authorities, setAuthorities] = useState([]);
  const [summary, setSummary] = useState(null);
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [broadcasting, setBroadcasting] = useState(false);
  const [selectedZoneId, setSelectedZoneId] = useState('');
  const [recipientEmail, setRecipientEmail] = useState('');
  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailPreviewModal, setEmailPreviewModal] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [filterAgency, setFilterAgency] = useState('ALL');
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState({ total: 0, pages: 1 });

  // Live SMTP Configuration states
  const [isSmtpModalOpen, setIsSmtpModalOpen] = useState(false);
  const [smtpConfig, setSmtpConfig] = useState(null);
  const [smtpForm, setSmtpForm] = useState({
    server: 'smtp.gmail.com',
    port: 587,
    username: '',
    password: '',
    sender: '',
  });
  const [testingSmtp, setTestingSmtp] = useState(false);
  const [savingSmtp, setSavingSmtp] = useState(false);
  const [smtpTestResult, setSmtpTestResult] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = { page, per_page: 12 };
      if (filterAgency !== 'ALL') params.authority_code = filterAgency;

      const [alertsRes, authRes, sumRes, zonesRes, smtpRes] = await Promise.all([
        apiService.getAlerts(params),
        apiService.getAuthorities(),
        apiService.getAlertsSummary(),
        apiService.getZones({ per_page: 50 }),
        apiService.getSmtpConfig().catch(() => null)
      ]);

      setAlerts(alertsRes.alerts || []);
      setPagination(alertsRes.pagination || { total: 0, pages: 1 });
      setAuthorities(authRes.authorities || []);
      setSummary(sumRes || {});
      setZones(zonesRes.zones || []);
      if (smtpRes) {
        setSmtpConfig(smtpRes);
        setSmtpForm(prev => ({
          ...prev,
          server: smtpRes.server || 'smtp.gmail.com',
          port: smtpRes.port || 587,
          username: smtpRes.username || '',
          sender: smtpRes.sender || smtpRes.username || '',
        }));
      }
      if (!selectedZoneId && zonesRes.zones?.length > 0) {
        setSelectedZoneId(zonesRes.zones[0].id);
      }
    } catch (err) {
      alert(`Error loading alerts: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, filterAgency]);

  const handleTriggerDrill = async () => {
    if (!selectedZoneId) {
      alert('Please select a micro-zone.');
      return;
    }
    setBroadcasting(true);
    try {
      const res = await apiService.broadcastDrill(selectedZoneId);
      alert(`✅ Emergency broadcast transmitted to ${res.count} authority channels.`);
      fetchData();
    } catch (err) {
      alert(`Broadcast failed: ${err.message}`);
    } finally {
      setBroadcasting(false);
    }
  };

  const handleSendEmailAlert = async () => {
    if (!selectedZoneId) {
      alert('Please select a micro-zone.');
      return;
    }
    if (!recipientEmail) {
      alert('Please enter a recipient email address.');
      return;
    }
    setSendingEmail(true);
    try {
      const res = await apiService.sendEmailAlert(selectedZoneId, recipientEmail);
      if (res.delivery_status === 'DELIVERED_VIA_SMTP') {
        alert(`📧 LIVE EMAIL DELIVERED VIA SMTP!\nSent directly to: ${recipientEmail}\nIncludes 5-Year Data Disaster Prediction & Human Behavior Awareness Guidelines.`);
      } else {
        alert(`📧 Alert sent! Note: Real SMTP credentials are not yet configured, so delivery was recorded and simulated. Click '⚙️ Configure SMTP' to send live emails to inboxes.`);
      }
      fetchData();
    } catch (err) {
      alert(`Email dispatch failed: ${err.message}`);
    } finally {
      setSendingEmail(false);
    }
  };

  const handleTestSmtp = async () => {
    if (!smtpForm.username || !smtpForm.password) {
      alert('Please enter both your SMTP email/username and password/app password to test the connection.');
      return;
    }
    setTestingSmtp(true);
    setSmtpTestResult(null);
    try {
      const res = await apiService.testSmtpConnection({
        server: smtpForm.server,
        port: parseInt(smtpForm.port, 10),
        username: smtpForm.username,
        password: smtpForm.password,
        sender: smtpForm.sender || smtpForm.username,
        test_recipient: recipientEmail || smtpForm.username
      });
      setSmtpTestResult(res);
      if (res.status === 'SUCCESS') {
        const fresh = await apiService.getSmtpConfig();
        setSmtpConfig(fresh);
      }
    } catch (err) {
      setSmtpTestResult({
        status: 'ERROR',
        message: err.message || 'SMTP Connection failed'
      });
    } finally {
      setTestingSmtp(false);
    }
  };

  const handleSaveSmtp = async () => {
    setSavingSmtp(true);
    try {
      const res = await apiService.saveSmtpConfig({
        server: smtpForm.server,
        port: parseInt(smtpForm.port, 10),
        username: smtpForm.username,
        password: smtpForm.password,
        sender: smtpForm.sender || smtpForm.username,
      });
      alert('✅ SMTP Settings saved and active! Real disaster alert emails will now be sent to recipient inboxes.');
      setSmtpConfig(res.config);
      setIsSmtpModalOpen(false);
    } catch (err) {
      alert(`Failed to save SMTP: ${err.message}`);
    } finally {
      setSavingSmtp(false);
    }
  };

  const handleOpenEmailPreview = async () => {
    if (!selectedZoneId) {
      alert('Please select a micro-zone.');
      return;
    }
    setLoadingPreview(true);
    try {
      const res = await apiService.getEmailPreview(selectedZoneId);
      setEmailPreviewModal(res);
    } catch (err) {
      alert(`Failed to load email preview: ${err.message}`);
    } finally {
      setLoadingPreview(false);
    }
  };

  if (loading && alerts.length === 0) {
    return (
      <div className="h-96 flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="h-8 w-8 text-rose-400 animate-spin" />
        <p className="text-sm text-slate-400">Loading emergency authority communications...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Radio className="w-5 h-5 text-rose-500 animate-pulse" />
            <h1 className="text-2xl font-black text-white tracking-tight">
              Authority Emergency Dispatch & Early-Warning Relays
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Automated signals and priority SMS/webhook messages transmitted to disaster management agencies upon High Risk detection
          </p>
        </div>

        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-slate-700 transition"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Signals</span>
        </button>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-xs font-medium">Dispatched Signals</span>
            <Radio className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">{summary?.total_dispatched || 0}</div>
          <span className="text-[11px] text-slate-500">Transmitted messages</span>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-xs font-medium">Critical Alerts</span>
            <ShieldAlert className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-extrabold text-rose-400">{summary?.critical_high_count || 0}</div>
          <span className="text-[11px] text-slate-500">High hazard triggers</span>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-xs font-medium">Active Agencies</span>
            <Building2 className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-extrabold text-sky-400">{authorities.length}</div>
          <span className="text-[11px] text-slate-500">DDMA, NDRF, SEOC, GCC</span>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-xs font-medium">Dispatch Relay</span>
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
          </div>
          <div className="text-sm font-bold text-emerald-400">AUTOMATED</div>
          <span className="text-[11px] text-slate-500">Auto-triggers on High Risk</span>
        </div>
      </div>

      {/* Registered Authority Agencies Directory */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <h2 className="text-base font-bold text-white mb-1 flex items-center gap-2">
          <Building2 className="w-4 h-4 text-indigo-400" />
          Configured Emergency Authority Channels
        </h2>
        <p className="text-xs text-slate-400 mb-4">
          Recipients automatically notified when any micro-zone scores ≥ 70% hazard probability
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {authorities.map((auth) => (
            <div key={auth.code} className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-sky-400 font-mono bg-sky-950/80 px-2 py-0.5 rounded border border-sky-800">
                    {auth.code}
                  </span>
                  <span className="text-[10px] text-emerald-400 font-semibold bg-emerald-950 px-1.5 py-0.5 rounded">
                    CONNECTED
                  </span>
                </div>
                <h3 className="text-xs font-bold text-white mb-1">{auth.name}</h3>
                <p className="text-[11px] text-slate-400 mb-2 leading-relaxed">{auth.role}</p>
              </div>

              <div className="pt-2 border-t border-slate-800/80 text-[11px] font-mono text-slate-300 flex items-center gap-1.5">
                <Phone className="w-3 h-3 text-emerald-400" />
                <span className="truncate">{auth.contact}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Human Behavior Aware Email Alert Dispatcher */}
      <div className="bg-gradient-to-r from-sky-950/40 via-indigo-950/30 to-slate-900 border border-sky-800/50 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Mail className="w-5 h-5 text-sky-400" />
              <h3 className="text-base font-bold text-white">
                Human Behavior Aware Email Alert Dispatcher
              </h3>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              Transmits AI disaster prediction warnings with actionable public safety instructions, evacuation guidance, and emergency kits via email
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className={`text-[11px] font-mono px-2.5 py-1 rounded-lg border flex items-center gap-1.5 ${
              smtpConfig?.is_configured 
                ? 'bg-emerald-950/80 text-emerald-300 border-emerald-700' 
                : 'bg-amber-950/80 text-amber-300 border-amber-700'
            }`}>
              <span className={`w-2 h-2 rounded-full ${smtpConfig?.is_configured ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              {smtpConfig?.is_configured ? 'SMTP Live Gateway Ready' : 'SMTP Simulated Gateway'}
            </span>

            <button
              onClick={() => setIsSmtpModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold border border-slate-700 transition cursor-pointer shadow-sm"
              title="Configure SMTP Server Credentials to send live emails to inboxes"
            >
              <Settings className="w-3.5 h-3.5 text-sky-400" />
              <span>Configure SMTP</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
          <div className="md:col-span-4 space-y-1">
            <label className="text-[11px] font-semibold text-slate-400">Target Micro-Zone:</label>
            <select
              value={selectedZoneId}
              onChange={(e) => setSelectedZoneId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:border-sky-500"
            >
              {zones.map((z) => (
                <option key={z.id} value={z.id}>
                  {z.zone_code} - {z.name}
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-4 space-y-1">
            <label className="text-[11px] font-semibold text-slate-400">Recipient Email Address:</label>
            <input
              type="email"
              value={recipientEmail}
              onChange={(e) => setRecipientEmail(e.target.value)}
              placeholder="e.g. collector@district.gov.in"
              className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:border-sky-500 placeholder-slate-600"
            />
          </div>

          <div className="md:col-span-4 flex items-center gap-2">
            <button
              onClick={handleOpenEmailPreview}
              disabled={loadingPreview}
              className="flex-1 py-2.5 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition flex items-center justify-center gap-1.5 cursor-pointer"
              title="Preview Human Behavior Safety Guide & Email"
            >
              <Eye className="w-3.5 h-3.5 text-sky-400" />
              <span>{loadingPreview ? 'Loading...' : 'Preview Guide'}</span>
            </button>

            <button
              onClick={handleSendEmailAlert}
              disabled={sendingEmail}
              className="flex-1 py-2.5 px-3 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-lg shadow-sky-950 transition flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <Send className={`w-3.5 h-3.5 ${sendingEmail ? 'animate-spin' : ''}`} />
              <span>{sendingEmail ? 'Sending...' : 'Send Alert Email'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Manual Emergency Drill Broadcast Form */}
      <div className="bg-gradient-to-r from-rose-950/30 via-slate-900 to-slate-900 border border-rose-900/40 rounded-2xl p-5 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-500 animate-pulse" />
            <h3 className="text-sm font-bold text-white">Manual Authority Broadcast Drill</h3>
          </div>
          <p className="text-xs text-slate-300 mt-1">
            Simulate transmitting an urgent early-warning signal across all four disaster management channels for presentation demonstration
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedZoneId}
            onChange={(e) => setSelectedZoneId(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:border-rose-500"
          >
            {zones.map((z) => (
              <option key={z.id} value={z.id}>
                {z.zone_code} - {z.name}
              </option>
            ))}
          </select>

          <button
            onClick={handleTriggerDrill}
            disabled={broadcasting}
            className="px-4 py-2.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold transition flex items-center gap-2 cursor-pointer shadow-lg shadow-rose-950 shrink-0"
          >
            <Send className={`w-3.5 h-3.5 ${broadcasting ? 'animate-spin' : ''}`} />
            <span>{broadcasting ? 'Transmitting...' : 'Transmit Signal'}</span>
          </button>
        </div>
      </div>

      {/* Transmitted Signals Feed */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-white">Live Dispatched Signals Feed</h2>
            <p className="text-xs text-slate-400">Chronological transmission log of messages dispatched to authorities</p>
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={filterAgency}
              onChange={(e) => { setFilterAgency(e.target.value); setPage(1); }}
              className="bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-sky-500"
            >
              <option value="ALL">All Authorities</option>
              {authorities.map((a) => (
                <option key={a.code} value={a.code}>{a.code}</option>
              ))}
            </select>
          </div>
        </div>

        {alerts.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-xs">
            No authority alerts have been dispatched yet. Run a prediction on a High-Risk zone to trigger automatic signals.
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 hover:border-slate-700 transition"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-2 mb-2.5 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-rose-400 font-mono bg-rose-950 px-2 py-0.5 rounded border border-rose-800">
                      {alert.authority_code}
                    </span>
                    <span className="font-semibold text-white">{alert.authority_name}</span>
                  </div>

                  <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
                    <span className="flex items-center gap-1 text-emerald-400">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>{alert.dispatch_status}</span>
                    </span>
                    <span>•</span>
                    <span>{new Date(alert.dispatched_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                  </div>
                </div>

                <div className="text-xs text-slate-300 font-mono bg-slate-900/70 p-3 rounded-lg border border-slate-800 leading-relaxed mb-2.5">
                  <MessageSquareText className="w-3.5 h-3.5 text-rose-400 inline mr-1.5" />
                  <span>{alert.message_body}</span>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
                  <div className="flex items-center gap-3">
                    <span>Sector: <strong className="text-slate-200">{alert.zone_name} ({alert.zone_code})</strong></span>
                    <span>Channel: <strong className="text-sky-300">{alert.channel}</strong></span>
                  </div>
                  <div>Recipient Relay: <strong className="text-slate-200">{alert.recipient_contact}</strong></div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-xs text-slate-400">
          <div>
            Page <span className="font-semibold text-slate-200">{page}</span> of <span className="font-semibold text-slate-200">{pagination.pages || 1}</span> ({pagination.total} signals total)
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(p - 1, 1))}
              disabled={page <= 1}
              className="p-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 rounded-lg transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage(p => Math.min(p + 1, pagination.pages || 1))}
              disabled={page >= (pagination.pages || 1)}
              className="p-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 rounded-lg transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Human Behavior Awareness & Email Preview Modal */}
      {emailPreviewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-2xl my-8">
            <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <span className="text-[10px] font-mono uppercase bg-rose-950 text-rose-300 border border-rose-800 px-2 py-0.5 rounded font-bold">
                  {emailPreviewModal.human_awareness_guide?.risk_level} HAZARD ({Math.round(emailPreviewModal.risk_score * 100)}%)
                </span>
                <h3 className="text-lg font-bold text-white mt-1">
                  Human Behavior Awareness & Safety Advisory
                </h3>
                <p className="text-xs text-slate-400">
                  Target Sector: {emailPreviewModal.zone_name} ({emailPreviewModal.zone_code})
                </p>
              </div>
              <button
                onClick={() => setEmailPreviewModal(null)}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Structured Guidelines */}
            <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
              {/* 1. Immediate Actions */}
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                <h4 className="text-xs font-bold text-rose-400 uppercase flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4" />
                  1. Immediate Human Safety Actions
                </h4>
                <ul className="space-y-1.5 text-xs text-slate-300">
                  {emailPreviewModal.human_awareness_guide?.immediate_actions?.map((act, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-rose-500 font-bold">•</span>
                      <span>{act}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* 2. Emergency Kit Checklist */}
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                <h4 className="text-xs font-bold text-amber-400 uppercase flex items-center gap-1.5">
                  <BookOpen className="w-4 h-4" />
                  2. Essential Emergency Kit Checklist
                </h4>
                <ul className="space-y-1.5 text-xs text-slate-300">
                  {emailPreviewModal.human_awareness_guide?.emergency_kit_checklist?.map((kit, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-amber-500 font-bold">•</span>
                      <span>{kit}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* 3. Community Behavior */}
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                <h4 className="text-xs font-bold text-sky-400 uppercase flex items-center gap-1.5">
                  <HeartHandshake className="w-4 h-4" />
                  3. Community Behavioral Advisory
                </h4>
                <ul className="space-y-1.5 text-xs text-slate-300">
                  {emailPreviewModal.human_awareness_guide?.community_behavioral_advisory?.map((com, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-sky-500 font-bold">•</span>
                      <span>{com}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* 4. Emergency Contacts */}
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                <h4 className="text-xs font-bold text-emerald-400 uppercase flex items-center gap-1.5">
                  <Phone className="w-4 h-4" />
                  4. Emergency Helplines
                </h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {emailPreviewModal.human_awareness_guide?.emergency_contacts?.map((c, i) => (
                    <div key={i} className="bg-slate-900 p-2 rounded-lg border border-slate-800">
                      <span className="text-slate-400 block text-[10px]">{c.agency}</span>
                      <strong className="text-emerald-400 font-mono">{c.phone}</strong>
                    </div>
                  ))}
                </div>
              </div>

              {/* Email Subject & Dispatch Info */}
              <div className="bg-sky-950/30 p-3.5 rounded-xl border border-sky-800/60 text-xs space-y-1">
                <span className="text-[11px] text-sky-400 font-bold block">Generated Email Subject:</span>
                <p className="text-slate-200 font-mono text-[11px]">{emailPreviewModal.email_subject}</p>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-3">
              <button
                onClick={() => setEmailPreviewModal(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition cursor-pointer"
              >
                Close Preview
              </button>
              <button
                onClick={() => {
                  setEmailPreviewModal(null);
                  handleSendEmailAlert();
                }}
                className="px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md transition flex items-center gap-2 cursor-pointer"
              >
                <Mail className="w-4 h-4" />
                <span>Send Alert Email to {recipientEmail}</span>
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Live SMTP Configuration Modal */}
      {isSmtpModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-5 animate-in fade-in duration-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-sky-950 rounded-xl border border-sky-800 text-sky-400">
                  <Settings className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">
                    SMTP Email Server Configuration
                  </h3>
                  <p className="text-xs text-slate-400">
                    Connect real email gateway (Gmail, Outlook, or Custom SMTP) to send alerts
                  </p>
                </div>
              </div>
              <button
                onClick={() => { setIsSmtpModalOpen(false); setSmtpTestResult(null); }}
                className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Instruction Tip */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs space-y-2">
              <div className="flex items-center gap-1.5 text-sky-400 font-semibold">
                <Key className="w-3.5 h-3.5" />
                <span>Gmail Setup Instructions:</span>
              </div>
              <ol className="list-decimal list-inside space-y-1 text-slate-300 text-[11px] leading-relaxed">
                <li>Make sure 2-Step Verification is enabled on your Google Account.</li>
                <li>Go to <strong className="text-white">Google Account &gt; Security &gt; 2-Step Verification &gt; App Passwords</strong>.</li>
                <li>Create an App Password for &quot;Mail&quot; (generates a 16-character code like <code className="bg-slate-900 text-amber-300 px-1 py-0.5 rounded">abcd efgh ijkl mnop</code>).</li>
                <li>Enter your Gmail address below, and paste the 16-character App Password.</li>
              </ol>
            </div>

            {/* Form Fields */}
            <div className="space-y-3.5 text-xs">
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2 space-y-1">
                  <label className="text-slate-400 font-medium">SMTP Server Host:</label>
                  <input
                    type="text"
                    value={smtpForm.server}
                    onChange={(e) => setSmtpForm({ ...smtpForm, server: e.target.value })}
                    placeholder="smtp.gmail.com"
                    className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500 font-mono text-xs"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-slate-400 font-medium">Port:</label>
                  <input
                    type="number"
                    value={smtpForm.port}
                    onChange={(e) => setSmtpForm({ ...smtpForm, port: e.target.value })}
                    placeholder="587"
                    className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500 font-mono text-xs"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Email / Username:</label>
                <input
                  type="email"
                  value={smtpForm.username}
                  onChange={(e) => setSmtpForm({ ...smtpForm, username: e.target.value })}
                  placeholder="e.g. yourname@gmail.com"
                  className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500 text-xs"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Password or Gmail 16-Char App Password:</label>
                <input
                  type="password"
                  value={smtpForm.password}
                  onChange={(e) => setSmtpForm({ ...smtpForm, password: e.target.value })}
                  placeholder={smtpConfig?.is_configured ? '•••••••••••••••• (Leave blank to keep existing)' : 'Enter 16-char App Password'}
                  className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500 text-xs"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Sender Display Address (Optional):</label>
                <input
                  type="email"
                  value={smtpForm.sender}
                  onChange={(e) => setSmtpForm({ ...smtpForm, sender: e.target.value })}
                  placeholder="Leave empty to use Email/Username"
                  className="w-full bg-slate-950 border border-slate-800 text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-sky-500 text-xs"
                />
              </div>
            </div>

            {/* Test Connection Output Feedback */}
            {smtpTestResult && (
              <div className={`p-3 rounded-xl border text-xs flex items-start gap-2.5 ${
                smtpTestResult.status === 'SUCCESS'
                  ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                  : 'bg-rose-950/40 border-rose-800 text-rose-300'
              }`}>
                {smtpTestResult.status === 'SUCCESS' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="font-bold">
                    {smtpTestResult.status === 'SUCCESS' ? 'SMTP Authentication Verified!' : 'SMTP Connection Error'}
                  </div>
                  <div className="text-[11px] opacity-90 mt-0.5">
                    {smtpTestResult.message}
                  </div>
                </div>
              </div>
            )}

            {/* Modal Buttons */}
            <div className="pt-3 border-t border-slate-800 flex items-center justify-between gap-3">
              <button
                onClick={handleTestSmtp}
                disabled={testingSmtp}
                className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition flex items-center gap-1.5 cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 text-sky-400 ${testingSmtp ? 'animate-spin' : ''}`} />
                <span>{testingSmtp ? 'Testing Handshake...' : 'Test SMTP Connection'}</span>
              </button>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => { setIsSmtpModalOpen(false); setSmtpTestResult(null); }}
                  className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveSmtp}
                  disabled={savingSmtp}
                  className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-md transition flex items-center gap-1.5 cursor-pointer"
                >
                  <Check className={`w-3.5 h-3.5 ${savingSmtp ? 'animate-spin' : ''}`} />
                  <span>{savingSmtp ? 'Saving...' : 'Save & Enable SMTP'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
