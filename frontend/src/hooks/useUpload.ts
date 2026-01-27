import { useState } from 'react';
import { analyzeDocument } from '../services/api';

export const useUpload = () => {
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [phase, setPhase] = useState<'idle' | 'uploading' | 'processing'>('idle');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async (file: File, request: string) => {
    try {
      setLoading(true);
      setPhase('uploading');
      setUploadProgress(0);
      setError(null);
      setResult(null);

      const response = await analyzeDocument(
        file,
        request,
        (percent) => {
          setUploadProgress(percent);
          // Switch to processing phase when upload completes
          if (percent === 100) {
            setPhase('processing');
          }
        }
      );

      setResult(response);
      setPhase('idle');
    } catch (err) {
      console.error('Upload failed:', err);
      setError(err instanceof Error ? err.message : 'Analysis failed. Please try again.');
      setPhase('idle');
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  return {
    handleUpload,
    loading,
    uploadProgress,
    phase,
    result,
    error,
  };
};