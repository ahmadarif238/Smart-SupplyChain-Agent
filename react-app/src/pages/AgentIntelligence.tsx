import { useState, useEffect } from 'react';
import {
  Brain, BarChart3, TrendingUp, CheckCircle, Target,
  Eye, Clock, Activity, BookOpen
} from 'lucide-react';
import { apiService } from '../api';

interface Decision {
  id: number;
  context: string;
  decision: string;
  reasoning: string;
  created_at: string;
}

interface AgentJob {
  id?: string;
  job_id?: string;
  status: string;
  created_at: string;
  completed_at?: string;
}

export default function AgentIntelligence() {
  const [activeTab, setActiveTab] = useState<'decisions' | 'memory' | 'execution'>('decisions');
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [jobs, setJobs] = useState<AgentJob[]>([]);
  const [totalJobs, setTotalJobs] = useState(0);
  const [loading, setLoading] = useState(true);
  const [expandedDecision, setExpandedDecision] = useState<number | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [memRes, jobsRes] = await Promise.all([
        apiService.agent.memory?.() || Promise.resolve({ data: [] }),
        apiService.agent.jobs?.() || Promise.resolve({ data: [] })
      ]);

      const memData = Array.isArray(memRes.data) ? memRes.data : [];

      let jobsData: AgentJob[] = [];
      if (Array.isArray(jobsRes.data)) {
        jobsData = jobsRes.data;
      } else if (jobsRes.data?.recent_jobs) {
        jobsData = jobsRes.data.recent_jobs;
      } else if (jobsRes.data?.jobs) {
        jobsData = jobsRes.data.jobs;
      }

      setDecisions(memData);
      setJobs(jobsData);
      setTotalJobs(jobsRes.data?.total || jobsData.length);
    } catch (error) {
      console.error('Error fetching agent data:', error);
    } finally {
      setLoading(false);
    }
  };

  const parseJson = (str: string) => {
    try {
      return JSON.parse(str);
    } catch {
      return str;
    }
  };

  if (loading && decisions.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-ink-900 to-ink-800 flex items-center justify-center">
        <p className="text-slate-400">Loading agent intelligence...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-ink-900 to-ink-800 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white flex items-center gap-3">
              <Brain className="w-10 h-10 text-accent" />
              Agent Intelligence Center
            </h1>
            <p className="text-slate-400 mt-2">See exactly what your AI agent thinks, decides, and learns</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-ink-800 rounded-none shadow-md p-1 mb-8 inline-flex gap-1">
          {[
            { id: 'execution', label: '🎬 Execution History', icon: Activity },
            { id: 'decisions', label: '🧠 Decisions', icon: Brain },
            { id: 'memory', label: '📚 Memory', icon: BookOpen }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 rounded-none font-semibold transition flex items-center gap-2 ${activeTab === tab.id
                ? 'bg-gradient-to-r from-accent to-accent-hover text-white shadow-md'
                : 'text-slate-300 hover:bg-ink-900'
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Execution History Tab */}
        {activeTab === 'execution' && (
          <div className="bg-ink-800 rounded-none shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-bold text-white mb-6">🎬 Agent Execution History</h2>

            <div className="bg-ink-900 rounded-none p-4">
              <h3 className="font-semibold text-white mb-3">Recent Cycles</h3>
              <div className="space-y-2">
                <div className="space-y-2">
                  {jobs.slice(0, 10).map((job, idx) => {
                    // Calculate cycle number: Total - Index (since list is descending)
                    // Note: This assumes 'totalJobs' is available. We need to store it in state.
                    // For now, let's assume we fetch 50 and total is available.
                    // We need to add 'totalJobs' state to the component first.
                    const cycleNum = totalJobs - idx;

                    return (
                      <div key={idx} className="flex items-center justify-between bg-ink-800 p-3 rounded border border-ink-700">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-full ${job.status === 'completed' ? 'bg-emerald-500/15' : job.status === 'running' ? 'bg-accent/10' : 'bg-ink-900'}`}>
                            <Clock className={`w-4 h-4 ${job.status === 'completed' ? 'text-emerald-400' : job.status === 'running' ? 'text-accent' : 'text-slate-400'}`} />
                          </div>
                          <div>
                            <p className="font-bold text-white">Cycle #{cycleNum}</p>
                            <p className="font-mono text-xs text-slate-500">ID: {(job.id || job.job_id || '???').slice(0, 8)}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold mb-1 ${job.status === 'completed' ? 'bg-emerald-500/15 text-emerald-300' :
                            job.status === 'running' ? 'bg-accent/10 text-accent' :
                              'bg-ink-900 text-white'
                            }`}>
                            {job.status}
                          </span>
                          <p className="text-xs text-slate-400">
                            {new Date(job.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Decisions Tab */}
        {activeTab === 'decisions' && (
          <div className="space-y-6">
            {decisions.length === 0 ? (
              <div className="bg-ink-800 rounded-none shadow-lg p-12 text-center">
                <Brain className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-400 text-lg">No decisions recorded yet</p>
                <p className="text-slate-400 mt-2">Run the agent to see decisions and reasoning</p>
              </div>
            ) : (
              decisions.map((decision, idx) => {
                const context = parseJson(decision.context);
                const rawData = parseJson(decision.decision);
                const decisionItems = Array.isArray(rawData) ? rawData : [rawData];
                const reasoning = parseJson(decision.reasoning);

                // Calculate summary stats
                const reorderCount = decisionItems.filter((i: any) => i?.reorder_required).length;
                const totalQty = decisionItems.reduce((acc: number, i: any) => acc + (i?.order_quantity || 0), 0);

                return (
                  <div key={idx} className="bg-ink-800 rounded-none shadow-lg overflow-hidden border-l-4 border-accent">
                    <button
                      onClick={() => setExpandedDecision(expandedDecision === idx ? null : idx)}
                      className="w-full p-6 text-left hover:bg-ink-900 transition flex items-center justify-between"
                    >
                      <div className="flex items-center gap-4">
                        <Brain className="w-6 h-6 text-accent" />
                        <div>
                          <h3 className="font-bold text-white">
                            Decision #{decision.id}
                          </h3>
                          <p className="text-sm text-slate-400">
                            {new Date(decision.created_at).toLocaleString()}
                          </p>
                        </div>
                        {/* Summary of Decision */}
                        <div className="hidden md:block px-4 py-2 bg-accent/10 rounded-none text-sm text-accent">
                          {reorderCount > 0
                            ? `${reorderCount} Reorders (${totalQty} units)`
                            : 'No Reorders Needed'}
                        </div>
                      </div>
                      <Eye className="w-5 h-5 text-slate-500" />
                    </button>

                    {expandedDecision === idx && (
                      <div className="border-t border-ink-700 p-6 bg-ink-900 space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          {/* Context Section */}
                          <div>
                            <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
                              <BarChart3 className="w-4 h-4 text-accent" /> Market Context
                            </h4>
                            <div className="bg-ink-800 rounded p-4 text-sm text-slate-300 shadow-sm max-h-60 overflow-y-auto">
                              <ul className="space-y-1">
                                {Array.isArray(context) ? (
                                  context.map((item: any, i: number) => (
                                    <li key={i} className="border-b border-ink-700 last:border-0 py-1">
                                      <span className="font-medium">{item.sku}:</span> Stock {item.quantity}
                                    </li>
                                  ))
                                ) : (
                                  Object.entries(context || {}).map(([key, value]: any) => (
                                    <li key={key} className="flex justify-between">
                                      <span className="font-medium text-slate-400">{key}:</span>
                                      <span>{String(value)}</span>
                                    </li>
                                  ))
                                )}
                              </ul>
                            </div>
                          </div>

                          {/* Decision Details */}
                          <div>
                            <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
                              <Target className="w-4 h-4 text-emerald-400" /> Decision Output
                            </h4>
                            <div className="bg-ink-800 rounded p-4 text-sm text-slate-300 shadow-sm max-h-60 overflow-y-auto">
                              <ul className="space-y-2">
                                {decisionItems.map((item: any, i: number) => (
                                  <li key={i} className={`p-2 rounded ${item?.reorder_required ? 'bg-emerald-500/10 border border-green-100' : 'bg-ink-900'}`}>
                                    <div className="flex justify-between font-medium">
                                      <span>{item?.sku}</span>
                                      <span className={item?.reorder_required ? 'text-emerald-400' : 'text-slate-400'}>
                                        {item?.reorder_required ? `Order ${item.order_quantity}` : 'Hold'}
                                      </span>
                                    </div>
                                    <p className="text-xs text-slate-400 mt-1">{item?.reason}</p>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </div>

                        {/* Reasoning */}
                        <div>
                          <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-orange-400" /> Cycle Summary
                          </h4>
                          <div className="bg-ink-800 rounded p-4 text-sm text-slate-300 shadow-sm">
                            <p className="whitespace-pre-wrap">{
                              typeof reasoning === 'string' ? reasoning : JSON.stringify(reasoning, null, 2)
                            }</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* Memory Tab */}
        {activeTab === 'memory' && (
          <div className="space-y-6">
            <div className="bg-ink-800 rounded-none shadow-lg p-8">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                <BookOpen className="w-6 h-6 text-accent" />
                Agent Decision Memory
              </h2>

              <p className="text-slate-400 mb-6">
                Total decisions recorded: <span className="font-bold text-lg">{decisions.length}</span>
              </p>

              {decisions.length > 0 && (
                <div className="bg-ink-900 rounded-none p-4">
                  <h3 className="font-semibold text-white mb-3">Decision Timeline</h3>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {decisions.flatMap((decision, idx) => {
                      const rawData = parseJson(decision.decision);
                      const items = Array.isArray(rawData) ? rawData : [rawData];

                      // Filter to show only interesting decisions (reorders or warnings)
                      // or show all if you prefer history. Let's show reorders + high urgency.
                      return items.map((item: any, itemIdx) => {
                        if (!item || !item.sku) return null;

                        const isReorder = item.reorder_required;
                        const actionLabel = isReorder ? 'Reorder' : 'Hold';
                        const quantity = item.order_quantity || 0;

                        return (
                          <div key={`${idx}-${itemIdx}`} className={`flex items-center gap-3 p-3 bg-ink-800 rounded border hover:shadow-sm transition ${isReorder ? 'border-accent/40' : 'border-ink-700'}`}>
                            <div className={`flex-shrink-0 w-2 h-2 rounded-full ${isReorder ? 'bg-accent' : 'bg-ink-700'}`}></div>
                            <div className="flex-grow">
                              <div className="flex justify-between items-center">
                                <p className="text-sm font-bold text-white">
                                  {actionLabel} {item.sku}
                                  {quantity > 0 ? ` (${quantity} units)` : ''}
                                </p>
                                <span className="text-xs text-slate-400">{new Date(decision.created_at).toLocaleString()}</span>
                              </div>
                              <p className="text-xs text-slate-400 mt-1 truncate" title={item.reason}>
                                {item.reason || 'No reasoning provided'}
                              </p>
                            </div>
                            {isReorder ? (
                              <CheckCircle className="w-4 h-4 text-emerald-400" />
                            ) : (
                              <div className="w-4 h-4" />
                            )}
                          </div>
                        );
                      });
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
