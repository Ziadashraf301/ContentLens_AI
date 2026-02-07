/**
 * ChatInput Component
 * Multimodal input bar with support for text, file uploads, and audio recording
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import AudioRecorder from './AudioRecorder';
import FilePreview from './FilePreview';
import { FileAttachment, AudioRecordingData, MessageType } from '../types/chat';

interface ChatInputProps {
  onSend: (text: string, attachments: FileAttachment[]) => Promise<void>;
  disabled?: boolean;
  placeholder?: string;
}

const ALLOWED_FILE_TYPES = {
  'document': ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'],
  'image': ['image/png', 'image/jpeg', 'image/jpg'],
};

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled = false,
  placeholder = 'Type a message... (Shift+Enter for new line)',
}) => {
  const [text, setText] = useState('');
  const [attachments, setAttachments] = useState<FileAttachment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textInputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  /**
   * Handle text input change
   */
  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setText(value);
    
    // Auto-expand textarea based on content
    if (textInputRef.current) {
      textInputRef.current.style.height = 'auto';
      textInputRef.current.style.height = Math.min(
        textInputRef.current.scrollHeight,
        200
      ) + 'px';
    }
  };

  /**
   * Handle keyboard events (Enter to send, Shift+Enter for new line)
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  /**
   * Handle file selection and validation
   */
  const handleFileSelect = useCallback(
    (files: FileList | null, type: 'document' | 'image') => {
      if (!files) return;

      setError(null);

      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const allowedMimes = ALLOWED_FILE_TYPES[type];

        if (!allowedMimes.includes(file.type)) {
          setError(`Invalid file type for ${type}. Allowed: ${allowedMimes.join(', ')}`);
          continue;
        }

        // Read file and create preview
        const reader = new FileReader();
        reader.onload = (event) => {
          const fileAttachment: FileAttachment = {
            id: `file-${Date.now()}-${i}`,
            name: file.name,
            type,
            size: file.size,
            mimeType: file.type,
            file,
            preview: type === 'image' ? (event.target?.result as string) : undefined,
          };

          setAttachments((prev) => [...prev, fileAttachment]);
        };

        reader.onerror = () => {
          setError(`Failed to read file: ${file.name}`);
        };

        if (type === 'image') {
          reader.readAsDataURL(file);
        } else {
          reader.readAsDataURL(file); // For preview/metadata
        }
      }

      // Reset file input
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (imageInputRef.current) imageInputRef.current.value = '';
    },
    []
  );

  /**
   * Handle document upload
   */
  const handleDocumentUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files, 'document');
  };

  /**
   * Handle image upload
   */
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files, 'image');
  };

  /**
   * Handle audio recording completion
   */
  const handleAudioRecordingComplete = useCallback(
    (data: AudioRecordingData) => {
      const audioAttachment: FileAttachment = {
        id: `audio-${Date.now()}`,
        name: `audio-${Date.now()}.webm`,
        type: 'audio',
        size: data.blob.size,
        mimeType: data.mimeType,
        file: data.blob,
        preview: URL.createObjectURL(data.blob),
      };

      setAttachments((prev) => [...prev, audioAttachment]);
      setError(null);
    },
    []
  );

  /**
   * Remove attachment
   */
  const handleRemoveAttachment = useCallback((fileId: string) => {
    setAttachments((prev) => prev.filter((att) => att.id !== fileId));
  }, []);

  /**
   * Send message
   */
  const handleSend = async () => {
    if (!text.trim() && attachments.length === 0) {
      setError('Please enter a message or attach a file.');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      await onSend(text, attachments);

      // Clear input after successful send
      setText('');
      setAttachments([]);
      if (textInputRef.current) {
        textInputRef.current.style.height = 'auto';
        textInputRef.current.focus();
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to send message'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-input">
      {/* Error message */}
      {error && (
        <div className="chat-input__error">
          <span>⚠️ {error}</span>
          <button
            className="chat-input__error-close"
            onClick={() => setError(null)}
            aria-label="Close error"
          >
            ✕
          </button>
        </div>
      )}

      {/* File previews */}
      {attachments.length > 0 && (
        <div className="chat-input__attachments">
          {attachments.map((attachment) => (
            <FilePreview
              key={attachment.id}
              file={attachment}
              onRemove={handleRemoveAttachment}
            />
          ))}
        </div>
      )}

      {/* Input area */}
      <div className="chat-input__container">
        {/* Text input */}
        <textarea
          ref={textInputRef}
          className="chat-input__text"
          value={text}
          onChange={handleTextChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isLoading}
          rows={1}
          aria-label="Message input"
        />

        {/* Action buttons */}
        <div className="chat-input__actions">
          {/* Audio recorder */}
          <AudioRecorder
            onRecordingComplete={handleAudioRecordingComplete}
            onRecordingStart={() => {}}
            onRecordingStop={() => {}}
          />

          {/* Document upload */}
          <button
            className="chat-input__action-btn chat-input__action-btn--file"
            onClick={() => fileInputRef.current?.click()}
            title="Upload document (PDF, DOCX, TXT)"
            aria-label="Upload document"
            disabled={disabled || isLoading}
          >
            📄
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx,.doc,.txt"
            onChange={handleDocumentUpload}
            className="chat-input__file-input"
            aria-label="Upload document file"
          />

          {/* Image upload */}
          <button
            className="chat-input__action-btn chat-input__action-btn--image"
            onClick={() => imageInputRef.current?.click()}
            title="Upload image (PNG, JPG)"
            aria-label="Upload image"
            disabled={disabled || isLoading}
          >
            🖼️
          </button>
          <input
            ref={imageInputRef}
            type="file"
            multiple
            accept="image/png,image/jpeg,image/jpg"
            onChange={handleImageUpload}
            className="chat-input__file-input"
            aria-label="Upload image file"
          />

          {/* Send button */}
          <button
            className="chat-input__send-btn"
            onClick={handleSend}
            disabled={disabled || isLoading || (!text.trim() && attachments.length === 0)}
            title="Send message"
            aria-label="Send message"
          >
            {isLoading ? (
              <span className="chat-input__send-spinner">⏳</span>
            ) : (
              '➤'
            )}
          </button>
        </div>
      </div>

      {/* Helper text */}
      <div className="chat-input__hint">
        Supports text, images, documents, and voice messages
      </div>
    </div>
  );
};

export default ChatInput;
