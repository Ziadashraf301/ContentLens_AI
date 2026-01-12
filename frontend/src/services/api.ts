const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const analyzeDocument = async (file: File, request: string): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_request', request);  // 

  const response = await fetch(`${API_URL}/api/process-document`, {  
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Analysis failed: ${response.status} ${text}`);
  }

  return response.json();
};