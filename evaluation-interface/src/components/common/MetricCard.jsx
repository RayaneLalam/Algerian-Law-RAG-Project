import React from 'react';

const MetricCard = ({ title, value, trend }) => (
  <div className="bg-white rounded-lg shadow p-6">
    <h3 className="text-sm text-gray-600 mb-2">{title}</h3>
    <div className="flex items-end justify-between">
      <span className="text-3xl font-bold">{value}</span>
      <span className={`text-sm ${trend.startsWith('+') ? 'text-green-600' : 'text-gray-600'}`}>
        {trend}
      </span>
    </div>
  </div>
);

export default MetricCard;