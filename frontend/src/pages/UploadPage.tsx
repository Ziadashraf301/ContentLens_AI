import React from 'react';
import { FileUploader } from '../components/FileUploader';

interface Props { onUpload: (file: File, req: string) => void; loading: boolean; }

export const UploadPage: React.FC<Props> = ({ onUpload, loading }) => (
  <div className="page fade-in">
    <h2>Upload Media Brief</h2>
    <p>Our AI agents will extract, summarize, and analyze your document.</p>
    <FileUploader onUpload={onUpload} loading={loading} />
  </div>
);