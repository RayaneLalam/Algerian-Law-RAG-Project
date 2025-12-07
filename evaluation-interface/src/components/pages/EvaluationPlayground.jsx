import React from 'react';

const EvaluationPlayground = ({ 
  query, setQuery, 
  numAnswers, setNumAnswers, 
  candidates, 
  handleGenerateAnswers, isGenerating, 
  moveCandidate, 
  referenceAnswer, setReferenceAnswer, 
  handleSaveRanking 
}) => {
  return (
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
                    >▲</button>
                    <span className="text-sm font-bold text-center">{candidate.rank}</span>
                    <button
                      onClick={() => moveCandidate(index, 'down')}
                      disabled={index === candidates.length - 1}
                      className="text-gray-500 hover:text-blue-600 disabled:text-gray-300"
                    >▼</button>
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-medium text-blue-600">{candidate.modelId}</span>
                      <span className="text-xs text-gray-500">Confidence: {(candidate.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-sm mb-2">{candidate.text}</p>
                    <div className="flex gap-2 flex-wrap">
                      {candidate.citations.map(cite => (
                        <span key={cite} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">{cite}</span>
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
};

export default EvaluationPlayground;