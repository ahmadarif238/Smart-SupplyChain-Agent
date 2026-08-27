import { useState, useEffect } from 'react';
import { Play, CheckCircle, AlertTriangle, DollarSign, Package, Clock, Activity, MessageSquare, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { apiService } from '../api';
import Card from '../components/ui/Card';

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    budgetRemaining: 0,
    pendingApprovals: 0,
    activeAlerts: 0,
    inventoryCount: 0
  });
  const [pendingOrders, setPendingOrders] = useState<any[]>([]);
  const [agentStatus, setAgentStatus] = useState<string>('idle');
  const [recentJobs, setRecentJobs] = useState<any[]>([]);
  const [narrative, setNarrative] = useState<string>("");

  const fetchData = async () => {
    try {
      // 1. Fetch Orders (for Pending Approvals)
      const ordersRes = await apiService.orders.list();
      const allOrders = ordersRes.data || [];
      const pending = allOrders.filter((o: any) => o.status === 'Needs Approval');
      setPendingOrders(pending);

      // 2. Fetch Alerts
      const alertsRes = await apiService.alerts.list();
      const alerts = alertsRes.data || [];

      // 3. Fetch Inventory
      const invRes = await apiService.inventory.list();

      // 4. Fetch Finance Summary (for Budget)
      const financeRes = await apiService.agent.financeSummary().catch(() => ({ data: { budget_remaining: 0 } }));

      // 5. Fetch Agent Jobs
      const jobsRes = await apiService.agent.jobs();
      let jobs = [];
      if (Array.isArray(jobsRes.data)) {
        jobs = jobsRes.data;
      } else if (jobsRes.data?.recent_jobs) {
        jobs = jobsRes.data.recent_jobs;
      } else if (jobsRes.data?.jobs) {
        jobs = jobsRes.data.jobs;
      }
      setRecentJobs(jobs.slice(0, 5)); // Keep top 5

      // Check if running
      const isRunning = jobs.some((j: any) => j.status === 'running');
      setAgentStatus(isRunning ? 'running' : 'idle');

      const budget = financeRes.data?.remaining ?? financeRes.data?.current_budget ?? 0;
      setStats({
        budgetRemaining: budget,
        pendingApprovals: pending.length,
        activeAlerts: alerts.length,
        inventoryCount: invRes.data?.length || 0
      });

      // GENERATE NARRATIVE
      let story = "I've analyzed your supply chain. ";
      if (pending.length > 0) {
        story += `I found ${pending.length} items that need restocking and drafted orders for them. Please review the 'Action Required' section below. `;
      } else {
        story += "Everything looks healthy. No immediate actions are needed by you. ";
      }

      if (budget < 1000) {
        story += " Warning: Your operating budget is very low ($" + budget.toLocaleString() + "). I might not be able to place necessary orders. Please visit Settings to add funds. ";
      }

      setNarrative(story);

    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  const handleStartAgent = async () => {
    try {
      setAgentStatus('running');
      await apiService.agent.runOnce();
      // Poll will catch the update
      setTimeout(fetchData, 1000);
    } catch (error) {
      console.error("Failed to start agent:", error);
      setAgentStatus('error');
    }
  };

  const handleApproveOrder = async (orderId: number) => {
    try {
      await apiService.orders.updateStatus(orderId, 'Approved');
      fetchData(); // Refresh list
    } catch (error) {
      console.error("Failed to approve order:", error);
    }
  };

  const handleRejectOrder = async (orderId: number) => {
    try {
      await apiService.orders.updateStatus(orderId, 'Rejected');
      fetchData();
    } catch (error) {
      console.error("Failed to reject order:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400 font-medium">Loading Supply Chain Center...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* NARRATIVE SECTION */}
      <div className="bg-gradient-to-r from-accent to-accent-hover rounded-none p-8 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-ink-800/20 backdrop-blur-sm rounded-none">
              <MessageSquare className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-xl font-bold">Agent Update</h2>
          </div>
          <p className="text-lg leading-relaxed font-medium opacity-95 max-w-3xl">
            "{narrative}"
          </p>

          <div className="mt-8 flex gap-4">
            <button
              onClick={handleStartAgent}
              disabled={agentStatus === 'running'}
              className={`px-6 py-3 rounded-none font-bold flex items-center gap-2 transition-all shadow-lg ${agentStatus === 'running'
                ? 'bg-ink-800/10 text-white/50 cursor-not-allowed'
                : 'bg-ink-800 text-accent hover:bg-ink-900 active:scale-95'
                }`}
            >
              {agentStatus === 'running' ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/50 border-t-transparent rounded-full animate-spin"></div>
                  Agent Working...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5 fill-current" />
                  Run New Analysis
                </>
              )}
            </button>
          </div>
        </div>

        {/* Background blobs */}
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-64 h-64 bg-ink-800/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 -mb-10 -ml-10 w-64 h-64 bg-accent/20 rounded-full blur-3xl"></div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Link to="/settings" className="block transform transition-transform hover:-translate-y-1">
          <KPI
            icon={<DollarSign className="w-6 h-6 text-emerald-400" />}
            label="Budget Remaining"
            value={`$${stats.budgetRemaining.toLocaleString()}`}
            color="bg-emerald-500/10"
            action={stats.budgetRemaining < 1000 ? "Add Funds" : undefined}
          />
        </Link>
        <KPI
          icon={<Clock className="w-6 h-6 text-orange-400" />}
          label="Pending Approvals"
          value={stats.pendingApprovals}
          color="bg-orange-500/10"
          highlight={stats.pendingApprovals > 0}
        />
        <KPI
          icon={<AlertTriangle className="w-6 h-6 text-red-400" />}
          label="Critical Alerts"
          value={stats.activeAlerts}
          color="bg-red-500/10"
        />
        <KPI
          icon={<Package className="w-6 h-6 text-accent" />}
          label="Total SKUs"
          value={stats.inventoryCount}
          color="bg-accent/10"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* Main Section: Action Items (2/3 width) */}
        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-accent" />
            Action Required
          </h2>

          {pendingOrders.length === 0 ? (
            <div className="bg-ink-800 rounded-none p-12 text-center border border-ink-700 shadow-sm border-dashed">
              <div className="w-16 h-16 bg-ink-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-slate-300" />
              </div>
              <h3 className="text-lg font-medium text-white">All Caught Up!</h3>
              <p className="text-slate-400 mt-2">The agent hasn't found any new issues to solve.</p>
            </div>
          ) : (
            <div className="bg-ink-800 rounded-none shadow-sm border border-ink-700 overflow-hidden animate-fade-in">
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-ink-900 border-b border-ink-700">
                    <tr>
                      <th className="px-6 py-4 text-sm font-semibold text-slate-400">Product</th>
                      <th className="px-6 py-4 text-sm font-semibold text-slate-400">Qty</th>
                      <th className="px-6 py-4 text-sm font-semibold text-slate-400">Cost</th>
                      <th className="px-6 py-4 text-sm font-semibold text-slate-400">Agent Reasoning</th>
                      <th className="px-6 py-4 text-sm font-semibold text-slate-400 text-right">Decision</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {pendingOrders.map((order) => (
                      <tr key={order.id} className="hover:bg-ink-900 transition-colors">
                        <td className="px-6 py-4">
                          <div className="font-bold text-white">{order.product_name}</div>
                          <div className="text-xs text-slate-500 font-mono">{order.sku}</div>
                        </td>
                        <td className="px-6 py-4 font-medium text-slate-300">{order.quantity} units</td>
                        <td className="px-6 py-4 text-slate-400 font-mono">${(order.total_price || 0).toLocaleString()}</td>
                        <td className="px-6 py-4 max-w-xs">
                          <div className="text-sm text-slate-400 italic">
                            "{parseReason(order.notes)}"
                          </div>
                        </td>
                        <td className="px-6 py-4 text-right space-x-2 whitespace-nowrap">
                          <button
                            onClick={() => handleApproveOrder(order.id)}
                            className="px-3 py-1.5 bg-emerald-500/10 text-emerald-400 text-sm font-bold rounded-none hover:bg-emerald-500/15 transition-colors border border-emerald-500/30"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleRejectOrder(order.id)}
                            className="px-3 py-1.5 bg-ink-800 text-slate-400 text-sm font-medium rounded-none hover:bg-ink-900 transition-colors border border-ink-700"
                          >
                            Reject
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar: Recent Activity (1/3 width) */}
        <div className="space-y-6">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-accent" />
            Recent Activity
          </h2>

          <div className="bg-ink-800 rounded-none shadow-sm border border-ink-700 p-4 space-y-4">
            {recentJobs.length === 0 && <p className="text-slate-400 text-sm">No recent activity.</p>}
            {recentJobs.map((job, idx) => (
              <div key={idx} className="flex gap-3 pb-3 border-b last:border-0 border-slate-50">
                <div className={`mt-1.5 w-2 h-2 rounded-full flex-shrink-0 ${job.status === 'completed' ? 'bg-emerald-500' :
                  job.status === 'running' ? 'bg-accent animate-pulse' : 'bg-ink-700'
                  }`} />
                <div>
                  <p className="text-sm font-medium text-white capitalize">{job.status}</p>
                  <p className="text-xs text-slate-400 font-mono">ID: {job.id?.substring(0, 8)}</p>
                  <span className="text-xs text-slate-500">{new Date(job.created_at).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}

// Sub-components
function KPI({ icon, label, value, color, highlight = false, action }: any) {
  return (
    <Card className={`border-l-4 ${highlight ? 'border-l-orange-500 ring-2 ring-orange-100' : 'border-l-transparent'} transition-all hover:shadow-md h-full`}>
      <div className="flex items-start justify-between h-full">
        <div className="flex flex-col justify-between h-full">
          <div>
            <p className="text-sm font-medium text-slate-400">{label}</p>
            <h3 className="text-2xl font-bold text-white mt-1">{value}</h3>
          </div>
          {action && (
            <div className="mt-2 text-xs font-bold text-accent flex items-center gap-1">
              {action} <ArrowRight className="w-3 h-3" />
            </div>
          )}
        </div>
        <div className={`p-3 rounded-none ${color}`}>
          {icon}
        </div>
      </div>
    </Card>
  );
}

function parseReason(notes: string) {
  try {
    if (!notes) return "Auto-reorder based on forecast.";
    const parsed = JSON.parse(notes);
    return parsed.reason || notes;
  } catch {
    return notes;
  }
}
