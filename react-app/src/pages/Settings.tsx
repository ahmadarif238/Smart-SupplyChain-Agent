import { useState, useEffect } from 'react';
import Card from '../components/ui/Card';
import { DollarSign, Save } from 'lucide-react';
import { apiService } from '../api';

export default function Settings() {
    const [budget, setBudget] = useState(10000);
    const [loading, setLoading] = useState(false);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        // In a real app, fetch current settings
        // For now, we'll just default to 10000 or try to fetch if an endpoint existed
    }, []);

    const handleSave = async () => {
        setLoading(true);
        try {
            // We will implement this backend endpoint next
            await apiService.post('/agent/settings/budget', { budget });
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } catch (error) {
            console.error("Failed to save settings", error);
            alert("Failed to save settings (Backend endpoint might be missing)");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-white">Agent Settings</h1>
                <p className="text-slate-400">Configure how your autonomous agent operates.</p>
            </div>

            <Card>
                <div className="p-6 space-y-6">
                    <div className="flex items-center gap-4 border-b border-ink-700 pb-4">
                        <div className="p-3 bg-emerald-500/10 rounded-none">
                            <DollarSign className="w-6 h-6 text-emerald-400" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-white">Operating Budget</h3>
                            <p className="text-sm text-slate-400">Maximum amount the agent can spend per approval cycle.</p>
                        </div>
                    </div>

                    <div className="grid gap-4">
                        <label className="block text-sm font-medium text-slate-300">
                            Weekly Budget Limit (USD)
                        </label>
                        <input
                            type="number"
                            value={budget}
                            onChange={(e) => setBudget(Number(e.target.value))}
                            className="w-full max-w-xs px-4 py-2 border border-ink-700 rounded-none focus:ring-2 focus:ring-accent focus:border-accent"
                        />
                        <p className="text-xs text-slate-500">
                            * The agent will check this budget before drafting any orders.
                        </p>
                    </div>

                    <div className="pt-4 flex items-center gap-4">
                        <button
                            onClick={handleSave}
                            disabled={loading}
                            className="flex items-center gap-2 px-6 py-2.5 bg-accent text-white font-medium rounded-none hover:bg-accent-hover transition-colors disabled:opacity-50"
                        >
                            <Save className="w-4 h-4" />
                            {loading ? 'Saving...' : 'Save Configuration'}
                        </button>
                        {saved && <span className="text-emerald-400 font-medium animate-fade-in">Settings saved successfully!</span>}
                    </div>
                </div>
            </Card>
        </div>
    );
}
