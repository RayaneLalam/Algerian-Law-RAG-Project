import { useState } from 'react';
import { fetchGeneratedAnswers, saveRanking } from '../api/evaluations';

export const useEvaluations = (onSaveDataset) => {
  const [query, setQuery] = useState('');
  const [numAnswers, setNumAnswers] = useState(3);
  const [candidates, setCandidates] = useState([]);
  const [referenceAnswer, setReferenceAnswer] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [evaluationHistory, setEvaluationHistory] = useState([]);

  const handleGenerateAnswers = async () => {
    if (!query.trim()) return;
    setIsGenerating(true);
    
    try {
      const data = await fetchGeneratedAnswers(query, numAnswers);
      setCandidates(data);
      
      // Add to history
      setEvaluationHistory(prev => [{
        id: Date.now(),
        query,
        numCandidates: numAnswers,
        timestamp: new Date().toISOString()
      }, ...prev].slice(0, 10));
    } catch (error) {
      console.error("Failed to generate answers", error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveRanking = async () => {
    try {
      await saveRanking({
        query,
        candidates: candidates.map(c => ({ id: c.id, rank: c.rank })),
        reference_answer: referenceAnswer
      });
      
      // Callback to update dataset state in parent/other hook
      if (referenceAnswer.trim() && onSaveDataset) {
        onSaveDataset({
          id: Date.now(),
          query,
          referenceAnswer,
          topCandidate: candidates[0],
          timestamp: new Date().toISOString()
        });
      }
      
      alert('Ranking and reference answer saved!');
    } catch (error) {
      console.error("Failed to save ranking", error);
    }
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

  return {
    query, setQuery,
    numAnswers, setNumAnswers,
    candidates, setCandidates,
    referenceAnswer, setReferenceAnswer,
    isGenerating,
    evaluationHistory,
    handleGenerateAnswers,
    handleSaveRanking,
    moveCandidate
  };
};