
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
        if (isRejection) return 'bg-red-50 border-red-200 text-red-800';
        if (isCounter) return 'bg-orange-50 border-orange-200 text-orange-800';
        if (isApproval) return 'bg-green-50 border-green-200 text-green-800';
        return 'bg-gray-50 border-gray-200 text-gray-800';
    };

    const getIcon = () => {
        if (isRejection) return <AlertCircle className="w-5 h-5 text-red-600" />;
        if (isCounter) return <MessageSquare className="w-5 h-5 text-orange-600" />;
        if (isApproval) return <CheckCircle className="w-5 h-5 text-green-600" />;
        return <MessageSquare className="w-5 h-5 text-gray-600" />;
    };

    const getAgentColor = (agent: string) => {
        switch (agent) {
            case 'Finance': return 'bg-yellow-100 text-yellow-800';
            case 'Decision': return 'bg-blue-100 text-blue-800';
            case 'Action': return 'bg-green-100 text-green-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className={`rounded-lg border p-4 mb-4 shadow-sm animate-fade-in ${getStyles()}`}>
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
                                <ArrowRight className="w-3 h-3 text-gray-400" />
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
