import { useState } from 'react';
import { analyzeDocument } from '../services/api';

export const useUpload = () => {
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [phase, setPhase] = useState<'idle' | 'uploading' | 'processing'>('idle');
  const [isFileUploaded, setIsFileUploaded] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async (file: File, request: string) => {
    try {
      setLoading(true);
      setPhase('uploading');
      setUploadProgress(0);
      setError(null);
      setResult(null);
      setIsFileUploaded(false);

      const response = await analyzeDocument(
        file,
        request,
        (percent) => {
          setUploadProgress(percent);
          
          // When upload completes (100%), mark file as uploaded
          if (percent === 100) {
            setIsFileUploaded(true);
            setPhase('idle'); // Reset to idle so user can click button
            
            // Small delay then switch to processing (simulating backend work)
            setTimeout(() => {
              setPhase('processing');
            }, 500);
          }
        }
      );

      setResult(response);
      setPhase('idle');
    } catch (err) {
      console.error('Upload failed:', err);
      setError(err instanceof Error ? err.message : 'Analysis failed. Please try again.');
      setPhase('idle');
      setIsFileUploaded(false);
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  const resetUpload = () => {
    setResult(null);
    setError(null);
    setIsFileUploaded(false);
    setUploadProgress(0);
    setPhase('idle');
  };

  return {
    handleUpload,
    loading,
    uploadProgress,
    phase,
    isFileUploaded,
    result,
    error,
    resetUpload,
  };
};