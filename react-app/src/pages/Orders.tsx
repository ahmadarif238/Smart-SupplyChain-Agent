import { useState, useEffect } from 'react';
import { ShoppingCart, Truck, CheckCircle, Clock, AlertCircle, Plus } from 'lucide-react';
import { apiService } from '../api';

export default function Orders() {
  const [orders, setOrders] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [newOrder, setNewOrder] = useState({ sku: '', quantity: 0 });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const [ordersRes, recsRes] = await Promise.all([
        apiService.orders.list(),
        apiService.orders.recommend(),
      ]);

      setOrders(ordersRes.data || []);
      setRecommendations(recsRes.data || []);
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrder = async () => {
    if (!newOrder.sku || newOrder.quantity <= 0) {
      alert('Please enter SKU and quantity');
      return;
    }

    try {
      setCreating(true);
      await apiService.orders.create(newOrder.sku, newOrder.quantity);
      setNewOrder({ sku: '', quantity: 0 });
      setShowForm(false);
      fetchOrders();
      alert('Order created successfully!');
    } catch (error) {
      console.error('Error creating order:', error);
      alert('Failed to create order');
    } finally {
      setCreating(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-amber-500/15 text-amber-300';
      case 'confirmed':
        return 'bg-accent/10 text-accent';
      case 'shipped':
        return 'bg-accent/10 text-accent';
      case 'delivered':
        return 'bg-emerald-500/15 text-emerald-300';
      case 'cancelled':
        return 'bg-red-500/15 text-red-300';
      default:
        return 'bg-ink-900 text-white';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return Clock;
      case 'confirmed':
        return CheckCircle;
      case 'shipped':
        return Truck;
      case 'delivered':
        return CheckCircle;
      default:
        return AlertCircle;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-ink-900 to-ink-800 flex items-center justify-center">
        <p className="text-slate-400">Loading orders...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-ink-900 to-ink-800 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white flex items-center gap-2">
              <ShoppingCart className="w-8 h-8 text-accent" />
              Orders Management
            </h1>
            <p className="text-slate-400 mt-2">Create and manage purchase orders</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-accent to-accent-hover text-white rounded-none hover:shadow-lg transition"
          >
            <Plus className="w-5 h-5" />
            New Order
          </button>
        </div>

        {/* Create Order Form */}
        {showForm && (
          <div className="bg-ink-800 rounded-none shadow-lg p-6 mb-8 border-l-4 border-accent">
            <h2 className="text-2xl font-bold text-white mb-4">Create New Order</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">SKU</label>
                <input
                  type="text"
                  value={newOrder.sku}
                  onChange={(e) => setNewOrder({ ...newOrder, sku: e.target.value })}
                  placeholder="Enter SKU"
                  className="w-full px-4 py-2 border border-ink-700 rounded-none focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">Quantity</label>
                <input
                  type="number"
                  value={newOrder.quantity}
                  onChange={(e) => setNewOrder({ ...newOrder, quantity: parseInt(e.target.value) })}
                  placeholder="Enter quantity"
                  className="w-full px-4 py-2 border border-ink-700 rounded-none focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
              <div className="flex items-end gap-2">
                <button
                  onClick={handleCreateOrder}
                  disabled={creating}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-none hover:shadow-lg transition disabled:bg-ink-700"
                >
                  {creating ? 'Creating...' : 'Create Order'}
                </button>
                <button
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 bg-ink-700 text-slate-300 rounded-none hover:bg-ink-700 transition"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Recommendations Section */}
        {recommendations.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4">🎯 AI Recommendations</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recommendations.map((rec: any, idx: number) => (
                <div key={idx} className="bg-gradient-to-br from-accent/10 to-accent/5 rounded-none p-6 border border-accent/40">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-lg font-semibold text-white">{rec.sku}</h3>
                      <p className="text-sm text-slate-400">{rec.product_name}</p>
                    </div>
                    <span className="px-3 py-1 bg-accent text-white rounded-full text-sm font-semibold">
                      {rec.urgency_level}
                    </span>
                  </div>
                  <div className="space-y-2 text-sm">
                    <p><strong>Recommended Qty:</strong> {rec.order_quantity}</p>
                    <p><strong>Current Stock:</strong> {rec.current_stock}</p>
                    <p><strong>Forecast:</strong> {rec.forecast_units} units</p>
                    <p className="text-slate-300 mt-3">{rec.reasoning}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Orders List */}
        <div className="bg-ink-800 rounded-none shadow-lg p-6">
          <h2 className="text-2xl font-bold text-white mb-4">Recent Orders ({orders.length})</h2>
          
          {orders.length === 0 ? (
            <div className="text-center py-12">
              <ShoppingCart className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-400 text-lg">No orders yet</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {orders.map((order: any, idx: number) => {
                const StatusIcon = getStatusIcon(order.status);
                const orderDate = order.order_date || order.created_at;
                const formattedDate = orderDate ? new Date(orderDate).toLocaleString() : 'Invalid Date';
                const productName = order.product_name || order.sku || 'UNKNOWN';
                
                return (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-4 border border-ink-700 rounded-none hover:bg-ink-900 transition"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <StatusIcon className="w-5 h-5 text-accent" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-semibold text-white">{productName}</p>
                          <span className="text-sm text-slate-400">×{order.quantity}</span>
                        </div>
                        <p className="text-xs text-slate-400">
                          {formattedDate}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p className="font-semibold text-white">${order.total_price || 'N/A'}</p>
                        <p className="text-xs text-slate-400">{order.supplier || 'Pending'}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(order.status)}`}>
                        {order.status}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
