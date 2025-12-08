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
    <div className="space-y-6 p-8 bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center max-w-7xl mx-auto">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">📊 Sales Tracking</h1>
          <p className="text-gray-600 mt-1">Monitor and record sales data</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition shadow-md"
        >
          <Plus size={20} />
          Record Sale
        </button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-7xl mx-auto">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-90 mb-2">Total Records</p>
              <p className="text-4xl font-bold">{sales.length}</p>
            </div>
            <TrendingUp size={40} className="opacity-30" />
          </div>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-lg p-6 shadow-lg">
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
        <div className="max-w-7xl mx-auto bg-white rounded-lg shadow-lg p-6 border-l-4 border-blue-600">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Record New Sale</h2>
          <form onSubmit={handleAddSale}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Product SKU"
                value={formData.sku}
                onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                required
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="number"
                placeholder="Quantity"
                value={formData.sold_quantity}
                onChange={(e) => setFormData({ ...formData, sold_quantity: parseInt(e.target.value) })}
                min="1"
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex gap-2 mt-4">
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition shadow-sm"
              >
                Record Sale
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Grouped Sales List */}
      <div className="max-w-7xl mx-auto space-y-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Sales by Product</h2>

        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading sales data...</div>
        ) : sortedSkus.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <TrendingUp className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg">No sales records yet</p>
          </div>
        ) : (
          sortedSkus.map((sku) => {
            const skuSales = groupedSales[sku];
            const isExpanded = expandedSku === sku;
            const totalSkuUnits = skuSales.reduce((sum, s) => sum + s.sold_quantity, 0);
            const recentSales = skuSales.slice(0, 20); // Limit to recent 20

            return (
              <div key={sku} className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200">
                <button
                  onClick={() => setExpandedSku(isExpanded ? null : sku)}
                  className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition"
                >
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-full ${isExpanded ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'}`}>
                      {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                    </div>
                    <div className="text-left">
                      <h3 className="text-lg font-bold text-gray-900">{sku}</h3>
                      <p className="text-sm text-gray-500">{skuSales.length} records • Last sale: {new Date(skuSales[0].date).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-blue-600">{totalSkuUnits}</p>
                    <p className="text-xs text-gray-500 uppercase font-semibold">Units Sold</p>
                  </div>
                </button>

                {isExpanded && (
                  <div className="border-t border-gray-100 bg-gray-50 p-4 animate-fade-in">
                    <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                      <Calendar size={16} />
                      Recent 20 Transactions
                    </h4>
                    <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50 border-b border-gray-200">
                          <tr>
                            <th className="px-4 py-2 text-left font-medium text-gray-600">ID</th>
                            <th className="px-4 py-2 text-left font-medium text-gray-600">Date</th>
                            <th className="px-4 py-2 text-right font-medium text-gray-600">Quantity</th>
                          </tr>
                        </thead>
                        <tbody>
                          {recentSales.map((sale) => (
                            <tr key={sale.id} className="border-b border-gray-100 last:border-0 hover:bg-blue-50 transition">
                              <td className="px-4 py-2 text-gray-500">#{sale.id}</td>
                              <td className="px-4 py-2 text-gray-900">
                                {new Date(sale.date).toLocaleString()}
                              </td>
                              <td className="px-4 py-2 text-right font-bold text-gray-900">
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
