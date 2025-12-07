// Simulate API latency
export const simulateFetch = (data, delay = 800) => {
  return new Promise(resolve => setTimeout(() => resolve(data), delay));
};

// Dummy LLM candidate answers generator
export const generateDummyAnswers = (query, n) => {
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