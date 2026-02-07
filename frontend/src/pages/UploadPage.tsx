import React from 'react';
import { useUpload } from '../hooks/useUpload';
import { FileUploader } from '../components/FileUploader';
import { ResultCard } from '../components/ResultCard';

/**
 * UploadPage Component
 * Handles document upload and initial analysis
 * Users can upload documents here to start the ContentLens AI workflow
 */
const UploadPage: React.FC = () => {
  const { 
    handleUpload, 
    loading, 
    uploadProgress, 
    phase, 
    isFileUploaded, 
    result, 
    error 
  } = useUpload();

  return (
    <div className="upload-page">
      <header className="upload-page__header">
        <div className="upload-page__container">
          <h1>ContentLens AI</h1>
          <p>Intelligent Document Analysis Platform</p>
        </div>
      </header>

      <main className="upload-page__main">
        <div className="upload-page__container">
          <section className="upload-page__section">
            <h2>Upload Your Document</h2>
            <p>Our AI agents will extract, summarize, and analyze your content.</p>
            
            <FileUploader 
              onUpload={handleUpload} 
              loading={loading} 
              uploadProgress={uploadProgress} 
              phase={phase}
              isFileUploaded={isFileUploaded}
            />
            
            {error && (
              <div className="upload-page__error">
                <span>⚠️ {error}</span>
              </div>
            )}
          </section>

          {result && (
            <section className="upload-page__section upload-page__section--results">
              <h2>Analysis Results</h2>
              <ResultCard data={result} />
            </section>
          )}
        </div>
      </main>
    </div>
  );
};

export default UploadPage;