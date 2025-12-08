import { useState, useEffect } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { isAuthenticated } from './auth';
import Dashboard from './pages/Dashboard';
import { Inventory } from './pages/Inventory';
import { Sales } from './pages/Sales';
import Orders from './pages/Orders';
import Alerts from './pages/Alerts';
import AgentComplete from './pages/AgentComplete';
import AgentIntelligence from './pages/AgentIntelligence';
import FinanceDashboard from './pages/FinanceDashboard';
import FinanceAnalytics from './pages/FinanceAnalytics';
import MemoryExplorer from './pages/MemoryExplorer';
import Login from './pages/Login';
import Layout from './components/Layout';
import ChatBot from './components/ChatBot';
import './App.css';

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is authenticated
    const checkAuth = () => {
      const isAuth = isAuthenticated();
      console.log('Auth check:', { isAuth, authenticated });
      if (isAuth) {
        setAuthenticated(true);
      } else {
        setAuthenticated(false);
      }
      setLoading(false);
    };

    checkAuth();

    // Listen for auth changes
    window.addEventListener('authChange', checkAuth);
    window.addEventListener('storage', checkAuth);

    return () => {
      window.removeEventListener('authChange', checkAuth);
      window.removeEventListener('storage', checkAuth);
    };
  }, []);

  // React to authentication state changes
  useEffect(() => {
    console.log('Auth state changed:', authenticated);
    if (!authenticated && location.pathname !== '/login' && !loading) {
      console.log('Redirecting to login...');
      navigate('/login', { replace: true });
    }
  }, [authenticated, loading, location, navigate]);

  // Show loading screen while checking auth
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="w-12 h-12 border-4 border-purple-500 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  // Show login page if not authenticated
  if (!authenticated) {
    return <Login />;
  }

  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
      <Layout setAuthenticated={setAuthenticated}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/inventory" element={<Inventory />} />
          <Route path="/sales" element={<Sales />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/agent" element={<AgentComplete />} />
          <Route path="/intelligence" element={<AgentIntelligence />} />
          <Route path="/finance" element={<FinanceDashboard />} />
          <Route path="/finance-analytics" element={<FinanceAnalytics />} />
          <Route path="/memory" element={<MemoryExplorer />} />
        </Routes>
        <ChatBot />
      </Layout>
    </>
  );
}

export default App;
