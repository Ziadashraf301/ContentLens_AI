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
  const isStreaming = isLastMessage && message.status === 'sending';

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
        {isUserMessage ? '👤' : '🤖'}
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
              {copied ? '✓' : '📋'}
            </button>
          )}

          {isLastMessage && onRegenerateClick && (
            <button
              className="chat-message__action-btn"
              onClick={onRegenerateClick}
              title="Regenerate response"
              aria-label="Regenerate response"
            >
              🔄
            </button>
          )}
        </div>
      )}

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
