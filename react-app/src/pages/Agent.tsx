import { useState, useEffect } from 'react';
import { Zap, Play, Pause, TrendingUp, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import { apiService } from '../api';
import LangGraphVisualizer from '../components/LangGraphVisualizer';
import DecisionExplainer from '../components/DecisionExplainer';
import NegotiationVisualizer from '../components/NegotiationVisualizer';

interface StreamEvent {
  type: string;
  message: string;
  stage?: string;
  details?: any;
  timestamp?: string;
}

export default function Agent() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [currentJob, setCurrentJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [agentRunning, setAgentRunning] = useState(false);
  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    failed: 0,
    running: 0,
  });

  const [cycleResult, setCycleResult] = useState<any>(null);
  const [currentStage, setCurrentStage] = useState<string | undefined>();
  const [completedStages, setCompletedStages] = useState<string[]>([]);
  const [selectedDecision, setSelectedDecision] = useState<any>(null);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      console.log('Fetching jobs from /agent/jobs...');
      const res = await apiService.agent.jobs();
      console.log('Jobs response:', res.data);

      // Handle both array and object responses
      let jobsList = [];
      if (Array.isArray(res.data)) {
        jobsList = res.data;
      } else if (res.data?.recent_jobs) {
        jobsList = res.data.recent_jobs;
      } else if (res.data?.jobs) {
        jobsList = res.data.jobs;
      }

      console.log('Processed jobs list:', jobsList);
      setJobs(jobsList);

      // Calculate stats
      const stats = {
        total: jobsList.length,
        completed: jobsList.filter((j: any) => j.status === 'completed').length,
        failed: jobsList.filter((j: any) => j.status === 'failed').length,
        running: jobsList.filter((j: any) => j.status === 'running').length,
      };
      setStats(stats);
      setAgentRunning(stats.running > 0);

      // Set current job to the first running or most recent
      const running = jobsList.find((j: any) => j.status === 'running');
      setCurrentJob(running || jobsList[0]);

      // If we have a completed job and no current result, fetch the details
      const completed = jobsList.find((j: any) => j.status === 'completed');
      if (completed && !cycleResult) {
        try {
          const jobDetails = await apiService.agent.jobStatus(completed.id || completed.job_id);
          if (jobDetails.data?.result) {
            setCycleResult(jobDetails.data.result);
          }
        } catch (err) {
          console.error('Error fetching job details:', err);
        }
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
      setJobs([]);
      setStats({ total: 0, completed: 0, failed: 0, running: 0 });
    } finally {
      setLoading(false);
    }
  };

  // Load stream logs from localStorage on mount
  useEffect(() => {
    const savedLogs = localStorage.getItem('agent_stream_logs');
    if (savedLogs) {
      try {
        setStreamEvents(JSON.parse(savedLogs));
      } catch (e) {
        console.error('Failed to parse saved logs', e);
      }
    }
  }, []);

  // Save stream logs to localStorage whenever they change
  useEffect(() => {
    if (streamEvents.length > 0) {
      localStorage.setItem('agent_stream_logs', JSON.stringify(streamEvents));
    }
  }, [streamEvents]);

  const handleRunAgent = async () => {
    try {
      setAgentRunning(true);
      const initEvent = { type: 'init', message: '🚀 Starting agent cycle...', timestamp: new Date().toISOString() };
      setStreamEvents([initEvent]);
      localStorage.setItem('agent_stream_logs', JSON.stringify([initEvent])); // Clear old logs
      setCycleResult(null); // Reset previous result
      setCurrentStage(undefined); // Reset workflow stages
      setCompletedStages([]);

      console.log('=== Agent Run Started ===');
      console.log('Calling agent runOnce...');

      const response = await apiService.agent.runOnce();
      console.log('✅ Agent response received:', response);
      console.log('Response data:', response.data);

      const jobId = response.data?.job_id;
      if (!jobId) {
        throw new Error('No job_id in response');
      }

      console.log('Job ID:', jobId);
      setCurrentJob({ job_id: jobId, status: 'running', created_at: new Date().toISOString() });

      // Add initial stream message
      setStreamEvents((prev) => [...prev, {
        type: 'info',
        message: `✅ Agent started with job ID: ${jobId}`,
        timestamp: new Date().toISOString()
      }]);

      // Start streaming
      streamAgentProgress(jobId);

      // Refresh jobs
      setTimeout(() => {
        console.log('Refreshing job list...');
        fetchJobs();
      }, 2000);
    } catch (error: any) {
      console.error('❌ Error running agent:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        code: error.code
      });

      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      setStreamEvents((prev) => [...prev, {
        type: 'error',
        message: `❌ Error: ${errorMsg}`,
        timestamp: new Date().toISOString()
      }]);
      setAgentRunning(false);
    }
  };

  const streamAgentProgress = (jobId: string) => {
    const token = localStorage.getItem('auth_token');
    const url = token
      ? `http://127.0.0.1:8000/agent/stream/${jobId}?token=${encodeURIComponent(token)}`
      : `http://127.0.0.1:8000/agent/stream/${jobId}`;

    const eventSource = new EventSource(url);
    let isClosed = false; // Flag to track if we intentionally closed the stream

    eventSource.onmessage = (event) => {
      if (isClosed) return;

      try {
        const data = JSON.parse(event.data);
        console.log('Stream event:', data);

        setStreamEvents((prev) => [...prev, {
          type: data.type,
          message: data.message,
          stage: data.stage,
          details: data.details,
          timestamp: data.timestamp || new Date().toISOString()
        }]);

        // Track workflow stages for visualizer
        if (data.stage) {
          const stage = data.stage.toUpperCase();
          setCurrentStage(stage);

          // Mark as complete if this is a completion event
          if (data.type === 'complete' || data.message?.includes('✓') || data.message?.includes('completed')) {
            setCompletedStages((prev) => {
              if (!prev.includes(stage)) {
                return [...prev, stage];
              }
              return prev;
            });
          }
        }

        // If completed, capture result and stop streaming
        if (data.type === 'complete') {
          if (data.details) {
            setCycleResult(data.details);
          }
          isClosed = true;
          eventSource.close();
          setAgentRunning(false);
          setTimeout(fetchJobs, 1000);
        }
        // If error, stop streaming
        else if (data.type === 'error') {
          isClosed = true;
          eventSource.close();
          setAgentRunning(false);
          setTimeout(fetchJobs, 1000);
        }
        // If stream explicitly closed by server
        else if (data.type === 'close') {
          isClosed = true;
          eventSource.close();
          setAgentRunning(false);
          setTimeout(fetchJobs, 1000);
        }
      } catch (error) {
        console.error('Error parsing stream event:', error);
      }
    };

    eventSource.onerror = (error) => {
      if (isClosed) return; // Ignore errors if we already closed it

      console.error('Stream error:', error);
      eventSource.close();
      setAgentRunning(false);

      // Only show error if it wasn't a clean close
      if (eventSource.readyState !== EventSource.CLOSED) {
        setStreamEvents((prev) => [...prev, {
          type: 'error',
          message: '❌ Streaming connection lost',
          timestamp: new Date().toISOString()
        }]);
      }
    };
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-emerald-500/15 text-emerald-300';
      case 'running':
        return 'bg-accent/10 text-accent';
      case 'failed':
        return 'bg-red-500/15 text-red-300';
      default:
        return 'bg-ink-900 text-white';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return CheckCircle;
      case 'running':
        return Pause;
      case 'failed':
        return AlertTriangle;
      default:
        return Clock;
    }
  };

  if (loading && jobs.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-ink-900 to-ink-800 p-8">
        <div className="max-w-7xl mx-auto">
          <p className="text-slate-400 text-center py-12">Loading agent data...</p>
        </div>
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
              <Zap className="w-8 h-8 text-accent" />
              Intelligent Agent Control
            </h1>
            <p className="text-slate-400 mt-2">Monitor and control the supply chain AI agent with live streaming</p>
          </div>
          <button
            onClick={handleRunAgent}
            disabled={agentRunning}
            className={`flex items-center gap-2 px-6 py-3 rounded-none font-semibold transition ${agentRunning
              ? 'bg-ink-700 text-white cursor-not-allowed'
              : 'bg-gradient-to-r from-accent to-accent-hover text-white hover:shadow-lg'
              }`}
          >
            {agentRunning ? (
              <>
                <Pause className="w-5 h-5 animate-spin" /> Running...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" /> Run Agent Now
              </>
            )}
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gradient-to-br from-accent/10 to-accent/5 rounded-none p-6 border border-accent/40">
            <p className="text-sm font-semibold text-accent mb-1">Total Runs</p>
            <p className="text-3xl font-bold text-accent">{stats.total}</p>
          </div>
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-none p-6 border border-emerald-500/30">
            <p className="text-sm font-semibold text-emerald-300 mb-1">Completed</p>
            <p className="text-3xl font-bold text-emerald-400">{stats.completed}</p>
          </div>
          <div className="bg-gradient-to-br from-accent/10 to-accent/5 rounded-none p-6 border border-accent/40">
            <p className="text-sm font-semibold text-accent mb-1">Running</p>
            <p className="text-3xl font-bold text-accent">{stats.running}</p>
          </div>
          <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-none p-6 border border-red-500/30">
            <p className="text-sm font-semibold text-red-300 mb-1">Failed</p>
            <p className="text-3xl font-bold text-red-400">{stats.failed}</p>
          </div>
        </div>

        {/* Workflow Visualization */}
        {(agentRunning || completedStages.length > 0 || currentJob) && (
          <LangGraphVisualizer
            currentStage={currentStage}
            completedStages={completedStages}
          />
        )}

        {/* Live Stream Console */}
        <div className="bg-ink-800 rounded-none shadow-lg p-8 mb-8 border-l-4 border-accent">
          <h2 className="text-2xl font-bold text-white mb-6">🎬 Live Agent Stream</h2>
          <div className="bg-ink-950 text-green-400 rounded-none p-6 font-mono text-sm max-h-96 overflow-y-auto border border-gray-700">
            {streamEvents.length === 0 ? (
              <p className="text-slate-400">Waiting for agent to run... Click "Run Agent Now" to start</p>
            ) : (
              streamEvents.map((event, idx) => (
                <div key={idx} className="mb-2">
                  <span className={`${event.type === 'error' ? 'text-red-400' :
                    event.type === 'complete' ? 'text-green-300' :
                      event.type === 'decision_item' ? 'text-yellow-300' :
                        event.type === 'action_item' ? 'text-accent' :
                          event.type === 'learn_item' ? 'text-purple-300' :
                            'text-green-400'
                    }`}>
                    {event.message}
                  </span>
                  {event.details && (
                    <div className="ml-4 text-slate-500 text-xs">
                      {typeof event.details === 'object'
                        ? JSON.stringify(event.details, null, 2)
                        : event.details}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Negotiation Rounds Visualization */}
        {currentJob?.id && <NegotiationVisualizer cycleId={currentJob.id} />}

        {/* Cycle Result Summary */}
        {cycleResult && (
          <div className="bg-ink-800 rounded-none shadow-lg p-8 mb-8 border-l-4 border-green-500 animate-fade-in">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <CheckCircle className="w-6 h-6 text-green-500" />
              Cycle Completed Successfully
            </h2>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-ink-900 p-4 rounded-none">
                <p className="text-sm text-slate-400">SKUs Processed</p>
                <p className="text-2xl font-bold text-white">{cycleResult.skus_processed || 0}</p>
              </div>
              <div className="bg-ink-900 p-4 rounded-none">
                <p className="text-sm text-slate-400">Reorders Triggered</p>
                <p className="text-2xl font-bold text-accent">{cycleResult.reorders_triggered || 0}</p>
              </div>
              <div className="bg-ink-900 p-4 rounded-none">
                <p className="text-sm text-slate-400">Actions Executed</p>
                <p className="text-2xl font-bold text-accent">{cycleResult.actions_executed || 0}</p>
              </div>
              <div className="bg-ink-900 p-4 rounded-none">
                <p className="text-sm text-slate-400">Errors</p>
                <p className={`text-2xl font-bold ${cycleResult.errors > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                  {cycleResult.errors || 0}
                </p>
              </div>
            </div>

            {/* Actions List */}
            {cycleResult.actions && cycleResult.actions.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-white mb-3">📦 Actions Executed</h3>
                <div className="overflow-x-auto border border-ink-700 rounded-none">
                  <table className="w-full text-sm text-left">
                    <thead className="bg-ink-900 text-slate-400 font-medium border-b border-ink-700">
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
                        <tr key={idx} className="border-b border-ink-700 hover:bg-ink-900">
                          <td className="py-3 px-4 font-medium text-accent">{action.action_type}</td>
                          <td className="py-3 px-4">{action.sku}</td>
                          <td className="py-3 px-4">{action.quantity}</td>
                          <td className="py-3 px-4">${action.total_cost?.toFixed(2)}</td>
                          <td className="py-3 px-4">
                            <span className="inline-block px-2 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300">
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

            {/* Decisions List (Reorders) */}
            {cycleResult.decisions && cycleResult.decisions.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-white mb-3">⚠️ Key Decisions (Reorders Needed)</h3>
                <div className="overflow-x-auto border border-ink-700 rounded-none">
                  <table className="w-full text-sm text-left">
                    <thead className="bg-ink-900 text-slate-400 font-medium border-b border-ink-700">
                      <tr>
                        <th className="py-3 px-4">SKU</th>
                        <th className="py-3 px-4">Confidence</th>
                        <th className="py-3 px-4">Reasoning</th>
                        <th className="py-3 px-4 text-center">Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cycleResult.decisions.map((decision: any, idx: number) => (
                        <tr key={idx} className="border-b border-ink-700 hover:bg-ink-900">
                          <td className="py-3 px-4 font-medium">{decision.sku}</td>
                          <td className="py-3 px-4">{(decision.confidence * 100).toFixed(0)}%</td>
                          <td className="py-3 px-4 text-slate-400 truncate max-w-md" title={decision.reasoning}>
                            {decision.reasoning}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <button
                              onClick={() => setSelectedDecision(decision)}
                              className="text-accent hover:text-accent hover:underline font-semibold text-sm"
                            >
                              Why? 🔍
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
        )}

        {/* Current Job Details */}
        {currentJob && (
          <div className="bg-ink-800 rounded-none shadow-lg p-8 mb-8 border-l-4 border-accent">
            <h2 className="text-2xl font-bold text-white mb-6">Current Job Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div>
                <p className="text-sm font-semibold text-slate-400 mb-1">Job ID</p>
                <p className="font-mono text-lg text-white">{currentJob.job_id?.slice(0, 16) || 'N/A'}...</p>
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-400 mb-1">Status</p>
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(currentJob.status)}`}>
                  {currentJob.status?.toUpperCase() || 'N/A'}
                </span>
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-400 mb-1">Created</p>
                <p className="text-white">{new Date(currentJob.created_at).toLocaleString()}</p>
              </div>
            </div>
          </div>
        )}

        {/* Job History */}
        <div className="bg-ink-800 rounded-none shadow-lg p-6">
          <h2 className="text-2xl font-bold text-white mb-4">Job History</h2>

          {jobs.length === 0 ? (
            <div className="text-center py-12">
              <Zap className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-400 text-lg">No agent runs yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-ink-700 bg-ink-900">
                    <th className="text-left py-3 px-4 font-semibold text-slate-300">Job ID</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-300">Status</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-300">Created</th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-300">Duration</th>
                    <th className="text-right py-3 px-4 font-semibold text-slate-300">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.slice(0, 10).map((job: any, idx: number) => {
                    const StatusIcon = getStatusIcon(job.status);
                    const jobId = job.job_id || job.id;
                    const duration = job.completed_at
                      ? `${(new Date(job.completed_at).getTime() - new Date(job.created_at).getTime()) / 1000}s`
                      : '-';

                    return (
                      <tr key={idx} className="border-b border-ink-700 hover:bg-ink-900 transition">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <StatusIcon className="w-4 h-4 text-accent" />
                            <span className="font-mono text-sm">{jobId?.slice(0, 12) || 'N/A'}...</span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(job.status)}`}>
                            {job.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm text-slate-400">
                          {new Date(job.created_at).toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-sm text-slate-400">
                          {duration}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button className="text-accent hover:text-accent font-semibold text-sm">
                            View Details
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Agent Performance */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-none p-6 border border-emerald-500/30">
            <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              Success Rate
            </h3>
            <p className="text-3xl font-bold text-emerald-400 mb-2">
              {stats.total > 0 ? ((stats.completed / stats.total) * 100).toFixed(1) : 0}%
            </p>
            <p className="text-sm text-slate-300">{stats.completed} of {stats.total} runs completed successfully</p>
          </div>

          <div className="bg-gradient-to-br from-accent/10 to-accent/5 rounded-none p-6 border border-accent/40">
            <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
              <Clock className="w-5 h-5 text-accent" />
              Average Cycle Time
            </h3>
            <p className="text-3xl font-bold text-accent mb-2">~60s</p>
            <p className="text-sm text-slate-300">Time to complete one full agent cycle</p>
          </div>
        </div>
      </div>

      {/* Decision Explainer Modal */}
      {selectedDecision && (
        <DecisionExplainer
          decision={selectedDecision}
          onClose={() => setSelectedDecision(null)}
        />
      )}
    </div>
  );
}

