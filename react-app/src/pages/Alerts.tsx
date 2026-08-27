import { useState, useEffect } from 'react';
import { AlertCircle, AlertTriangle, Info, X, RefreshCw } from 'lucide-react';
import { apiService } from '../api';

export default function Alerts() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, critical, warning, info

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const [alertsRes, analysisRes] = await Promise.all([
        apiService.alerts.list(),
        apiService.alerts.analyze().catch(() => null),
      ]);

      setAlerts(alertsRes.data || []);
      if (analysisRes) setAnalysis(analysisRes.data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const getAlertColor = (alert: any) => {
    const type = alert.type?.toLowerCase();
    const priority = String(alert.priority || '').toLowerCase();
    const msg = alert.message?.toLowerCase() || '';

    if (priority === '1' || priority === 'critical' || msg.includes('urgency: critical')) {
      return 'bg-red-500/10 text-red-300 border-red-500/30';
    }
    if (priority === '2' || priority === '3' || priority === 'high' || priority === 'medium' || msg.includes('urgency: high') || msg.includes('urgency: medium')) {
      return 'bg-amber-500/10 text-amber-300 border-amber-500/30';
    }
    if (type === 'info' || priority === '4' || priority === 'low') {
      return 'bg-accent/10 text-accent border-accent/40';
    }
    return 'bg-ink-900 text-white border-ink-700';
  };

  const getAlertIcon = (alert: any) => {
    const priority = String(alert.priority || '').toLowerCase();
    const msg = alert.message?.toLowerCase() || '';

    if (priority === '1' || priority === 'critical' || msg.includes('urgency: critical')) {
      return AlertTriangle;
    }
    if (priority === '2' || priority === '3' || priority === 'high' || priority === 'medium') {
      return AlertCircle;
    }
    return Info;
  };

  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'all') return true;

    const priority = String(alert.priority || '').toLowerCase();
    const msg = alert.message?.toLowerCase() || '';
    const type = alert.type?.toLowerCase();

    if (filter === 'critical') {
      return priority === '1' || priority === 'critical' || msg.includes('urgency: critical');
    }
    if (filter === 'warning') {
      return priority === '2' || priority === '3' || priority === 'high' || priority === 'medium' || msg.includes('urgency: high') || msg.includes('urgency: medium');
    }
    if (filter === 'info') {
      return type === 'info' || priority === '4' || priority === '5' || priority === 'low';
    }
    return false;
  });

  // Limit to recent 50 alerts
  const displayedAlerts = filteredAlerts.slice(0, 50);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-ink-900 to-ink-800 flex items-center justify-center">
        <p className="text-slate-400">Loading alerts...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-ink-900 to-ink-800 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white flex items-center gap-2">
              <AlertCircle className="w-8 h-8 text-orange-400" />
              Alerts & Notifications
            </h1>
            <p className="text-slate-400 mt-2">Monitor system alerts and inventory warnings</p>
          </div>
          <button
            onClick={fetchAlerts}
            className="flex items-center gap-2 px-4 py-2 bg-ink-700 text-slate-300 rounded-none hover:bg-ink-700 transition"
          >
            <RefreshCw className="w-5 h-5" />
            Refresh
          </button>
        </div>

        {/* Alert Analysis */}
        {analysis && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-none p-6 border border-red-500/30">
              <p className="text-sm font-semibold text-red-300 mb-1">Critical</p>
              <p className="text-3xl font-bold text-red-400">{analysis.critical_count || 0}</p>
            </div>
            <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-none p-6 border border-amber-500/30">
              <p className="text-sm font-semibold text-amber-300 mb-1">Warnings</p>
              <p className="text-3xl font-bold text-amber-400">{analysis.warning_count || 0}</p>
            </div>
            <div className="bg-gradient-to-br from-accent/10 to-accent/5 rounded-none p-6 border border-accent/40">
              <p className="text-sm font-semibold text-accent mb-1">Info</p>
              <p className="text-3xl font-bold text-accent">{analysis.info_count || 0}</p>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-none p-6 border border-emerald-500/30">
              <p className="text-sm font-semibold text-emerald-300 mb-1">Resolved</p>
              <p className="text-3xl font-bold text-emerald-400">{analysis.resolved_count || 0}</p>
            </div>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          {['all', 'critical', 'warning', 'info'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-none font-semibold transition capitalize ${filter === f
                ? 'bg-gradient-to-r from-accent to-accent-hover text-white'
                : 'bg-ink-800 text-slate-300 border border-ink-700 hover:bg-ink-900'
                }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Alerts List */}
        <div className="bg-ink-800 rounded-none shadow-lg p-6">
          <h2 className="text-2xl font-bold text-white mb-4">
            {filter === 'all' ? 'Recent Alerts' : `${filter.toUpperCase()} Alerts`}
            <span className="text-slate-400 text-lg font-normal ml-2">
              (Showing {displayedAlerts.length} of {filteredAlerts.length})
            </span>
          </h2>

          {displayedAlerts.length === 0 ? (
            <div className="text-center py-12">
              <AlertCircle className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-400 text-lg">No {filter === 'all' ? '' : filter} alerts</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
              {displayedAlerts.map((alert: any, idx: number) => {
                const AlertIcon = getAlertIcon(alert);
                return (
                  <div
                    key={idx}
                    className={`flex items-start gap-4 p-4 rounded-none border transition hover:shadow-md ${getAlertColor(alert)}`}
                  >
                    <AlertIcon className="w-5 h-5 mt-1 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="flex justify-between items-start">
                        <p className="font-semibold whitespace-pre-line">{alert.message}</p>
                        <span className="text-xs font-medium px-2 py-1 bg-ink-800 bg-opacity-50 rounded-full border border-ink-700 ml-2">
                          {alert.type}
                        </span>
                      </div>
                      <p className="text-xs opacity-75 mt-2 flex items-center gap-1">
                        <span className="font-medium">Created:</span>
                        {new Date(alert.created_at || Date.now()).toLocaleString()}
                      </p>
                      {alert.details && (
                        <div className="text-sm mt-2 opacity-85 bg-ink-800 bg-opacity-40 p-2 rounded">
                          <p>SKU: {alert.details.sku}</p>
                          {alert.details.stock && <p>Stock: {alert.details.stock}</p>}
                          {alert.details.threshold && <p>Threshold: {alert.details.threshold}</p>}
                        </div>
                      )}
                    </div>
                    <button
                      className="text-lg hover:opacity-60 transition p-1"
                      title="Dismiss"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Key Insights */}
        {analysis && (
          <div className="mt-8 bg-gradient-to-br from-accent/10 to-accent/5 rounded-none p-6 border border-accent/40">
            <h3 className="text-xl font-bold text-white mb-3">🔍 Key Insights</h3>
            <div className="text-slate-300 space-y-2">
              <p>• System is monitoring <strong>{analysis.total_sku_monitored || 0}</strong> SKUs</p>
              <p>• Average alert resolution time: <strong>{analysis.avg_resolution_time || 'N/A'}</strong></p>
              <p>• Most common alert: <strong>{analysis.most_common_alert || 'N/A'}</strong></p>
              {analysis.recommendation && <p>• {analysis.recommendation}</p>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
