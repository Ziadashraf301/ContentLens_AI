/**
 * ChatMessage Component
 * Displays individual messages in the chat (user & AI)
 */

import React, { useState, useCallback } from 'react';
import { ChatMessage as ChatMessageType } from '../types/chat';

interface ChatMessageProps {
  message: ChatMessageType;
  onRetry?: (messageId: string) => void;
  onRegenerateClick?: () => void;
  isLastMessage?: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onRetry,
  onRegenerateClick,
  isLastMessage,
}) => {
  const [copied, setCopied] = useState(false);

  const isUserMessage = message.role === 'user';
  const isStreaming = isLastMessage && !isUserMessage && message.status === 'sending';

  /**
   * Copy message text to clipboard
   */
  const handleCopyText = useCallback(() => {
    if (message.text) {
      navigator.clipboard.writeText(message.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [message.text]);

  /**
   * Render status indicator
   */
  const renderStatusIndicator = () => {
    if (message.status === 'sending') {
      return (
        <div className="chat-message__status chat-message__status--sending">
          <span className="chat-message__spinner"></span>
          Sending...
        </div>
      );
    }

    if (message.status === 'error') {
      return (
        <div className="chat-message__status chat-message__status--error">
          ⚠️ {message.error || 'Failed to send'}
        </div>
      );
    }

    return null;
  };

  /**
   * Render typing indicator for streaming AI response
   */
  const renderTypingIndicator = () => {
    if (isStreaming) {
      return (
        <div className="chat-message__typing">
          <span className="chat-message__dot"></span>
          <span className="chat-message__dot"></span>
          <span className="chat-message__dot"></span>
        </div>
      );
    }
    return null;
  };

  /**
   * Render attachments
   */
  const renderAttachments = () => {
    if (!message.attachments || message.attachments.length === 0) {
      return null;
    }

    return (
      <div className="chat-message__attachments">
        {message.attachments.map((attachment) => (
          <div
            key={attachment.id}
            className={`chat-message__attachment chat-message__attachment--${attachment.type}`}
          >
            {/* Image attachment */}
            {attachment.type === 'image' && attachment.preview && (
              <div className="chat-message__image-wrapper">
                <img
                  src={attachment.preview}
                  alt={attachment.name}
                  className="chat-message__image"
                />
              </div>
            )}

            {/* Document attachment */}
            {attachment.type === 'document' && (
              <div className="chat-message__document">
                <span className="chat-message__attachment-icon">📄</span>
                <div className="chat-message__attachment-info">
                  <div className="chat-message__attachment-name">
                    {attachment.name}
                  </div>
                  <div className="chat-message__attachment-size">
                    {Math.round(attachment.size / 1024)} KB
                  </div>
                </div>
              </div>
            )}

            {/* Audio attachment */}
            {attachment.type === 'audio' && (
              <div className="chat-message__audio">
                <span className="chat-message__attachment-icon">🎵</span>
                <audio
                  controls
                  className="chat-message__audio-player"
                  crossOrigin="anonymous"
                >
                  <source src={attachment.preview} type={attachment.mimeType} />
                  Your browser does not support the audio element.
                </audio>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  /**
   * Simple markdown parsing (basic support)
   */
  const parseMarkdown = (text: string): React.ReactNode => {
    // Very basic markdown support - can be extended
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    // Bold text: **text**
    const boldRegex = /\*\*(.+?)\*\*/g;
    let boldMatch;
    while ((boldMatch = boldRegex.exec(text)) !== null) {
      if (boldMatch.index > lastIndex) {
        parts.push(text.substring(lastIndex, boldMatch.index));
      }
      parts.push(
        <strong key={`bold-${boldMatch.index}`}>{boldMatch[1]}</strong>
      );
      lastIndex = boldRegex.lastIndex;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    // If no formatting found, return original text
    if (parts.length === 0) {
      return text;
    }

    return parts;
  };

  return (
    <div
      className={`chat-message ${
        isUserMessage
          ? 'chat-message--user'
          : 'chat-message--ai'
      } ${isStreaming ? 'chat-message--streaming' : ''}`}
    >
      {/* Avatar/Role indicator */}
      <div className="chat-message__avatar">
        {isUserMessage ? (
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" style={{ width: '1.15rem', height: '1.15rem' }}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0zM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" style={{ width: '1.15rem', height: '1.15rem' }}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 21l-.813-5.096L3 15l5.096-.813L9 9l.813 5.096L15 15l-5.096.813zM18.666 5.666L18 9l-.666-3.334L14 5l3.334-.666L18 1l.666 3.334L22 5l-3.334.666z" />
          </svg>
        )}
      </div>

      {/* Message content */}
      <div className="chat-message__content">
        {/* Role label for accessibility */}
        <div className="chat-message__role">
          {isUserMessage ? 'You' : 'AI Assistant'}
        </div>

        {/* Text content */}
        {message.text && (
          <div className="chat-message__text">
            {parseMarkdown(message.text)}
          </div>
        )}

        {/* Attachments */}
        {renderAttachments()}

        {/* Typing indicator */}
        {renderTypingIndicator()}

        {/* Status indicator */}
        {renderStatusIndicator()}

        {/* Message timestamp */}
        <div className="chat-message__timestamp">
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>

        {/* Action buttons */}
        {!isUserMessage && (
          <div className="chat-message__actions">
            {message.text && (
              <button
                className="chat-message__action-btn"
                onClick={handleCopyText}
                title={copied ? 'Copied!' : 'Copy message'}
                aria-label="Copy message"
              >
                {copied ? (
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" style={{ width: '0.9rem', height: '0.9rem', display: 'block', color: '#10b981' }}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" style={{ width: '0.9rem', height: '0.9rem', display: 'block' }}>
                    <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
                    <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
                  </svg>
                )}
              </button>
            )}

            {isLastMessage && onRegenerateClick && (
              <button
                className="chat-message__action-btn"
                onClick={onRegenerateClick}
                title="Regenerate response"
                aria-label="Regenerate response"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" style={{ width: '0.9rem', height: '0.9rem', display: 'block' }}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                </svg>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Retry button for failed messages */}
      {message.status === 'error' && onRetry && (
        <button
          className="chat-message__retry-btn"
          onClick={() => onRetry(message.id)}
        >
          Retry
        </button>
      )}
    </div>
  );
};

export default ChatMessage;
