import React, { useState } from 'react';
import Sidebar from './Sidebar';
import RightPanel from './RightPanel';

const Layout = ({ children, currentPage, setCurrentPage, evaluationHistory, savedDatasets }) => {
  const [rightPanelOpen, setRightPanelOpen] = useState(true);

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden">
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />

      {/* MIDDLE CONTENT AREA */}
      <main className="flex-1 overflow-auto p-8 relative">
        {children}
        
        {/* Toggle Right Panel Button */}
        <button
          onClick={() => setRightPanelOpen(!rightPanelOpen)}
          className="fixed right-4 top-4 bg-white shadow-lg rounded-full p-2 hover:bg-gray-100 z-10"
          aria-label={rightPanelOpen ? 'Close panel' : 'Open panel'}
        >
          {rightPanelOpen ? '→' : '←'}
        </button>
      </main>

      <RightPanel 
        isOpen={rightPanelOpen} 
        currentPage={currentPage} 
        evaluationHistory={evaluationHistory}
        savedDatasets={savedDatasets}
      />
    </div>
  );
};

export default Layout;