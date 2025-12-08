import { useState, useEffect } from 'react';
import { Zap, Play, FileText, Activity, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { apiService } from '../api';
import LangGraphVisualizer from '../components/LangGraphVisualizer';
import DecisionBreakdown from '../components/DecisionBreakdown';
import AgentDialogue from '../components/AgentDialogue';

interface StreamEvent {
  type: string;
  message: string;
  stage?: string;
  details?: any;
  timestamp?: string;
}

interface Job {
  id: string;
  status: string;
  created_at: string;
  completed_at: string | null;
}

export default function AgentComplete() {
  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([]);
  const [agentRunning, setAgentRunning] = useState(false);
  const [currentCycle, setCurrentCycle] = useState<any>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'stream' | 'summary'>('stream');
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [totalJobs, setTotalJobs] = useState<number>(0);

  // New state for Visualizer and Decision Breakdown
  const [currentStage, setCurrentStage] = useState<string | undefined>();
  const [completedStages, setCompletedStages] = useState<string[]>([]);
  const [errorStage, setErrorStage] = useState<string | undefined>();
  const [selectedDecision, setSelectedDecision] = useState<any>(null);
  const [cycleResult, setCycleResult] = useState<any>(null);
  const [activeInteraction, setActiveInteraction] = useState<{ from: string; to: string; type: any } | null>(null);

  // Load stream logs from localStorage on mount (but NOT summary - let it be fresh)
  const fetchRecentJobs = async () => {
    try {
      const response = await apiService.agent.jobs();
      if (response.data?.recent_jobs) {
        setRecentJobs(response.data.recent_jobs.slice(0, 10)); // Limit to 10
        setTotalJobs(response.data.total || 0);
      }
    } catch (error) {
      console.error('Failed to fetch recent jobs:', error);
    }
  };

  // Load stream logs from localStorage on mount (but NOT summary - let it be fresh)
  useEffect(() => {
    const savedLogs = localStorage.getItem('agent_stream_logs');

    if (savedLogs) {
      try {
        setStreamEvents(JSON.parse(savedLogs));
      } catch (e) {
        console.error('Failed to parse saved logs', e);
      }
    }

    fetchRecentJobs();
  }, []);

  // Save stream logs to localStorage whenever they change
  useEffect(() => {
    if (streamEvents.length > 0) {
      localStorage.setItem('agent_stream_logs', JSON.stringify(streamEvents));
    }
  }, [streamEvents]);

  // Save summary to localStorage whenever it changes (for persistence across page refresh during same cycle)
  useEffect(() => {
    if (summary) {
      localStorage.setItem('agent_last_summary', summary);
    }
  }, [summary]);

  const fetchSummary = async (jobId: string) => {
    try {
      setStreamEvents((prev) => [...prev, {
        type: 'info',
        message: '🤖 Generating cycle summary with AI...',
        timestamp: new Date().toISOString()
      }]);

      // Fetch AI Summary
      const res = await apiService.agent.getSummary(jobId);

      if (res.data?.summary) {
        setSummary(res.data.summary);
        setActiveTab('summary'); // Auto-switch to summary tab
        setStreamEvents((prev) => [...prev, {
          type: 'info',
          message: '✨ Summary generated successfully',
          timestamp: new Date().toISOString()
        }]);
      }

      // Also ensure we have the structured result if not already present
      if (!cycleResult) {
        const jobDetails = await apiService.agent.jobStatus(jobId);
        if (jobDetails.data?.result) {
          setCycleResult(jobDetails.data.result);
        }
      }

    } catch (error) {
      console.error('Error fetching summary:', error);
      setStreamEvents((prev) => [...prev, {
        type: 'error',
        message: '❌ Failed to generate summary',
        timestamp: new Date().toISOString()
      }]);
    }
  };

  const streamAgentProgress = (jobId: string) => {
    const token = localStorage.getItem('auth_token');
    const url = token
      ? `http://127.0.0.1:8000/agent/stream/${jobId}?token=${encodeURIComponent(token)}`
      : `http://127.0.0.1:8000/agent/stream/${jobId}`;

    const eventSource = new EventSource(url);
    let isClosed = false;

    eventSource.onmessage = (event) => {
      if (isClosed) return;

      try {
        const data = JSON.parse(event.data);

        setStreamEvents((prev) => [...prev, {
          type: data.type,
          message: data.message,
          stage: data.stage,
          details: data.details,
          timestamp: data.timestamp || new Date().toISOString()
        }]);

        // Handle active interaction for visualizer
        if (data.type === 'agent_dialogue' && data.details?.target) {
          setActiveInteraction({
            from: data.details.agent,
            to: data.details.target,
            type: data.details.type
          });

          // Clear interaction after 5 seconds
          setTimeout(() => setActiveInteraction(null), 5000);
        }

        // Track workflow stages for visualizer
        if (data.stage) {
          const stage = data.stage.toUpperCase();
          setCurrentStage(stage);

          // Mark as complete if this is a completion event or implies completion
          if (data.type === 'complete' || data.message?.includes('✓') || data.message?.includes('completed')) {
            setCompletedStages((prev) => {
              if (!prev.includes(stage)) {
                return [...prev, stage];
              }
              return prev;
            });
          }
        }

        if (data.type === 'complete' || (data.type === 'status' && data.status === 'completed')) {
          isClosed = true;
          eventSource.close();
          setAgentRunning(false);
          setCurrentCycle((prev: any) => ({ ...prev, status: 'complete' }));

          // Capture result from stream if available
          if (data.details) {
            setCycleResult(data.details);
          }

          // Fetch summary after completion
          fetchSummary(jobId);
          fetchRecentJobs(); // Refresh job list
        }
        else if (data.type === 'error') {
          isClosed = true;
          eventSource.close();
          setAgentRunning(false);
          setCurrentCycle((prev: any) => ({ ...prev, status: 'failed' }));
          if (data.stage) setErrorStage(data.stage.toUpperCase());
          fetchRecentJobs(); // Refresh job list
        }
        else if (data.type === 'close') {
          isClosed = true;
          eventSource.close();
          setAgentRunning(false);
        }
      } catch (error) {
        console.error('Error parsing stream event:', error);
      }
    };

    eventSource.onerror = (error) => {
      if (isClosed) return;

      console.error('Stream error:', error);
      eventSource.close();
      setAgentRunning(false);

      if (eventSource.readyState !== EventSource.CLOSED) {
        setStreamEvents((prev) => [...prev, {
          type: 'error',
          message: '❌ Streaming connection lost',
          timestamp: new Date().toISOString()
        }]);
      }
    };
  };

  // Helper to load a past job's details
  const loadJobDetails = async (jobId: string) => {
    try {
      const res = await apiService.agent.jobStatus(jobId);
      if (res.data) {
        setCurrentCycle({
          job_id: res.data.id,
          status: res.data.status,
          started_at: res.data.created_at
        });
        if (res.data.result) {
          setCycleResult(res.data.result);
        }
        // Also try to get summary
        fetchSummary(jobId);
      }
    } catch (err) {
      console.error("Failed to load job details", err);
    }
  };

  const handleRunAgent = async () => {
    setAgentRunning(true);
    setStreamEvents([]); // Clear previous events
    setSummary(null); // Clear previous summary
    setCycleResult(null); // Clear previous result
    setCurrentCycle(null);
    setCompletedStages([]);
    setCurrentStage(undefined);
    setErrorStage(undefined);
    setActiveInteraction(null);

    try {
      const response = await apiService.agent.runOnce();
      const jobId = response.data.job_id;

      if (!jobId) {
        throw new Error('No job_id in response');
      }

      setCurrentCycle({ job_id: jobId, status: 'running', started_at: new Date().toISOString() });
      streamAgentProgress(jobId);
    } catch (error: any) {
      console.error('Error running agent:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      setStreamEvents((prev) => [...prev, {
        type: 'error',
        message: `❌ Error: ${errorMsg}`,
        timestamp: new Date().toISOString()
      }]);
      setAgentRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-4 gap-8">

        {/* Main Content Area */}
        <div className="lg:col-span-3 space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 flex items-center gap-3">
                <Zap className="w-10 h-10 text-purple-600" />
                Agent Control
              </h1>
              <p className="text-gray-600 mt-2">Monitor real-time decisions and learning</p>
            </div>
            <button
              onClick={handleRunAgent}
              disabled={agentRunning}
              className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition whitespace-nowrap ${agentRunning
                ? 'bg-gray-400 text-white cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:shadow-lg'
                }`}
            >
              {agentRunning ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" /> Run Agent Now
                </>
              )}
            </button>
          </div>

          {/* Workflow Visualization */}
          {(agentRunning || completedStages.length > 0 || currentCycle) && (
            <LangGraphVisualizer
              currentStage={currentStage}
              completedStages={completedStages}
              errorStage={errorStage}
              activeInteraction={activeInteraction}
            />
          )}

          {/* Current Cycle Status */}
          {currentCycle && (
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-6 border-l-4 border-blue-600 shadow-sm">
              <div className="flex justify-between items-start">
                <h3 className="text-lg font-bold text-gray-900 mb-3">Current Cycle</h3>
                {currentCycle.status === 'complete' && !summary && (
                  <button
                    onClick={() => fetchSummary(currentCycle.job_id)}
                    className="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 transition flex items-center gap-2"
                  >
                    <Zap className="w-4 h-4" /> Generate Summary
                  </button>
                )}
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Job ID</p>
                  <p className="font-mono font-medium">{currentCycle.job_id?.slice(0, 8)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Status</p>
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${currentCycle.status === 'running' ? 'bg-blue-200 text-blue-800' :
                    currentCycle.status === 'complete' ? 'bg-green-200 text-green-800' :
                      'bg-gray-200 text-gray-800'
                    }`}>
                    {currentCycle.status}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Started</p>
                  <p className="text-sm font-medium">{new Date(currentCycle.started_at).toLocaleTimeString()}</p>
                </div>
              </div>
            </div>
          )}

          {/* Tab Navigation */}
          <div className="bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden min-h-[500px]">
            <div className="flex border-b border-gray-200">
              <button
                onClick={() => setActiveTab('stream')}
                className={`flex-1 py-4 text-center font-medium text-sm transition-colors ${activeTab === 'stream'
                  ? 'text-purple-600 border-b-2 border-purple-600 bg-purple-50'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
              >
                <div className="flex items-center justify-center gap-2">
                  <Activity className="w-4 h-4" />
                  Live Stream
                </div>
              </button>
              <button
                onClick={() => setActiveTab('summary')}
                className={`flex-1 py-4 text-center font-medium text-sm transition-colors ${activeTab === 'summary'
                  ? 'text-indigo-600 border-b-2 border-indigo-600 bg-indigo-50'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
              >
                <div className="flex items-center justify-center gap-2">
                  <FileText className="w-4 h-4" />
                  Cycle Summary
                </div>
              </button>
            </div>

            <div className="p-6">
              {activeTab === 'stream' && (
                <div>
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                      <Activity className="w-5 h-5 text-purple-600" />
                      War Room Chat
                    </h2>
                    <span className="text-xs font-medium px-2 py-1 bg-green-100 text-green-700 rounded-full animate-pulse">
                      ● Live Collaboration
                    </span>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4 h-[500px] overflow-y-auto border border-gray-200 shadow-inner space-y-4">
                    {streamEvents.length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center text-gray-400">
                        <div className="flex -space-x-4 mb-4">
                          <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center border-2 border-white">🔮</div>
                          <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center border-2 border-white">📦</div>
                          <div className="w-12 h-12 rounded-full bg-yellow-100 flex items-center justify-center border-2 border-white">💰</div>
                        </div>
                        <p>Waiting for the team to assemble...</p>
                        <p className="text-sm mt-2">Click "Run Agent" to start the session.</p>
                      </div>
                    ) : (
                      streamEvents.map((event, idx) => {
                        // Determine Persona based on event type
                        let persona = { name: 'System', icon: '⚙️', color: 'bg-gray-200 text-gray-700', align: 'left' };

                        if (event.type === 'forecast' || event.type === 'forecast_done') {
                          persona = { name: 'Forecaster', icon: '🔮', color: 'bg-purple-100 text-purple-800', align: 'left' };
                        } else if (event.type === 'decide' || event.type === 'decision_item') {
                          persona = { name: 'Inventory Manager', icon: '📦', color: 'bg-blue-100 text-blue-800', align: 'left' };
                        } else if (event.type === 'finance' || event.type === 'finance_feedback') {
                          persona = { name: 'Finance Controller', icon: '💰', color: 'bg-yellow-100 text-yellow-800', align: 'right' };
                        } else if (event.type === 'act' || event.type === 'action_item') {
                          persona = { name: 'Procurement', icon: '🛒', color: 'bg-green-100 text-green-800', align: 'right' };
                        } else if (event.type === 'learn' || event.type === 'learn_item') {
                          persona = { name: 'AI Analyst', icon: '🧠', color: 'bg-pink-100 text-pink-800', align: 'left' };
                        } else if (event.type === 'error') {
                          persona = { name: 'System Alert', icon: '🚨', color: 'bg-red-100 text-red-800', align: 'center' };
                        } else if (event.type === 'agent_dialogue') {
                          // Render the new AgentDialogue component
                          return (
                            <div key={idx} className="w-full max-w-3xl mx-auto">
                              <AgentDialogue dialogue={{
                                agent: event.details?.agent || 'Unknown',
                                target: event.details?.target,
                                message: event.message,
                                type: event.details?.type || 'info',
                                sku: event.details?.sku,
                                timestamp: event.timestamp
                              }} />
                            </div>
                          );
                        }

                        // Skip generic progress messages if desired, or style them differently
                        if (event.type === 'progress' && !event.message.includes('done')) return null;

                        const isSystem = persona.name === 'System' || persona.name === 'System Alert';
                        const isRight = persona.align === 'right';

                        return (
                          <div key={idx} className={`flex w-full ${isSystem ? 'justify-center my-2' : isRight ? 'justify-end my-1' : 'justify-start my-1'}`}>
                            <div className={`flex max-w-[85%] ${isRight ? 'flex-row-reverse' : 'flex-row'} items-start gap-3 group`}>

                              {!isSystem && (
                                <div className={`w-10 h-10 rounded-full flex-shrink-0 flex items-center justify-center text-lg shadow-sm border border-gray-100 bg-white z-10`}>
                                  {persona.icon}
                                </div>
                              )}

                              <div className={`flex flex-col ${isRight ? 'items-end' : isSystem ? 'items-center' : 'items-start'}`}>
                                {!isSystem && <span className="text-xs font-semibold text-gray-500 mb-1 ml-1">{persona.name}</span>}

                                <div className={`px-5 py-3 shadow-sm text-sm transition-all duration-200 hover:shadow-md ${persona.color} ${isSystem ? 'rounded-full text-xs font-mono py-1 px-3 opacity-75' :
                                  isRight ? 'rounded-2xl rounded-tr-none' : 'rounded-2xl rounded-tl-none'
                                  }`}>
                                  <div className="leading-relaxed">{event.message}</div>

                                  {event.details && Object.keys(event.details).length > 0 && (
                                    <details className="mt-2 group/details">
                                      <summary className="cursor-pointer text-[10px] font-medium opacity-60 hover:opacity-100 flex items-center gap-1 select-none">
                                        <span className="group-open/details:hidden">▶ View Data</span>
                                        <span className="hidden group-open/details:inline">▼ Hide Data</span>
                                      </summary>
                                      <div className="mt-2 bg-black/5 rounded p-2 overflow-hidden">
                                        <pre className="text-[10px] font-mono overflow-x-auto whitespace-pre-wrap break-all">
                                          {JSON.stringify(event.details, null, 2)}
                                        </pre>
                                      </div>
                                    </details>
                                  )}
                                </div>

                                {!isSystem && (
                                  <span className="text-[10px] text-gray-300 mt-1 px-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    {new Date(event.timestamp || '').toLocaleTimeString()}
                                  </span>
                                )}
                              </div>

                            </div>
                          </div>
                        );
                      })
                    )}
                    {/* Auto-scroll anchor */}
                    <div id="chat-end" />
                  </div>
                </div>
              )}

              {activeTab === 'summary' && (
                <div className="animate-fade-in space-y-6">
                  {/* AI Summary Section */}
                  <div>
                    <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                      <FileText className="w-5 h-5 text-indigo-600" />
                      AI Generated Summary
                    </h2>
                    {summary ? (
                      <div className="prose prose-indigo max-w-none text-gray-700 whitespace-pre-line bg-indigo-50 p-6 rounded-lg border border-indigo-100 max-h-[400px] overflow-y-auto">
                        {summary}
                      </div>
                    ) : (
                      <div className="p-6 flex flex-col items-center justify-center text-gray-500 bg-gray-50 rounded-lg border border-gray-100 border-dashed">
                        {agentRunning ? (
                          <p className="animate-pulse">Generating summary...</p>
                        ) : (
                          <p>No summary available. Run the agent to generate one.</p>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Structured Decisions Table */}
                  {cycleResult?.decisions && cycleResult.decisions.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-orange-500" />
                        Key Decisions (Reorders Needed)
                      </h3>
                      <div className="overflow-x-auto border border-gray-200 rounded-lg">
                        <table className="w-full text-sm text-left">
                          <thead className="bg-gray-50 text-gray-600 font-medium border-b border-gray-200">
                            <tr>
                              <th className="py-3 px-4">SKU</th>
                              <th className="py-3 px-4">Confidence</th>
                              <th className="py-3 px-4">Reasoning</th>
                              <th className="py-3 px-4 text-center">Details</th>
                            </tr>
                          </thead>
                          <tbody>
                            {cycleResult.decisions.map((decision: any, idx: number) => (
                              <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                                <td className="py-3 px-4 font-medium">{decision.sku}</td>
                                <td className="py-3 px-4">{(decision.confidence * 100).toFixed(0)}%</td>
                                <td className="py-3 px-4 text-gray-600 truncate max-w-md" title={decision.reasoning}>
                                  {decision.reasoning}
                                </td>
                                <td className="py-3 px-4 text-center">
                                  <button
                                    onClick={() => setSelectedDecision(decision)}
                                    className="text-blue-600 hover:text-blue-800 hover:underline font-semibold text-sm flex items-center justify-center gap-1 mx-auto"
                                  >
                                    Why? <span className="text-xs">🔍</span>
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Actions Table */}
                  {cycleResult?.actions && cycleResult.actions.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-green-500" />
                        Actions Executed
                      </h3>
                      <div className="overflow-x-auto border border-gray-200 rounded-lg">
                        <table className="w-full text-sm text-left">
                          <thead className="bg-gray-50 text-gray-600 font-medium border-b border-gray-200">
                            <tr>
                              <th className="py-3 px-4">Action</th>
                              <th className="py-3 px-4">SKU</th>
                              <th className="py-3 px-4">Quantity</th>
                              <th className="py-3 px-4">Cost</th>
                              <th className="py-3 px-4">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {cycleResult.actions.map((action: any, idx: number) => (
                              <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                                <td className="py-3 px-4 font-medium text-blue-600">{action.action_type}</td>
                                <td className="py-3 px-4">{action.sku}</td>
                                <td className="py-3 px-4">{action.quantity}</td>
                                <td className="py-3 px-4">${action.total_cost?.toFixed(2)}</td>
                                <td className="py-3 px-4">
                                  <span className="inline-block px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                                    Success
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar - Recent Jobs */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden sticky top-6">
            <div className="p-4 bg-gray-50 border-b border-gray-200">
              <h2 className="font-bold text-gray-900 flex items-center gap-2">
                <Clock className="w-5 h-5 text-gray-600" />
                Recent Cycles
              </h2>
            </div>
            <div className="divide-y divide-gray-100 max-h-[600px] overflow-y-auto">
              {recentJobs.length === 0 ? (
                <div className="p-8 text-center text-gray-500 text-sm">
                  No recent jobs found.
                </div>
              ) : (
                recentJobs.map((job, index) => (
                  <button
                    key={job.id}
                    onClick={() => loadJobDetails(job.id)}
                    className="w-full text-left p-4 hover:bg-gray-50 transition group"
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-bold text-sm text-indigo-600">Cycle #{totalJobs - index}</span>
                      {job.status === 'completed' ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : job.status === 'failed' ? (
                        <XCircle className="w-4 h-4 text-red-500" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
                      )}
                    </div>
                    <div className="text-sm font-medium text-gray-900 mb-1 group-hover:text-indigo-600 transition-colors">
                      {new Date(job.created_at).toLocaleString(undefined, {
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                      })}
                    </div>
                    <div className="text-xs text-gray-500 capitalize flex justify-between">
                      <span>{job.status.replace('_', ' ')}</span>
                      <span className="font-mono text-[10px] text-gray-400">#{job.id.slice(0, 6)}</span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

      </div>

      {/* Decision Breakdown Modal */}
      {selectedDecision && (
        <DecisionBreakdown
          decision={selectedDecision}
          onClose={() => setSelectedDecision(null)}
        />
      )}
    </div>
  );
}
