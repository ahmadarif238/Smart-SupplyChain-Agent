import { useState } from 'react';
import { X, Calculator, TrendingUp, Shield, Lightbulb, DollarSign } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface DecisionExplainerProps {
    decision: any;
    onClose: () => void;
}

export default function DecisionExplainer({ decision, onClose }: DecisionExplainerProps) {
    // Extract decision details
    const details = decision.details || {};
    const costAnalysis = decision.cost_analysis || {};

    // Initial values from decision
    const [orderQty, setOrderQty] = useState(decision.order_quantity || 100);
    const [leadTime, setLeadTime] = useState(details.lead_time || 7);
    const [serviceLevel, setServiceLevel] = useState(0.95);
    const [demandRate, setDemandRate] = useState(details.avg_demand || 10);

    // Get unit cost
    const unitCost = costAnalysis.purchasing_cost_per_unit || details.unit_price || 10;
    const holdingCostRate = 0.25; // 25% per year
    const orderingCost = 50; // Fixed ordering cost

    // Calculate EOQ
    const calculateEOQ = () => {
        const annualDemand = demandRate * 365;
        const eoq = Math.sqrt((2 * annualDemand * orderingCost) / (unitCost * holdingCostRate));
        return Math.round(eoq);
    };

    // Calculate Safety Stock
    const calculateSafetyStock = () => {
        const zScore = serviceLevel >= 0.99 ? 2.33 : serviceLevel >= 0.95 ? 1.65 : 1.28;
        const demandStdDev = demandRate * 0.3; // Assume 30% variability
        const safetyStock = zScore * demandStdDev * Math.sqrt(leadTime);
        return Math.round(safetyStock);
    };

    // Calculate costs
    const calculateCosts = (qty: number) => {
        const annualDemand = demandRate * 365;
        const numberOfOrders = annualDemand / qty;
        const avgInventory = qty / 2;

        const orderingCosts = numberOfOrders * orderingCost;
        const holdingCosts = avgInventory * unitCost * holdingCostRate;
        const totalCost = orderingCosts + holdingCosts;

        return {
            ordering: orderingCosts,
            holding: holdingCosts,
            total: totalCost,
            numberOfOrders: numberOfOrders
        };
    };

    // Calculate ROI
    const calculateROI = () => {
        const revenue = orderQty * unitCost * 1.4; // Assume 40% markup
        const cost = orderQty * unitCost;
        const stockoutCost = details.stockout_cost || 100;
        const roi = (revenue - cost - stockoutCost) / cost;
        return roi;
    };

    const eoq = calculateEOQ();
    const safetyStock = calculateSafetyStock();
    const costs = calculateCosts(orderQty);
    const eoqCosts = calculateCosts(eoq);
    const roi = calculateROI();

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                onClick={onClose}
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-auto"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className="sticky top-0 bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6 flex items-center justify-between rounded-t-2xl">
                        <div className="flex items-center gap-3">
                            <Calculator className="w-6 h-6" />
                            <div>
                                <h2 className="text-2xl font-bold">Decision Explainer</h2>
                                <p className="text-indigo-100 text-sm">Interactive "What-If" Analysis for {decision.sku}</p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </div>

                    <div className="p-6 space-y-6">
                        {/* Interactive Parameters */}
                        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-indigo-200">
                            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                                <Lightbulb className="w-5 h-5 text-indigo-600" />
                                Adjust Parameters - See Impact in Real-Time
                            </h3>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Order Quantity Slider */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Order Quantity: <span className="text-indigo-600 font-bold">{orderQty}</span> units
                                    </label>
                                    <input
                                        type="range"
                                        min="10"
                                        max="500"
                                        value={orderQty}
                                        onChange={(e) => setOrderQty(Number(e.target.value))}
                                        className="w-full h-2 bg-indigo-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                                    />
                                    <div className="flex justify-between text-xs text-slate-500 mt-1">
                                        <span>10</span>
                                        <span>EOQ: {eoq}</span>
                                        <span>500</span>
                                    </div>
                                </div>

                                {/* Lead Time Slider */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Lead Time: <span className="text-indigo-600 font-bold">{leadTime}</span> days
                                    </label>
                                    <input
                                        type="range"
                                        min="1"
                                        max="30"
                                        value={leadTime}
                                        onChange={(e) => setLeadTime(Number(e.target.value))}
                                        className="w-full h-2 bg-indigo-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                                    />
                                    <div className="flex justify-between text-xs text-slate-500 mt-1">
                                        <span>1 day</span>
                                        <span>30 days</span>
                                    </div>
                                </div>

                                {/* Service Level Slider */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Service Level: <span className="text-indigo-600 font-bold">{(serviceLevel * 100).toFixed(0)}%</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0.85"
                                        max="0.99"
                                        step="0.01"
                                        value={serviceLevel}
                                        onChange={(e) => setServiceLevel(Number(e.target.value))}
                                        className="w-full h-2 bg-indigo-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                                    />
                                    <div className="flex justify-between text-xs text-slate-500 mt-1">
                                        <span>85%</span>
                                        <span>99%</span>
                                    </div>
                                </div>

                                {/* Demand Rate Slider */}
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        Daily Demand: <span className="text-indigo-600 font-bold">{demandRate}</span> units/day
                                    </label>
                                    <input
                                        type="range"
                                        min="1"
                                        max="50"
                                        value={demandRate}
                                        onChange={(e) => setDemandRate(Number(e.target.value))}
                                        className="w-full h-2 bg-indigo-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                                    />
                                    <div className="flex justify-between text-xs text-slate-500 mt-1">
                                        <span>1</span>
                                        <span>50</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* EOQ Calculation Breakdown */}
                        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
                            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                                <Calculator className="w-5 h-5 text-green-600" />
                                Economic Order Quantity (EOQ) Calculation
                            </h3>

                            <div className="bg-slate-50 rounded-lg p-4 mb-4 font-mono text-sm">
                                <div className="text-center mb-2 text-slate-600">Formula:</div>
                                <div className="text-center text-lg font-bold text-slate-900">
                                    EOQ = √((2 × D × S) / (H × C))
                                </div>
                                <div className="grid grid-cols-2 gap-2 mt-4 text-xs text-slate-600">
                                    <div>D = Annual Demand = {demandRate * 365}</div>
                                    <div>S = Ordering Cost = ${orderingCost}</div>
                                    <div>C = Unit Cost = ${unitCost}</div>
                                    <div>H = Holding Cost Rate = {holdingCostRate * 100}%</div>
                                </div>
                            </div>

                            <div className="grid grid-cols-3 gap-4">
                                <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                                    <p className="text-sm text-green-700 font-medium">Calculated EOQ</p>
                                    <p className="text-3xl font-bold text-green-600">{eoq}</p>
                                    <p className="text-xs text-green-600 mt-1">units per order</p>
                                </div>
                                <div className={`rounded-lg p-4 border ${orderQty === eoq ? 'bg-green-50 border-green-200' :
                                    Math.abs(orderQty - eoq) < 20 ? 'bg-yellow-50 border-yellow-200' :
                                        'bg-red-50 border-red-200'
                                    }`}>
                                    <p className="text-sm font-medium">Current Order</p>
                                    <p className="text-3xl font-bold">{orderQty}</p>
                                    <p className="text-xs mt-1">
                                        {orderQty === eoq ? '✓ Optimal' :
                                            Math.abs(orderQty - eoq) < 20 ? '~ Close to optimal' :
                                                orderQty > eoq ? '⚠️ Overordering' : '⚠️ Underordering'}
                                    </p>
                                </div>
                                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                                    <p className="text-sm text-blue-700 font-medium">Cost Difference</p>
                                    <p className="text-3xl font-bold text-blue-600">
                                        ${Math.abs(costs.total - eoqCosts.total).toFixed(0)}
                                    </p>
                                    <p className="text-xs text-blue-600 mt-1">vs EOQ annually</p>
                                </div>
                            </div>
                        </div>

                        {/* Cost Breakdown */}
                        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
                            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                                <DollarSign className="w-5 h-5 text-purple-600" />
                                Annual Cost Analysis
                            </h3>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                                <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                                    <p className="text-sm text-orange-700 font-medium">Ordering Costs</p>
                                    <p className="text-2xl font-bold text-orange-600">${costs.ordering.toFixed(0)}</p>
                                    <p className="text-xs text-orange-600 mt-1">{costs.numberOfOrders.toFixed(1)} orders/year</p>
                                </div>
                                <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                                    <p className="text-sm text-purple-700 font-medium">Holding Costs</p>
                                    <p className="text-2xl font-bold text-purple-600">${costs.holding.toFixed(0)}</p>
                                    <p className="text-xs text-purple-600 mt-1">Avg inventory: {(orderQty / 2).toFixed(0)} units</p>
                                </div>
                                <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
                                    <p className="text-sm text-indigo-700 font-medium">Total Annual Cost</p>
                                    <p className="text-2xl font-bold text-indigo-600">${costs.total.toFixed(0)}</p>
                                    <p className="text-xs text-indigo-600 mt-1">Ordering + Holding</p>
                                </div>
                            </div>

                            {/* Visual Cost Comparison */}
                            <div className="bg-slate-50 rounded-lg p-4">
                                <p className="text-sm font-medium text-slate-700 mb-3">Cost Breakdown:</p>
                                <div className="flex gap-2 h-8 rounded-lg overflow-hidden">
                                    <div
                                        className="bg-orange-500 flex items-center justify-center text-white text-xs font-bold"
                                        style={{ width: `${(costs.ordering / costs.total) * 100}%` }}
                                    >
                                        {((costs.ordering / costs.total) * 100).toFixed(0)}%
                                    </div>
                                    <div
                                        className="bg-purple-500 flex items-center justify-center text-white text-xs font-bold"
                                        style={{ width: `${(costs.holding / costs.total) * 100}%` }}
                                    >
                                        {((costs.holding / costs.total) * 100).toFixed(0)}%
                                    </div>
                                </div>
                                <div className="flex justify-between text-xs text-slate-600 mt-2">
                                    <span>🟠 Ordering</span>
                                    <span>🟣 Holding</span>
                                </div>
                            </div>
                        </div>

                        {/* Safety Stock Justification */}
                        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
                            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                                <Shield className="w-5 h-5 text-blue-600" />
                                Safety Stock Calculation
                            </h3>

                            <div className="bg-blue-50 rounded-lg p-4 mb-4">
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                                    <div>
                                        <p className="text-xs text-blue-700">Service Level</p>
                                        <p className="text-2xl font-bold text-blue-600">{(serviceLevel * 100).toFixed(0)}%</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-blue-700">Z-Score</p>
                                        <p className="text-2xl font-bold text-blue-600">
                                            {serviceLevel >= 0.99 ? '2.33' : serviceLevel >= 0.95 ? '1.65' : '1.28'}
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-blue-700">Lead Time</p>
                                        <p className="text-2xl font-bold text-blue-600">{leadTime}d</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-blue-700">Safety Stock</p>
                                        <p className="text-2xl font-bold text-blue-600">{safetyStock}</p>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-slate-50 rounded-lg p-4">
                                <p className="text-sm text-slate-700 mb-2">
                                    <strong>Why {safetyStock} units?</strong>
                                </p>
                                <p className="text-sm text-slate-600">
                                    Based on a {(serviceLevel * 100).toFixed(0)}% service level, we need {safetyStock} units
                                    as buffer stock to cover demand variability during the {leadTime}-day lead time.
                                    This ensures stockouts occur less than {((1 - serviceLevel) * 100).toFixed(1)}% of the time.
                                </p>
                            </div>
                        </div>

                        {/* ROI Analysis */}
                        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
                            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                                <TrendingUp className="w-5 h-5 text-green-600" />
                                Return on Investment (ROI)
                            </h3>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div>
                                    <p className="text-sm text-green-700">Order Cost</p>
                                    <p className="text-xl font-bold text-green-900">${(orderQty * unitCost).toFixed(0)}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-green-700">Expected Revenue</p>
                                    <p className="text-xl font-bold text-green-900">${(orderQty * unitCost * 1.4).toFixed(0)}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-green-700">Profit</p>
                                    <p className="text-xl font-bold text-green-900">${(orderQty * unitCost * 0.4).toFixed(0)}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-green-700">ROI</p>
                                    <p className={`text-xl font-bold ${roi > 0.3 ? 'text-green-600' : 'text-orange-600'}`}>
                                        {(roi * 100).toFixed(1)}%
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Recommendation */}
                        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6 border border-indigo-200">
                            <h3 className="text-lg font-bold text-slate-900 mb-3">💡 Recommendation</h3>
                            <p className="text-slate-700 leading-relaxed">
                                {orderQty === eoq ? (
                                    <span className="text-green-600 font-medium">✓ Your current order quantity matches the EOQ! This is optimal for minimizing total costs.</span>
                                ) : orderQty < eoq ? (
                                    <span className="text-orange-600">Consider increasing order quantity to {eoq} units (EOQ) to reduce ordering frequency and lower total annual costs by ${(costs.total - eoqCosts.total).toFixed(0)}.</span>
                                ) : (
                                    <span className="text-orange-600">Consider reducing order quantity to {eoq} units (EOQ) to minimize holding costs and lower total annual costs by ${(costs.total - eoqCosts.total).toFixed(0)}.</span>
                                )}
                            </p>
                        </div>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
