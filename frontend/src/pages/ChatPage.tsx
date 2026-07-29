import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import { Loader } from '../components/Loader';
import {
  ChatMessage as ChatMessageType,
  FileAttachment,
  ChatMessagePayload,
} from '../types/chat';
import * as chatService from '../services/chatService';
import '../styles/chat.css';

export const ChatPage: React.FC = () => {
  const { sessionId: routeSessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessionTitle, setSessionTitle] = useState('Chat Workspace');

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const isInitializingRef = useRef(false);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  /**
   * Load history for a given session, or initialize a new one if none exists
   */
  const loadChatHistory = useCallback(async (sessionId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Load chat history for the session
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
      
      // Get the title of the session
      const sessions = await chatService.fetchChatSessions();
      const currentSession = sessions.find(s => s.id === sessionId);
      if (currentSession) {
        setSessionTitle(currentSession.title);
      } else {
        setSessionTitle('Active Chat');
      }
      
      setCurrentSessionId(sessionId);
    } catch (err) {
      console.error('Failed to load chat history:', err);
      setError('Failed to load chat history. Redirecting...');
      setTimeout(() => navigate('/chat'), 2000);
    } finally {
      setIsLoading(false);
      setIsInitializing(false);
    }
  }, [navigate]);

  /**
   * Session synchronization logic based on URL params
   */
  useEffect(() => {
    const syncSession = async () => {
      if (routeSessionId) {
        // Load the session from the URL
        loadChatHistory(routeSessionId);
      } else {
        // Prevent concurrent double-initialization (e.g. React 18 StrictMode double firing)
        if (isInitializingRef.current) return;
        isInitializingRef.current = true;

        try {
          setIsInitializing(true);
          const sessions = await chatService.fetchChatSessions();
          if (sessions.length > 0) {
            navigate(`/chat/${sessions[0].id}`, { replace: true });
          } else {
            // Lazy Session Mode: do not auto-create session. Just clear local view.
            setCurrentSessionId(null);
            setMessages([]);
            setSessionTitle('New Chat');
          }
        } catch (err) {
          console.error('Failed to initialize sessions:', err);
          setError('Failed to load sessions. Please try refreshing.');
        } finally {
          setIsInitializing(false);
          isInitializingRef.current = false;
        }
      }

    };

    syncSession();
  }, [routeSessionId, loadChatHistory, navigate]);


  /**
   * Handle sending a message
   */
  const handleSendMessage = useCallback(
    async (text: string, attachments: FileAttachment[], isLeadSearch = false) => {
      let sessionId = currentSessionId;
      let isNewSession = false;

      if (!sessionId) {
        try {
          setIsLoading(true);
          setIsGenerating(true);
          sessionId = await chatService.createChatSession();
          setCurrentSessionId(sessionId);
          isNewSession = true;
        } catch (err) {
          console.error('Failed to create lazy session:', err);
          setError('Failed to create a new session. Please try again.');
          return;
        }
      }

      try {
        setIsLoading(true);
        setIsGenerating(true);
        setError(null);

        // Display user message in UI instantly (optimistic update)
        const userMessageId = `msg-${Date.now()}`;
        const userMessage: ChatMessageType = {
          id: userMessageId,
          sessionId: sessionId,
          role: 'user',
          messageType: isLeadSearch ? 'text' : (attachments.length > 0 ? attachments[0].type : 'text'),
          text: isLeadSearch ? `[Lead Search] ${text}` : (text || undefined),
          attachments: attachments.length > 0 ? attachments : undefined,
          timestamp: new Date().toISOString(),
          status: 'sending',
        };

        setMessages((prev) => [...prev, userMessage]);

        // Prepare payload
        let messageToSend: ChatMessagePayload;
        if (attachments.length > 0 && !isLeadSearch) {
          const attachment = attachments[0];
          messageToSend = {
            session_id: sessionId,
            message_type: attachment.type,
            text: text || undefined,
            file: attachment.file,
            timestamp: new Date().toISOString(),
          };
        } else {
          messageToSend = {
            session_id: sessionId,
            message_type: 'text',
            text: text,
            timestamp: new Date().toISOString(),
            is_lead_search: isLeadSearch,
          };
        }

        // Send to backend
        const response = await chatService.sendChatMessage(messageToSend);

        // Update user message status to sent
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === userMessageId ? { ...msg, status: 'sent' as const } : msg
          )
        );

        // Add AI response message to feed
        const aiMessage: ChatMessageType = {
          id: response.message_id,
          sessionId: response.session_id,
          role: response.role,
          messageType: response.messageType,
          text: response.text,
          attachments: response.attachments,
          timestamp: response.timestamp,
          status: 'sent',
        };

        setMessages((prev) => [...prev, aiMessage]);
        
        // If it was a new session, sync URL and sidebar
        if (isNewSession) {
          window.dispatchEvent(new Event('sessions-changed'));
          navigate(`/chat/${sessionId}`, { replace: true });
        } else {
          // Update local header title if it is currently a default placeholder or cleared session
          if (sessionTitle === 'New Chat' || sessionTitle === 'Chat Workspace' || sessionTitle === 'Cleared Chat' || messages.length <= 1) {
            if (text) {
              setSessionTitle(text.substring(0, 40) + (text.length > 40 ? '...' : ''));
            } else if (attachments.length > 0) {
              setSessionTitle(`File: ${attachments[0].name.substring(0, 30)}`);
            }
          }
          window.dispatchEvent(new Event('sessions-changed'));
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
        setError(errorMessage);

        setMessages((prev) =>
          prev.map((msg) =>
            msg.status === 'sending'
              ? { ...msg, status: 'error' as const, error: errorMessage }
              : msg
          )
        );
      } finally {
        setIsLoading(false);
        setIsGenerating(false);
      }
    },
    [currentSessionId, messages, sessionTitle, navigate]
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
    if (!currentSessionId || messages.length === 0) return;

    try {
      setIsLoading(true);
      setIsGenerating(true);
      setError(null);

      // Find and remove last AI message
      // Optimistically remove the old AI response(s) from local state to match backend truncation
      setMessages((prev) => {
        const lastUserIndex = [...prev].reverse().findIndex(m => m.role === 'user');
        if (lastUserIndex !== -1) {
          const actualIndex = prev.length - 1 - lastUserIndex;
          return prev.slice(0, actualIndex + 1);
        }
        return prev;
      });

      // Call regenerate response endpoint
      const response = await chatService.regenerateLastResponse(currentSessionId);
      
      const aiMessage: ChatMessageType = {
        id: response.message_id,
        sessionId: response.session_id,
        role: response.role,
        messageType: response.messageType,
        text: response.text,
        attachments: response.attachments,
        timestamp: response.timestamp,
        status: 'sent',
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate response');
    } finally {
      setIsLoading(false);
      setIsGenerating(false);
    }
  }, [currentSessionId, messages]);

  /**
   * Clear current chat
   */
  const handleClearChat = useCallback(async () => {
    if (!currentSessionId) return;

    if (!window.confirm('Are you sure you want to clear this chat session?')) {
      return;
    }

    try {
      setIsLoading(true);
      await chatService.clearChatSession(currentSessionId);
      setMessages([]);
      window.dispatchEvent(new Event('sessions-changed'));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear chat');
    } finally {
      setIsLoading(false);
    }
  }, [currentSessionId]);

  if (isInitializing) {
    return (
      <div className="chat-page chat-page--loading">
        <Loader />
        <p>Initializing Sales Assistant...</p>
      </div>
    );
  }

  return (
    <div className="sales-chat-page-workspace">
      {/* Top Workspace Bar */}
      <div className="sales-workspace-bar">
        <div className="sales-workspace-title">
          <span className="sales-workspace-icon">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" style={{ width: '1.25rem', height: '1.25rem', display: 'block' }}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 .621-.504 1.125-1.125 1.125H4.875A1.125 1.125 0 0 1 3.75 18.4V14.15m16.5 0c0-.621-.504-1.125-1.125-1.125H4.875c-.621 0-1.125.504-1.125 1.125m16.5 0v-2.625c0-.621-.504-1.125-1.125-1.125H4.875c-.621 0-1.125.504-1.125 1.125v2.625M15 9V5.25c0-.621-.504-1.125-1.125-1.125h-3.75c-.621 0-1.125.504-1.125 1.125V9" />
            </svg>
          </span>
          <span className="sales-workspace-text">{sessionTitle}</span>
        </div>
        <div className="sales-workspace-actions">
          <button
            className="sales-workspace-action-btn"
            onClick={handleClearChat}
            disabled={isLoading || messages.length === 0}
            title="Clear Chat History"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" style={{ width: '1rem', height: '1rem' }}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
            Clear Chat
          </button>
        </div>
      </div>

      {/* Messages Container */}
      <div
        ref={messagesContainerRef}
        className="chat-messages"
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
      >
        {messages.length === 0 && (
          <div className="chat-messages__empty">
            <div className="chat-messages__empty-icon">🤝</div>
            <h2>Welcome to SalesLens AI</h2>
            <p>
              I am your Salesperson Assistant. You can upload client briefs or meeting notes 
              using the <strong>＋</strong> button to extract insights, or write a query and click 
              <strong>🔍 Search Leads</strong> to find prospects.
            </p>
          </div>
        )}

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
            isLastMessage={index === messages.length - 1 && !isGenerating}
          />
        ))}

        {isGenerating && (
          <ChatMessage
            key="thinking-indicator"
            message={{
              id: 'thinking-indicator',
              sessionId: currentSessionId || '',
              role: 'ai',
              messageType: 'text',
              text: '',
              timestamp: new Date().toISOString(),
              status: 'sending',
            }}
            isLastMessage={true}
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="chat-error">
          <span>⚠️ {error}</span>
          <button className="chat-error__close" onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* Input Area */}
      <ChatInput
        onSend={handleSendMessage}
        disabled={isLoading || isGenerating}
      />
    </div>
  );
};


export default ChatPage;
