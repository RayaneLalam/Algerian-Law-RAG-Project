import React from 'react';

const RightPanel = ({ isOpen, currentPage, evaluationHistory, savedDatasets }) => {
  const getContextualContent = () => {
    switch (currentPage) {
      case 'playground':
        return (
          <div className="space-y-4">
            <h3 className="font-semibold">Evaluation History</h3>
            {evaluationHistory.length === 0 ? (
              <p className="text-sm text-gray-500">No evaluations yet</p>
            ) : (
              <div className="space-y-2">
                {evaluationHistory.map(item => (
                  <div key={item.id} className="text-sm border-b pb-2">
                    <p className="font-medium truncate">{item.query}</p>
                    <p className="text-xs text-gray-500">{item.numCandidates} candidates</p>
                    <p className="text-xs text-gray-400">{new Date(item.timestamp).toLocaleTimeString()}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      case 'dataset':
        return (
          <div className="space-y-4">
            <h3 className="font-semibold">Dataset Stats</h3>
            <div className="text-sm space-y-2">
              <p>Total Entries: <strong>{savedDatasets.length}</strong></p>
              <p>Last Updated: <strong>{savedDatasets[0] ? new Date(savedDatasets[0].timestamp).toLocaleDateString() : 'N/A'}</strong></p>
            </div>
          </div>
        );
      default:
        return (
          <div className="space-y-4">
            <h3 className="font-semibold">Quick Actions</h3>
            <div className="space-y-2">
              <button className="w-full text-left text-sm p-2 hover:bg-gray-100 rounded">New Evaluation</button>
              <button className="w-full text-left text-sm p-2 hover:bg-gray-100 rounded">View Reports</button>
              <button className="w-full text-left text-sm p-2 hover:bg-gray-100 rounded">Export Data</button>
            </div>
          </div>
        );
    }
  };

  return (
    <div className={`bg-white border-l transition-all duration-300 ${isOpen ? 'w-80' : 'w-0 overflow-hidden'}`}>
      <div className="p-6 h-full overflow-y-auto">
        {getContextualContent()}
      </div>
    </div>
  );
};

export default RightPanel;