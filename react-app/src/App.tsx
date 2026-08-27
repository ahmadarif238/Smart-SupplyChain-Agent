import { useState, useEffect } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { isAuthenticated } from './auth';
import Dashboard from './pages/Dashboard';
import { Inventory } from './pages/Inventory';
import Orders from './pages/Orders';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Layout from './components/Layout';
import ChatBot from './components/ChatBot';
import OnboardingModal from './components/OnboardingModal';
import './App.css';

// DEMO MODE: Set to true for public demo (no login required)
const DEMO_MODE = true;

function App() {
  const [authenticated, setAuthenticated] = useState(DEMO_MODE);
  const [loading, setLoading] = useState(!DEMO_MODE);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user should see onboarding (first visit)
    const hasSeenOnboarding = localStorage.getItem('hasSeenOnboarding');
    if (!hasSeenOnboarding) {
      setShowOnboarding(true);
    }
  }, []);

  const handleCloseOnboarding = () => {
    setShowOnboarding(false);
    localStorage.setItem('hasSeenOnboarding', 'true');
  };

  useEffect(() => {
    // DEMO MODE: Skip auth check
    if (DEMO_MODE) {
      setAuthenticated(true);
      setLoading(false);
      return;
    }

    // Check if user is authenticated
    const checkAuth = () => {
      const isAuth = isAuthenticated();
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

  // React to authentication state changes (disabled in demo mode)
  useEffect(() => {
    if (!DEMO_MODE && !authenticated && location.pathname !== '/login' && !loading) {
      navigate('/login', { replace: true });
    }
  }, [authenticated, loading, location, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="w-12 h-12 border-4 border-accent border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

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

      {/* Onboarding Modal - Shows on first visit */}
      {showOnboarding && (
        <OnboardingModal onClose={handleCloseOnboarding} />
      )}

      <Layout setAuthenticated={setAuthenticated}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/inventory" element={<Inventory />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
        <ChatBot />
      </Layout>
    </>
  );
}

export default App;

