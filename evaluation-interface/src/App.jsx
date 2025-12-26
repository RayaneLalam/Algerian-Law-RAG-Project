import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const API_BASE = 'http://localhost:5000/api/evaluation';

const App = () => {
  const [activeTab, setActiveTab] = useState('playground');
  const [query, setQuery] = useState('');
  const [numCandidates, setNumCandidates] = useState(3);
  const [goldenLabel, setGoldenLabel] = useState(''); // New state for Golden Label
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
      const res = await fetch(`${API_BASE}/history`);
      const data = await res.json();
      setEvaluationHistory(data.evaluations || []);
    } catch (err) {
      console.error('Error fetching history:', err);
    }
  };

  const fetchAnonymousQueries = async () => {
    try {
      const res = await fetch(`${API_BASE}/anonymous-queries`);
      const data = await res.json();
      setAnonymousQueries(data.queries || []);
    } catch (err) {
      console.error('Error fetching queries:', err);
    }
  };

  const fetchModels = async () => {
    try {
      const res = await fetch(`${API_BASE}/models`);
      const data = await res.json();
      setModels(data.models || []);
      if (data.models?.length > 0) setSelectedModel(data.models[0].id);
    } catch (err) {
      console.error('Error fetching models:', err);
    }
  };

  const fetchDatasets = async () => {
    try {
      const res = await fetch(`${API_BASE}/datasets`);
      const data = await res.json();
      setDatasets(data.datasets || []);
      if (data.datasets?.length > 0) setSelectedDataset(data.datasets[0].id);
    } catch (err) {
      console.error('Error fetching datasets:', err);
    }
  };

  const fetchMetrics = async () => {
    try {
      const res = await fetch(`${API_BASE}/metrics?model_version_id=${selectedModel}&dataset_id=${selectedDataset}`);
      const data = await res.json();
      setMetrics(data.metrics || []);
    } catch (err) {
      console.error('Error fetching metrics:', err);
    }
  };

  const generateAnswers = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: query,
          num_responses: numCandidates,
          model_version_id: selectedModel,
          golden_label: goldenLabel.trim() || null // Added golden_label to API call
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
      await fetch(`${API_BASE}/rank`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candidateId,
          rank: rank
        })
      });
      fetchEvaluationHistory();
    } catch (err) {
      console.error('Error ranking candidate:', err);
    }
  };

  const markHallucination = async (queryId, isHallucination, notes) => {
    try {
      await fetch(`${API_BASE}/mark-hallucination`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message_id: queryId,
          is_hallucination: isHallucination,
          notes: notes
        })
      });
      fetchAnonymousQueries();
    } catch (err) {
      console.error('Error marking hallucination:', err);
    }
  };

  const completeEvaluation = async () => {
    if (!currentEvaluation) return;

    try {
      await fetch(`${API_BASE}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          evaluation_id: currentEvaluation.id
        })
      });
      setCurrentEvaluation(null);
      setCandidates([]);
      setQuery('');
      setGoldenLabel(''); // Clear golden label on completion
      fetchEvaluationHistory();
    } catch (err) {
      console.error('Error completing evaluation:', err);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-slate-900 text-white">
        <div className="p-6">
          <h1 className="text-2xl font-bold">Evaluator UI</h1>
        </div>
        <nav className="mt-6">
          <NavItem icon="📊" label="Dashboard" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
          <NavItem icon="🎮" label="Evaluation Playground" active={activeTab === 'playground'} onClick={() => setActiveTab('playground')} />
          <NavItem icon="📋" label="User Queries Review" active={activeTab === 'queries'} onClick={() => setActiveTab('queries')} />
          <NavItem icon="⚖️" label="Model Comparison" active={activeTab === 'comparison'} onClick={() => setActiveTab('comparison')} />
          <NavItem icon="🎨" label="Dataset Builder" active={activeTab === 'dataset'} onClick={() => setActiveTab('dataset')} />
          <NavItem icon="🔒" label="Governance" active={activeTab === 'governance'} onClick={() => setActiveTab('governance')} />
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        <div className="flex-1 p-8 overflow-auto">
          {activeTab === 'playground' && (
            <div>
              <h2 className="text-3xl font-bold mb-8">Evaluation Playground</h2>

              <div className="bg-white rounded-lg shadow p-6 mb-6">
                <div className="grid grid-cols-2 gap-6 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Query</label>
                    <textarea
                      className="w-full border border-gray-300 rounded-lg p-3"
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
                      className="w-full border border-gray-300 rounded-lg p-3"
                      rows="4"
                      placeholder="Enter the ground truth/perfect response..."
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
                      min="1"
                      max="10"
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
                    className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                    onClick={generateAnswers}
                    disabled={loading || currentEvaluation}
                  >
                    {loading ? 'Generating...' : 'Generate Answers'}
                  </button>
                </div>
              </div>

              {candidates.length > 0 && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-xl font-bold">Rank Candidates (RLHF)</h3>
                    <button
                      className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                      onClick={completeEvaluation}
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

          {activeTab === 'queries' && (
            <div>
              <h2 className="text-3xl font-bold mb-8">Anonymous User Queries Review</h2>
              <div className="space-y-4">
                {anonymousQueries.map((q) => (
                  <QueryReviewCard
                    key={q.id}
                    query={q}
                    onMarkHallucination={markHallucination}
                  />
                ))}
                {anonymousQueries.length === 0 && (
                  <p className="text-gray-500">No queries to review</p>
                )}
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
                      {models.map(m => (
                        <option key={m.id} value={m.id}>{m.name} - {m.version}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Dataset</label>
                    <select
                      className="w-full border border-gray-300 rounded-lg p-3"
                      value={selectedDataset || ''}
                      onChange={(e) => setSelectedDataset(parseInt(e.target.value))}
                    >
                      {datasets.map(d => (
                        <option key={d.id} value={d.id}>{d.title}</option>
                      ))}
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

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-bold mb-4">Metric Details</h3>
                <div className="space-y-2">
                  {metrics.map((m, idx) => (
                    <div key={idx} className="flex justify-between p-3 border-b">
                      <span className="font-medium">{m.name}</span>
                      <span className="text-blue-600">{m.score.toFixed(3)}</span>
                    </div>
                  ))}
                  {metrics.length === 0 && (
                    <p className="text-gray-500">No metrics available</p>
                  )}
                </div>
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

          {activeTab === 'dataset' && (
            <div>
              <h2 className="text-3xl font-bold mb-8">Dataset Builder</h2>
              <p className="text-gray-600">Dataset management interface coming soon...</p>
            </div>
          )}

          {activeTab === 'governance' && (
            <div>
              <h2 className="text-3xl font-bold mb-8">Governance</h2>
              <p className="text-gray-600">Governance and compliance tools coming soon...</p>
            </div>
          )}
        </div>

        {/* Right Sidebar - Evaluation History */}
        <div className="w-80 bg-white border-l border-gray-200 p-6 overflow-auto">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold">Evaluation History</h3>
            <span className="text-gray-400">→</span>
          </div>

          {evaluationHistory.length === 0 ? (
            <p className="text-gray-500 text-sm">No evaluations yet</p>
          ) : (
            <div className="space-y-3">
              {evaluationHistory.map((evaluation) => (
                <div key={evaluation.id} className="border border-gray-200 rounded-lg p-3 text-sm">
                  <div className="font-medium mb-1 truncate">{evaluation.prompt}</div>
                  <div className="text-gray-500 text-xs">
                    {evaluation.status} • {evaluation.num_responses} candidates
                  </div>
                  <div className="text-gray-400 text-xs mt-1">
                    {new Date(evaluation.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const NavItem = ({ icon, label, active, onClick }) => (
  <button
    className={`w-full text-left px-6 py-3 flex items-center gap-3 transition ${
      active ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-slate-800'
    }`}
    onClick={onClick}
  >
    <span>{icon}</span>
    <span>{label}</span>
  </button>
);

const CandidateCard = ({ candidate, index, onRank }) => {
  const [rank, setRank] = useState(candidate.rank_by_evaluator || '');
  const [comment, setComment] = useState(candidate.evaluator_comment || '');

  const handleRank = () => {
    if (rank) {
      onRank(candidate.id, parseInt(rank));
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-start mb-4">
        <h4 className="font-bold text-lg">Candidate {index + 1}</h4>
        <div className="flex gap-2 items-center">
          <input
            type="number"
            min="1"
            max="10"
            placeholder="Rank"
            className="w-20 border border-gray-300 rounded px-2 py-1 text-sm"
            value={rank}
            onChange={(e) => setRank(e.target.value)}
          />
          <button
            className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
            onClick={handleRank}
          >
            Rank
          </button>
        </div>
      </div>
      <p className="text-gray-700 mb-3">{candidate.response_text}</p>
      <textarea
        className="w-full border border-gray-300 rounded p-2 text-sm"
        placeholder="Add evaluation comments..."
        rows="2"
        value={comment}
        onChange={(e) => setComment(e.target.value)}
      />
      {candidate.tokens && (
        <div className="text-xs text-gray-500 mt-2">Tokens: {candidate.tokens}</div>
      )}
    </div>
  );
};

const QueryReviewCard = ({ query, onMarkHallucination }) => {
  const [notes, setNotes] = useState('');
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <div className="font-medium mb-2">Query from Anonymous User</div>
          <p className="text-gray-600 text-sm mb-2">{query.content}</p>
          <button
            className="text-blue-600 text-sm hover:underline"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? 'Hide' : 'Show'} Response
          </button>
        </div>
      </div>

      {showDetails && query.response && (
        <div className="mb-4 p-3 bg-gray-50 rounded text-sm">
          <div className="font-medium mb-1">Model Response:</div>
          <p className="text-gray-700">{query.response}</p>
        </div>
      )}

      <textarea
        className="w-full border border-gray-300 rounded p-2 text-sm mb-3"
        placeholder="Add notes about hallucination..."
        rows="2"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />

      <div className="flex gap-2">
        <button
          className="bg-red-600 text-white px-4 py-2 rounded text-sm hover:bg-red-700"
          onClick={() => onMarkHallucination(query.id, true, notes)}
        >
          Mark as Hallucination
        </button>
        <button
          className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700"
          onClick={() => onMarkHallucination(query.id, false, notes)}
        >
          Mark as Accurate
        </button>
      </div>
    </div>
  );
};

const StatCard = ({ title, value }) => (
  <div className="bg-white rounded-lg shadow p-6">
    <div className="text-gray-500 text-sm mb-2">{title}</div>
    <div className="text-3xl font-bold text-blue-600">{value}</div>
  </div>
);

export default App;