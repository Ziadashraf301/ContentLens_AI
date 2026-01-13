// Use REACT_APP_API_URL for explicit override (e.g., https://app.example.com).
// When not set, use a relative path so the browser will call the current origin
// (prevents exposing raw deployment IPs such as http://174.129.170.30:3000/).
const API_BASE = (process.env.REACT_APP_API_URL || '').replace(/\/$/, '');

export const analyzeDocument = async (file: File, request: string): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_request', request);

  const endpoint = API_BASE ? `${API_BASE}/api/process-document` : '/api/process-document';
  // If API_BASE is empty this will result in '/api/process-document' (same-origin)
  const response = await fetch(endpoint, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Analysis failed: ${response.status} ${text}`);
  }

  return response.json();
};