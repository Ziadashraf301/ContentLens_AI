import React, { useState, useRef, useCallback } from 'react';
import AudioRecorder from './AudioRecorder';
import FilePreview from './FilePreview';
import { FileAttachment, AudioRecordingData } from '../types/chat';
import '../styles/chat.css';

interface ChatInputProps {
  onSend: (text: string, attachments: FileAttachment[], isLeadSearch?: boolean) => Promise<void>;
  disabled?: boolean;
  placeholder?: string;
}

const ALLOWED_MIME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
  'image/png',
  'image/jpeg',
  'image/jpg'
];

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled = false,
  placeholder = 'Ask anything related to your work...',
}) => {
  const [text, setText] = useState('');
  const [attachments, setAttachments] = useState<FileAttachment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLiveVoiceActive, setIsLiveVoiceActive] = useState(false);
  
  const textInputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    if (textInputRef.current) {
      textInputRef.current.style.height = 'auto';
      textInputRef.current.style.height = Math.min(textInputRef.current.scrollHeight, 120) + 'px';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(false);
    }
  };

  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files) return;
    setError(null);

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (!ALLOWED_MIME_TYPES.includes(file.type)) {
        setError(`Unsupported file type: ${file.name}. Please upload PDF, DOCX, TXT, PNG, or JPG.`);
        continue;
      }

      const isImage = file.type.startsWith('image/');
      const type = isImage ? 'image' : 'document';

      const reader = new FileReader();
      reader.onload = (event) => {
        const fileAttachment: FileAttachment = {
          id: `file-${Date.now()}-${i}`,
          name: file.name,
          type,
          size: file.size,
          mimeType: file.type,
          file,
          preview: isImage ? (event.target?.result as string) : undefined,
        };
        setAttachments((prev) => [...prev, fileAttachment]);
      };
      reader.readAsDataURL(file);
    }

    if (fileInputRef.current) fileInputRef.current.value = '';
  }, []);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleAudioRecordingComplete = useCallback((data: AudioRecordingData) => {
    // In Sprint 1, we add the audio note to attachments.
    // In Sprint 3, we will use backend ASR to automatically transcribe this into text!
    const audioAttachment: FileAttachment = {
      id: `audio-${Date.now()}`,
      name: `voice-note-${Date.now()}.webm`,
      type: 'audio',
      size: data.blob.size,
      mimeType: data.mimeType,
      file: new File([data.blob], `voice-note-${Date.now()}.webm`, { type: data.mimeType }),
      preview: URL.createObjectURL(data.blob),
    };

    setAttachments((prev) => [...prev, audioAttachment]);
    setError(null);
  }, []);

  const handleRemoveAttachment = useCallback((fileId: string) => {
    setAttachments((prev) => prev.filter((att) => att.id !== fileId));
  }, []);

  const handleSend = async (isLeadSearch = false) => {
    if (!text.trim() && attachments.length === 0) {
      setError('Please enter a query or upload a file.');
      return;
    }

    const originalText = text;
    const originalAttachments = attachments;

    try {
      setIsLoading(true);
      setError(null);

      // Clear input instantly to return placeholder to "Ask anything..."
      setText('');
      setAttachments([]);
      if (textInputRef.current) {
        textInputRef.current.style.height = 'auto';
      }

      await onSend(originalText, originalAttachments, isLeadSearch);
    } catch (err) {
      // Restore input if message failed to send
      setText(originalText);
      setAttachments(originalAttachments);
      setError(err instanceof Error ? err.message : 'Failed to process request');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleLiveVoice = () => {
    setIsLiveVoiceActive(prev => !prev);
    // Placeholder message for Live Voice toggle in Sprint 1
    if (!isLiveVoiceActive) {
      alert("Live Voice activated (STT/TTS streaming will be implemented in Sprint 3).");
    }
  };

  return (
    <div className="chat-input-wrapper">
      {error && (
        <div className="chat-input__error">
          <span>⚠️ {error}</span>
          <button className="chat-input__error-close" onClick={() => setError(null)}>✕</button>
        </div>
      )}

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

      <div className="sales-chat-container">
        <textarea
          ref={textInputRef}
          className="sales-chat-textarea"
          value={text}
          onChange={handleTextChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isLoading}
          rows={1}
        />

        <div className="sales-chat-toolbar">
          <div className="sales-chat-actions-left">
            {/* Upload Button (+) */}
            <button
              className="sales-btn sales-btn-circle"
              onClick={handleUploadClick}
              title="Upload PDF, DOCX, TXT, or Image"
              disabled={disabled || isLoading}
            >
              ＋
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.doc,.txt,image/png,image/jpeg,image/jpg"
              onChange={(e) => handleFileSelect(e.target.files)}
              style={{ display: 'none' }}
            />

            {/* Search Leads Button */}
            <button
              className="sales-btn sales-btn-search"
              onClick={() => handleSend(true)}
              title="Search Leads"
              disabled={disabled || isLoading || !text.trim()}
            >
              🔍 Search Leads
            </button>
          </div>

          <div className="sales-chat-actions-right">
            {/* Record Voice Button */}
            <div className="sales-recorder-wrapper">
              <AudioRecorder
                onRecordingComplete={handleAudioRecordingComplete}
              />
            </div>

            {/* Live Voice Button */}
            <button
              className={`sales-btn sales-btn-live-voice ${isLiveVoiceActive ? 'active' : ''}`}
              onClick={toggleLiveVoice}
              title="Toggle Live Voice note"
            >
              {isLiveVoiceActive ? '⏸️ Live Voice' : '▶️ Live Voice'}
            </button>

            {/* Send Query Button */}
            <button
              className="sales-btn sales-btn-send"
              onClick={() => handleSend(false)}
              disabled={disabled || isLoading || (!text.trim() && attachments.length === 0)}
            >
              {isLoading ? '⏳' : '➤'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
