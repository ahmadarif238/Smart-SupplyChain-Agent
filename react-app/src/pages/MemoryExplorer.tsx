import { useState, useEffect } from 'react';
import { Database, Clock, Tag, Search, BookMarked, Archive, Filter } from 'lucide-react';
import { apiService } from '../api';
import Card from '../components/ui/Card';

interface Fact {
    id: number;
    fact_type: string;
    subject: string;
    predicate: string;
    object: string;
    confidence: number;
    source: string;
    created_at: string;
}

interface Episode {
    id: number;
    event_id: string;
    event_type: string;
    sku: string;
    description: string;
    outcome: string;
    timestamp: string;
}

interface Checkpoint {
    id: number;
    checkpoint_id: string;
    cycle_number: number;
    goal: string;
    is_stable: boolean;
    created_at: string;
}

export default function MemoryExplorer() {
    const [activeTab, setActiveTab] = useState<'facts' | 'episodes' | 'checkpoints'>('facts');
    const [loading, setLoading] = useState(true);

    // Facts state
    const [facts, setFacts] = useState<Fact[]>([]);
    const [factCategory, setFactCategory] = useState<string>('all');
    const [factSearch, setFactSearch] = useState<string>('');

    // Episodes state
    const [episodes, setEpisodes] = useState<Episode[]>([]);
    const [episodeType, setEpisodeType] = useState<string>('all');

    // Checkpoints state
    const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);

    useEffect(() => {
        fetchMemoryData();
    }, [activeTab, factCategory, episodeType]);

    const fetchMemoryData = async () => {
        try {
            setLoading(true);

            if (activeTab === 'facts') {
                const res = await apiService.get(
                    factCategory === 'all'
                        ? '/facts/retrieve?limit=50'
                        : `/facts/by-category?category=${factCategory}&limit=50`
                );
                setFacts(res.data || []);
            } else if (activeTab === 'episodes') {
                const res = await apiService.get(
                    episodeType === 'all'
                        ? '/episodes/retrieve?limit=50'
                        : `/episodes/retrieve?event_type=${episodeType}&limit=50`
                );
                setEpisodes(res.data || []);
            } else {
                const res = await apiService.get('/checkpoints/history?limit=20');
                setCheckpoints(res.data || []);
            }
        } catch (error) {
            console.error('Error fetching memory data:', error);
        } finally {
            setLoading(false);
        }
    };

    const filteredFacts = facts.filter(fact =>
        factSearch === '' ||
        fact.subject.toLowerCase().includes(factSearch.toLowerCase()) ||
        fact.predicate.toLowerCase().includes(factSearch.toLowerCase()) ||
        fact.object.toLowerCase().includes(factSearch.toLowerCase())
    );

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                    <Database className="w-7 h-7 text-indigo-600" />
                    Agent Memory Explorer
                </h1>
                <p className="text-slate-500 mt-1">Browse semantic facts, episodic memories, and system checkpoints</p>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 border-b border-slate-200">
                <button
                    onClick={() => setActiveTab('facts')}
                    className={`px-6 py-3 font-medium transition-colors border-b-2 ${activeTab === 'facts'
                        ? 'border-indigo-600 text-indigo-600'
                        : 'border-transparent text-slate-600 hover:text-slate-900'
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <Tag className="w-4 h-4" />
                        Semantic Facts
                    </div>
                </button>
                <button
                    onClick={() => setActiveTab('episodes')}
                    className={`px-6 py-3 font-medium transition-colors border-b-2 ${activeTab === 'episodes'
                        ? 'border-indigo-600 text-indigo-600'
                        : 'border-transparent text-slate-600 hover:text-slate-900'
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <BookMarked className="w-4 h-4" />
                        Episodes
                    </div>
                </button>
                <button
                    onClick={() => setActiveTab('checkpoints')}
                    className={`px-6 py-3 font-medium transition-colors border-b-2 ${activeTab === 'checkpoints'
                        ? 'border-indigo-600 text-indigo-600'
                        : 'border-transparent text-slate-600 hover:text-slate-900'
                        }`}
                >
                    <div className="flex items-center gap-2">
                        <Archive className="w-4 h-4" />
                        Checkpoints
                    </div>
                </button>
            </div>

            {/* Facts Tab */}
            {activeTab === 'facts' && (
                <div className="space-y-6">
                    {/* Filters */}
                    <Card>
                        <div className="flex flex-col md:flex-row gap-4">
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                                <input
                                    type="text"
                                    placeholder="Search facts..."
                                    value={factSearch}
                                    onChange={(e) => setFactSearch(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                            </div>
                            <select
                                value={factCategory}
                                onChange={(e) => setFactCategory(e.target.value)}
                                className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                            >
                                <option value="all">All Categories</option>
                                <option value="inventory">Inventory</option>
                                <option value="demand">Demand</option>
                                <option value="supplier">Supplier</option>
                                <option value="performance">Performance</option>
                            </select>
                        </div>
                    </Card>

                    {/* Facts List */}
                    <Card title={`Semantic Facts (${filteredFacts.length})`}>
                        {loading ? (
                            <div className="text-center py-12">
                                <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                                <p className="text-slate-500">Loading facts...</p>
                            </div>
                        ) : filteredFacts.length > 0 ? (
                            <div className="space-y-3">
                                {filteredFacts.map((fact) => (
                                    <div key={fact.id} className="p-4 bg-slate-50 rounded-lg border border-slate-200 hover:border-indigo-300 transition-colors">
                                        <div className="flex items-start justify-between mb-2">
                                            <div className="flex-1">
                                                <p className="text-slate-900 font-medium">
                                                    <span className="text-indigo-600">{fact.subject}</span>
                                                    <span className="mx-2 text-slate-400">→</span>
                                                    <span className="text-slate-700">{fact.predicate}</span>
                                                    <span className="mx-2 text-slate-400">→</span>
                                                    <span className="text-green-600">{fact.object}</span>
                                                </p>
                                                <p className="text-sm text-slate-500 mt-1">Source: {fact.source}</p>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${fact.confidence >= 0.8 ? 'bg-green-100 text-green-700' :
                                                    fact.confidence >= 0.5 ? 'bg-blue-100 text-blue-700' :
                                                        'bg-orange-100 text-orange-700'
                                                    }`}>
                                                    {(fact.confidence * 100).toFixed(0)}% confident
                                                </span>
                                                <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                                                    {fact.fact_type}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 text-xs text-slate-400">
                                            <Clock className="w-3 h-3" />
                                            <span>{new Date(fact.created_at).toLocaleString()}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <Tag className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                                <p className="text-slate-500">No facts found</p>
                                <p className="text-sm text-slate-400 mt-1">Try adjusting your search or category filter</p>
                            </div>
                        )}
                    </Card>
                </div>
            )}

            {/* Episodes Tab */}
            {activeTab === 'episodes' && (
                <div className="space-y-6">
                    {/* Filters */}
                    <Card>
                        <div className="flex items-center gap-2">
                            <Filter className="w-5 h-5 text-slate-400" />
                            <select
                                value={episodeType}
                                onChange={(e) => setEpisodeType(e.target.value)}
                                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                            >
                                <option value="all">All Event Types</option>
                                <option value="decision_made">Decisions</option>
                                <option value="order_placed">Orders</option>
                                <option value="cycle_completed">Cycles</option>
                                <option value="error_encountered">Errors</option>
                            </select>
                        </div>
                    </Card>

                    {/* Episodes Timeline */}
                    <Card title={`Episode Timeline (${episodes.length})`}>
                        {loading ? (
                            <div className="text-center py-12">
                                <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                                <p className="text-slate-500">Loading episodes...</p>
                            </div>
                        ) : episodes.length > 0 ? (
                            <div className="relative">
                                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-200"></div>
                                <div className="space-y-4">
                                    {episodes.map((episode) => (
                                        <div key={episode.id} className="relative pl-12">
                                            <div className={`absolute left-0 w-8 h-8 rounded-full flex items-center justify-center ${episode.outcome === 'success' ? 'bg-green-500' :
                                                episode.outcome === 'failure' ? 'bg-red-500' :
                                                    'bg-blue-500'
                                                }`}>
                                                <div className="w-3 h-3 rounded-full bg-white"></div>
                                            </div>
                                            <div className="bg-white border border-slate-200 rounded-lg p-4 hover:border-indigo-300 transition-colors">
                                                <div className="flex items-start justify-between mb-2">
                                                    <div>
                                                        <p className="font-semibold text-slate-900">{episode.description}</p>
                                                        <p className="text-sm text-slate-600 mt-1">
                                                            {episode.sku && <span className="font-medium">SKU: {episode.sku}</span>}
                                                        </p>
                                                    </div>
                                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${episode.outcome === 'success' ? 'bg-green-100 text-green-700' :
                                                        episode.outcome === 'failure' ? 'bg-red-100 text-red-700' :
                                                            'bg-blue-100 text-blue-700'
                                                        }`}>
                                                        {episode.outcome}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-4 text-xs text-slate-500">
                                                    <span className="px-2 py-1 bg-slate-100 rounded">{episode.event_type}</span>
                                                    <span className="flex items-center gap-1">
                                                        <Clock className="w-3 h-3" />
                                                        {new Date(episode.timestamp).toLocaleString()}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <BookMarked className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                                <p className="text-slate-500">No episodes recorded yet</p>
                            </div>
                        )}
                    </Card>
                </div>
            )}

            {/* Checkpoints Tab */}
            {activeTab === 'checkpoints' && (
                <Card title={`System Checkpoints (${checkpoints.length})`}>
                    {loading ? (
                        <div className="text-center py-12">
                            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                            <p className="text-slate-500">Loading checkpoints...</p>
                        </div>
                    ) : checkpoints.length > 0 ? (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead className="bg-slate-50 border-b border-slate-200">
                                    <tr>
                                        <th className="text-left py-3 px-4 font-semibold text-slate-700">Checkpoint ID</th>
                                        <th className="text-left py-3 px-4 font-semibold text-slate-700">Cycle</th>
                                        <th className="text-left py-3 px-4 font-semibold text-slate-700">Goal</th>
                                        <th className="text-left py-3 px-4 font-semibold text-slate-700">Status</th>
                                        <th className="text-left py-3 px-4 font-semibold text-slate-700">Created</th>
                                        <th className="text-right py-3 px-4 font-semibold text-slate-700">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {checkpoints.map((checkpoint) => (
                                        <tr key={checkpoint.id} className="border-b border-slate-100 hover:bg-slate-50">
                                            <td className="py-3 px-4 font-mono text-xs">{checkpoint.checkpoint_id.slice(0, 16)}...</td>
                                            <td className="py-3 px-4">
                                                <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs font-medium">
                                                    #{checkpoint.cycle_number}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4 text-slate-700">{checkpoint.goal}</td>
                                            <td className="py-3 px-4">
                                                {checkpoint.is_stable ? (
                                                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                                                        Stable
                                                    </span>
                                                ) : (
                                                    <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-medium">
                                                        Unstable
                                                    </span>
                                                )}
                                            </td>
                                            <td className="py-3 px-4 text-slate-600">{new Date(checkpoint.created_at).toLocaleString()}</td>
                                            <td className="py-3 px-4 text-right">
                                                <button className="text-indigo-600 hover:text-indigo-800 font-medium text-xs">
                                                    Restore
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="text-center py-12">
                            <Archive className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                            <p className="text-slate-500">No checkpoints available</p>
                        </div>
                    )}
                </Card>
            )}
        </div>
    );
}
