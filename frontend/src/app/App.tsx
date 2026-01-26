import React from 'react';
import { useUpload } from '../hooks/useUpload';
import { FileUploader } from '../components/FileUploader';
import { ResultCard } from '../components/ResultCard';

const App: React.FC = () => {
  const { handleUpload, loading, uploadProgress, phase, result, error } = useUpload();

  return (
    <div className="main-app">
      <header><h1>ContentLens AI</h1></header>
      <main>
        <FileUploader onUpload={handleUpload} loading={loading} uploadProgress={uploadProgress} phase={phase} />
        {error && <p className="error">{error}</p>}
        {result && <ResultCard data={result} />}
      </main>
    </div>
  );
};

export default App;