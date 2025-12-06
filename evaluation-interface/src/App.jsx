// App.jsx
import React, { useState } from 'react';

// =============================================================================
// DUMMY DATA & API SIMULATION
// =============================================================================

// Simulate API latency
const simulateFetch = (data, delay = 800) => {
  return new Promise(resolve => setTimeout(() => resolve(data), delay));
};

// Dummy LLM candidate answers generator
const generateDummyAnswers = (query, n) => {
  const templates = [
    { text: "Based on the documentation, {query} involves...", score: 0.92, citations: ["doc_1", "doc_3"] },
    { text: "The answer to {query} is that it depends on...", score: 0.88, citations: ["doc_2"] },
    { text: "To address {query}, you should consider...", score: 0.85, citations: ["doc_1", "doc_4"] },
    { text: "In the context of {query}, research shows...", score: 0.81, citations: ["doc_3", "doc_5"] },
    { text: "The most effective approach to {query} would be...", score: 0.79, citations: ["doc_2", "doc_4"] },
  ];
  
  return Array.from({ length: n }, (_, i) => ({
    id: `answer_${Date.now()}_${i}`,
    text: templates[i % templates.length].text.replace('{query}', query),
    modelId: `model_${String.fromCharCode(65 + (i % 3))}`,
    confidence: templates[i % templates.length].score,
    citations: templates[i % templates.length].citations,
    rank: i + 1,
  }));
};

// =============================================================================
// MAIN APP COMPONENT
// =============================================================================

export default function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [rightPanelOpen, setRightPanelOpen] = useState(true);
  
  // Evaluation Playground state
  const [query, setQuery] = useState('');
  const [numAnswers, setNumAnswers] = useState(3);
  const [candidates, setCandidates] = useState([]);
  const [referenceAnswer, setReferenceAnswer] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [evaluationHistory, setEvaluationHistory] = useState([]);

  // Dataset builder state
  const [savedDatasets, setSavedDatasets] = useState([]);

  // =============================================================================
  // API CALL PLACEHOLDERS - Replace these with real fetch() calls
  // =============================================================================
  
  const handleGenerateAnswers = async () => {
    setIsGenerating(true);
    
    // 🔄 REPLACE THIS: simulateFetch -> real API call
    // const response = await fetch('/api/generate-answers', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ query, num_answers: numAnswers })
    // });
    // const data = await response.json();
    // setCandidates(data.candidates);
    
    const dummyAnswers = generateDummyAnswers(query, numAnswers);
    await simulateFetch(dummyAnswers);
    setCandidates(dummyAnswers);
    
    setIsGenerating(false);
    
    // Add to history
    setEvaluationHistory(prev => [{
      id: Date.now(),
      query,
      numCandidates: numAnswers,
      timestamp: new Date().toISOString()
    }, ...prev].slice(0, 10));
  };

  const handleSaveRanking = async () => {
    // 🔄 REPLACE THIS: simulateFetch -> real API call
    // await fetch('/api/save-ranking', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({
    //     query,
    //     candidates: candidates.map(c => ({ id: c.id, rank: c.rank })),
    //     reference_answer: referenceAnswer
    //   })
    // });
    
    await simulateFetch({ status: 'saved' });
    
    // Save to local dataset builder
    if (referenceAnswer.trim()) {
      setSavedDatasets(prev => [{
        id: Date.now(),
        query,
        referenceAnswer,
        topCandidate: candidates[0],
        timestamp: new Date().toISOString()
      }, ...prev]);
    }
    
    alert('Ranking and reference answer saved!');
  };

  const moveCandidate = (index, direction) => {
    const newCandidates = [...candidates];
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (newIndex < 0 || newIndex >= newCandidates.length) return;
    
    [newCandidates[index], newCandidates[newIndex]] = [newCandidates[newIndex], newCandidates[index]];
    
    // Update ranks
    newCandidates.forEach((c, i) => c.rank = i + 1);
    setCandidates(newCandidates);
  };

  // =============================================================================
  // PAGE CONTENT COMPONENTS
  // =============================================================================

  const DashboardPage = () => (
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

  const EvaluationPlaygroundPage = () => (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Evaluation Playground</h1>
      
      {/* Input Section */}
      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Query</label>
          <textarea
            className="w-full border rounded-lg p-3 h-24"
            placeholder="Enter your query here..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium mb-2">Number of Candidates</label>
            <input
              type="number"
              min="2"
              max="10"
              className="w-full border rounded-lg p-2"
              value={numAnswers}
              onChange={(e) => setNumAnswers(parseInt(e.target.value) || 2)}
            />
          </div>
          <button
            onClick={handleGenerateAnswers}
            disabled={!query.trim() || isGenerating}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {isGenerating ? 'Generating...' : 'Generate Answers'}
          </button>
        </div>
      </div>

      {/* Candidates Ranking Section */}
      {candidates.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <h2 className="text-xl font-semibold">Rank Candidate Answers</h2>
          <div className="space-y-3">
            {candidates.map((candidate, index) => (
              <div key={candidate.id} className="border rounded-lg p-4 bg-gray-50">
                <div className="flex items-start gap-4">
                  <div className="flex flex-col gap-1">
                    <button
                      onClick={() => moveCandidate(index, 'up')}
                      disabled={index === 0}
                      className="text-gray-500 hover:text-blue-600 disabled:text-gray-300"
                      aria-label="Move up"
                    >
                      ▲
                    </button>
                    <span className="text-sm font-bold text-center">{candidate.rank}</span>
                    <button
                      onClick={() => moveCandidate(index, 'down')}
                      disabled={index === candidates.length - 1}
                      className="text-gray-500 hover:text-blue-600 disabled:text-gray-300"
                      aria-label="Move down"
                    >
                      ▼
                    </button>
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-medium text-blue-600">{candidate.modelId}</span>
                      <span className="text-xs text-gray-500">Confidence: {(candidate.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-sm mb-2">{candidate.text}</p>
                    <div className="flex gap-2 flex-wrap">
                      {candidate.citations.map(cite => (
                        <span key={cite} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                          {cite}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reference Answer Section */}
      {candidates.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <h2 className="text-xl font-semibold">Reference Answer (Ground Truth)</h2>
          <textarea
            className="w-full border rounded-lg p-3 h-32"
            placeholder="Write the ideal reference answer here..."
            value={referenceAnswer}
            onChange={(e) => setReferenceAnswer(e.target.value)}
          />
          <button
            onClick={handleSaveRanking}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
          >
            Save Ranking & Reference Answer
          </button>
        </div>
      )}
    </div>
  );

  const UserQueriesPage = () => (
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

  const ModelComparisonPage = () => (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Model Comparison (A vs B)</h1>
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Model A</h3>
          <div className="space-y-2 text-sm">
            <p><strong>Accuracy:</strong> 87.3%</p>
            <p><strong>Latency:</strong> 245ms</p>
            <p><strong>Citation Quality:</strong> 8.1/10</p>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Model B</h3>
          <div className="space-y-2 text-sm">
            <p><strong>Accuracy:</strong> 89.1%</p>
            <p><strong>Latency:</strong> 312ms</p>
            <p><strong>Citation Quality:</strong> 7.8/10</p>
          </div>
        </div>
      </div>
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Head-to-Head Comparison</h3>
        <p className="text-sm text-gray-600">Run side-by-side tests and analyze model performance differences.</p>
      </div>
    </div>
  );

  const DatasetBuilderPage = () => (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dataset Builder</h1>
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Saved Reference Answers ({savedDatasets.length})</h3>
        <div className="space-y-3">
          {savedDatasets.length === 0 ? (
            <p className="text-sm text-gray-500">No saved datasets yet. Create reference answers in the Evaluation Playground.</p>
          ) : (
            savedDatasets.map(dataset => (
              <div key={dataset.id} className="border rounded-lg p-4 bg-gray-50">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-medium text-sm">{dataset.query}</span>
                  <span className="text-xs text-gray-500">{new Date(dataset.timestamp).toLocaleDateString()}</span>
                </div>
                <p className="text-sm text-gray-700 mb-2">{dataset.referenceAnswer}</p>
                <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                  Top: {dataset.topCandidate.modelId}
                </span>
              </div>
            ))
          )}
        </div>
        <div className="mt-4 flex gap-2">
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">
            Export Dataset
          </button>
          <button className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 text-sm">
            Import Dataset
          </button>
        </div>
      </div>
    </div>
  );

  const GovernancePage = () => (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Governance & Version Log</h1>
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Model Version History</h3>
        <div className="space-y-3">
          {['v2.3.1', 'v2.3.0', 'v2.2.5', 'v2.2.4'].map((version, i) => (
            <div key={version} className="border-l-4 border-blue-500 pl-4 py-2">
              <div className="flex justify-between items-center">
                <div>
                  <span className="font-medium">{version}</span>
                  <p className="text-sm text-gray-600">Deployed on 2024-{12 - i}-{String(15 - i * 3).padStart(2, '0')}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${i === 0 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                  {i === 0 ? 'Current' : 'Previous'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // =============================================================================
  // HELPER COMPONENTS
  // =============================================================================

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

  const RightPanel = () => {
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
      <div className={`bg-white border-l transition-all duration-300 ${rightPanelOpen ? 'w-80' : 'w-0 overflow-hidden'}`}>
        <div className="p-6">
          {getContextualContent()}
        </div>
      </div>
    );
  };

  // =============================================================================
  // MAIN RENDER
  // =============================================================================

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard': return <DashboardPage />;
      case 'playground': return <EvaluationPlaygroundPage />;
      case 'queries': return <UserQueriesPage />;
      case 'comparison': return <ModelComparisonPage />;
      case 'dataset': return <DatasetBuilderPage />;
      case 'governance': return <GovernancePage />;
      default: return <DashboardPage />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* LEFT SIDEBAR */}
      <aside className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-6 border-b border-gray-700">
          <h1 className="text-xl font-bold">Evaluator UI</h1>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          <NavButton
            active={currentPage === 'dashboard'}
            onClick={() => setCurrentPage('dashboard')}
          >
            📊 Dashboard
          </NavButton>
          <NavButton
            active={currentPage === 'playground'}
            onClick={() => setCurrentPage('playground')}
          >
            🎮 Evaluation Playground
          </NavButton>
          <NavButton
            active={currentPage === 'queries'}
            onClick={() => setCurrentPage('queries')}
          >
            📝 User Queries Review
          </NavButton>
          <NavButton
            active={currentPage === 'comparison'}
            onClick={() => setCurrentPage('comparison')}
          >
            ⚖️ Model Comparison
          </NavButton>
          <NavButton
            active={currentPage === 'dataset'}
            onClick={() => setCurrentPage('dataset')}
          >
            📦 Dataset Builder
          </NavButton>
          <NavButton
            active={currentPage === 'governance'}
            onClick={() => setCurrentPage('governance')}
          >
            🔒 Governance
          </NavButton>
        </nav>
      </aside>

      {/* MIDDLE CONTENT AREA */}
      <main className="flex-1 overflow-auto p-8">
        {renderPage()}
      </main>

      {/* RIGHT PANEL */}
      <RightPanel />

      {/* Toggle Right Panel Button */}
      <button
        onClick={() => setRightPanelOpen(!rightPanelOpen)}
        className="fixed right-4 top-4 bg-white shadow-lg rounded-full p-2 hover:bg-gray-100 z-10"
        aria-label={rightPanelOpen ? 'Close panel' : 'Open panel'}
      >
        {rightPanelOpen ? '→' : '←'}
      </button>
    </div>
  );
}

// Navigation Button Component
const NavButton = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
      active ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800'
    }`}
  >
    {children}
  </button>
);

// =============================================================================
// BACKEND INTEGRATION GUIDE
// =============================================================================
/*
To connect to a real backend, replace the simulateFetch calls with actual fetch() calls:

1. Generate Answers:
   Replace in handleGenerateAnswers():
   
   const response = await fetch('/api/generate-answers', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ 
       query, 
       num_answers: numAnswers 
     })
   });
   const data = await response.json();
   setCandidates(data.candidates);

2. Save Ranking & Reference Answer:
   Replace in handleSaveRanking():
   
   const response = await fetch('/api/save-ranking', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       query,
       candidates: candidates.map(c => ({ 
         id: c.id, 
         rank: c.rank,
         model_id: c.modelId 
       })),
       reference_answer: referenceAnswer,
       timestamp: new Date().toISOString()
     })
   });
   const result = await response.json();

3. Load Evaluation History:
   Add on component mount:
   
   useEffect(() => {
     const loadHistory = async () => {
       const response = await fetch('/api/evaluation-history');
       const data = await response.json();
       setEvaluationHistory(data.history);
     };
     loadHistory();
   }, []);

4. Load Saved Datasets:
   Add on component mount:
   
   useEffect(() => {
     const loadDatasets = async () => {
       const response = await fetch('/api/datasets');
       const data = await response.json();
       setSavedDatasets(data.datasets);
     };
     loadDatasets();
   }, []);

Expected Backend API Endpoints:
- POST /api/generate-answers -> { candidates: [...] }
- POST /api/save-ranking -> { status: 'success', id: '...' }
- GET /api/evaluation-history -> { history: [...] }
- GET /api/datasets -> { datasets: [...] }
- GET /api/metrics -> { total_evaluations: N, avg_score: X, ... }
*/