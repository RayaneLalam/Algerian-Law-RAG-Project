import { simulateFetch, generateDummyAnswers } from './mock';

export const fetchGeneratedAnswers = async (query, numAnswers) => {
  // In real app: return axios.post('/api/generate', { query, numAnswers });
  const dummyAnswers = generateDummyAnswers(query, numAnswers);
  await simulateFetch(dummyAnswers);
  return dummyAnswers;
};

export const saveRanking = async (payload) => {
  // In real app: return axios.post('/api/ranking', payload);
  await simulateFetch({ status: 'saved' });
  return { success: true };
};