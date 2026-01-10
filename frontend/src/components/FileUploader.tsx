import React, { useState } from 'react';

interface Props {
  onUpload: (file: File, request: string) => void;
  loading: boolean;
}

export const FileUploader: React.FC<Props> = ({ onUpload, loading }) => {
  const [file, setFile] = useState<File | null>(null);
  const [request, setRequest] = useState('Analyze this brief');

  return (
    <div className="uploader-container">
      <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      <textarea 
        value={request} 
        onChange={(e) => setRequest(e.target.value)}
        placeholder="Instructions (e.g., Translate to Arabic)"
      />
      <button onClick={() => file && onUpload(file, request)} disabled={loading || !file}>
        {loading ? 'Agents working...' : 'Run Analysis'}
      </button>
    </div>
  );
};