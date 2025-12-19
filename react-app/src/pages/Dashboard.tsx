import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, AlertCircle, Zap, RefreshCw, Play, DollarSign, Package, Award} from 'lucide-react';
import { Link } from 'react-router-dom';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { apiService } from '../api';
import Card from '../components/ui/Card';

export default function Dashboard() {
  const [stats, setStats] = useState({
    inventory: 0,
    orders: 0,
    alerts: 0,
    totalValue: 0,
  });

  const [trends, setTrends] = useState({
    inventoryTrend: 0,
    ordersTrend: 0,
    valueTrend: 0,
    negotiationWins: 0,
  });

  const [sparklineData, setSparklineData] = useState<any>({
    inventory: [],
    orders: [],
    value: [],
  });

  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [agentRunning, setAgentRunning] = useState(false);
  const [agentJobs, setAgentJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [previousStats, setPreviousStats] = useState<any>(null);

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      // Check system health
      const healthRes = await apiService.health();
      setSystemStatus(healthRes.data);

      // Fetch all data in parallel
      const [inventoryRes, ordersRes, alertsRes, jobsRes, financeRes] = await Promise.all([
        apiService.inventory.list().catch(() => ({ data: [] })),
        apiService.orders.list().catch(() => ({ data: [] })),
        apiService.alerts.list().catch(() => ({ data: [] })),
        apiService.agent.jobs().catch(() => ({ data: [] })),
        apiService.get('/agent/finance-summary').catch(() => ({ data: null })),
      ]);

      const inventory = inventoryRes.data || [];
      const orders = ordersRes.data || [];
      const alerts = alertsRes.data || [];
      const financeData = financeRes.data;

      // Handle jobs response
      let jobs = [];
      if (Array.isArray(jobsRes.data)) {
        jobs = jobsRes.data;
      } else if (jobsRes.data?.recent_jobs) {
        jobs = jobsRes.data.recent_jobs;
      } else if (jobsRes.data?.jobs) {
        jobs = jobsRes.data.jobs;
      }

      // Calculate total value
      const totalValue = inventory.reduce((sum: number, item: any) => {
        return sum + ((item.quantity || 0) * (item.unit_price || 0));
      }, 0);

      const currentStats = {
        inventory: inventory.length,
        orders: orders.length,
        alerts: alerts.length,
        totalValue,
      };

      // Calculate trends (compare with previous)
      if (previousStats) {
        setTrends({
          inventoryTrend: calculatePercentageChange(previousStats.inventory, currentStats.inventory),
          ordersTrend: calculatePercentageChange(previousStats.orders, currentStats.orders),
          valueTrend: calculatePercentageChange(previousStats.totalValue, currentStats.totalValue),
          negotiationWins: financeData?.override_count || 0,
        });
      } else {
        // First load - generate mock trend data
        setTrends({
          inventoryTrend: 12,
          ordersTrend: 8,
          valueTrend: 15,
          negotiationWins: financeData?.override_count || 0,
        });
      }

      // Generate sparkline data (last 7 data points)
      setSparklineData({
        inventory: generateSparklineData(currentStats.inventory, 7),
        orders: generateSparklineData(currentStats.orders, 7),
        value: generateSparklineData(currentStats.totalValue / 1000, 7),
      });

      setStats(currentStats);
      setPreviousStats(currentStats);
      setAgentJobs(jobs);
      setAgentRunning(jobs.some((j: any) => j.status === 'running'));
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Calculate percentage change
  const calculatePercentageChange = (oldVal: number, newVal: number) => {
    if (oldVal === 0) return newVal > 0 ? 100 : 0;
    return ((newVal - oldVal) / oldVal) * 100;
  };

  // Generate sparkline data (mock for now, replace with real historical data)
  const generateSparklineData = (current: number, points: number) => {
    const data = [];
    for (let i = points - 1; i >= 0; i--) {
      const variance = (Math.random() - 0.5) * 0.2; // ±10% variance
      const value = Math.max(0, current * (1 + variance * (i / points)));
      data.push({ value });
    }
    return data;
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // Mini Sparkline Component
  const MiniSparkline = ({ data, color }: { data: any[], color: string }) => (
    <ResponsiveContainer width="100%" height={40}>
      <LineChart data={data}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );

  // Trend Indicator Component
  const TrendIndicator = ({ value }: { value: number }) => {
    const isPositive = value >= 0;
    const Icon = isPositive ? TrendingUp : TrendingDown;
    const colorClass = isPositive ? 'text-green-600' : 'text-red-600';

    return (
      <div className={`flex items-center gap-1 text-xs font-medium ${colorClass}`}>
        <Icon className="w-3 h-3" />
        <span>{Math.abs(value).toFixed(1)}%</span>
        <span className="text-slate-400 ml-1">vs last update</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-500 font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard Overview</h1>
          <p className="text-slate-500">Welcome back! Here's what's happening with your supply chain.</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${systemStatus?.status === 'healthy'
            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
            : 'bg-red-50 text-red-700 border-red-200'
            }`}>
            {systemStatus?.status === 'healthy' ? 'System Online' : 'System Offline'}
          </span>
          {trends.negotiationWins > 0 && (
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200 flex items-center gap-1">
              <Award className="w-3 h-3" />
              {trends.negotiationWins} Negotiation Win{trends.negotiationWins !== 1 ? 's' : ''}
            </span>
          )}
          <button
            onClick={fetchDashboardData}
            className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Stats Grid with Sparklines */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-l-4 border-l-blue-500">
          <div className="flex justify-between items-start mb-3">
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-500">Total Inventory</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{stats.inventory}</h3>
              <TrendIndicator value={trends.inventoryTrend} />
            </div>
            <div className="p-3 bg-blue-50 rounded-xl">
              <Package className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <MiniSparkline data={sparklineData.inventory} color="#3b82f6" />
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <div className="flex justify-between items-start mb-3">
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-500">Active Orders</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{stats.orders}</h3>
              <TrendIndicator value={trends.ordersTrend} />
            </div>
            <div className="p-3 bg-purple-50 rounded-xl">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <MiniSparkline data={sparklineData.orders} color="#7c3aed" />
        </Card>

        <Card className="border-l-4 border-l-orange-500">
          <div className="flex justify-between items-start mb-3">
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-500">Active Alerts</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{stats.alerts}</h3>
              <div className="flex items-center mt-2 text-xs text-orange-600">
                <AlertCircle className="w-3 h-3 mr-1" />
                <span className="font-medium">Action Needed</span>
              </div>
            </div>
            <div className="p-3 bg-orange-50 rounded-xl">
              <AlertCircle className="w-6 h-6 text-orange-600" />
            </div>
          </div>
          <div className="h-10 flex items-center justify-center">
            {stats.alerts > 0 ? (
              <Link to="/alerts" className="text-xs text-orange-600 hover:text-orange-700 font-medium">
                View Alerts →
              </Link>
            ) : (
              <p className="text-xs text-slate-400">No active alerts</p>
            )}
          </div>
        </Card>

        <Card className="border-l-4 border-l-emerald-500">
          <div className="flex justify-between items-start mb-3">
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-500">Total Value</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">${(stats.totalValue / 1000).toFixed(1)}K</h3>
              <TrendIndicator value={trends.valueTrend} />
            </div>
            <div className="p-3 bg-emerald-50 rounded-xl">
              <DollarSign className="w-6 h-6 text-emerald-600" />
            </div>
          </div>
          <MiniSparkline data={sparklineData.value} color="#10b981" />
        </Card>
      </div>

      {/* Agent Status Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card className="lg:col-span-2" title="Agent Activity">
          <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100 mb-6">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-full ${agentRunning ? 'bg-green-100 animate-pulse' : 'bg-slate-200'}`}>
                <Zap className={`w-6 h-6 ${agentRunning ? 'text-green-600' : 'text-slate-500'}`} />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Autonomous Agent</h3>
                <p className="text-sm text-slate-500">
                  Status: <span className={agentRunning ? 'text-green-600 font-medium' : 'text-slate-600'}>
                    {agentRunning ? 'Running Cycle...' : 'Idle - Waiting for Schedule'}
                  </span>
                </p>
              </div>
            </div>
            <Link
              to="/agent"
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors text-sm font-medium shadow-sm shadow-indigo-200"
            >
              <Play className="w-4 h-4" /> Control Center
            </Link>
          </div>

          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Recent Jobs</h4>
            <div className="space-y-3">
              {agentJobs.slice(0, 3).map((job, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-white border border-slate-100 rounded-lg hover:border-indigo-100 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${job.status === 'completed' ? 'bg-emerald-500' :
                      job.status === 'running' ? 'bg-blue-500 animate-ping' : 'bg-slate-300'
                      }`} />
                    <span className="font-mono text-xs text-slate-500">#{job.id?.slice(0, 8) || job.job_id?.slice(0, 8)}</span>
                    <span className={`text-sm font-medium ${job.status === 'completed' ? 'text-emerald-700' :
                      job.status === 'running' ? 'text-blue-700' : 'text-slate-700'
                      }`}>
                      {job.status}
                    </span>
                  </div>
                  <span className="text-xs text-slate-400">
                    {new Date(job.created_at).toLocaleTimeString()}
                  </span>
                </div>
              ))}
              {agentJobs.length === 0 && (
                <p className="text-sm text-slate-500 italic">No recent jobs found.</p>
              )}
            </div>
          </div>
        </Card>

        {/* Quick Actions - Dynamic */}
        <Card title="Quick Actions">
          <div className="space-y-3">
            {stats.alerts > 0 ? (
              <Link to="/alerts" className="block w-full p-3 text-left text-sm font-medium text-white bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 rounded-lg transition-all transform hover:scale-105 shadow-md">
                ⚠️ View {stats.alerts} Active Alert{stats.alerts !== 1 ? 's' : ''}
              </Link>
            ) : null}

            {agentRunning ? (
              <Link to="/agent" className="block w-full p-3 text-left text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 rounded-lg transition-all transform hover:scale-105 shadow-md">
                🔄 Monitor Running Agent
              </Link>
            ) : (
              <Link to="/agent" className="block w-full p-3 text-left text-sm font-medium text-slate-700 bg-slate-50 hover:bg-indigo-50 hover:text-indigo-700 rounded-lg transition-colors border border-slate-100 hover:border-indigo-100">
                🚀 Start New Agent Cycle
              </Link>
            )}

            <Link to="/inventory" className="block w-full p-3 text-left text-sm font-medium text-slate-700 bg-slate-50 hover:bg-indigo-50 hover:text-indigo-700 rounded-lg transition-colors border border-slate-100 hover:border-indigo-100">
              📦 Manage Inventory ({stats.inventory} items)
            </Link>

            {trends.negotiationWins > 0 && (
              <Link to="/finance-analytics" className="block w-full p-3 text-left text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-lg transition-all transform hover:scale-105 shadow-md">
                ✨ View {trends.negotiationWins} Negotiation Win{trends.negotiationWins !== 1 ? 's' : ''}
              </Link>
            )}

            <Link to="/orders" className="block w-full p-3 text-left text-sm font-medium text-slate-700 bg-slate-50 hover:bg-indigo-50 hover:text-indigo-700 rounded-lg transition-colors border border-slate-100 hover:border-indigo-100">
              🚚 Review Orders ({stats.orders} active)
            </Link>

            <Link to="/learning" className="block w-full p-3 text-left text-sm font-medium text-slate-700 bg-slate-50 hover:bg-indigo-50 hover:text-indigo-700 rounded-lg transition-colors border border-slate-100 hover:border-indigo-100">
              🧠 Learning Insights
            </Link>

            <Link to="/memory" className="block w-full p-3 text-left text-sm font-medium text-slate-700 bg-slate-50 hover:bg-indigo-50 hover:text-indigo-700 rounded-lg transition-colors border border-slate-100 hover:border-indigo-100">
              💾 Explore Memory
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
