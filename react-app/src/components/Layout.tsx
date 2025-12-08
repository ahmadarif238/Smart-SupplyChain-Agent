import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
    BarChart3, ShoppingCart, AlertCircle, Zap, Home, Truck,
    Brain, LogOut, Cpu, Menu, ChevronRight, DollarSign, Database, TrendingUp
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
        { path: '/sales', icon: BarChart3, label: 'Sales' },
        { path: '/orders', icon: Truck, label: 'Orders' },
        { path: '/alerts', icon: AlertCircle, label: 'Alerts' },
        { path: '/agent', icon: Zap, label: 'Agent Control' },
        { path: '/intelligence', icon: Brain, label: 'AI Intelligence' },
        { path: '/finance', icon: DollarSign, label: 'Finance Dashboard' },
        { path: '/finance-analytics', icon: TrendingUp, label: 'Finance Analytics' },
        { path: '/memory', icon: Database, label: 'Memory Explorer' },
    ];

    return (
        <div className="min-h-screen bg-slate-50 flex">
            {/* Mobile Sidebar Overlay */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden backdrop-blur-sm"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside className={`
        fixed lg:static inset-y-0 left-0 z-50 w-72 bg-slate-900 text-white shadow-2xl transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        flex flex-col
      `}>
                {/* Logo Area */}
                <div className="p-6 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/20">
                            <Brain className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold tracking-tight">SupplyChain<span className="text-indigo-400">AI</span></h1>
                            <p className="text-slate-400 text-xs font-medium">Autonomous Agent v2.0</p>
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
                  group flex items-center justify-between px-4 py-3.5 rounded-xl transition-all duration-200
                  ${active
                                        ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-900/20'
                                        : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'
                                    }
                `}
                            >
                                <div className="flex items-center gap-3">
                                    <Icon className={`w-5 h-5 transition-colors ${active ? 'text-white' : 'text-slate-500 group-hover:text-indigo-400'}`} />
                                    <span className="font-medium text-sm">{label}</span>
                                </div>
                                {active && <ChevronRight className="w-4 h-4 text-white/50" />}
                            </Link>
                        );
                    })}
                </nav>

                {/* Footer / Status */}
                <div className="p-4 border-t border-slate-800 bg-slate-900/50 backdrop-blur-md space-y-4">
                    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
                        <div className="flex items-center justify-between mb-2">
                            <p className="text-xs font-semibold text-slate-300">System Status</p>
                            <span className="flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                            </span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                            <Cpu className="w-3 h-3" />
                            <span>Agent Active</span>
                        </div>
                    </div>

                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors text-sm font-medium border border-red-500/10"
                    >
                        <LogOut className="w-4 h-4" />
                        Sign Out
                    </button>
                </div>
            </aside>

            {/* Main Content Wrapper */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                {/* Mobile Header */}
                <header className="lg:hidden bg-white border-b border-slate-200 p-4 flex items-center justify-between sticky top-0 z-30">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-600 rounded-lg">
                            <Brain className="w-5 h-5 text-white" />
                        </div>
                        <span className="font-bold text-slate-900">SupplyChainAI</span>
                    </div>
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="p-2 text-slate-600 hover:bg-slate-100 rounded-lg"
                    >
                        <Menu className="w-6 h-6" />
                    </button>
                </header>

                {/* Page Content */}
                <main className="flex-1 overflow-auto bg-slate-50/50 p-4 lg:p-8 scroll-smooth">
                    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
}
