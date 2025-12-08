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
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <p className="text-gray-600">Loading agent intelligence...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 flex items-center gap-3">
              <Brain className="w-10 h-10 text-purple-600" />
              Agent Intelligence Center
            </h1>
            <p className="text-gray-600 mt-2">See exactly what your AI agent thinks, decides, and learns</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-md p-1 mb-8 inline-flex gap-1">
          {[
            { id: 'execution', label: '🎬 Execution History', icon: Activity },
            { id: 'decisions', label: '🧠 Decisions', icon: Brain },
            { id: 'memory', label: '📚 Memory', icon: BookOpen }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 rounded-lg font-semibold transition flex items-center gap-2 ${activeTab === tab.id
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-md'
                : 'text-gray-700 hover:bg-gray-100'
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Execution History Tab */}
        {activeTab === 'execution' && (
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">🎬 Agent Execution History</h2>

            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Recent Cycles</h3>
              <div className="space-y-2">
                <div className="space-y-2">
                  {jobs.slice(0, 10).map((job, idx) => {
                    // Calculate cycle number: Total - Index (since list is descending)
                    // Note: This assumes 'totalJobs' is available. We need to store it in state.
                    // For now, let's assume we fetch 50 and total is available.
                    // We need to add 'totalJobs' state to the component first.
                    const cycleNum = totalJobs - idx;

                    return (
                      <div key={idx} className="flex items-center justify-between bg-white p-3 rounded border border-gray-200">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-full ${job.status === 'completed' ? 'bg-green-100' : job.status === 'running' ? 'bg-blue-100' : 'bg-gray-100'}`}>
                            <Clock className={`w-4 h-4 ${job.status === 'completed' ? 'text-green-600' : job.status === 'running' ? 'text-blue-600' : 'text-gray-500'}`} />
                          </div>
                          <div>
                            <p className="font-bold text-gray-900">Cycle #{cycleNum}</p>
                            <p className="font-mono text-xs text-gray-400">ID: {(job.id || job.job_id || '???').slice(0, 8)}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold mb-1 ${job.status === 'completed' ? 'bg-green-100 text-green-800' :
                            job.status === 'running' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                            {job.status}
                          </span>
                          <p className="text-xs text-gray-500">
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
              <div className="bg-white rounded-lg shadow-lg p-12 text-center">
                <Brain className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-600 text-lg">No decisions recorded yet</p>
                <p className="text-gray-500 mt-2">Run the agent to see decisions and reasoning</p>
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
                  <div key={idx} className="bg-white rounded-lg shadow-lg overflow-hidden border-l-4 border-purple-600">
                    <button
                      onClick={() => setExpandedDecision(expandedDecision === idx ? null : idx)}
                      className="w-full p-6 text-left hover:bg-gray-50 transition flex items-center justify-between"
                    >
                      <div className="flex items-center gap-4">
                        <Brain className="w-6 h-6 text-purple-600" />
                        <div>
                          <h3 className="font-bold text-gray-900">
                            Decision #{decision.id}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {new Date(decision.created_at).toLocaleString()}
                          </p>
                        </div>
                        {/* Summary of Decision */}
                        <div className="hidden md:block px-4 py-2 bg-purple-50 rounded-lg text-sm text-purple-900">
                          {reorderCount > 0
                            ? `${reorderCount} Reorders (${totalQty} units)`
                            : 'No Reorders Needed'}
                        </div>
                      </div>
                      <Eye className="w-5 h-5 text-gray-400" />
                    </button>

                    {expandedDecision === idx && (
                      <div className="border-t border-gray-200 p-6 bg-gray-50 space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          {/* Context Section */}
                          <div>
                            <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                              <BarChart3 className="w-4 h-4 text-blue-600" /> Market Context
                            </h4>
                            <div className="bg-white rounded p-4 text-sm text-gray-700 shadow-sm max-h-60 overflow-y-auto">
                              <ul className="space-y-1">
                                {Array.isArray(context) ? (
                                  context.map((item: any, i: number) => (
                                    <li key={i} className="border-b border-gray-100 last:border-0 py-1">
                                      <span className="font-medium">{item.sku}:</span> Stock {item.quantity}
                                    </li>
                                  ))
                                ) : (
                                  Object.entries(context || {}).map(([key, value]: any) => (
                                    <li key={key} className="flex justify-between">
                                      <span className="font-medium text-gray-600">{key}:</span>
                                      <span>{String(value)}</span>
                                    </li>
                                  ))
                                )}
                              </ul>
                            </div>
                          </div>

                          {/* Decision Details */}
                          <div>
                            <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                              <Target className="w-4 h-4 text-green-600" /> Decision Output
                            </h4>
                            <div className="bg-white rounded p-4 text-sm text-gray-700 shadow-sm max-h-60 overflow-y-auto">
                              <ul className="space-y-2">
                                {decisionItems.map((item: any, i: number) => (
                                  <li key={i} className={`p-2 rounded ${item?.reorder_required ? 'bg-green-50 border border-green-100' : 'bg-gray-50'}`}>
                                    <div className="flex justify-between font-medium">
                                      <span>{item?.sku}</span>
                                      <span className={item?.reorder_required ? 'text-green-600' : 'text-gray-500'}>
                                        {item?.reorder_required ? `Order ${item.order_quantity}` : 'Hold'}
                                      </span>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">{item?.reason}</p>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </div>

                        {/* Reasoning */}
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-orange-600" /> Cycle Summary
                          </h4>
                          <div className="bg-white rounded p-4 text-sm text-gray-700 shadow-sm">
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
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <BookOpen className="w-6 h-6 text-blue-600" />
                Agent Decision Memory
              </h2>

              <p className="text-gray-600 mb-6">
                Total decisions recorded: <span className="font-bold text-lg">{decisions.length}</span>
              </p>

              {decisions.length > 0 && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Decision Timeline</h3>
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
                          <div key={`${idx}-${itemIdx}`} className={`flex items-center gap-3 p-3 bg-white rounded border hover:shadow-sm transition ${isReorder ? 'border-purple-200' : 'border-gray-200'}`}>
                            <div className={`flex-shrink-0 w-2 h-2 rounded-full ${isReorder ? 'bg-purple-600' : 'bg-gray-400'}`}></div>
                            <div className="flex-grow">
                              <div className="flex justify-between items-center">
                                <p className="text-sm font-bold text-gray-900">
                                  {actionLabel} {item.sku}
                                  {quantity > 0 ? ` (${quantity} units)` : ''}
                                </p>
                                <span className="text-xs text-gray-500">{new Date(decision.created_at).toLocaleString()}</span>
                              </div>
                              <p className="text-xs text-gray-600 mt-1 truncate" title={item.reason}>
                                {item.reason || 'No reasoning provided'}
                              </p>
                            </div>
                            {isReorder ? (
                              <CheckCircle className="w-4 h-4 text-green-600" />
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
