import React, { useState } from 'react';

interface Props {
  onUpload: (file: File, request: string) => void;
  loading: boolean;
  uploadProgress?: number;
  phase?: 'idle' | 'uploading' | 'processing';
}

export const FileUploader: React.FC<Props> = ({ onUpload, loading, uploadProgress = 0, phase = 'idle' }) => {
  const [file, setFile] = useState<File | null>(null);
  const [request, setRequest] = useState('');

  return (
    <div className="uploader-container">
      <input
        type="file"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />

      <textarea
        value={request}
        onChange={(e) => setRequest(e.target.value)}
        placeholder="Optional instructions (leave empty to only extract text)"
        disabled={!file}
      />

      {phase !== 'idle' && (
        <div className="upload-progress">
          <div className="progress-bar" style={{ width: `${uploadProgress}%` }} />
          <div className="progress-label">
            {phase === 'uploading' ? `Uploading ${uploadProgress}%` : 'Processing...'}
          </div>
        </div>
      )}

      <button
        onClick={() => file && onUpload(file, request)}
        disabled={loading || !file}
      >
        {loading ? 'Processing...' : 'Run Analysis'}
      </button>
    </div>
  );
};