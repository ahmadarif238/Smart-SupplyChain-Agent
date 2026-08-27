
import { MessageSquare, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';

interface AgentDialogueProps {
    dialogue: {
        agent: string;
        target?: string;
        message: string;
        type: 'rejection' | 'counter_argument' | 'override_approval' | 'info';
        sku?: string;
        timestamp?: string;
    };
}

export default function AgentDialogue({ dialogue }: AgentDialogueProps) {
    const isRejection = dialogue.type === 'rejection';
    const isCounter = dialogue.type === 'counter_argument';
    const isApproval = dialogue.type === 'override_approval';

    const getStyles = () => {
        if (isRejection) return 'bg-red-500/10 border-red-500/30 text-red-300';
        if (isCounter) return 'bg-orange-500/10 border-orange-500/30 text-orange-300';
        if (isApproval) return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300';
        return 'bg-ink-900 border-ink-700 text-white';
    };

    const getIcon = () => {
        if (isRejection) return <AlertCircle className="w-5 h-5 text-red-400" />;
        if (isCounter) return <MessageSquare className="w-5 h-5 text-orange-400" />;
        if (isApproval) return <CheckCircle className="w-5 h-5 text-emerald-400" />;
        return <MessageSquare className="w-5 h-5 text-slate-400" />;
    };

    const getAgentColor = (agent: string) => {
        switch (agent) {
            case 'Finance': return 'bg-amber-500/15 text-amber-300';
            case 'Decision': return 'bg-accent/10 text-accent';
            case 'Action': return 'bg-emerald-500/15 text-emerald-300';
            default: return 'bg-ink-900 text-white';
        }
    };

    return (
        <div className={`rounded-none border p-4 mb-4 shadow-sm animate-fade-in ${getStyles()}`}>
            <div className="flex items-start gap-3">
                <div className="mt-1 flex-shrink-0">
                    {getIcon()}
                </div>
                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${getAgentColor(dialogue.agent)}`}>
                            {dialogue.agent}
                        </span>

                        {dialogue.target && (
                            <>
                                <ArrowRight className="w-3 h-3 text-slate-500" />
                                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${getAgentColor(dialogue.target)}`}>
                                    {dialogue.target}
                                </span>
                            </>
                        )}

                        <span className="text-xs font-medium opacity-60 ml-auto">
                            {dialogue.type.replace('_', ' ').toUpperCase()}
                        </span>
                    </div>

                    <p className="text-sm leading-relaxed font-medium">
                        {dialogue.message}
                    </p>

                    {dialogue.sku && (
                        <div className="mt-2 text-xs opacity-75 font-mono bg-black/5 inline-block px-2 py-1 rounded">
                            Ref: {dialogue.sku}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
