/**
 * AudioRecorder Component
 * Handles microphone input for audio messages
 */

import React, { useState, useRef, useCallback } from 'react';
import { AudioRecordingData } from '../types/chat';

interface AudioRecorderProps {
  onRecordingComplete: (data: AudioRecordingData) => void;
  onRecordingStart?: () => void;
  onRecordingStop?: () => void;
}

export const AudioRecorder: React.FC<AudioRecorderProps> = ({
  onRecordingComplete,
  onRecordingStart,
  onRecordingStop,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startTimeRef = useRef<number>(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Start recording audio from microphone
   */
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });

      chunksRef.current = [];
      startTimeRef.current = Date.now();
      setDuration(0);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const recordingDuration = duration;

        // Clean up stream
        streamRef.current?.getTracks().forEach((track) => track.stop());

        onRecordingComplete({
          blob: audioBlob,
          duration: recordingDuration,
          mimeType: 'audio/webm',
        });

        // Reset state
        setIsRecording(false);
        setDuration(0);
        if (timerRef.current) {
          clearInterval(timerRef.current);
        }
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
      onRecordingStart?.();

      // Timer to track duration
      timerRef.current = setInterval(() => {
        setDuration((prev) => prev + 1);
      }, 1000);
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Unable to access microphone. Please check permissions.');
    }
  }, [duration, onRecordingComplete, onRecordingStart]);

  /**
   * Stop recording and process audio
   */
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      onRecordingStop?.();
    }
  }, [isRecording, onRecordingStop]);

  /**
   * Format duration as MM:SS
   */
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="audio-recorder">
      {isRecording ? (
        <>
          <button
            className="audio-recorder__stop-btn"
            onClick={stopRecording}
            title="Stop recording"
            aria-label="Stop recording"
          >
            <span className="audio-recorder__stop-icon">⛔</span>
          </button>
          <span className="audio-recorder__duration">
            {formatDuration(duration)}
          </span>
          <span className="audio-recorder__indicator">
            <span className="audio-recorder__pulse"></span>
            Recording...
          </span>
        </>
      ) : (
        <button
          className="audio-recorder__start-btn"
          onClick={startRecording}
          title="Start recording audio"
          aria-label="Start recording"
        >
          <span className="audio-recorder__icon">🎤</span>
        </button>
      )}
    </div>
  );
};

export default AudioRecorder;
