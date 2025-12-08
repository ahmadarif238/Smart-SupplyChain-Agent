import { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, CheckCircle, XCircle, Award } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, PieChart as RechartsPie, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { apiService } from '../api';
import Card from '../components/ui/Card';

const COLORS = ['#10b981', '#ef4444', '#3b82f6', '#f59e0b', '#8b5cf6'];

export default function FinanceAnalytics() {
    const [loading, setLoading] = useState(true);
    const [financeSummary, setFinanceSummary] = useState<any>(null);
    const [budgetHistory, setBudgetHistory] = useState<any[]>([]);
    const [roiDistribution, setRoiDistribution] = useState<any[]>([]);
    const [approvalTrends, setApprovalTrends] = useState<any[]>([]);

    useEffect(() => {
        fetchFinanceData();
    }, []);

    const fetchFinanceData = async () => {
        try {
            setLoading(true);

            // Fetch finance summary
            const summaryRes = await apiService.get('/agent/finance-summary');
            setFinanceSummary(summaryRes.data);

            // Parse and prepare chart data
            prepareChartData(summaryRes.data);

        } catch (error) {
            console.error('Error fetching finance data:', error);
        } finally {
            setLoading(false);
        }
    };

    const prepareChartData = (data: any) => {
        // Budget utilization over cycles
        const budgetData = data?.cycles?.map((cycle: any, idx: number) => ({
            cycle: `C${idx + 1}`,
            budget: cycle.total_budget || 5000,
            spent: cycle.total_spent || 0,
            savings: (cycle.total_budget || 5000) - (cycle.total_spent || 0)
        })) || [];
        setBudgetHistory(budgetData);

        // ROI distribution
        const roiData = [
            { name: 'High ROI (>2.0)', value: data?.high_roi_count || 0, color: COLORS[0] },
            { name: 'Medium ROI (1.0-2.0)', value: data?.medium_roi_count || 0, color: COLORS[2] },
            { name: 'Low ROI (<1.0)', value: data?.low_roi_count || 0, color: COLORS[1] },
        ].filter(item => item.value > 0);
        setRoiDistribution(roiData);

        // Approval trends
        const approvalData = data?.cycles?.map((cycle: any, idx: number) => ({
            cycle: `C${idx + 1}`,
            approved: cycle.approved_count || 0,
            rejected: cycle.rejected_count || 0,
            overrides: cycle.override_count || 0,
        })) || [];
        setApprovalTrends(approvalData);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="text-center">
                    <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-slate-500 font-medium">Loading finance analytics...</p>
                </div>
            </div>
        );
    }

    const stats = {
        totalBudget: financeSummary?.total_budget || 5000,
        totalSpent: financeSummary?.total_spent || 0,
        approvalRate: financeSummary?.approval_rate || 0,
        overrideCount: financeSummary?.override_count || 0,
        avgNegotiationWins: financeSummary?.avg_negotiation_wins || 0,
    };

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                    <DollarSign className="w-7 h-7 text-green-600" />
                    Finance Analytics & Insights
                </h1>
                <p className="text-slate-500 mt-1">Track budget utilization, approval rates, and ROI performance</p>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="border-l-4 border-l-green-500">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-slate-500">Total Budget</p>
                            <h3 className="text-2xl font-bold text-slate-900 mt-1">${stats.totalBudget.toLocaleString()}</h3>
                            <p className="text-xs text-slate-400 mt-2">Per cycle allocation</p>
                        </div>
                        <div className="p-3 bg-green-50 rounded-xl">
                            <DollarSign className="w-6 h-6 text-green-600" />
                        </div>
                    </div>
                </Card>

                <Card className="border-l-4 border-l-blue-500">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-slate-500">Approval Rate</p>
                            <h3 className="text-2xl font-bold text-slate-900 mt-1">{(stats.approvalRate * 100).toFixed(1)}%</h3>
                            <div className="flex items-center mt-2 text-xs text-green-600">
                                <TrendingUp className="w-3 h-3 mr-1" />
                                <span className="font-medium">Efficient decisions</span>
                            </div>
                        </div>
                        <div className="p-3 bg-blue-50 rounded-xl">
                            <CheckCircle className="w-6 h-6 text-blue-600" />
                        </div>
                    </div>
                </Card>

                <Card className="border-l-4 border-l-purple-500">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-slate-500">Negotiation Wins</p>
                            <h3 className="text-2xl font-bold text-slate-900 mt-1">{stats.overrideCount}</h3>
                            <p className="text-xs text-purple-600 mt-2 font-medium">Overrides granted</p>
                        </div>
                        <div className="p-3 bg-purple-50 rounded-xl">
                            <Award className="w-6 h-6 text-purple-600" />
                        </div>
                    </div>
                </Card>

                <Card className="border-l-4 border-l-orange-500">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-slate-500">Avg Savings</p>
                            <h3 className="text-2xl font-bold text-slate-900 mt-1">
                                ${((stats.totalBudget - stats.totalSpent) || 0).toLocaleString()}
                            </h3>
                            <p className="text-xs text-slate-400 mt-2">Budget remaining</p>
                        </div>
                        <div className="p-3 bg-orange-50 rounded-xl">
                            <TrendingUp className="w-6 h-6 text-orange-600" />
                        </div>
                    </div>
                </Card>
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Budget Utilization */}
                <Card title="Budget Utilization Over Time">
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={budgetHistory}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey="cycle" stroke="#64748b" />
                            <YAxis stroke="#64748b" />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
                            />
                            <Legend />
                            <Bar dataKey="budget" fill="#3b82f6" name="Total Budget" />
                            <Bar dataKey="spent" fill="#10b981" name="Amount Spent" />
                            <Bar dataKey="savings" fill="#f59e0b" name="Savings" />
                        </BarChart>
                    </ResponsiveContainer>
                </Card>

                {/* ROI Distribution */}
                <Card title="ROI Distribution">
                    <ResponsiveContainer width="100%" height={300}>
                        <RechartsPie>
                            <Pie
                                data={roiDistribution}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey="value"
                            >
                                {roiDistribution.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </RechartsPie>
                    </ResponsiveContainer>
                </Card>

                {/* Approval Trends */}
                <Card title="Approval vs Rejection Trends" className="lg:col-span-2">
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={approvalTrends}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey="cycle" stroke="#64748b" />
                            <YAxis stroke="#64748b" />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
                            />
                            <Legend />
                            <Line type="monotone" dataKey="approved" stroke="#10b981" strokeWidth={2} name="Approved" />
                            <Line type="monotone" dataKey="rejected" stroke="#ef4444" strokeWidth={2} name="Rejected" />
                            <Line type="monotone" dataKey="overrides" stroke="#8b5cf6" strokeWidth={2} name="Overrides" />
                        </LineChart>
                    </ResponsiveContainer>
                </Card>
            </div>

            {/* Recent Decisions Table */}
            <Card title="Recent Finance Decisions">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-slate-50 border-b border-slate-200">
                            <tr>
                                <th className="text-left py-3 px-4 font-semibold text-slate-700">SKU</th>
                                <th className="text-left py-3 px-4 font-semibold text-slate-700">Cost</th>
                                <th className="text-left py-3 px-4 font-semibold text-slate-700">ROI</th>
                                <th className="text-left py-3 px-4 font-semibold text-slate-700">Decision</th>
                                <th className="text-left py-3 px-4 font-semibold text-slate-700">Reason</th>
                            </tr>
                        </thead>
                        <tbody>
                            {financeSummary?.recent_decisions?.slice(0, 10).map((decision: any, idx: number) => (
                                <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                                    <td className="py-3 px-4 font-medium">{decision.sku}</td>
                                    <td className="py-3 px-4">${decision.total_cost?.toFixed(2)}</td>
                                    <td className="py-3 px-4">
                                        <span className={`font-medium ${decision.roi > 2 ? 'text-green-600' :
                                            decision.roi > 1 ? 'text-blue-600' : 'text-orange-600'
                                            }`}>
                                            {decision.roi?.toFixed(2)}x
                                        </span>
                                    </td>
                                    <td className="py-3 px-4">
                                        {decision.approved ? (
                                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                                                <CheckCircle className="w-3 h-3" />
                                                Approved
                                            </span>
                                        ) : (
                                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                                                <XCircle className="w-3 h-3" />
                                                Rejected
                                            </span>
                                        )}
                                    </td>
                                    <td className="py-3 px-4 text-slate-600 truncate max-w-xs">{decision.reason}</td>
                                </tr>
                            )) || (
                                    <tr>
                                        <td colSpan={5} className="py-8 text-center text-slate-500">
                                            No recent decisions available
                                        </td>
                                    </tr>
                                )}
                        </tbody>
                    </table>
                </div>
            </Card>
        </div>
    );
}
