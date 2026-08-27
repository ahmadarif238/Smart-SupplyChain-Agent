import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
    ShoppingCart, Home, Truck,
    Brain, LogOut, Cpu, Menu, ChevronRight
} from 'lucide-react';
import { logout } from '../auth';

interface LayoutProps {
    children: React.ReactNode;
    setAuthenticated: (auth: boolean) => void;
}

export default function Layout({ children, setAuthenticated }: LayoutProps) {
    const location = useLocation();
    const navigate = useNavigate();
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const handleLogout = () => {
        logout();
        setAuthenticated(false);
        navigate('/login');
    };

    const isActive = (path: string) => location.pathname === path;

    const navItems = [
        { path: '/', icon: Home, label: 'Dashboard' },
        { path: '/inventory', icon: ShoppingCart, label: 'Inventory' },
        { path: '/orders', icon: Truck, label: 'Orders' },
        // { path: '/sales', icon: BarChart3, label: 'Sales' },
        // { path: '/alerts', icon: AlertCircle, label: 'Alerts' },
        // { path: '/agent', icon: Zap, label: 'Agent Control' },
        // { path: '/intelligence', icon: Brain, label: 'AI Intelligence' },
        // { path: '/finance', icon: DollarSign, label: 'Finance Dashboard' },
        // { path: '/finance-analytics', icon: TrendingUp, label: 'Finance Analytics' },
        // { path: '/memory', icon: Database, label: 'Memory Explorer' },
        { path: '/settings', icon: Cpu, label: 'Settings' },
    ];

    return (
        <div className="min-h-screen bg-ink-950 flex">
            {/* Mobile Sidebar Overlay */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden backdrop-blur-sm"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside className={`
        fixed lg:static inset-y-0 left-0 z-50 w-72 bg-ink-950 text-white shadow-2xl transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        flex flex-col
      `}>
                {/* Logo Area */}
                <div className="p-6 border-b border-ink-700 bg-ink-950/50 backdrop-blur-md">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 bg-accent shadow-lg shadow-accent/20">
                            <Brain className="w-6 h-6 text-black" />
                        </div>
                        <div>
                            <h1 className="font-heading text-2xl font-bold uppercase tracking-tight">SupplyChain<span className="text-accent">AI</span></h1>
                            <p className="eyebrow mt-0.5">Autonomous Agent v2.0</p>
                        </div>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700">
                    {navItems.map(({ path, icon: Icon, label }) => {
                        const active = isActive(path);
                        return (
                            <Link
                                key={path}
                                to={path}
                                onClick={() => setSidebarOpen(false)}
                                className={`
                  group flex items-center justify-between px-4 py-3.5 rounded-none transition-all duration-200
                  ${active
                                        ? 'bg-accent text-black font-bold border-l-2 border-accent-hover'
                                        : 'text-slate-400 border-l-2 border-transparent hover:bg-ink-800 hover:text-white hover:border-ink-700'
                                    }
                `}
                            >
                                <div className="flex items-center gap-3">
                                    <Icon className={`w-5 h-5 transition-colors ${active ? 'text-black' : 'text-slate-500 group-hover:text-accent'}`} />
                                    <span className="text-xs font-bold uppercase tracking-widest">{label}</span>
                                </div>
                                {active && <ChevronRight className="w-4 h-4 text-black/60" />}
                            </Link>
                        );
                    })}
                </nav>

                {/* Footer / Status */}
                <div className="p-4 border-t border-ink-700 bg-ink-950/50 backdrop-blur-md space-y-4">
                    <div className="bg-ink-800/50 rounded-none p-4 border border-ink-700">
                        <div className="flex items-center justify-between mb-2">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-300">System Status</p>
                            <span className="flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                            </span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-slate-500">
                            <Cpu className="w-3 h-3" />
                            <span>Agent Active</span>
                        </div>
                    </div>

                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-none transition-colors text-sm font-medium border border-red-500/10"
                    >
                        <LogOut className="w-4 h-4" />
                        Sign Out
                    </button>
                </div>
            </aside>

            {/* Main Content Wrapper */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                {/* Mobile Header */}
                <header className="lg:hidden bg-ink-800 border-b border-ink-700 p-4 flex items-center justify-between sticky top-0 z-30">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-accent rounded-none">
                            <Brain className="w-5 h-5 text-white" />
                        </div>
                        <span className="font-bold text-white">SupplyChainAI</span>
                    </div>
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="p-2 text-slate-400 hover:bg-ink-900 rounded-none"
                    >
                        <Menu className="w-6 h-6" />
                    </button>
                </header>

                {/* Page Content */}
                <main className="flex-1 overflow-auto bg-ink-900/50 p-4 lg:p-8 scroll-smooth">
                    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
}
