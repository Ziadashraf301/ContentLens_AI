import { useState } from 'react';
import { analyzeDocument } from '../services/api';
import { AnalysisResponse } from '../types/api';

export const useUpload = () => {
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [phase, setPhase] = useState<'idle' | 'uploading' | 'processing'>('idle');
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async (file: File, request: string) => {
    setLoading(true);
    setError(null);
    setUploadProgress(0);
    setPhase('uploading');

    try {
      const data = await analyzeDocument(file, request, (percent) => {
        setUploadProgress(percent);
        if (percent >= 100) {
          setPhase('processing');
        }
      });

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setLoading(false);
      setPhase('idle');
      setUploadProgress(0);
    }
  };

  return { handleUpload, loading, uploadProgress, phase, result, error };
};