import { useState } from 'react';
import { X, Cpu, BarChart3, ShoppingCart, Settings, ArrowRight, CheckCircle2 } from 'lucide-react';

interface OnboardingModalProps {
    onClose: () => void;
}

export default function OnboardingModal({ onClose }: OnboardingModalProps) {
    const [step, setStep] = useState(0);

    const steps = [
        {
            title: "Welcome to SupplyChain AI",
            description: "Your autonomous AI agent for smart inventory management. Let me show you how it works!",
            icon: <Cpu className="w-12 h-12 text-indigo-500" />,
            features: [
                "LLM-powered demand forecasting",
                "Automatic reorder recommendations",
                "Budget-aware decision making",
                "Human-in-the-loop approval"
            ]
        },
        {
            title: "1. Run the Agent",
            description: "Click 'Run New Analysis' on the Dashboard to start the AI agent. It will:",
            icon: <BarChart3 className="w-12 h-12 text-green-500" />,
            features: [
                "Sync with your inventory data",
                "Analyze market trends using AI",
                "Identify items that need restocking",
                "Draft purchase orders for your approval"
            ]
        },
        {
            title: "2. Review & Approve Orders",
            description: "The agent drafts orders but YOU make the final decision:",
            icon: <ShoppingCart className="w-12 h-12 text-orange-500" />,
            features: [
                "See the 'Action Required' section on Dashboard",
                "Review agent's reasoning for each order",
                "Click 'Approve' or 'Reject' for each item",
                "Budget updates automatically after approval"
            ]
        },
        {
            title: "3. Configure Your Budget",
            description: "Control how much the agent can spend:",
            icon: <Settings className="w-12 h-12 text-purple-500" />,
            features: [
                "Go to Settings page",
                "Set your weekly budget limit",
                "The agent respects your budget constraints",
                "See remaining budget on the Dashboard"
            ]
        }
    ];

    const isLastStep = step === steps.length - 1;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden animate-fade-in">
                {/* Header */}
                <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 text-white relative">
                    <button
                        onClick={onClose}
                        className="absolute top-4 right-4 p-1 hover:bg-white/20 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                    <div className="flex items-center gap-4">
                        {steps[step].icon}
                        <div>
                            <h2 className="text-xl font-bold">{steps[step].title}</h2>
                            <p className="text-indigo-100 text-sm mt-1">{steps[step].description}</p>
                        </div>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6">
                    <ul className="space-y-3">
                        {steps[step].features.map((feature, idx) => (
                            <li key={idx} className="flex items-start gap-3">
                                <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                                <span className="text-slate-700">{feature}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Footer */}
                <div className="px-6 pb-6 flex items-center justify-between">
                    {/* Step indicators */}
                    <div className="flex gap-2">
                        {steps.map((_, idx) => (
                            <button
                                key={idx}
                                onClick={() => setStep(idx)}
                                className={`w-2 h-2 rounded-full transition-colors ${idx === step ? 'bg-indigo-600' : 'bg-slate-300 hover:bg-slate-400'
                                    }`}
                            />
                        ))}
                    </div>

                    {/* Navigation buttons */}
                    <div className="flex gap-3">
                        {step > 0 && (
                            <button
                                onClick={() => setStep(step - 1)}
                                className="px-4 py-2 text-slate-600 hover:text-slate-800 font-medium"
                            >
                                Back
                            </button>
                        )}
                        <button
                            onClick={() => isLastStep ? onClose() : setStep(step + 1)}
                            className="flex items-center gap-2 px-5 py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors"
                        >
                            {isLastStep ? "Get Started" : "Next"}
                            <ArrowRight className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
