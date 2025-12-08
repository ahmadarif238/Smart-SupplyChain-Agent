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
            <div className="bg-white rounded-lg shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="sticky top-0 bg-gradient-to-r from-purple-600 to-pink-600 text-white p-6 rounded-t-lg">
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
                            className="text-white hover:bg-white hover:bg-opacity-20 rounded-full p-2 transition"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                    {/* Decision Summary */}
                    <div className={`p-4 rounded-lg border-2 ${decision.reorder_required ? 'bg-green-50 border-green-300' : 'bg-gray-50 border-gray-300'}`}>
                        <div className="flex items-center justify-between">
                            <div>
                                <span className="font-bold text-lg">
                                    {decision.reorder_required ? '✅ Reorder Recommended' : '⏸️ Hold / No Action'}
                                </span>
                                {decision.reorder_required && orderQty > 0 && (
                                    <p className="text-sm text-gray-700 mt-1">
                                        Order Quantity: <span className="font-bold text-blue-600">{orderQty} units</span>
                                    </p>
                                )}
                            </div>
                            {decision.reorder_required && (
                                <TrendingUp className="w-10 h-10 text-green-600" />
                            )}
                        </div>
                        <p className="text-sm text-gray-600 mt-2">{decision.reason}</p>
                    </div>

                    {/* Economic Order Quantity (EOQ) */}
                    {decision.reorder_required && orderQty > 0 && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-5">
                            <h3 className="font-bold text-lg text-blue-900 mb-3 flex items-center gap-2">
                                <Calculator className="w-5 h-5" />
                                📊 Economic Order Quantity (EOQ)
                            </h3>
                            <div className="space-y-2 text-sm text-gray-800">
                                <p className="font-mono bg-white p-3 rounded border border-blue-100">
                                    EOQ = sqrt(2 × Annual Demand × Order Cost / Holding Cost)
                                </p>
                                <p className="text-gray-600">
                                    In this case, the agent calculated an optimal order quantity of{' '}
                                    <span className="font-bold text-blue-700">{orderQty} units</span> based on forecast demand,
                                    lead time ({leadTime} days), and safety stock requirements.
                                </p>
                                <div className="grid grid-cols-2 gap-3 mt-3">
                                    <div className="bg-white p-2 rounded">
                                        <p className="text-xs text-gray-500">Daily Demand</p>
                                        <p className="font-bold text-gray-900">{dailyDemand.toFixed(1)} units/day</p>
                                    </div>
                                    <div className="bg-white p-2 rounded">
                                        <p className="text-xs text-gray-500">Lead Time</p>
                                        <p className="font-bold text-gray-900">{leadTime} days</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Reorder Point */}
                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-5">
                        <h3 className="font-bold text-lg text-orange-900 mb-3 flex items-center gap-2">
                            <Target className="w-5 h-5" />
                            🎯 Reorder Point Analysis
                        </h3>
                        <div className="space-y-2 text-sm text-gray-800">
                            <p className="font-mono bg-white p-3 rounded border border-orange-100">
                                Reorder Point = (Daily Demand × Lead Time) + Safety Stock
                            </p>
                            <p className="font-mono bg-white p-3 rounded border border-orange-100">
                                = ({dailyDemand.toFixed(1)} × {leadTime}) + {safetyStock} = <span className="font-bold text-orange-700">{reorderPoint} units</span>
                            </p>
                            <div className="grid grid-cols-2 gap-3 mt-3">
                                <div className="bg-white p-2 rounded">
                                    <p className="text-xs text-gray-500">Current Stock</p>
                                    <p className={`font-bold ${currentStock < reorderPoint ? 'text-red-600' : 'text-green-600'}`}>
                                        {currentStock} units
                                    </p>
                                </div>
                                <div className="bg-white p-2 rounded">
                                    <p className="text-xs text-gray-500">Safety Stock</p>
                                    <p className="font-bold text-gray-900">{safetyStock} units</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* ROI Calcul

ation */}
                    {roi > 0 && (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-5">
                            <h3 className="font-bold text-lg text-green-900 mb-3 flex items-center gap-2">
                                <DollarSign className="w-5 h-5" />
                                💰 Return on Investment (ROI)
                            </h3>
                            <div className="space-y-2 text-sm text-gray-800">
                                <p className="font-mono bg-white p-3 rounded border border-green-100">
                                    ROI = Projected Value / Order Cost
                                </p>
                                <p className="font-mono bg-white p-3 rounded border border-green-100">
                                    = ${projectedValue.toLocaleString()} / ${totalCost.toLocaleString()} = <span className="font-bold text-green-700">{roi.toFixed(1)}x</span>
                                </p>
                                <p className="text-gray-600 mt-2">
                                    This order is expected to generate <span className="font-bold text-green-700">{((roi - 1) * 100).toFixed(0)}% return</span> on investment.
                                </p>
                                <div className="grid grid-cols-2 gap-3 mt-3">
                                    <div className="bg-white p-2 rounded">
                                        <p className="text-xs text-gray-500">Order Cost</p>
                                        <p className="font-bold text-gray-900">${totalCost.toLocaleString()}</p>
                                    </div>
                                    <div className="bg-white p-2 rounded">
                                        <p className="text-xs text-gray-500">Projected Value</p>
                                        <p className="font-bold text-green-600">${projectedValue.toLocaleString()}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Stockout Risk */}
                    <div className={`border rounded-lg p-5 ${isStockoutCritical ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'}`}>
                        <h3 className={`font-bold text-lg mb-3 flex items-center gap-2 ${isStockoutCritical ? 'text-red-900' : 'text-gray-900'}`}>
                            <AlertTriangle className="w-5 h-5" />
                            ⚠️ Stockout Risk
                        </h3>
                        <div className="space-y-2 text-sm text-gray-800">
                            <p className="font-mono bg-white p-3 rounded border">
                                Days Until Stockout = Current Stock / Daily Demand
                            </p>
                            <p className="font-mono bg-white p-3 rounded border">
                                = {currentStock} / {dailyDemand.toFixed(1)} = <span className={`font-bold ${isStockoutCritical ? 'text-red-700' : 'text-green-700'}`}>{daysUntilStockout.toFixed(1)} days</span>
                            </p>
                            <div className={`mt-3 p-3 rounded ${isStockoutCritical ? 'bg-red-100 border border-red-300' : 'bg-green-100 border border-green-300'}`}>
                                <p className={`font-bold ${isStockoutCritical ? 'text-red-900' : 'text-green-900'}`}>
                                    {isStockoutCritical ? `🚨 CRITICAL: Stockout before next delivery!` : `✅ Safe: Sufficient stock until delivery`}
                                </p>
                                <p className={`text-xs mt-1 ${isStockoutCritical ? 'text-red-700' : 'text-green-700'}`}>
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
                        <div className="bg-purple-50 border border-purple-200 rounded-lg p-5">
                            <h3 className="font-bold text-lg text-purple-900 mb-3">
                                💭 Agent Reasoning
                            </h3>
                            <p className="text-sm text-gray-800 whitespace-pre-wrap">{decision.reasoning}</p>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 p-4 rounded-b-lg">
                    <button
                        onClick={onClose}
                        className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold py-3 px-6 rounded-lg hover:shadow-lg transition"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div >
    );
}
