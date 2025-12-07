import React from 'react';

const UserQueries = () => (
  <div className="space-y-6">
    <h1 className="text-3xl font-bold">User Queries Review</h1>
    <div className="bg-white rounded-lg shadow">
      <table className="w-full">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th className="text-left p-4 text-sm font-medium">Query ID</th>
            <th className="text-left p-4 text-sm font-medium">Query (Anonymized)</th>
            <th className="text-left p-4 text-sm font-medium">Timestamp</th>
            <th className="text-left p-4 text-sm font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {[1, 2, 3, 4, 5].map(i => (
            <tr key={i} className="border-b hover:bg-gray-50">
              <td className="p-4 text-sm">Q{1000 + i}</td>
              <td className="p-4 text-sm">User asked about [REDACTED] feature...</td>
              <td className="p-4 text-sm text-gray-500">2024-12-{String(i).padStart(2, '0')}</td>
              <td className="p-4">
                <button className="text-red-600 hover:text-red-800 text-sm">🚩 Flag</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

export default UserQueries;