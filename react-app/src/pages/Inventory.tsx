import React, { useState, useEffect } from 'react';
import { Plus } from 'lucide-react';
import { apiService } from '../api';

interface InventoryItem {
  id: number;
  product_name: string;
  sku: string;
  quantity: number;
  threshold: number;
  unit_price?: number;
  supplier?: string;
  lead_time_days?: number;
  category?: string;
  is_active?: boolean;
}

export const Inventory: React.FC = () => {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    product_name: '',
    sku: '',
    quantity: 0,
    threshold: 10,
    unit_price: 0,
    supplier: '',
    lead_time_days: 0,
    category: '',
    safety_stock: 10,
  });

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    try {
      const response = await apiService.inventory.list();
      setItems(response.data);
    } catch (error) {
      console.error('Failed to fetch inventory:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiService.inventory.add(formData);
      setFormData({
        product_name: '',
        sku: '',
        quantity: 0,
        threshold: 10,
        unit_price: 0,
        supplier: '',
        lead_time_days: 0,
        category: '',
        safety_stock: 10,
      });
      setShowForm(false);
      fetchInventory();
    } catch (error) {
      console.error('Failed to add item:', error);
    }
  };

  const lowStockCount = items.filter(i => i.quantity < i.threshold).length;
  const totalValue = items.reduce((sum, i) => sum + ((i.quantity || 0) * (i.unit_price || 0)), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">📦 Inventory Management</h1>
          <p className="text-slate-400 mt-1">Manage products with supply chain data</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-accent text-white rounded-none hover:bg-accent-hover transition"
        >
          <Plus size={20} />
          Add Product
        </button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-accent to-accent-hover text-white rounded-none p-4 shadow-lg">
          <p className="text-sm opacity-90 mb-1">Total Items</p>
          <p className="text-3xl font-bold">{items.length}</p>
        </div>
        <div className="bg-gradient-to-br from-red-500 to-red-600 text-white rounded-none p-4 shadow-lg">
          <p className="text-sm opacity-90 mb-1">Low Stock</p>
          <p className="text-3xl font-bold">{lowStockCount}</p>
        </div>
        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white rounded-none p-4 shadow-lg">
          <p className="text-sm opacity-90 mb-1">Total Value</p>
          <p className="text-3xl font-bold">${totalValue.toFixed(0)}</p>
        </div>
        <div className="bg-gradient-to-br from-accent to-accent-hover text-white rounded-none p-4 shadow-lg">
          <p className="text-sm opacity-90 mb-1">Active</p>
          <p className="text-3xl font-bold">{items.filter(i => i.is_active).length}</p>
        </div>
      </div>

      {/* Add Form */}
      {showForm && (
        <div className="bg-ink-800 rounded-none shadow-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">Add New Product</h2>
          <form onSubmit={handleAddItem}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Product Name"
                value={formData.product_name}
                onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
                required
                className="px-4 py-2 border border-ink-700 rounded-none focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <input
                type="text"
                placeholder="SKU"
                value={formData.sku}
                onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                required
                className="px-4 py-2 border border-ink-700 rounded-none focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <input
                type="number"
                placeholder="Quantity"
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) })}
                className="px-4 py-2 border border-ink-700 rounded-none focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <input
                type="number"
                placeholder="Threshold"
                value={formData.threshold}
                onChange={(e) => setFormData({ ...formData, threshold: parseInt(e.target.value) })}
                className="px-4 py-2 border border-ink-700 rounded-none focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <input
                type="number"
                placeholder="Unit Price"
                value={formData.unit_price}
                onChange={(e) => setFormData({ ...formData, unit_price: parseFloat(e.target.value) })}
                className="px-4 py-2 border border-ink-700 rounded-none focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <input
                type="text"
                placeholder="Supplier"
                value={formData.supplier}
                onChange={(e) => setFormData({ ...formData, supplier: e.target.value })}
                className="px-4 py-2 border border-ink-700 rounded-none focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <input
                type="text"
                placeholder="Category"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="px-4 py-2 border border-ink-700 rounded-none focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <input
                type="number"
                placeholder="Lead Time (Days)"
                value={formData.lead_time_days}
                onChange={(e) => setFormData({ ...formData, lead_time_days: parseInt(e.target.value) })}
                className="px-4 py-2 border border-ink-700 rounded-none focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <input
                type="number"
                placeholder="Safety Stock"
                value={formData.safety_stock}
                onChange={(e) => setFormData({ ...formData, safety_stock: parseInt(e.target.value) })}
                className="px-4 py-2 border border-ink-700 rounded-none focus:outline-none focus:ring-2 focus:ring-accent"
              />
            </div>
            <div className="flex gap-2 mt-4">
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded-none hover:bg-green-700 transition"
              >
                Add Product
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 bg-ink-700 text-white rounded-none hover:bg-ink-700 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Table */}
      <div className="bg-ink-800 rounded-none shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-ink-900 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-white">Product</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-white">SKU</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-white">Quantity</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-white">Threshold</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-white">Price</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-white">Status</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-white">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-slate-400">
                    Loading...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-slate-400">
                    No items yet
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id} className="border-b hover:bg-ink-900 transition">
                    <td className="px-6 py-4 font-medium text-white">{item.product_name}</td>
                    <td className="px-6 py-4 text-slate-400">{item.sku}</td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${item.quantity < item.threshold
                        ? 'bg-red-500/15 text-red-300'
                        : 'bg-emerald-500/15 text-emerald-300'
                        }`}>
                        {item.quantity}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-400">{item.threshold}</td>
                    <td className="px-6 py-4 text-slate-400">${item.unit_price?.toFixed(2) || '0.00'}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-sm font-medium ${item.is_active
                        ? 'bg-accent/10 text-accent'
                        : 'bg-ink-900 text-white'
                        }`}>
                        {item.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 flex gap-2">
                      {/* Actions placeholder - add edit/delete later */}
                      <span className="text-slate-500 text-sm">-</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
