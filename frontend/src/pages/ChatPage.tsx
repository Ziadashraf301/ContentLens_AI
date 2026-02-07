/**
 * ChatPage Component
 * Main chat interface page with message list and input
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import Loader from '../components/Loader';
import {
  ChatMessage as ChatMessageType,
  ChatSession,
  FileAttachment,
  ChatMessagePayload,
} from '../types/chat';
import * as chatService from '../services/chatService';

/**
 * ChatPage Component
 * Provides real-time message interface with multimodal support
 */
export const ChatPage: React.FC = () => {
  // Chat state
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  /**
   * Initialize chat - create or load session
   */
  useEffect(() => {
    const initializeChat = async () => {
      try {
        setIsInitializing(true);

        // First, try to fetch existing sessions
        const existingSessions = await chatService.fetchChatSessions();
        setSessions(existingSessions);

        // Use most recent session or create new one
        if (existingSessions.length > 0) {
          const sessionId = existingSessions[0].id;
          setCurrentSessionId(sessionId);

          // Load chat history for that session
          const history = await chatService.fetchChatHistory(sessionId);
          setMessages(
            history.map((msg) => ({
              id: msg.message_id,
              sessionId: msg.session_id,
              role: msg.role,
              messageType: msg.messageType,
              text: msg.text,
              attachments: msg.attachments,
              timestamp: msg.timestamp,
              status: 'sent' as const,
            }))
          );
        } else {
          // Create a new session
          const newSessionId = await chatService.createChatSession();
          setCurrentSessionId(newSessionId);
          setMessages([]);
        }
      } catch (err) {
        console.error('Failed to initialize chat:', err);
        setError('Failed to load chat. Please refresh the page.');
      } finally {
        setIsInitializing(false);
      }
    };

    initializeChat();
  }, []);

  /**
   * Auto-scroll to latest message
   */
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  /**
   * Handle sending a message
   */
  const handleSendMessage = useCallback(
    async (text: string, attachments: FileAttachment[]) => {
      if (!currentSessionId) {
        setError('No active chat session');
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        // Create user message for UI (optimistic update)
        const userMessageId = `msg-${Date.now()}`;
        const userMessage: ChatMessageType = {
          id: userMessageId,
          sessionId: currentSessionId,
          role: 'user',
          messageType: attachments.length > 0 ? attachments[0].type : 'text',
          text: text || undefined,
          attachments: attachments.length > 0 ? attachments : undefined,
          timestamp: new Date().toISOString(),
          status: 'sending',
        };

        // Add user message to UI
        setMessages((prev) => [...prev, userMessage]);

        // Send first attachment (if any) or text
        let messageToSend: ChatMessagePayload;

        if (attachments.length > 0) {
          const attachment = attachments[0];
          messageToSend = {
            session_id: currentSessionId,
            message_type: attachment.type,
            text: text || undefined,
            file: attachment.file,
            timestamp: new Date().toISOString(),
          };
        } else {
          messageToSend = {
            session_id: currentSessionId,
            message_type: 'text',
            text,
            timestamp: new Date().toISOString(),
          };
        }

        // Send to backend
        const response = await chatService.sendChatMessage(messageToSend);

        // Update user message status
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === userMessageId
              ? { ...msg, status: 'sent' as const }
              : msg
          )
        );

        // Add AI response
        const aiMessage: ChatMessageType = {
          id: response.message_id,
          sessionId: response.session_id,
          role: 'ai',
          messageType: response.messageType,
          text: response.text,
          attachments: response.attachments,
          timestamp: response.timestamp,
          status: 'sent',
        };

        setMessages((prev) => [...prev, aiMessage]);

        // Optionally update session title from first message
        if (messages.length === 0 && text) {
          const sessionTitle = text.substring(0, 50);
          setSessions((prev) =>
            prev.map((s) =>
              s.id === currentSessionId
                ? { ...s, title: sessionTitle }
                : s
            )
          );
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to send message';
        setError(errorMessage);

        // Mark user message as errored
        setMessages((prev) =>
          prev.map((msg) =>
            msg.status === 'sending'
              ? {
                  ...msg,
                  status: 'error' as const,
                  error: errorMessage,
                }
              : msg
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [currentSessionId, messages.length]
  );

  /**
   * Retry sending a failed message
   */
  const handleRetryMessage = useCallback(
    async (messageId: string) => {
      const failedMessage = messages.find((m) => m.id === messageId);
      if (!failedMessage || !failedMessage.text) return;

      // Remove failed message
      setMessages((prev) => prev.filter((m) => m.id !== messageId));

      // Resend
      await handleSendMessage(failedMessage.text, failedMessage.attachments || []);
    },
    [messages, handleSendMessage]
  );

  /**
   * Regenerate last AI response
   */
  const handleRegenerateResponse = useCallback(async () => {
    if (!currentSessionId) return;

    try {
      setIsLoading(true);
      setError(null);

      // Find and remove last AI message
      const lastAIMessageIndex = messages.findIndex(
        (m) => m.role === 'ai'
      );
      
      if (lastAIMessageIndex === -1) {
        setError('No message to regenerate');
        return;
      }

      // Remove last AI message and set status to sending
      const lastUserMessage = messages[lastAIMessageIndex - 1];
      setMessages((prev) =>
        prev.filter((_, i) => i !== lastAIMessageIndex)
      );

      // Re-send last user message
      if (lastUserMessage && lastUserMessage.text) {
        await handleSendMessage(
          lastUserMessage.text,
          lastUserMessage.attachments || []
        );
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to regenerate response'
      );
    } finally {
      setIsLoading(false);
    }
  }, [currentSessionId, messages, handleSendMessage]);

  /**
   * Create a new chat session
   */
  const handleNewChat = useCallback(async () => {
    try {
      setIsLoading(true);
      const newSessionId = await chatService.createChatSession();
      setCurrentSessionId(newSessionId);
      setMessages([]);

      // Refresh sessions list
      const updatedSessions = await chatService.fetchChatSessions();
      setSessions(updatedSessions);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to create new chat'
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Switch to different session
   */
  const handleSwitchSession = useCallback(
    async (sessionId: string) => {
      try {
        setIsLoading(true);
        setCurrentSessionId(sessionId);

        // Load chat history
        const history = await chatService.fetchChatHistory(sessionId);
        setMessages(
          history.map((msg) => ({
            id: msg.message_id,
            sessionId: msg.session_id,
            role: msg.role,
            messageType: msg.messageType,
            text: msg.text,
            attachments: msg.attachments,
            timestamp: msg.timestamp,
            status: 'sent' as const,
          }))
        );
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'Failed to load chat'
        );
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  /**
   * Clear current chat
   */
  const handleClearChat = useCallback(async () => {
    if (!currentSessionId) return;

    if (!window.confirm('Are you sure you want to clear this chat?')) {
      return;
    }

    try {
      await chatService.clearChatSession(currentSessionId);
      setMessages([]);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to clear chat'
      );
    }
  }, [currentSessionId]);

  if (isInitializing) {
    return (
      <div className="chat-page chat-page--loading">
        <Loader />
        <p>Initializing chat...</p>
      </div>
    );
  }

  return (
    <div className="chat-page">
      {/* Sidebar - Chat History */}
      <aside className={`chat-sidebar ${showSidebar ? 'chat-sidebar--open' : ''}`}>
        <div className="chat-sidebar__header">
          <h2>Chats</h2>
          <button
            className="chat-sidebar__close-btn"
            onClick={() => setShowSidebar(false)}
            aria-label="Close sidebar"
            title="Close sidebar"
          >
            ✕
          </button>
        </div>

        <button
          className="chat-sidebar__new-btn"
          onClick={handleNewChat}
          disabled={isLoading}
        >
          ➕ New Chat
        </button>

        <div className="chat-sidebar__sessions">
          {sessions.length === 0 ? (
            <p className="chat-sidebar__empty">No chats yet. Start a new one!</p>
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                className={`chat-sidebar__session ${
                  currentSessionId === session.id
                    ? 'chat-sidebar__session--active'
                    : ''
                }`}
                onClick={() => handleSwitchSession(session.id)}
                title={session.title}
              >
                <span className="chat-sidebar__session-title">
                  {session.title}
                </span>
                <span className="chat-sidebar__session-count">
                  {session.messageCount}
                </span>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* Main Chat Area */}
      <div className="chat-main">
        {/* Header */}
        <header className="chat-header">
          <button
            className="chat-header__menu-btn"
            onClick={() => setShowSidebar(!showSidebar)}
            aria-label="Toggle sidebar"
            title="Toggle sidebar"
          >
            ☰
          </button>

          <h1 className="chat-header__title">ContentLens AI Chat</h1>

          <div className="chat-header__actions">
            <button
              className="chat-header__action-btn"
              onClick={handleClearChat}
              disabled={isLoading || messages.length === 0}
              title="Clear chat history"
              aria-label="Clear chat"
            >
              🗑️
            </button>
          </div>
        </header>

        {/* Messages Container */}
        <div
          ref={messagesContainerRef}
          className="chat-messages"
          role="log"
          aria-live="polite"
          aria-label="Chat messages"
        >
          {/* Empty state */}
          {messages.length === 0 && (
            <div className="chat-messages__empty">
              <div className="chat-messages__empty-icon">💬</div>
              <h2>Start a conversation</h2>
              <p>Send a message to begin. You can include text, images, documents, or voice messages.</p>
            </div>
          )}

          {/* Messages */}
          {messages.map((message, index) => (
            <ChatMessage
              key={message.id}
              message={message}
              onRetry={handleRetryMessage}
              onRegenerateClick={
                index === messages.length - 1 && message.role === 'ai'
                  ? handleRegenerateResponse
                  : undefined
              }
              isLastMessage={index === messages.length - 1}
            />
          ))}

          {/* Scroll anchor */}
          <div ref={messagesEndRef} />
        </div>

        {/* Error message */}
        {error && (
          <div className="chat-error">
            <span>⚠️ {error}</span>
            <button
              className="chat-error__close"
              onClick={() => setError(null)}
              aria-label="Close error"
            >
              ✕
            </button>
          </div>
        )}

        {/* Input Area */}
        <ChatInput
          onSend={handleSendMessage}
          disabled={isLoading || !currentSessionId}
          placeholder="Type your message... (Shift+Enter for new line)"
        />
      </div>
    </div>
  );
};

export default ChatPage;
