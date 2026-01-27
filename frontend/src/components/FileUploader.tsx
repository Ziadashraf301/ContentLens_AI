import React, { useState } from 'react';

interface Props {
  onUpload: (file: File, request: string) => void;
  loading: boolean;
  uploadProgress?: number;
  phase?: 'idle' | 'uploading' | 'processing';
  isFileUploaded?: boolean;
}

export const FileUploader: React.FC<Props> = ({ 
  onUpload, 
  loading, 
  uploadProgress = 0, 
  phase = 'idle',
  isFileUploaded = false 
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [request, setRequest] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
  };

  return (
    <div className="uploader-container">
      <h2>Upload Document</h2>
      
      <input
        type="file"
        onChange={handleFileChange}
        disabled={loading}
        accept=".pdf,.doc,.docx,.txt"
      />

      {phase === 'uploading' && (
        <div className="upload-progress">
          <div className="progress-bar" style={{ width: `${uploadProgress}%` }} />
          <div className="progress-label">
            Uploading: {uploadProgress}%
          </div>
        </div>
      )}

      {isFileUploaded && phase === 'idle' && (
        <div className="upload-success">
          ✓ File uploaded successfully! You can now run the analysis.
        </div>
      )}

      <textarea
        value={request}
        onChange={(e) => setRequest(e.target.value)}
        placeholder="Optional instructions (e.g., 'Extract key points and translate to Arabic')"
        disabled={!isFileUploaded || loading}
      />

      <button
        onClick={() => file && onUpload(file, request)}
        disabled={loading || !isFileUploaded}
        className={loading ? 'processing' : ''}
      >
        {phase === 'processing' ? (
          <>
            <div className="spinner-small"></div>
            Processing...
          </>
        ) : (
          'Run Analysis'
        )}
      </button>
    </div>
  );
};