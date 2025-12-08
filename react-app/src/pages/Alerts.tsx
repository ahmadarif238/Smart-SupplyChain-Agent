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
      return 'bg-red-50 text-red-900 border-red-200';
    }
    if (priority === '2' || priority === '3' || priority === 'high' || priority === 'medium' || msg.includes('urgency: high') || msg.includes('urgency: medium')) {
      return 'bg-yellow-50 text-yellow-900 border-yellow-200';
    }
    if (type === 'info' || priority === '4' || priority === 'low') {
      return 'bg-blue-50 text-blue-900 border-blue-200';
    }
    return 'bg-gray-50 text-gray-900 border-gray-200';
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
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <p className="text-gray-600">Loading alerts...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 flex items-center gap-2">
              <AlertCircle className="w-8 h-8 text-orange-600" />
              Alerts & Notifications
            </h1>
            <p className="text-gray-600 mt-2">Monitor system alerts and inventory warnings</p>
          </div>
          <button
            onClick={fetchAlerts}
            className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
          >
            <RefreshCw className="w-5 h-5" />
            Refresh
          </button>
        </div>

        {/* Alert Analysis */}
        {analysis && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-lg p-6 border border-red-300">
              <p className="text-sm font-semibold text-red-900 mb-1">Critical</p>
              <p className="text-3xl font-bold text-red-600">{analysis.critical_count || 0}</p>
            </div>
            <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg p-6 border border-yellow-300">
              <p className="text-sm font-semibold text-yellow-900 mb-1">Warnings</p>
              <p className="text-3xl font-bold text-yellow-600">{analysis.warning_count || 0}</p>
            </div>
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-300">
              <p className="text-sm font-semibold text-blue-900 mb-1">Info</p>
              <p className="text-3xl font-bold text-blue-600">{analysis.info_count || 0}</p>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6 border border-green-300">
              <p className="text-sm font-semibold text-green-900 mb-1">Resolved</p>
              <p className="text-3xl font-bold text-green-600">{analysis.resolved_count || 0}</p>
            </div>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          {['all', 'critical', 'warning', 'info'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg font-semibold transition capitalize ${filter === f
                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Alerts List */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            {filter === 'all' ? 'Recent Alerts' : `${filter.toUpperCase()} Alerts`}
            <span className="text-gray-500 text-lg font-normal ml-2">
              (Showing {displayedAlerts.length} of {filteredAlerts.length})
            </span>
          </h2>

          {displayedAlerts.length === 0 ? (
            <div className="text-center py-12">
              <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No {filter === 'all' ? '' : filter} alerts</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
              {displayedAlerts.map((alert: any, idx: number) => {
                const AlertIcon = getAlertIcon(alert);
                return (
                  <div
                    key={idx}
                    className={`flex items-start gap-4 p-4 rounded-lg border transition hover:shadow-md ${getAlertColor(alert)}`}
                  >
                    <AlertIcon className="w-5 h-5 mt-1 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="flex justify-between items-start">
                        <p className="font-semibold whitespace-pre-line">{alert.message}</p>
                        <span className="text-xs font-medium px-2 py-1 bg-white bg-opacity-50 rounded-full border border-gray-200 ml-2">
                          {alert.type}
                        </span>
                      </div>
                      <p className="text-xs opacity-75 mt-2 flex items-center gap-1">
                        <span className="font-medium">Created:</span>
                        {new Date(alert.created_at || Date.now()).toLocaleString()}
                      </p>
                      {alert.details && (
                        <div className="text-sm mt-2 opacity-85 bg-white bg-opacity-40 p-2 rounded">
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
          <div className="mt-8 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6 border border-purple-300">
            <h3 className="text-xl font-bold text-gray-900 mb-3">🔍 Key Insights</h3>
            <div className="text-gray-700 space-y-2">
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
