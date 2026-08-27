import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, TrendingUp, DollarSign, ArrowRight, CheckCircle, XCircle, RefreshCw } from 'lucide-react';

interface NegotiationRound {
    round: number;
    rejectedItems: Array<{
        sku: string;
        productName: string;
        originalQty: number;
        originalCost: number;
        rejectionReason: string;
    }>;
    counterArguments: Array<{
        sku: string;
        strategy: string;
        argument: string;
        proposal: string;
    }>;
    reductions: Array<{
        sku: string;
        fromQty: number;
        toQty: number;
        fromCost: number;
        toCost: number;
    }>;
    budgetReallocations: Array<{
        targetSku: string;
        beneficiarySku: string;
        reducedBy: number;
    }>;
    outcome: 'approved' | 'rejected' | 'pending';
}

interface NegotiationVisualizerProps {
    cycleId: string;
}

export default function NegotiationVisualizer({ cycleId }: NegotiationVisualizerProps) {
    const [rounds, setRounds] = useState<NegotiationRound[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedRound, setExpandedRound] = useState<number | null>(null);

    useEffect(() => {
        // Poll for negotiation events
        const fetchNegotiationData = async () => {
            try {
                // This would come from your streaming events or a dedicated endpoint
                // For now, we'll parse from the dialogue events
                const response = await fetch(`http://127.0.0.1:8000/agent/job/${cycleId}`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    // Parse negotiation rounds from events
                    parseNegotiationRounds(data);
                }
            } catch (error) {
                console.error('Error fetching negotiation data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchNegotiationData();
        const interval = setInterval(fetchNegotiationData, 5000);
        return () => clearInterval(interval);
    }, [cycleId]);

    const parseNegotiationRounds = (_data: any) => {
        // TODO: Parse actual negotiation events from backend
        // This is a placeholder - you'll need to adapt to your actual data structure
        const mockRounds: NegotiationRound[] = [
            {
                round: 1,
                rejectedItems: [
                    {
                        sku: 'CHAI',
                        productName: 'Chai',
                        originalQty: 95,
                        originalCost: 19000,
                        rejectionReason: 'Budget exceeded by $15,000'
                    }
                ],
                counterArguments: [
                    {
                        sku: 'CHAI',
                        strategy: 'Budget Reallocation',
                        argument: 'Stock critically low, 45 units below reorder point',
                        proposal: 'Reduce other orders to free up $10,000'
                    }
                ],
                reductions: [
                    {
                        sku: 'CHAI',
                        fromQty: 95,
                        toQty: 48,
                        fromCost: 19000,
                        toCost: 9600
                    }
                ],
                budgetReallocations: [],
                outcome: 'rejected'
            }
        ];
        setRounds(mockRounds);
    };

    if (loading) {
        return (
            <div className="bg-ink-800 rounded-none shadow-lg p-6 border-l-4 border-accent">
                <div className="flex items-center gap-2 mb-4">
                    <RefreshCw className="w-5 h-5 text-accent animate-spin" />
                    <h3 className="text-xl font-bold text-white">Loading Negotiation Data...</h3>
                </div>
            </div>
        );
    }

    if (rounds.length === 0) {
        return (
            <div className="bg-ink-800 rounded-none shadow-lg p-6 border-l-4 border-ink-700">
                <div className="text-center py-8">
                    <MessageSquare className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                    <p className="text-slate-400">No negotiations occurred in this cycle</p>
                    <p className="text-sm text-slate-500 mt-1">All orders were approved without negotiation</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-ink-800 rounded-none shadow-lg p-6 border-l-4 border-accent mb-8">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                <MessageSquare className="w-6 h-6 text-accent" />
                Agent Negotiation Rounds
            </h2>

            <div className="space-y-4">
                {rounds.map((round, index) => (
                    <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="border border-ink-700 rounded-none overflow-hidden"
                    >
                        {/* Round Header */}
                        <button
                            onClick={() => setExpandedRound(expandedRound === index ? null : index)}
                            className="w-full px-4 py-3 bg-gradient-to-r from-accent/10 to-accent/5 hover:from-accent/20 hover:to-accent/10 transition-colors flex items-center justify-between"
                        >
                            <div className="flex items-center gap-3">
                                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-accent text-white font-bold text-sm">
                                    {round.round}
                                </div>
                                <div className="text-left">
                                    <p className="font-semibold text-white">Round {round.round}</p>
                                    <p className="text-sm text-slate-400">
                                        {round.rejectedItems.length} item{round.rejectedItems.length !== 1 ? 's' : ''} negotiated
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                {round.outcome === 'approved' ? (
                                    <span className="flex items-center gap-1 px-3 py-1 bg-emerald-500/15 text-emerald-400 rounded-full text-sm font-medium">
                                        <CheckCircle className="w-4 h-4" />
                                        Approved
                                    </span>
                                ) : round.outcome === 'rejected' ? (
                                    <span className="flex items-center gap-1 px-3 py-1 bg-red-500/15 text-red-400 rounded-full text-sm font-medium">
                                        <XCircle className="w-4 h-4" />
                                        Rejected
                                    </span>
                                ) : (
                                    <span className="flex items-center gap-1 px-3 py-1 bg-accent/10 text-accent rounded-full text-sm font-medium">
                                        <RefreshCw className="w-4 h-4" />
                                        Pending
                                    </span>
                                )}
                                <ArrowRight className={`w-5 h-5 text-slate-500 transition-transform ${expandedRound === index ? 'rotate-90' : ''}`} />
                            </div>
                        </button>

                        {/* Round Details */}
                        <AnimatePresence>
                            {expandedRound === index && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    transition={{ duration: 0.3 }}
                                    className="overflow-hidden"
                                >
                                    <div className="p-4 space-y-4">
                                        {/* Rejected Items */}
                                        {round.rejectedItems.map((item, idx) => (
                                            <div key={idx} className="bg-red-500/10 border border-red-500/30 rounded-none p-4">
                                                <div className="flex items-start justify-between mb-2">
                                                    <div>
                                                        <p className="font-semibold text-white">{item.productName}</p>
                                                        <p className="text-sm text-slate-400">SKU: {item.sku}</p>
                                                    </div>
                                                    <div className="text-right">
                                                        <p className="text-lg font-bold text-red-400">${item.originalCost.toLocaleString()}</p>
                                                        <p className="text-sm text-slate-400">{item.originalQty} units</p>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/15 px-3 py-2 rounded">
                                                    <XCircle className="w-4 h-4" />
                                                    <span>{item.rejectionReason}</span>
                                                </div>
                                            </div>
                                        ))}

                                        {/* Counter Arguments */}
                                        {round.counterArguments.map((arg, idx) => (
                                            <div key={idx} className="bg-accent/10 border border-accent/40 rounded-none p-4">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <TrendingUp className="w-5 h-5 text-accent" />
                                                    <p className="font-semibold text-accent">Strategy: {arg.strategy}</p>
                                                </div>
                                                <p className="text-sm text-slate-300 mb-2">{arg.argument}</p>
                                                <div className="bg-accent/10 px-3 py-2 rounded text-sm text-accent">
                                                    <strong>Proposal:</strong> {arg.proposal}
                                                </div>
                                            </div>
                                        ))}

                                        {/* Quantity Reductions */}
                                        {round.reductions.length > 0 && (
                                            <div className="bg-amber-500/10 border border-amber-500/30 rounded-none p-4">
                                                <p className="font-semibold text-amber-300 mb-3 flex items-center gap-2">
                                                    <DollarSign className="w-5 h-5" />
                                                    Quantity Adjustments
                                                </p>
                                                {round.reductions.map((reduction, idx) => (
                                                    <div key={idx} className="flex items-center justify-between text-sm">
                                                        <span className="text-slate-300">{reduction.sku}:</span>
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-slate-400">{reduction.fromQty} units (${reduction.fromCost.toLocaleString()})</span>
                                                            <ArrowRight className="w-4 h-4 text-slate-500" />
                                                            <span className="font-semibold text-emerald-400">{reduction.toQty} units (${reduction.toCost.toLocaleString()})</span>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}

                                        {/* Budget Reallocations */}
                                        {round.budgetReallocations.length > 0 && (
                                            <div className="bg-accent/10 border border-accent/40 rounded-none p-4">
                                                <p className="font-semibold text-accent mb-3">Budget Reallocations</p>
                                                {round.budgetReallocations.map((realloc, idx) => (
                                                    <div key={idx} className="text-sm text-slate-300">
                                                        Reduced <strong>{realloc.targetSku}</strong> by {realloc.reducedBy}% to fund <strong>{realloc.beneficiarySku}</strong>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                ))}
            </div>
        </div>
    );
}
