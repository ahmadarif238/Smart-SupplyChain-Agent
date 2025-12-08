import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../auth';
import { Brain } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('secret');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await login(username, password);
      console.log('Login response:', response);
      console.log('Token stored:', localStorage.getItem('auth_token'));

      // Dispatch a storage event to notify other components
      window.dispatchEvent(new Event('authChange'));

      // Navigate after a brief delay to allow state updates
      setTimeout(() => {
        console.log('Navigating to dashboard...');
        navigate('/', { replace: true });
      }, 200);
    } catch (err: any) {
      console.error('Login error:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Login failed. Check credentials.';
      setError(String(errorMsg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center px-4">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
      </div>

      {/* Login card */}
      <div className="relative z-10 w-full max-w-md">
        <div className="bg-white/10 backdrop-blur-xl rounded-2xl shadow-2xl p-8 border border-white/20">
          {/* Logo and title */}
          <div className="flex flex-col items-center mb-8">
            <div className="p-3 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl mb-4">
              <Brain className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white">SupplyChain</h1>
            <p className="text-gray-300 text-sm mt-2">AI Agent v1.0</p>
          </div>

          {/* Login form */}
          <form onSubmit={handleLogin} className="space-y-5">
            {/* Username field */}
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-2">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              />
            </div>

            {/* Password field */}
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              />
            </div>

            {/* Error message */}
            {error && (
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3">
                <p className="text-red-200 text-sm">{error}</p>
              </div>
            )}

            {/* Login button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  Logging in...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Credentials hint */}
          <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <p className="text-sm text-blue-200">
              <span className="font-semibold">Test Credentials:</span>
            </p>
            <p className="text-xs text-blue-300 mt-1">
              Username: <span className="font-mono">admin</span>
            </p>
            <p className="text-xs text-blue-300">
              Password: <span className="font-mono">secret</span>
            </p>
          </div>

          {/* Footer */}
          <p className="text-center text-gray-400 text-xs mt-6">
            © 2025 Smart SupplyChain AI Agent
          </p>
        </div>
      </div>
    </div>
  );
}
