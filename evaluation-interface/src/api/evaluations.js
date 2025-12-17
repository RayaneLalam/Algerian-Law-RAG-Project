import { simulateFetch, generateDummyAnswers } from './mock';

// Configuration
const API_BASE_URL = 'http://127.0.0.1:5000/evaluation'; // Adjust if your blueprint is mounted differently

export const fetchGeneratedAnswers = async (query, numAnswers, modelVersionId = 'default-model-v1') => {
  try {
    // Step 1: Create evaluation
    const createResponse = await fetch(`${API_BASE_URL}/evaluations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_version_id: modelVersionId,
        prompt: query,
        num_responses: numAnswers,
        evaluator_id: null, // Optional: add evaluator tracking
        dataset_example_id: null // Optional: link to dataset
      })
    });

    if (!createResponse.ok) {
      throw new Error('Failed to create evaluation');
    }

    const { evaluation_id } = await createResponse.json();

    // Step 2: Generate candidates
    const generateResponse = await fetch(`${API_BASE_URL}/evaluations/${evaluation_id}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_responses: numAnswers })
    });

    if (!generateResponse.ok) {
      throw new Error('Failed to generate candidates');
    }

    const { candidate_ids } = await generateResponse.json();

    // Step 3: Fetch the evaluation with all candidates
    const detailsResponse = await fetch(`${API_BASE_URL}/evaluations/${evaluation_id}`);
    
    if (!detailsResponse.ok) {
      throw new Error('Failed to fetch evaluation details');
    }

    const { evaluation, candidates } = await detailsResponse.json();

    // Transform backend format to match frontend expectations
    return candidates.map((candidate, index) => ({
      id: candidate.id,
      text: candidate.response_text,
      modelId: candidate.model_version_id,
      confidence: candidate.response_json ? JSON.parse(candidate.response_json).mock_variant / 10 : 0.8,
      citations: [], // Backend doesn't provide citations yet
      rank: index + 1,
      evaluationId: evaluation_id, // Store for later ranking submission
      metadata: candidate.metadata
    }));

  } catch (error) {
    console.error('Error fetching generated answers:', error);
    // Fallback to dummy data if API fails
    console.warn('Falling back to dummy data');
    const dummyAnswers = generateDummyAnswers(query, numAnswers);
    await simulateFetch(dummyAnswers);
    return dummyAnswers;
  }
};

export const saveRanking = async (payload) => {
  try {
    // payload should have structure: { evaluationId, rankings: [{candidate_id, rank, comment}] }
    const { evaluationId, rankings, finalize = true } = payload;

    if (!evaluationId || !rankings || rankings.length === 0) {
      throw new Error('Invalid ranking payload');
    }

    const response = await fetch(`${API_BASE_URL}/evaluations/${evaluationId}/rank`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ranks: rankings.map(r => ({
          candidate_id: r.candidate_id || r.id,
          rank: r.rank,
          comment: r.comment || ''
        })),
        finalize: finalize
      })
    });

    if (!response.ok) {
      throw new Error('Failed to save ranking');
    }

    const result = await response.json();
    return { success: true, ...result };

  } catch (error) {
    console.error('Error saving ranking:', error);
    // Fallback to mock behavior
    console.warn('Falling back to mock save');
    await simulateFetch({ status: 'saved' });
    return { success: true };
  }
};

// Additional helper: Fetch existing evaluation
export const fetchEvaluation = async (evaluationId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/evaluations/${evaluationId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch evaluation');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching evaluation:', error);
    throw error;
  }
};

// Additional helper: Check API health
export const checkAPIHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch (error) {
    console.error('API health check failed:', error);
    return false;
  }
};