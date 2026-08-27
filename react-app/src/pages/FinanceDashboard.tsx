import { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, CheckCircle, XCircle, BarChart3, Award, MessageSquare, Calendar } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiService } from '../api';

export default function FinanceDashboard() {
    const [loading, setLoading] = useState(true);
    const [summary, setSummary] = useState<any>(null);
    const [overrideHistory, setOverrideHistory] = useState<any[]>([]);
    const [budgetForecast, setBudgetForecast] = useState<any[]>([]);

    useEffect(() => {
        fetchFinanceSummary();
    }, []);

    const fetchFinanceSummary = async () => {
        try {
            setLoading(true);
            const response = await apiService.agent.financeSummary();
            const data = response.data;
            setSummary(data);

            // Mock override history (replace with real data from backend)
            const mockOverrides = [
                { date: '2024-12-01', sku: 'CHAI', amount: 500, reason: 'Critical stock level', success: true },
                { date: '2024-12-02', sku: 'CHEF', amount: 300, reason: 'High ROI opportunity', success: true },
                { date: '2024-12-03', sku: 'ANISE', amount: 400, reason: 'Seasonal demand spike', success: false },
            ];
            setOverrideHistory(mockOverrides);

            // Generate budget forecast (next 7 days)
            const forecast = [];
            const basebudget = data?.current_budget || 5000;
            const dailySpend = (data?.spent || 0) / 7; // Avg daily spend

            for (let i = 0; i < 7; i++) {
                forecast.push({
                    day: `Day ${i + 1}`,
                    projected: Math.max(0, basebudget - (dailySpend * i)),
                    actual: i === 0 ? data?.remaining || basebudget : null,
                });
            }
            setBudgetForecast(forecast);

        } catch (error) {
            console.error('Error fetching finance summary:', error);
            setSummary({
                current_budget: 5000,
                spent: 0,
                remaining: 5000,
                approved_count: 0,
                rejected_count: 0,
                override_count: 0,
                avg_roi: 0,
                total_value: 0,
            });
            setOverrideHistory([]);
            setBudgetForecast([]);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="text-xl text-slate-400">Loading finance data...</div>
            </div>
        );
    }

    const budgetUsedPercent = summary ? (summary.spent / summary.current_budget) * 100 : 0;
    const totalDecisions = (summary?.approved_count || 0) + (summary?.rejected_count || 0);
    const negotiationSuccessRate = totalDecisions > 0
        ? ((summary?.override_count || 0) / (summary?.rejected_count || 1)) * 100
        : 0;

    return (
        <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                    <DollarSign className="w-8 h-8 text-emerald-400" />
                    Finance Dashboard
                </h1>
                <p className="text-slate-400 mt-2">Budget analytics, negotiation metrics, and spending forecasts</p>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-ink-800 rounded-none shadow p-6 border-l-4 border-green-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-slate-400">Current Budget</p>
                            <p className="text-2xl font-bold text-white">${summary?.current_budget?.toLocaleString()}</p>
                        </div>
                        <DollarSign className="w-10 h-10 text-green-500 opacity-20" />
                    </div>
                </div>

                <div className="bg-ink-800 rounded-none shadow p-6 border-l-4 border-accent">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-slate-400">Total Spent</p>
                            <p className="text-2xl font-bold text-white">${summary?.spent?.toLocaleString()}</p>
                        </div>
                        <TrendingUp className="w-10 h-10 text-accent opacity-20" />
                    </div>
                </div>

                <div className="bg-ink-800 rounded-none shadow p-6 border-l-4 border-yellow-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-slate-400">Remaining</p>
                            <p className="text-2xl font-bold text-white">${summary?.remaining?.toLocaleString()}</p>
                        </div>
                        <BarChart3 className="w-10 h-10 text-yellow-500 opacity-20" />
                    </div>
                </div>

                <div className="bg-ink-800 rounded-none shadow p-6 border-l-4 border-accent">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-slate-400">Avg ROI</p>
                            <p className="text-2xl font-bold text-white">{summary?.avg_roi?.toFixed(1)}x</p>
                        </div>
                        <TrendingUp className="w-10 h-10 text-accent opacity-20" />
                    </div>
                </div>
            </div>

            {/* Negotiation Success Rate */}
            <div className="bg-gradient-to-br from-accent/10 to-accent/5 rounded-none shadow-lg p-6 border border-accent/40">
                <div className="flex items-center gap-3 mb-4">
                    <Award className="w-6 h-6 text-accent" />
                    <h2 className="text-xl font-bold text-white">Negotiation Success Rate</h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                        <p className="text-sm text-accent mb-2">Total Rejections</p>
                        <p className="text-4xl font-bold text-accent">{summary?.rejected_count || 0}</p>
                    </div>
                    <div className="text-center">
                        <p className="text-sm text-pink-400 mb-2">Successful Overrides</p>
                        <p className="text-4xl font-bold text-pink-400">{summary?.override_count || 0}</p>
                    </div>
                    <div className="text-center">
                        <p className="text-sm text-accent mb-2">Success Rate</p>
                        <p className="text-4xl font-bold text-accent">{negotiationSuccessRate.toFixed(0)}%</p>
                    </div>
                </div>

                <div className="mt-4 bg-ink-800/50 rounded-none p-4">
                    <p className="text-sm text-slate-300">
                        <strong>What this means:</strong> {negotiationSuccessRate > 50 ?
                            'Agent is highly effective at negotiating budget overrides for critical items! 🌟' :
                            negotiationSuccessRate > 25 ?
                                'Agent successfully negotiates about ⅓ of rejections, maintaining good budget control.' :
                                'Agent maintains strict budget discipline, only overriding when absolutely critical.'}
                    </p>
                </div>
            </div>

            {/* Budget Burn-Down */}
            <div className="bg-ink-800 rounded-none shadow p-6">
                <h2 className="text-xl font-bold text-white mb-4">Budget Usage</h2>
                <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Used: ${summary?.spent?.toLocaleString()}</span>
                        <span className="text-slate-400">{budgetUsedPercent.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-ink-700 rounded-full h-4">
                        <div
                            className={`h-4 rounded-full transition-all ${budgetUsedPercent > 90 ? 'bg-red-500' : budgetUsedPercent > 70 ? 'bg-yellow-500' : 'bg-green-500'
                                }`}
                            style={{ width: `${Math.min(budgetUsedPercent, 100)}%` }}
                        ></div>
                    </div>
                    <div className="flex justify-between text-sm text-slate-400">
                        <span>$0</span>
                        <span>${summary?.current_budget?.toLocaleString()}</span>
                    </div>
                </div>
            </div>

            {/* Budget Forecast Chart */}
            <div className="bg-ink-800 rounded-none shadow p-6">
                <div className="flex items-center gap-3 mb-4">
                    <Calendar className="w-6 h-6 text-accent" />
                    <h2 className="text-xl font-bold text-white">7-Day Budget Forecast</h2>
                </div>
                <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={budgetForecast}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="day" stroke="#64748b" />
                        <YAxis stroke="#64748b" />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
                        />
                        <Line
                            type="monotone"
                            dataKey="projected"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            name="Projected Budget"
                            strokeDasharray="5 5"
                        />
                        <Line
                            type="monotone"
                            dataKey="actual"
                            stroke="#10b981"
                            strokeWidth={3}
                            name="Actual Budget"
                        />
                    </LineChart>
                </ResponsiveContainer>
                <p className="text-sm text-slate-400 mt-4">
                    <strong>Projection assumes:</strong> Average daily spending of ${((summary?.spent || 0) / 7).toFixed(0)}.
                    Actual spending may vary based on agent decisions and market conditions.
                </p>
            </div>

            {/* Override History */}
            <div className="bg-ink-800 rounded-none shadow p-6">
                <div className="flex items-center gap-3 mb-4">
                    <MessageSquare className="w-6 h-6 text-accent" />
                    <h2 className="text-xl font-bold text-white">Recent Override History</h2>
                </div>

                <div className="space-y-3">
                    {overrideHistory.length > 0 ? overrideHistory.map((override, idx) => (
                        <div key={idx} className={`p-4 rounded-none border-l-4 ${override.success ? 'bg-emerald-500/10 border-green-500' : 'bg-red-500/10 border-red-500'}`}>
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-3">
                                    {override.success ? (
                                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                                    ) : (
                                        <XCircle className="w-5 h-5 text-red-400" />
                                    )}
                                    <div>
                                        <p className="font-semibold text-white">{override.sku}</p>
                                        <p className="text-sm text-slate-400">{override.reason}</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className="font-bold text-lg">${override.amount}</p>
                                    <p className="text-xs text-slate-400">{new Date(override.date).toLocaleDateString()}</p>
                                </div>
                            </div>
                            <span className={`text-xs px-2 py-1 rounded-full ${override.success ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>
                                {override.success ? '✓ Override Approved' : '✗ Override Denied'}
                            </span>
                        </div>
                    )) : (
                        <p className="text-sm text-slate-400 italic text-center py-8">No override history available yet.</p>
                    )}
                </div>
            </div>

            {/* Approval Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-ink-800 rounded-none shadow p-6">
                    <div className="flex items-center gap-3 mb-2">
                        <CheckCircle className="w-6 h-6 text-green-500" />
                        <h3 className="text-lg font-semibold text-white">Approved</h3>
                    </div>
                    <p className="text-3xl font-bold text-emerald-400">{summary?.approved_count}</p>
                    <p className="text-sm text-slate-400 mt-1">Orders funded</p>
                </div>

                <div className="bg-ink-800 rounded-none shadow p-6">
                    <div className="flex items-center gap-3 mb-2">
                        <XCircle className="w-6 h-6 text-red-500" />
                        <h3 className="text-lg font-semibold text-white">Rejected</h3>
                    </div>
                    <p className="text-3xl font-bold text-red-400">{summary?.rejected_count}</p>
                    <p className="text-sm text-slate-400 mt-1">Budget exceeded</p>
                </div>

                <div className="bg-ink-800 rounded-none shadow p-6">
                    <div className="flex items-center gap-3 mb-2">
                        <TrendingUp className="w-6 h-6 text-accent" />
                        <h3 className="text-lg font-semibold text-white">Overrides</h3>
                    </div>
                    <p className="text-3xl font-bold text-accent">{summary?.override_count}</p>
                    <p className="text-sm text-slate-400 mt-1">Negotiation wins</p>
                </div>
            </div>

            {/* Info Box */}
            <div className="bg-accent/10 border border-accent/40 rounded-none p-6">
                <h3 className="text-lg font-semibold text-accent mb-2">💡 Dynamic Budgeting</h3>
                <p className="text-accent">
                    The budget automatically adjusts based on recent sales revenue: <strong>Base ($5,000) + 30% of 7-day revenue</strong>.
                    Orders are prioritized by ROI, and critical high-ROI items can override budget limits after agent negotiation.
                </p>
            </div>
        </div>
    );
}
