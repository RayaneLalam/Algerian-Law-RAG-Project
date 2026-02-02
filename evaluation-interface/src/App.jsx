import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AuthScreen from './components/AuthScreen';
import AuthService from './services/AuthService';

const API_BASE = 'http://localhost:5000/api/evaluation';

// --- New UX Components ---

const ProgressBar = ({ isAnimating }) => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let interval;
    if (isAnimating) {
      setProgress(0);
      interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 95) return prev; // Hold at 95% until finished
          return prev + Math.random() * 10;
        });
      }, 500);
    } else {
      setProgress(0);
    }
    return () => clearInterval(interval);
  }, [isAnimating]);

  if (!isAnimating) return null;

  return (
    <div className="w-full bg-gray-200 rounded-full h-2.5 mb-6 overflow-hidden">
      <div 
        className="bg-blue-600 h-2.5 rounded-full transition-all duration-500 ease-out" 
        style={{ width: `${progress}%` }}
      ></div>
    </div>
  );
};

const ConfirmationModal = ({ isOpen, title, message, onConfirm, onCancel, confirmText = "Confirm", variant = "blue" }) => {
  if (!isOpen) return null;
  const colors = {
    blue: "bg-blue-600 hover:bg-blue-700",
    red: "bg-red-600 hover:bg-red-700",
    green: "bg-green-600 hover:bg-green-700"
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg p-6 max-w-sm w-full shadow-xl">
        <h3 className="text-xl font-bold mb-2">{title}</h3>
        <p className="text-gray-600 mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button onClick={onCancel} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
          <button onClick={onConfirm} className={`${colors[variant]} text-white px-4 py-2 rounded-lg`}>{confirmText}</button>
        </div>
      </div>
    </div>
  );
};

// --- Main App ---

const MainApp = () => {
  const { logout, user } = useAuth();
  const [activeTab, setActiveTab] = useState('playground');
  const [query, setQuery] = useState('');
  const [numCandidates, setNumCandidates] = useState(3);
  const [goldenLabel, setGoldenLabel] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentEvaluation, setCurrentEvaluation] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [evaluationHistory, setEvaluationHistory] = useState([]);
  const [anonymousQueries, setAnonymousQueries] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [models, setModels] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(true);

  // UX State
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [showCompleteConfirm, setShowCompleteConfirm] = useState(false);

  const authFetch = async (url, options = {}) => {
    const authHeaders = AuthService.getAuthHeader();
    const mergedOptions = {
      ...options,
      headers: { ...options.headers, ...authHeaders },
    };
    return fetch(url, mergedOptions);
  };

  useEffect(() => {
    fetchEvaluationHistory();
    fetchAnonymousQueries();
    fetchModels();
    fetchDatasets();
  }, []);

  useEffect(() => {
    if (selectedModel && selectedDataset) {
      fetchMetrics();
    }
  }, [selectedModel, selectedDataset]);

  const fetchEvaluationHistory = async () => {
    try {
      const res = await authFetch(`${API_BASE}/history`);
      const data = await res.json();
      setEvaluationHistory(data.evaluations || []);
    } catch (err) { console.error('Error fetching history:', err); }
  };

  const fetchAnonymousQueries = async () => {
    try {
      const res = await authFetch(`${API_BASE}/anonymous-queries`);
      const data = await res.json();
      setAnonymousQueries(data.queries || []);
    } catch (err) { console.error('Error fetching queries:', err); }
  };

  const fetchModels = async () => {
    try {
      const res = await authFetch(`${API_BASE}/models`);
      const data = await res.json();
      setModels(data.models || []);
      if (data.models?.length > 0) setSelectedModel(data.models[0].id);
    } catch (err) { console.error('Error fetching models:', err); }
  };

  const fetchDatasets = async () => {
    try {
      const res = await authFetch(`${API_BASE}/datasets`);
      const data = await res.json();
      setDatasets(data.datasets || []);
      if (data.datasets?.length > 0) setSelectedDataset(data.datasets[0].id);
    } catch (err) { console.error('Error fetching datasets:', err); }
  };

  const fetchMetrics = async () => {
    try {
      const res = await authFetch(`${API_BASE}/metrics?model_version_id=${selectedModel}&dataset_id=${selectedDataset}`);
      const data = await res.json();
      setMetrics(data.metrics || []);
    } catch (err) { console.error('Error fetching metrics:', err); }
  };

  const generateAnswers = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await authFetch(`${API_BASE}/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: query,
          num_responses: numCandidates,
          model_version_id: selectedModel,
          golden_label: goldenLabel.trim() || null
        })
      });
      const data = await res.json();
      setCurrentEvaluation(data.evaluation);
      setCandidates(data.candidates || []);
      fetchEvaluationHistory();
    } catch (err) {
      console.error('Error generating answers:', err);
    } finally {
      setLoading(false);
    }
  };

  const rankCandidate = async (candidateId, rank) => {
    try {
      await authFetch(`${API_BASE}/rank`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_id: candidateId, rank: rank })
      });
      fetchEvaluationHistory();
    } catch (err) { console.error('Error ranking candidate:', err); }
  };

  const markHallucination = async (responseId, isHallucination, notes) => {
    if (!responseId) return;
    try {
      await authFetch(`${API_BASE}/mark-hallucination`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message_id: responseId, is_hallucination: isHallucination, notes: notes })
      });
      fetchAnonymousQueries();
    } catch (err) { console.error('Error marking hallucination:', err); }
  };

  const completeEvaluation = async () => {
    if (!currentEvaluation) return;
    try {
      await authFetch(`${API_BASE}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ evaluation_id: currentEvaluation.id })
      });
      setCurrentEvaluation(null);
      setCandidates([]);
      setQuery('');
      setGoldenLabel('');
      fetchEvaluationHistory();
      setShowCompleteConfirm(false); // Close modal on success
    } catch (err) { console.error('Error completing evaluation:', err); }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Modals */}
      <ConfirmationModal 
        isOpen={showLogoutConfirm}
        title="Logout"
        message="Are you sure you want to log out of the session?"
        onConfirm={logout}
        onCancel={() => setShowLogoutConfirm(false)}
        variant="red"
      />

      <ConfirmationModal 
        isOpen={showCompleteConfirm}
        title="Complete Evaluation"
        message="This will finalize all rankings for this query. You won't be able to change them later."
        onConfirm={completeEvaluation}
        onCancel={() => setShowCompleteConfirm(false)}
        variant="green"
        confirmText="Finalize"
      />

      {/* Sidebar */}
      <div className="w-64 bg-slate-900 text-white flex flex-col">
        <div className="p-6">
          <h1 className="text-2xl font-bold">Evaluator UI</h1>
          <div className="mt-2 text-sm text-gray-400">{user?.username}</div>
        </div>
        <nav className="mt-6 flex-1">
          <NavItem icon="📊" label="Dashboard" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
          <NavItem icon="🎮" label="Evaluation Playground" active={activeTab === 'playground'} onClick={() => setActiveTab('playground')} />
          <NavItem icon="📋" label="User Queries Review" active={activeTab === 'queries'} onClick={() => setActiveTab('queries')} />
          <NavItem icon="⚖️" label="Model Comparison" active={activeTab === 'comparison'} onClick={() => setActiveTab('comparison')} />
          <NavItem icon="🎨" label="Dataset Builder" active={activeTab === 'dataset'} onClick={() => setActiveTab('dataset')} />
          <NavItem icon="🔒" label="Governance" active={activeTab === 'governance'} onClick={() => setActiveTab('governance')} />
        </nav>
        <div className="p-6">
          <button
            onClick={() => setShowLogoutConfirm(true)}
            className="w-full bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 p-8 overflow-auto">
          {activeTab === 'playground' && (
            <div>
              <h2 className="text-3xl font-bold mb-8">Evaluation Playground</h2>
              
              <div className="bg-white rounded-lg shadow p-6 mb-6">
                <ProgressBar isAnimating={loading} />
                
                <div className="grid grid-cols-2 gap-6 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Query</label>
                    <textarea
                      className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 outline-none"
                      rows="4"
                      placeholder="Enter your query here..."
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      disabled={loading || currentEvaluation}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Golden Label (Optional)</label>
                    <textarea
                      className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 outline-none"
                      rows="4"
                      placeholder="Enter the ground truth..."
                      value={goldenLabel}
                      onChange={(e) => setGoldenLabel(e.target.value)}
                      disabled={loading || currentEvaluation}
                    />
                  </div>
                </div>

                <div className="flex gap-4 items-end">
                  <div className="flex-1">
                    <label className="block text-sm font-medium mb-2">Number of Candidates</label>
                    <input
                      type="number"
                      className="w-full border border-gray-300 rounded-lg p-3"
                      value={numCandidates}
                      onChange={(e) => setNumCandidates(parseInt(e.target.value))}
                      disabled={loading || currentEvaluation}
                    />
                  </div>
                  <div className="flex-1">
                    <label className="block text-sm font-medium mb-2">Model Version</label>
                    <select
                      className="w-full border border-gray-300 rounded-lg p-3"
                      value={selectedModel || ''}
                      onChange={(e) => setSelectedModel(parseInt(e.target.value))}
                      disabled={loading || currentEvaluation}
                    >
                      {models.map(m => (
                        <option key={m.id} value={m.id}>{m.name} - {m.version}</option>
                      ))}
                    </select>
                  </div>
                  <button
                    className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 min-w-[160px]"
                    onClick={generateAnswers}
                    disabled={loading || currentEvaluation || !query.trim()}
                  >
                    {loading ? 'Processing...' : 'Generate Answers'}
                  </button>
                </div>
              </div>

              {candidates.length > 0 && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center bg-blue-50 p-4 rounded-lg border border-blue-100">
                    <div>
                      <h3 className="text-xl font-bold text-blue-900">Rank Candidates (RLHF)</h3>
                      <p className="text-sm text-blue-700">Assign ranks to the responses below based on quality.</p>
                    </div>
                    <button
                      className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 shadow-sm"
                      onClick={() => setShowCompleteConfirm(true)}
                    >
                      Complete Evaluation
                    </button>
                  </div>
                  {candidates.map((candidate, idx) => (
                    <CandidateCard
                      key={candidate.id}
                      candidate={candidate}
                      index={idx}
                      onRank={rankCandidate}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ... Other tabs (queries, comparison, dashboard) remain the same structurally ... */}
          {activeTab === 'queries' && (
            <div>
              <h2 className="text-3xl font-bold mb-8">Anonymous User Queries Review</h2>
              <div className="space-y-4">
                {anonymousQueries.map((q) => (
                  <QueryReviewCard key={q.id} query={q} onMarkHallucination={markHallucination} />
                ))}
                {anonymousQueries.length === 0 && <p className="text-gray-500">No queries to review</p>}
              </div>
            </div>
          )}

          {activeTab === 'comparison' && (
            <div>
              <h2 className="text-3xl font-bold mb-8">Model Performance Metrics</h2>
              <div className="bg-white rounded-lg shadow p-6 mb-6">
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium mb-2">Model Version</label>
                    <select
                      className="w-full border border-gray-300 rounded-lg p-3"
                      value={selectedModel || ''}
                      onChange={(e) => setSelectedModel(parseInt(e.target.value))}
                    >
                      {models.map(m => <option key={m.id} value={m.id}>{m.name} - {m.version}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Dataset</label>
                    <select
                      className="w-full border border-gray-300 rounded-lg p-3"
                      value={selectedDataset || ''}
                      onChange={(e) => setSelectedDataset(parseInt(e.target.value))}
                    >
                      {datasets.map(d => <option key={d.id} value={d.id}>{d.title}</option>)}
                    </select>
                  </div>
                </div>
                {metrics.length > 0 && (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={metrics}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="score" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          )}

          {activeTab === 'dashboard' && (
            <div>
              <h2 className="text-3xl font-bold mb-8">Dashboard</h2>
              <div className="grid grid-cols-3 gap-6">
                <StatCard title="Total Evaluations" value={evaluationHistory.length} />
                <StatCard title="Pending Reviews" value={anonymousQueries.length} />
                <StatCard title="Active Models" value={models.length} />
              </div>
            </div>
          )}
        </div>

        {/* Right Sidebar */}
        <div className={`relative transition-all duration-300 ${isHistoryOpen ? 'w-80' : 'w-12'}`}>
          <div className="absolute -left-5 top-6 z-10">
            <button
              onClick={() => setIsHistoryOpen(open => !open)}
              className="w-10 h-10 bg-white border rounded-full shadow flex items-center justify-center hover:bg-gray-50"
            >
              <span className={`${isHistoryOpen ? 'transform rotate-180' : ''} transition-transform`}>❯</span>
            </button>
          </div>
          <div className={`h-full bg-white border-l border-gray-200 p-6 overflow-auto transition-opacity duration-200 ${isHistoryOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
            <h3 className="text-lg font-bold mb-6">Evaluation History</h3>
            <div className="space-y-3">
              {evaluationHistory.map((evaluation) => (
                <div key={evaluation.id} className="border border-gray-200 rounded-lg p-3 text-sm hover:border-blue-300 transition-colors">
                  <div className="font-medium mb-1 truncate">{evaluation.prompt}</div>
                  <div className="text-gray-500 text-xs">{evaluation.status} • {evaluation.num_responses} candidates</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const NavItem = ({ icon, label, active, onClick }) => (
  <button
    className={`w-full text-left px-6 py-4 flex items-center gap-3 transition ${
      active ? 'bg-blue-600 text-white shadow-inner' : 'text-gray-300 hover:bg-slate-800'
    }`}
    onClick={onClick}
  >
    <span className="text-xl">{icon}</span>
    <span className="font-medium">{label}</span>
  </button>
);

const CandidateCard = ({ candidate, index, onRank }) => {
  const [rank, setRank] = useState(candidate.rank_by_evaluator || '');
  const [comment, setComment] = useState(candidate.evaluator_comment || '');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleRank = async () => {
    if (rank) {
      setIsSubmitting(true);
      await onRank(candidate.id, parseInt(rank));
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <h4 className="font-bold text-lg text-gray-800">Candidate {index + 1}</h4>
        <div className="flex gap-2 items-center">
          <input
            type="number"
            placeholder="Rank"
            className="w-20 border border-gray-300 rounded px-2 py-1 text-sm focus:ring-1 focus:ring-blue-500 outline-none"
            value={rank}
            onChange={(e) => setRank(e.target.value)}
          />
          <button
            className="bg-blue-600 text-white px-4 py-1 rounded text-sm hover:bg-blue-700 disabled:bg-gray-400"
            onClick={handleRank}
            disabled={isSubmitting || !rank}
          >
            {isSubmitting ? '...' : 'Save Rank'}
          </button>
        </div>
      </div>
      <div className="prose max-w-none text-gray-700 mb-4 bg-gray-50 p-4 rounded-lg border border-gray-100">
        {candidate.response_text}
      </div>
      <textarea
        className="w-full border border-gray-200 rounded p-3 text-sm focus:ring-1 focus:ring-blue-500 outline-none"
        placeholder="Add evaluation comments (strengths, weaknesses, hallucinations)..."
        rows="2"
        value={comment}
        onChange={(e) => setComment(e.target.value)}
      />
    </div>
  );
};

const QueryReviewCard = ({ query, onMarkHallucination }) => {
  const [notes, setNotes] = useState('');
  const [showDetails, setShowDetails] = useState(false);
  const [isProcessing, setIsProcessing] = useState(null); // 'hallucination' or 'accurate'

  const handleMark = async (type) => {
    setIsProcessing(type);
    await onMarkHallucination(query.response_id, type === 'hallucination', notes);
    setIsProcessing(null);
  };

  const hasReview = query.response_metadata?.hallucination_review;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold uppercase tracking-wider text-gray-400">User Query</span>
          {hasReview && (
            <span className={`text-xs font-bold px-2 py-1 rounded ${
              hasReview.is_hallucination ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
            }`}>
              {hasReview.is_hallucination ? 'HALLUCINATION' : 'ACCURATE'}
            </span>
          )}
        </div>
        <p className="text-gray-800 font-medium">{query.content}</p>
      </div>

      {query.response && (
        <div className="mb-4">
          <button 
            onClick={() => setShowDetails(!showDetails)}
            className="text-blue-600 text-sm font-medium flex items-center gap-1 hover:text-blue-800"
          >
            {showDetails ? 'Hide' : 'View'} Model Response {showDetails ? '↑' : '↓'}
          </button>
          {showDetails && (
            <div className="mt-2 p-4 bg-slate-50 border-l-4 border-blue-400 rounded text-gray-700 text-sm whitespace-pre-wrap">
              {query.response}
            </div>
          )}
        </div>
      )}

      <textarea
        className="w-full border border-gray-300 rounded p-3 text-sm mb-4 focus:ring-1 focus:ring-blue-500 outline-none"
        placeholder="Enter reasoning for your assessment..."
        rows="2"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />

      <div className="flex gap-3">
        <button
          className="flex-1 bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-bold hover:bg-red-600 hover:text-white transition-colors disabled:opacity-50"
          onClick={() => handleMark('hallucination')}
          disabled={!query.response_id || !!isProcessing}
        >
          {isProcessing === 'hallucination' ? 'Marking...' : 'Mark Hallucination'}
        </button>
        <button
          className="flex-1 bg-green-50 text-green-600 border border-green-200 px-4 py-2 rounded-lg text-sm font-bold hover:bg-green-600 hover:text-white transition-colors disabled:opacity-50"
          onClick={() => handleMark('accurate')}
          disabled={!query.response_id || !!isProcessing}
        >
          {isProcessing === 'accurate' ? 'Verifying...' : 'Mark Accurate'}
        </button>
      </div>
    </div>
  );
};

const StatCard = ({ title, value }) => (
  <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
    <div className="text-gray-500 text-xs font-bold uppercase tracking-widest mb-2">{title}</div>
    <div className="text-4xl font-extrabold text-slate-800">{value}</div>
  </div>
);

// Auth components (App/AuthWrapper) remain as provided...
const App = () => (
  <AuthProvider>
    <AuthWrapper />
  </AuthProvider>
);

const AuthWrapper = () => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return (
    <div className="flex items-center justify-center h-screen bg-gray-50">
      <div className="animate-pulse text-xl font-bold text-gray-400">Initializing Evaluator...</div>
    </div>
  );
  return isAuthenticated ? <MainApp /> : <AuthScreen />;
};

export default App;