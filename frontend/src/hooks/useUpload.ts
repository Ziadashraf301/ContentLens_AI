import { useState } from 'react';
import { analyzeDocument } from '../services/api';
import { AnalysisResponse } from '../types/api';

export const useUpload = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async (file: File, request: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeDocument(file, request);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return { handleUpload, loading, result, error };
};