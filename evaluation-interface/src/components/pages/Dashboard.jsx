import React from 'react';
import MetricCard from '../common/MetricCard';

const Dashboard = () => (
  <div className="space-y-6">
    <h1 className="text-3xl font-bold">Evaluation Dashboard</h1>
    <div className="grid grid-cols-3 gap-4">
      <MetricCard title="Total Evaluations" value="1,247" trend="+12%" />
      <MetricCard title="Avg. Quality Score" value="8.3/10" trend="+0.4" />
      <MetricCard title="Active Models" value="5" trend="0" />
    </div>
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
      <div className="space-y-2">
        {[1, 2, 3].map(i => (
          <div key={i} className="flex justify-between items-center py-2 border-b">
            <span className="text-sm">Evaluation #{1248 - i}</span>
            <span className="text-xs text-gray-500">2 hours ago</span>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default Dashboard;