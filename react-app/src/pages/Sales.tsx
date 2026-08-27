import React, { useState, useEffect } from 'react';
import { Plus, TrendingUp, ChevronRight, ChevronDown, Package, Calendar } from 'lucide-react';
import { apiService } from '../api';

interface SalesRecord {
  id: number;
  sku: string;
  sold_quantity: number;
  date: string; // Changed from sale_date to match backend
}

interface GroupedSales {
  [sku: string]: SalesRecord[];
}

export const Sales: React.FC = () => {
  const [sales, setSales] = useState<SalesRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    sku: '',
    sold_quantity: 1,
  });
  const [expandedSku, setExpandedSku] = useState<string | null>(null);

  useEffect(() => {
    fetchSales();
  }, []);

  const fetchSales = async () => {
    try {
      const response = await apiService.sales.list();
      setSales(response.data);
    } catch (error) {
      console.error('Failed to fetch sales:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSale = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiService.sales.add(formData);
      setFormData({ sku: '', sold_quantity: 1 });
      setShowForm(false);
      fetchSales();
    } catch (error) {
      console.error('Failed to add sale:', error);
    }
  };

  const totalUnits = sales.reduce((sum, s) => sum + s.sold_quantity, 0);

  // Group sales by SKU
  const groupedSales: GroupedSales = sales.reduce((acc, sale) => {
    if (!acc[sale.sku]) {
      acc[sale.sku] = [];
    }
    acc[sale.sku].push(sale);
    return acc;
  }, {} as GroupedSales);

  // Get list of SKUs sorted by most recent sale
  const sortedSkus = Object.keys(groupedSales).sort((a, b) => {
    const dateA = new Date(groupedSales[a][0].date).getTime();
    const dateB = new Date(groupedSales[b][0].date).getTime();
    return dateB - dateA;
  });

  return (
    <div className="space-y-6 p-8 bg-gradient-to-br from-ink-900 to-ink-800 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center max-w-7xl mx-auto">
        <div>
          <h1 className="text-3xl font-bold text-white">📊 Sales Tracking</h1>
          <p className="text-slate-400 mt-1">Monitor and record sales data</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-accent text-white rounded-none hover:bg-accent-hover transition shadow-md"
        >
          <Plus size={20} />
          Record Sale
        </button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-7xl mx-auto">
        <div className="bg-gradient-to-br from-accent to-accent-hover text-white rounded-none p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-90 mb-2">Total Records</p>
              <p className="text-4xl font-bold">{sales.length}</p>
            </div>
            <TrendingUp size={40} className="opacity-30" />
          </div>
        </div>
        <div className="bg-gradient-to-br from-accent to-accent-hover text-white rounded-none p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-90 mb-2">Units Sold</p>
              <p className="text-4xl font-bold">{totalUnits}</p>
            </div>
            <Package size={40} className="opacity-30" />
          </div>
        </div>
      </div>

      {/* Add Form */}
      {showForm && (
        <div className="max-w-7xl mx-auto bg-ink-800 rounded-none shadow-lg p-6 border-l-4 border-accent">
          <h2 className="text-xl font-bold text-white mb-4">Record New Sale</h2>
          <form onSubmit={handleAddSale}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Product SKU"
                value={formData.sku}
                onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                required
                className="px-4 py-2 border border-ink-700 rounded-none focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <input
                type="number"
                placeholder="Quantity"
                value={formData.sold_quantity}
                onChange={(e) => setFormData({ ...formData, sold_quantity: parseInt(e.target.value) })}
                min="1"
                className="px-4 py-2 border border-ink-700 rounded-none focus:outline-none focus:ring-2 focus:ring-accent"
              />
            </div>
            <div className="flex gap-2 mt-4">
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded-none hover:bg-green-700 transition shadow-sm"
              >
                Record Sale
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 bg-ink-700 text-slate-300 rounded-none hover:bg-ink-700 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Grouped Sales List */}
      <div className="max-w-7xl mx-auto space-y-4">
        <h2 className="text-2xl font-bold text-white mb-4">Sales by Product</h2>

        {loading ? (
          <div className="text-center py-12 text-slate-400">Loading sales data...</div>
        ) : sortedSkus.length === 0 ? (
          <div className="text-center py-12 bg-ink-800 rounded-none shadow">
            <TrendingUp className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-400 text-lg">No sales records yet</p>
          </div>
        ) : (
          sortedSkus.map((sku) => {
            const skuSales = groupedSales[sku];
            const isExpanded = expandedSku === sku;
            const totalSkuUnits = skuSales.reduce((sum, s) => sum + s.sold_quantity, 0);
            const recentSales = skuSales.slice(0, 20); // Limit to recent 20

            return (
              <div key={sku} className="bg-ink-800 rounded-none shadow-md overflow-hidden border border-ink-700">
                <button
                  onClick={() => setExpandedSku(isExpanded ? null : sku)}
                  className="w-full flex items-center justify-between p-4 hover:bg-ink-900 transition"
                >
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-full ${isExpanded ? 'bg-accent/10 text-accent' : 'bg-ink-900 text-slate-400'}`}>
                      {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                    </div>
                    <div className="text-left">
                      <h3 className="text-lg font-bold text-white">{sku}</h3>
                      <p className="text-sm text-slate-400">{skuSales.length} records • Last sale: {new Date(skuSales[0].date).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-accent">{totalSkuUnits}</p>
                    <p className="text-xs text-slate-400 uppercase font-semibold">Units Sold</p>
                  </div>
                </button>

                {isExpanded && (
                  <div className="border-t border-ink-700 bg-ink-900 p-4 animate-fade-in">
                    <h4 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
                      <Calendar size={16} />
                      Recent 20 Transactions
                    </h4>
                    <div className="overflow-x-auto bg-ink-800 rounded-none border border-ink-700">
                      <table className="w-full text-sm">
                        <thead className="bg-ink-900 border-b border-ink-700">
                          <tr>
                            <th className="px-4 py-2 text-left font-medium text-slate-400">ID</th>
                            <th className="px-4 py-2 text-left font-medium text-slate-400">Date</th>
                            <th className="px-4 py-2 text-right font-medium text-slate-400">Quantity</th>
                          </tr>
                        </thead>
                        <tbody>
                          {recentSales.map((sale) => (
                            <tr key={sale.id} className="border-b border-ink-700 last:border-0 hover:bg-accent/10 transition">
                              <td className="px-4 py-2 text-slate-400">#{sale.id}</td>
                              <td className="px-4 py-2 text-white">
                                {new Date(sale.date).toLocaleString()}
                              </td>
                              <td className="px-4 py-2 text-right font-bold text-white">
                                {sale.sold_quantity}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
