import React, { useState } from 'react';
import Layout from './components/layout/Layout';
import { useDatasets } from './hooks/useDatasets';
import { useEvaluations } from './hooks/useEvaluations';

// Page Components
import Dashboard from './components/pages/Dashboard';
import EvaluationPlayground from './components/pages/EvaluationPlayground';
import UserQueries from './components/pages/UserQueries';
import ModelComparison from './components/pages/ModelComparison';
import DatasetBuilder from './components/pages/DatasetBuilder';
import Governance from './components/pages/Governance';

export default function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  
  // Custom hooks for logic and state
  const { savedDatasets, addDataset } = useDatasets();
  const evaluationState = useEvaluations(addDataset); // Pass callback to link modules

  // Render logic
  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard': return <Dashboard />;
      case 'playground': 
        // Pass all evaluation logic props to the playground
        return <EvaluationPlayground {...evaluationState} />;
      case 'queries': return <UserQueries />;
      case 'comparison': return <ModelComparison />;
      case 'dataset': return <DatasetBuilder savedDatasets={savedDatasets} />;
      case 'governance': return <Governance />;
      default: return <Dashboard />;
    }
  };

  return (
    <Layout 
      currentPage={currentPage} 
      setCurrentPage={setCurrentPage}
      evaluationHistory={evaluationState.evaluationHistory}
      savedDatasets={savedDatasets}
    >
      {renderPage()}
    </Layout>
  );
}