// //API client configuration


// const API_BASE_URL = '/api';

// export const apiClient = {
//   async get(endpoint) {
//     const response = await fetch(`${API_BASE_URL}${endpoint}`);
//     if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
//     return response.json();
//   },

//   async post(endpoint, data) {
//     const response = await fetch(`${API_BASE_URL}${endpoint}`, {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify(data)
//     });
//     if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
//     return response.json();
//   }
// };
