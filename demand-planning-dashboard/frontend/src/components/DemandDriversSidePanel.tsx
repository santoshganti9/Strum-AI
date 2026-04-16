"use client";

import { useState } from "react";
import { X } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { format, parseISO } from "date-fns";

interface DemandDriversSidePanelProps {
  isOpen: boolean;
  onClose: () => void;
  itemId: string;
  itemName: string;
  demandDriversData?: any[];
  loading?: boolean;
}

const DemandDriversSidePanel = ({
  isOpen,
  onClose,
  itemId,
  itemName,
  demandDriversData = [],
  loading = false,
}: DemandDriversSidePanelProps) => {
  const [selectedMetric, setSelectedMetric] = useState<
    "units_sold" | "revenue"
  >("units_sold");

  // Format data for chart
  const chartData = demandDriversData.map((item) => ({
    date: format(parseISO(item.week_ending), "MMM dd"),
    fullDate: item.week_ending,
    units: item.units_sold,
    revenue: item.revenue,
    type: item.type,
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900 text-sm">
            {format(parseISO(data.fullDate), "MMM dd, yyyy")}
          </p>
          {selectedMetric === "units_sold" ? (
            <p className="text-blue-600 text-sm">
              Units: {data.units?.toLocaleString() || "N/A"}
            </p>
          ) : (
            <p className="text-green-600 text-sm">
              Revenue: ${data.revenue?.toLocaleString() || "N/A"}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="relative ml-auto h-full w-full max-w-2xl bg-white shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Demand Drivers
            </h2>
            <p className="text-sm text-gray-600">
              {itemName} ({itemId})
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-2 hover:bg-gray-100 transition-colors"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-4 border-b px-6 py-3 bg-gray-50">
          <label className="text-sm font-medium text-gray-700">Metric:</label>
          <select
            value={selectedMetric}
            onChange={(e) =>
              setSelectedMetric(e.target.value as "units_sold" | "revenue")
            }
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="units_sold">Units Sold</option>
            <option value="revenue">Revenue</option>
          </select>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : chartData.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              No demand driver data available
            </div>
          ) : (
            <div className="space-y-6">
              {/* Chart */}
              <div className="bg-white rounded-lg border">
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart
                    data={chartData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                      dataKey="date"
                      stroke="#666"
                      fontSize={12}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis
                      stroke="#666"
                      fontSize={12}
                      tickFormatter={(value) =>
                        selectedMetric === "revenue"
                          ? `$${(value / 1000).toFixed(0)}K`
                          : value.toLocaleString()
                      }
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />

                    <Line
                      type="monotone"
                      dataKey={
                        selectedMetric === "units_sold" ? "units" : "revenue"
                      }
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ fill: "#3b82f6", strokeWidth: 2, r: 4 }}
                      name={
                        selectedMetric === "units_sold"
                          ? "Units Sold"
                          : "Revenue"
                      }
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Summary Stats */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Total Weeks</div>
                  <div className="text-2xl font-bold text-blue-900">
                    {chartData.length}
                  </div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">
                    Avg {selectedMetric === "units_sold" ? "Units" : "Revenue"}
                  </div>
                  <div className="text-2xl font-bold text-green-900">
                    {selectedMetric === "units_sold"
                      ? Math.round(
                          chartData.reduce(
                            (sum, d) => sum + (d.units || 0),
                            0,
                          ) / chartData.length,
                        ).toLocaleString()
                      : `$${Math.round(chartData.reduce((sum, d) => sum + (d.revenue || 0), 0) / chartData.length).toLocaleString()}`}
                  </div>
                </div>
              </div>

              {/* Note about data availability */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm text-yellow-800">
                  <strong>Note:</strong> Currently showing units sold and
                  revenue as demand drivers. Full demand drivers
                  (avg_unit_price, cust_instock) would require adding a
                  demand_drivers JSON column to the SalesData model with price
                  and stock level data.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DemandDriversSidePanel;
