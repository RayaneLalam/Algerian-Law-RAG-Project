import { useState } from 'react';
import { fetchGeneratedAnswers, saveRanking } from '../api/evaluations';

export const useEvaluations = (onSaveDataset) => {
  const [query, setQuery] = useState('');
  const [numAnswers, setNumAnswers] = useState(3);
  const [candidates, setCandidates] = useState([]);
  const [referenceAnswer, setReferenceAnswer] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [evaluationHistory, setEvaluationHistory] = useState([]);
  const [currentEvaluationId, setCurrentEvaluationId] = useState(null);

  const handleGenerateAnswers = async () => {
    if (!query.trim()) return;
    setIsGenerating(true);
    
    try {
      const data = await fetchGeneratedAnswers(query, numAnswers);
      setCandidates(data);
      
      // Extract evaluationId from the first candidate (they all share the same one)
      if (data.length > 0 && data[0].evaluationId) {
        setCurrentEvaluationId(data[0].evaluationId);
      }
      
      // Add to history
      setEvaluationHistory(prev => [{
        id: Date.now(),
        query,
        numCandidates: numAnswers,
        timestamp: new Date().toISOString()
      }, ...prev].slice(0, 10));
    } catch (error) {
      console.error("Failed to generate answers", error);
      alert('Failed to generate answers. Check console for details.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveRanking = async () => {
    if (!currentEvaluationId) {
      alert('No evaluation ID found. Please generate answers first.');
      return;
    }

    try {
      // Prepare rankings payload with the correct structure
      const rankings = candidates.map(c => ({
        candidate_id: c.id,
        rank: c.rank,
        comment: referenceAnswer.trim() ? `Reference: ${referenceAnswer}` : ''
      }));

      await saveRanking({
        evaluationId: currentEvaluationId,
        rankings: rankings,
        finalize: true
      });
      
      // Callback to update dataset state in parent/other hook
      if (referenceAnswer.trim() && onSaveDataset) {
        onSaveDataset({
          id: currentEvaluationId,
          query,
          referenceAnswer,
          topCandidate: candidates[0],
          timestamp: new Date().toISOString()
        });
      }
      
      alert('Ranking and reference answer saved successfully!');
      
      // Reset state after successful save
      setReferenceAnswer('');
    } catch (error) {
      console.error("Failed to save ranking", error);
      alert('Failed to save ranking. Check console for details.');
    }
  };

  const moveCandidate = (index, direction) => {
    const newCandidates = [...candidates];
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (newIndex < 0 || newIndex >= newCandidates.length) return;
    
    // Swap candidates
    [newCandidates[index], newCandidates[newIndex]] = [newCandidates[newIndex], newCandidates[index]];
    
    // Update ranks to reflect new positions
    newCandidates.forEach((c, i) => c.rank = i + 1);
    setCandidates(newCandidates);
  };

  return {
    query, setQuery,
    numAnswers, setNumAnswers,
    candidates, setCandidates,
    referenceAnswer, setReferenceAnswer,
    isGenerating,
    evaluationHistory,
    currentEvaluationId,
    handleGenerateAnswers,
    handleSaveRanking,
    moveCandidate
  };
};