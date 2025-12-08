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
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
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
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
        <div className="max-w-7xl mx-auto">
          <p className="text-gray-600 text-center py-12">Loading agent data...</p>
        </div>
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
              <Zap className="w-8 h-8 text-purple-600" />
              Intelligent Agent Control
            </h1>
            <p className="text-gray-600 mt-2">Monitor and control the supply chain AI agent with live streaming</p>
          </div>
          <button
            onClick={handleRunAgent}
            disabled={agentRunning}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition ${agentRunning
              ? 'bg-gray-400 text-white cursor-not-allowed'
              : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:shadow-lg'
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
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-300">
            <p className="text-sm font-semibold text-blue-900 mb-1">Total Runs</p>
            <p className="text-3xl font-bold text-blue-600">{stats.total}</p>
          </div>
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6 border border-green-300">
            <p className="text-sm font-semibold text-green-900 mb-1">Completed</p>
            <p className="text-3xl font-bold text-green-600">{stats.completed}</p>
          </div>
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6 border border-purple-300">
            <p className="text-sm font-semibold text-purple-900 mb-1">Running</p>
            <p className="text-3xl font-bold text-purple-600">{stats.running}</p>
          </div>
          <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-lg p-6 border border-red-300">
            <p className="text-sm font-semibold text-red-900 mb-1">Failed</p>
            <p className="text-3xl font-bold text-red-600">{stats.failed}</p>
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
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8 border-l-4 border-purple-600">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">🎬 Live Agent Stream</h2>
          <div className="bg-gray-900 text-green-400 rounded-lg p-6 font-mono text-sm max-h-96 overflow-y-auto border border-gray-700">
            {streamEvents.length === 0 ? (
              <p className="text-gray-500">Waiting for agent to run... Click "Run Agent Now" to start</p>
            ) : (
              streamEvents.map((event, idx) => (
                <div key={idx} className="mb-2">
                  <span className={`${event.type === 'error' ? 'text-red-400' :
                    event.type === 'complete' ? 'text-green-300' :
                      event.type === 'decision_item' ? 'text-yellow-300' :
                        event.type === 'action_item' ? 'text-blue-300' :
                          event.type === 'learn_item' ? 'text-purple-300' :
                            'text-green-400'
                    }`}>
                    {event.message}
                  </span>
                  {event.details && (
                    <div className="ml-4 text-gray-400 text-xs">
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
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8 border-l-4 border-green-500 animate-fade-in">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
              <CheckCircle className="w-6 h-6 text-green-500" />
              Cycle Completed Successfully
            </h2>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-500">SKUs Processed</p>
                <p className="text-2xl font-bold text-gray-900">{cycleResult.skus_processed || 0}</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-500">Reorders Triggered</p>
                <p className="text-2xl font-bold text-blue-600">{cycleResult.reorders_triggered || 0}</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-500">Actions Executed</p>
                <p className="text-2xl font-bold text-purple-600">{cycleResult.actions_executed || 0}</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-500">Errors</p>
                <p className={`text-2xl font-bold ${cycleResult.errors > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {cycleResult.errors || 0}
                </p>
              </div>
            </div>

            {/* Actions List */}
            {cycleResult.actions && cycleResult.actions.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">📦 Actions Executed</h3>
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

            {/* Decisions List (Reorders) */}
            {cycleResult.decisions && cycleResult.decisions.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">⚠️ Key Decisions (Reorders Needed)</h3>
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
                              className="text-blue-600 hover:text-blue-800 hover:underline font-semibold text-sm"
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
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8 border-l-4 border-purple-600">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Current Job Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div>
                <p className="text-sm font-semibold text-gray-600 mb-1">Job ID</p>
                <p className="font-mono text-lg text-gray-900">{currentJob.job_id?.slice(0, 16) || 'N/A'}...</p>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-600 mb-1">Status</p>
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(currentJob.status)}`}>
                  {currentJob.status?.toUpperCase() || 'N/A'}
                </span>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-600 mb-1">Created</p>
                <p className="text-gray-900">{new Date(currentJob.created_at).toLocaleString()}</p>
              </div>
            </div>
          </div>
        )}

        {/* Job History */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Job History</h2>

          {jobs.length === 0 ? (
            <div className="text-center py-12">
              <Zap className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No agent runs yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-300 bg-gray-50">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Job ID</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Created</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Duration</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-700">Actions</th>
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
                      <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50 transition">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <StatusIcon className="w-4 h-4 text-blue-600" />
                            <span className="font-mono text-sm">{jobId?.slice(0, 12) || 'N/A'}...</span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(job.status)}`}>
                            {job.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">
                          {new Date(job.created_at).toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">
                          {duration}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button className="text-blue-600 hover:text-blue-800 font-semibold text-sm">
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
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6 border border-green-300">
            <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              Success Rate
            </h3>
            <p className="text-3xl font-bold text-green-600 mb-2">
              {stats.total > 0 ? ((stats.completed / stats.total) * 100).toFixed(1) : 0}%
            </p>
            <p className="text-sm text-gray-700">{stats.completed} of {stats.total} runs completed successfully</p>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-300">
            <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-600" />
              Average Cycle Time
            </h3>
            <p className="text-3xl font-bold text-blue-600 mb-2">~60s</p>
            <p className="text-sm text-gray-700">Time to complete one full agent cycle</p>
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

