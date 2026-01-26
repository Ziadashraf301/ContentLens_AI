// Use REACT_APP_API_URL for explicit override (e.g., https://app.example.com).
// When not set, use a relative path so the browser will call the current origin
// (prevents exposing raw deployment IPs such as http://174.129.170.30:3000/).
const API_BASE = (process.env.REACT_APP_API_URL || '').replace(/\/$/, '');

export const analyzeDocument = (
  file: File,
  request: string,
  onProgress?: (percent: number) => void,
): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_request', request);
  // If request is empty, signal backend to run extractor+router flow
  formData.append('extract_only', String(request.trim() === ''));

  const endpoint = API_BASE ? `${API_BASE}/api/process-document` : '/api/process-document';

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', endpoint);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        const percent = Math.round((e.loaded / e.total) * 100);
        onProgress(percent);
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const json = JSON.parse(xhr.responseText || '{}');
          resolve(json);
        } catch (err) {
          reject(new Error('Invalid JSON response'));
        }
      } else {
        reject(new Error(`Analysis failed: ${xhr.status} ${xhr.statusText}`));
      }
    };

    xhr.onerror = () => reject(new Error('Network error during upload'));
    xhr.ontimeout = () => reject(new Error('Upload timed out'));

    xhr.send(formData);
  });
};