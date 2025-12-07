import React from 'react';
import NavButton from '../common/NavButton';

const Sidebar = ({ currentPage, setCurrentPage }) => {
  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col shrink-0">
      <div className="p-6 border-b border-gray-700">
        <h1 className="text-xl font-bold">Evaluator UI</h1>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        <NavButton active={currentPage === 'dashboard'} onClick={() => setCurrentPage('dashboard')}>
          📊 Dashboard
        </NavButton>
        <NavButton active={currentPage === 'playground'} onClick={() => setCurrentPage('playground')}>
          🎮 Evaluation Playground
        </NavButton>
        <NavButton active={currentPage === 'queries'} onClick={() => setCurrentPage('queries')}>
          📝 User Queries Review
        </NavButton>
        <NavButton active={currentPage === 'comparison'} onClick={() => setCurrentPage('comparison')}>
          ⚖️ Model Comparison
        </NavButton>
        <NavButton active={currentPage === 'dataset'} onClick={() => setCurrentPage('dataset')}>
          📦 Dataset Builder
        </NavButton>
        <NavButton active={currentPage === 'governance'} onClick={() => setCurrentPage('governance')}>
          🔒 Governance
        </NavButton>
      </nav>
    </aside>
  );
};

export default Sidebar;