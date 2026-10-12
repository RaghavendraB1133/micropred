import React, { useState, useEffect } from 'react';
import {
  Database, UploadCloud, CheckCircle2, AlertTriangle,
  FileText, Calendar, HardDrive, RefreshCw
} from 'lucide-react';
import apiService from '../services/api';

export default function DatasetStatus() {
  const [datasetInfo, setDatasetInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await apiService.getDatasetStatus();
      setDatasetInfo(res);
    } catch (err) {
      alert(`Failed to load dataset status: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleValidateFile = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      alert('Please select a CSV file first.');
      return;
    }

    setUploading(true);
    setValidationResult(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await apiService.validateDataset(formData);
      setValidationResult(res.validation_report);
    } catch (err) {
      alert(`Validation failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="h-96 flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="h-8 w-8 text-sky-400 animate-spin" />
        <p className="text-sm text-slate-400">Loading dataset metadata & provenance...</p>
      </div>
    );
  }

  const datasets = datasetInfo?.datasets || [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-md">
        <h1 className="text-2xl font-black text-white tracking-tight">Dataset Status & Provenance</h1>
        <p className="text-xs text-slate-400 mt-1">
          Historical dataset registration, data schema integrity checks, and validation reporting
        </p>
      </div>

      {/* Dataset Overview Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Registered Datasets</span>
            <Database className="h-4 w-4 text-sky-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">{datasets.length}</div>
          <span className="text-[11px] text-slate-500">Verified historical corpora</span>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Weather Observations</span>
            <FileText className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-400">
            {datasetInfo?.total_observations || 0}
          </div>
          <span className="text-[11px] text-slate-500">Sequential records in DB</span>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Storage Pipeline</span>
            <HardDrive className="h-4 w-4 text-indigo-400" />
          </div>
          <div className="text-sm font-bold text-slate-300">data/raw/</div>
          <span className="text-[11px] text-slate-500 font-mono">CSV Schema Compliant</span>
        </div>
      </div>

      {/* Registered Datasets List */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h2 className="text-base font-bold text-white mb-4">Active Historical Datasets</h2>
        {datasets.length === 0 ? (
          <p className="text-xs text-slate-500">No datasets registered yet.</p>
        ) : (
          <div className="space-y-3">
            {datasets.map((d) => (
              <div
                key={d.id}
                className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-sm text-white">{d.filename}</span>
                    <span className="inline-flex items-center gap-1 text-[10px] bg-emerald-950 border border-emerald-800 text-emerald-400 px-2 py-0.5 rounded-full font-semibold">
                      <CheckCircle2 className="w-3 h-3" />
                      {d.validation_status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mb-2">{d.description}</p>
                  <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 font-mono">
                    <span>{d.row_count} rows</span>
                    <span>•</span>
                    <span>{(d.file_size_bytes / 1024).toFixed(1)} KB</span>
                    <span>•</span>
                    <span>
                      {d.date_range_start ? new Date(d.date_range_start).toLocaleDateString() : 'N/A'} -{' '}
                      {d.date_range_end ? new Date(d.date_range_end).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Interactive CSV Dataset Validator Form */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h2 className="text-base font-bold text-white mb-1">CSV Dataset Integrity Validator</h2>
        <p className="text-xs text-slate-400 mb-4">
          Test any CSV dataset against schema requirements (missing values, geospatial bounds, timestamps)
        </p>

        <form onSubmit={handleValidateFile} className="space-y-4">
          <div className="border-2 border-dashed border-slate-800 hover:border-slate-700 rounded-xl p-6 text-center cursor-pointer bg-slate-950/40">
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setSelectedFile(e.target.files[0])}
              className="hidden"
              id="csvFileInput"
            />
            <label htmlFor="csvFileInput" className="cursor-pointer flex flex-col items-center">
              <UploadCloud className="h-8 w-8 text-sky-400 mb-2" />
              <span className="text-xs font-semibold text-slate-300">
                {selectedFile ? selectedFile.name : 'Click to select CSV dataset'}
              </span>
              <span className="text-[11px] text-slate-500 mt-1">
                Supported schema: timestamp, zone_code, latitude, longitude, rainfall_mm, temperature_c, etc.
              </span>
            </label>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={uploading || !selectedFile}
              className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold transition flex items-center gap-2 cursor-pointer"
            >
              <CheckCircle2 className={`w-4 h-4 ${uploading ? 'animate-spin' : ''}`} />
              <span>{uploading ? 'Validating Schema...' : 'Validate Dataset'}</span>
            </button>
          </div>
        </form>

        {/* Validation Result Inspection Card */}
        {validationResult && (
          <div className="mt-5 bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 animate-fade-in">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-xs font-bold text-white">Validation Results</span>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  validationResult.is_valid
                    ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                    : 'bg-rose-950 text-rose-400 border border-rose-800'
                }`}
              >
                {validationResult.is_valid ? 'PASSED SCHEMA CHECK' : 'VALIDATION FAILED'}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
              <div className="bg-slate-900 p-2.5 rounded-lg">
                <span className="text-slate-400 text-[10px]">Total Rows:</span>
                <div className="font-bold text-white mt-0.5">{validationResult.total_rows}</div>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-lg">
                <span className="text-slate-400 text-[10px]">Duplicates:</span>
                <div className="font-bold text-white mt-0.5">{validationResult.duplicate_rows_count}</div>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-lg">
                <span className="text-slate-400 text-[10px]">Detected Columns:</span>
                <div className="font-bold text-white mt-0.5">{validationResult.detected_columns?.length || 0}</div>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-lg">
                <span className="text-slate-400 text-[10px]">Hazard Events:</span>
                <div className="font-bold text-emerald-400 mt-0.5">
                  {validationResult.disaster_occurrence_rate !== null ? `${validationResult.disaster_occurrence_rate}%` : 'N/A'}
                </div>
              </div>
            </div>

            {validationResult.errors?.length > 0 && (
              <div className="text-xs text-rose-400 bg-rose-950/30 p-2.5 rounded-lg border border-rose-900/50">
                <strong>Errors: </strong> {validationResult.errors.join('; ')}
              </div>
            )}
            {validationResult.warnings?.length > 0 && (
              <div className="text-xs text-amber-400 bg-amber-950/30 p-2.5 rounded-lg border border-amber-900/50">
                <strong>Warnings: </strong> {validationResult.warnings.join('; ')}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
