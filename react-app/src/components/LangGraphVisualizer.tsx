import React from 'react';
import { CheckCircle, Clock, AlertCircle, Database, TrendingUp, Brain, DollarSign, ShoppingCart, BookOpen, MessageSquare } from 'lucide-react';

interface LangGraphVisualizerProps {
    currentStage?: string;
    completedStages: string[];
    errorStage?: string;
    activeInteraction?: {
        from: string;
        to: string;
        type: 'rejection' | 'counter_argument' | 'override_approval';
    } | null;
}

interface WorkflowNode {
    id: string;
    label: string;
    icon: React.ComponentType<any>;
    stage: string;
}

const WORKFLOW_NODES: WorkflowNode[] = [
    { id: 'fetch', label: 'Fetch Data', icon: Database, stage: 'FETCH' },
    { id: 'forecast', label: 'Forecast', icon: TrendingUp, stage: 'FORECAST' },
    { id: 'decision', label: 'Decision', icon: Brain, stage: 'DECISION' },
    { id: 'finance', label: 'Finance', icon: DollarSign, stage: 'FINANCE' },
    { id: 'action', label: 'Action', icon: ShoppingCart, stage: 'ACTION' },
    { id: 'memory', label: 'Memory', icon: BookOpen, stage: 'MEMORY' },
];

export default function LangGraphVisualizer({ currentStage, completedStages, errorStage, activeInteraction }: LangGraphVisualizerProps) {
    const getNodeState = (node: WorkflowNode): 'pending' | 'active' | 'complete' | 'error' | 'interacting' => {
        if (errorStage === node.stage) return 'error';

        // Check if this node is part of an active interaction
        if (activeInteraction) {
            const isSource = node.label.toLowerCase() === activeInteraction.from.toLowerCase();
            const isTarget = node.label.toLowerCase() === activeInteraction.to.toLowerCase();
            if (isSource || isTarget) return 'interacting';
        }

        if (completedStages.includes(node.stage)) return 'complete';
        if (currentStage === node.stage) return 'active';
        return 'pending';
    };

    const getNodeStyles = (state: string, interactionType?: string) => {
        switch (state) {
            case 'interacting':
                let colorClass = 'border-accent bg-accent/10 text-accent';
                if (interactionType === 'rejection') colorClass = 'border-red-500 bg-red-500/10 text-red-300';
                if (interactionType === 'counter_argument') colorClass = 'border-orange-500 bg-orange-500/10 text-orange-300';
                if (interactionType === 'override_approval') colorClass = 'border-green-500 bg-emerald-500/10 text-emerald-300';

                return {
                    border: `${colorClass.split(' ')[0]} border-2`,
                    bg: colorClass.split(' ')[1],
                    text: colorClass.split(' ')[2],
                    icon: colorClass.split(' ')[2].replace('900', '600'),
                    pulse: 'animate-pulse ring-2 ring-offset-2 ring-opacity-50',
                };
            case 'active':
                return {
                    border: 'border-accent border-2',
                    bg: 'bg-accent/10',
                    text: 'text-accent',
                    icon: 'text-accent',
                    pulse: 'animate-pulse',
                };
            case 'complete':
                return {
                    border: 'border-green-500 border-2',
                    bg: 'bg-emerald-500/10',
                    text: 'text-emerald-300',
                    icon: 'text-emerald-400',
                    pulse: '',
                };
            case 'error':
                return {
                    border: 'border-red-500 border-2',
                    bg: 'bg-red-500/10',
                    text: 'text-red-300',
                    icon: 'text-red-400',
                    pulse: '',
                };
            default:
                return {
                    border: 'border-ink-700',
                    bg: 'bg-ink-900',
                    text: 'text-slate-400',
                    icon: 'text-slate-500',
                    pulse: '',
                };
        }
    };

    const getStateIcon = (state: string) => {
        switch (state) {
            case 'interacting':
                return <MessageSquare className="w-4 h-4 animate-bounce" />;
            case 'active':
                return <Clock className="w-4 h-4 text-accent animate-spin" />;
            case 'complete':
                return <CheckCircle className="w-4 h-4 text-emerald-400" />;
            case 'error':
                return <AlertCircle className="w-4 h-4 text-red-400" />;
            default:
                return <Clock className="w-4 h-4 text-slate-500" />;
        }
    };

    return (
        <div className="bg-ink-800 rounded-none shadow-lg p-6 mb-8">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">🔄 Agent Workflow</h2>
                {activeInteraction && (
                    <div className="flex items-center gap-2 px-3 py-1 bg-amber-500/15 text-amber-300 rounded-full text-xs font-bold animate-pulse">
                        <MessageSquare className="w-3 h-3" />
                        Negotiation in Progress: {activeInteraction.from} ↔ {activeInteraction.to}
                    </div>
                )}
            </div>

            <div className="relative">
                {/* Desktop View - Horizontal Flow */}
                <div className="hidden md:block">
                    <div className="flex items-center justify-between gap-2">
                        {WORKFLOW_NODES.map((node, index) => {
                            const state = getNodeState(node);
                            const styles = getNodeStyles(state, activeInteraction?.type);
                            const Icon = node.icon;

                            return (
                                <React.Fragment key={node.id}>
                                    {/* Node */}
                                    <div className="flex flex-col items-center flex-1 relative group">
                                        <div
                                            className={`${styles.border} ${styles.bg} ${styles.pulse} rounded-none p-4 w-full transition-all duration-300 hover:shadow-md z-10 relative`}
                                        >
                                            <div className="flex flex-col items-center gap-2">
                                                <Icon className={`w-8 h-8 ${styles.icon}`} />
                                                <span className={`text-sm font-semibold ${styles.text} text-center`}>
                                                    {node.label}
                                                </span>
                                                <div className="mt-1">
                                                    {getStateIcon(state)}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Interaction Message Bubble Animation */}
                                        {state === 'interacting' && activeInteraction && node.label.toLowerCase() === activeInteraction.from.toLowerCase() && (
                                            <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 animate-bounce z-20">
                                                <div className={`px-2 py-1 rounded text-xs font-bold text-white shadow-lg
                                                    ${activeInteraction.type === 'rejection' ? 'bg-red-500' :
                                                        activeInteraction.type === 'counter_argument' ? 'bg-orange-500' : 'bg-green-500'}`}>
                                                    {activeInteraction.type === 'rejection' ? 'REJECT' :
                                                        activeInteraction.type === 'counter_argument' ? 'COUNTER' : 'APPROVE'}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Arrow */}
                                    {index < WORKFLOW_NODES.length - 1 && (
                                        <div className="flex items-center relative">
                                            <svg className="w-6 h-6 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                            </svg>

                                            {/* Flying Packet Animation if interacting between these nodes */}
                                            {activeInteraction &&
                                                ((node.label.toLowerCase() === activeInteraction.from.toLowerCase() && WORKFLOW_NODES[index + 1].label.toLowerCase() === activeInteraction.to.toLowerCase()) ||
                                                    (node.label.toLowerCase() === activeInteraction.to.toLowerCase() && WORKFLOW_NODES[index + 1].label.toLowerCase() === activeInteraction.from.toLowerCase())) && (
                                                    <div className="absolute top-1/2 left-0 w-full h-1 bg-transparent overflow-hidden transform -translate-y-1/2">
                                                        <div className={`w-2 h-2 rounded-full absolute top-0 animate-ping
                                                        ${activeInteraction.type === 'rejection' ? 'bg-red-500' :
                                                                activeInteraction.type === 'counter_argument' ? 'bg-orange-500' : 'bg-green-500'}`}
                                                            style={{ animationDuration: '1s', left: '50%' }} />
                                                    </div>
                                                )}
                                        </div>
                                    )}
                                </React.Fragment>
                            );
                        })}
                    </div>
                </div>

                {/* Mobile View - Vertical Flow */}
                <div className="md:hidden space-y-3">
                    {WORKFLOW_NODES.map((node, index) => {
                        const state = getNodeState(node);
                        const styles = getNodeStyles(state, activeInteraction?.type);
                        const Icon = node.icon;

                        return (
                            <React.Fragment key={node.id}>
                                {/* Node */}
                                <div
                                    className={`${styles.border} ${styles.bg} ${styles.pulse} rounded-none p-4 transition-all duration-300`}
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <Icon className={`w-6 h-6 ${styles.icon}`} />
                                            <span className={`font-semibold ${styles.text}`}>
                                                {node.label}
                                            </span>
                                        </div>
                                        {getStateIcon(state)}
                                    </div>
                                </div>

                                {/* Arrow */}
                                {index < WORKFLOW_NODES.length - 1 && (
                                    <div className="flex justify-center">
                                        <svg className="w-6 h-6 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                        </svg>
                                    </div>
                                )}
                            </React.Fragment>
                        );
                    })}
                </div>
            </div>

            {/* Legend */}
            <div className="mt-6 pt-4 border-t border-ink-700">
                <div className="flex flex-wrap gap-4 text-sm">
                    <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-slate-500" />
                        <span className="text-slate-400">Pending</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-accent animate-spin" />
                        <span className="text-slate-400">Active</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 text-orange-400" />
                        <span className="text-slate-400">Negotiating</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                        <span className="text-slate-400">Complete</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
