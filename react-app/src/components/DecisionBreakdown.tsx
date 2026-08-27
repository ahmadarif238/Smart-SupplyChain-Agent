import { X, Calculator, Target, DollarSign, AlertTriangle, TrendingUp } from 'lucide-react';

interface DecisionBreakdownProps {
    decision: {
        sku: string;
        product_name?: string;
        reorder_required: boolean;
        order_quantity?: number;
        reason: string;
        reasoning?: string;
        details?: {
            current_stock: number;
            daily_avg_demand: number;
            lead_time_days: number;
            safety_stock?: number;
            reorder_point?: number;
            forecast?: number;
        };
        cost_analysis?: {
            cost_per_unit: number;
            total_cost: number;
            roi?: number;
        };
        finance_metrics?: {
            roi: number;
            total_cost: number;
            projected_value: number;
            days_until_stockout: number;
            stockout_risk_factor: number;
        };
    };
    onClose: () => void;
}

export default function DecisionBreakdown({ decision, onClose }: DecisionBreakdownProps) {
    const details = decision.details;
    const costAnalysis = decision.cost_analysis;
    const financeMetrics = decision.finance_metrics;

    const currentStock = details?.current_stock || 0;
    const dailyDemand = details?.daily_avg_demand || 0;
    const leadTime = details?.lead_time_days || 7;
    const safetyStock = details?.safety_stock || 10;
    const reorderPoint = details?.reorder_point || 0;

    const orderQty = decision.order_quantity || 0;
    const costPerUnit = costAnalysis?.cost_per_unit || (financeMetrics && orderQty > 0 ? financeMetrics.total_cost / orderQty : 0) || 0;
    const totalCost = financeMetrics?.total_cost || costAnalysis?.total_cost || (orderQty * costPerUnit);
    const roi = financeMetrics?.roi || costAnalysis?.roi || 0;
    const projectedValue = financeMetrics?.projected_value || 0;

    const daysUntilStockout = dailyDemand > 0 ? currentStock / dailyDemand : 999;
    const isStockoutCritical = daysUntilStockout < leadTime;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-ink-800 rounded-none shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="sticky top-0 bg-gradient-to-r from-accent to-accent-hover text-white p-6 rounded-t-lg">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-2xl font-bold flex items-center gap-2">
                                <Calculator className="w-7 h-7" />
                                Decision Breakdown
                            </h2>
                            <p className="text-purple-100 mt-1">
                                {decision.product_name || decision.sku}
                            </p>
                        </div>
                        <button
                            onClick={onClose}
                            className="text-white hover:bg-ink-800 hover:bg-opacity-20 rounded-full p-2 transition"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                    {/* Decision Summary */}
                    <div className={`p-4 rounded-none border-2 ${decision.reorder_required ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-ink-900 border-ink-700'}`}>
                        <div className="flex items-center justify-between">
                            <div>
                                <span className="font-bold text-lg">
                                    {decision.reorder_required ? '✅ Reorder Recommended' : '⏸️ Hold / No Action'}
                                </span>
                                {decision.reorder_required && orderQty > 0 && (
                                    <p className="text-sm text-slate-300 mt-1">
                                        Order Quantity: <span className="font-bold text-accent">{orderQty} units</span>
                                    </p>
                                )}
                            </div>
                            {decision.reorder_required && (
                                <TrendingUp className="w-10 h-10 text-emerald-400" />
                            )}
                        </div>
                        <p className="text-sm text-slate-400 mt-2">{decision.reason}</p>
                    </div>

                    {/* Economic Order Quantity (EOQ) */}
                    {decision.reorder_required && orderQty > 0 && (
                        <div className="bg-accent/10 border border-accent/40 rounded-none p-5">
                            <h3 className="font-bold text-lg text-accent mb-3 flex items-center gap-2">
                                <Calculator className="w-5 h-5" />
                                📊 Economic Order Quantity (EOQ)
                            </h3>
                            <div className="space-y-2 text-sm text-white">
                                <p className="font-mono bg-ink-800 p-3 rounded border border-blue-100">
                                    EOQ = sqrt(2 × Annual Demand × Order Cost / Holding Cost)
                                </p>
                                <p className="text-slate-400">
                                    In this case, the agent calculated an optimal order quantity of{' '}
                                    <span className="font-bold text-accent">{orderQty} units</span> based on forecast demand,
                                    lead time ({leadTime} days), and safety stock requirements.
                                </p>
                                <div className="grid grid-cols-2 gap-3 mt-3">
                                    <div className="bg-ink-800 p-2 rounded">
                                        <p className="text-xs text-slate-400">Daily Demand</p>
                                        <p className="font-bold text-white">{dailyDemand.toFixed(1)} units/day</p>
                                    </div>
                                    <div className="bg-ink-800 p-2 rounded">
                                        <p className="text-xs text-slate-400">Lead Time</p>
                                        <p className="font-bold text-white">{leadTime} days</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Reorder Point */}
                    <div className="bg-orange-500/10 border border-orange-500/30 rounded-none p-5">
                        <h3 className="font-bold text-lg text-orange-300 mb-3 flex items-center gap-2">
                            <Target className="w-5 h-5" />
                            🎯 Reorder Point Analysis
                        </h3>
                        <div className="space-y-2 text-sm text-white">
                            <p className="font-mono bg-ink-800 p-3 rounded border border-orange-100">
                                Reorder Point = (Daily Demand × Lead Time) + Safety Stock
                            </p>
                            <p className="font-mono bg-ink-800 p-3 rounded border border-orange-100">
                                = ({dailyDemand.toFixed(1)} × {leadTime}) + {safetyStock} = <span className="font-bold text-orange-400">{reorderPoint} units</span>
                            </p>
                            <div className="grid grid-cols-2 gap-3 mt-3">
                                <div className="bg-ink-800 p-2 rounded">
                                    <p className="text-xs text-slate-400">Current Stock</p>
                                    <p className={`font-bold ${currentStock < reorderPoint ? 'text-red-400' : 'text-emerald-400'}`}>
                                        {currentStock} units
                                    </p>
                                </div>
                                <div className="bg-ink-800 p-2 rounded">
                                    <p className="text-xs text-slate-400">Safety Stock</p>
                                    <p className="font-bold text-white">{safetyStock} units</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* ROI Calcul

ation */}
                    {roi > 0 && (
                        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-none p-5">
                            <h3 className="font-bold text-lg text-emerald-300 mb-3 flex items-center gap-2">
                                <DollarSign className="w-5 h-5" />
                                💰 Return on Investment (ROI)
                            </h3>
                            <div className="space-y-2 text-sm text-white">
                                <p className="font-mono bg-ink-800 p-3 rounded border border-green-100">
                                    ROI = Projected Value / Order Cost
                                </p>
                                <p className="font-mono bg-ink-800 p-3 rounded border border-green-100">
                                    = ${projectedValue.toLocaleString()} / ${totalCost.toLocaleString()} = <span className="font-bold text-emerald-400">{roi.toFixed(1)}x</span>
                                </p>
                                <p className="text-slate-400 mt-2">
                                    This order is expected to generate <span className="font-bold text-emerald-400">{((roi - 1) * 100).toFixed(0)}% return</span> on investment.
                                </p>
                                <div className="grid grid-cols-2 gap-3 mt-3">
                                    <div className="bg-ink-800 p-2 rounded">
                                        <p className="text-xs text-slate-400">Order Cost</p>
                                        <p className="font-bold text-white">${totalCost.toLocaleString()}</p>
                                    </div>
                                    <div className="bg-ink-800 p-2 rounded">
                                        <p className="text-xs text-slate-400">Projected Value</p>
                                        <p className="font-bold text-emerald-400">${projectedValue.toLocaleString()}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Stockout Risk */}
                    <div className={`border rounded-none p-5 ${isStockoutCritical ? 'bg-red-500/10 border-red-500/30' : 'bg-ink-900 border-ink-700'}`}>
                        <h3 className={`font-bold text-lg mb-3 flex items-center gap-2 ${isStockoutCritical ? 'text-red-300' : 'text-white'}`}>
                            <AlertTriangle className="w-5 h-5" />
                            ⚠️ Stockout Risk
                        </h3>
                        <div className="space-y-2 text-sm text-white">
                            <p className="font-mono bg-ink-800 p-3 rounded border">
                                Days Until Stockout = Current Stock / Daily Demand
                            </p>
                            <p className="font-mono bg-ink-800 p-3 rounded border">
                                = {currentStock} / {dailyDemand.toFixed(1)} = <span className={`font-bold ${isStockoutCritical ? 'text-red-400' : 'text-emerald-400'}`}>{daysUntilStockout.toFixed(1)} days</span>
                            </p>
                            <div className={`mt-3 p-3 rounded ${isStockoutCritical ? 'bg-red-500/15 border border-red-500/30' : 'bg-emerald-500/15 border border-emerald-500/30'}`}>
                                <p className={`font-bold ${isStockoutCritical ? 'text-red-300' : 'text-emerald-300'}`}>
                                    {isStockoutCritical ? `🚨 CRITICAL: Stockout before next delivery!` : `✅ Safe: Sufficient stock until delivery`}
                                </p>
                                <p className={`text-xs mt-1 ${isStockoutCritical ? 'text-red-400' : 'text-emerald-400'}`}>
                                    {isStockoutCritical
                                        ? `Stock will run out in ${daysUntilStockout.toFixed(1)} days, but lead time is ${leadTime} days.`
                                        : `Stock will last ${daysUntilStockout.toFixed(1)} days, which exceeds the ${leadTime}-day lead time.`
                                    }
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Additional Reasoning */}
                    {decision.reasoning && (
                        <div className="bg-accent/10 border border-accent/40 rounded-none p-5">
                            <h3 className="font-bold text-lg text-accent mb-3">
                                💭 Agent Reasoning
                            </h3>
                            <p className="text-sm text-white whitespace-pre-wrap">{decision.reasoning}</p>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="sticky bottom-0 bg-ink-900 border-t border-ink-700 p-4 rounded-b-lg">
                    <button
                        onClick={onClose}
                        className="w-full bg-gradient-to-r from-accent to-accent-hover text-white font-semibold py-3 px-6 rounded-none hover:shadow-lg transition"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div >
    );
}
