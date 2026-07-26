/**
 * Chat Types and Interfaces
 * Defines all type structures for the chat system
 */

export type MessageType = 'text' | 'image' | 'audio' | 'document';
export type MessageRole = 'user' | 'ai';
export type MessageStatus = 'sending' | 'sent' | 'error';

/**
 * File attachment metadata
 */
export interface FileAttachment {
  id: string;
  name: string;
  type: MessageType;
  size: number;
  mimeType: string;
  preview?: string; // base64 or URL
  file?: File; // Original file object for sending
}

/**
 * Core Message structure for chat
 */
export interface ChatMessage {
  id: string;
  sessionId: string;
  role: MessageRole;
  messageType: MessageType;
  text?: string;
  attachments?: FileAttachment[];
  timestamp: string;
  status?: MessageStatus;
  error?: string;
}

/**
 * Payload sent to backend
 */
export interface ChatMessagePayload {
  session_id: string;
  message_type: MessageType;
  text?: string;
  file?: File | Blob; // Will be sent as FormData
  timestamp: string;
  is_lead_search?: boolean;
}

/**
 * Response from backend
 */
export interface ChatMessageResponse {
  message_id: string;
  session_id: string;
  role: MessageRole;
  messageType: MessageType;
  text?: string;
  attachments?: FileAttachment[];
  timestamp: string;
}

/**
 * Chat session metadata
 */
export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

/**
 * Audio recording data
 */
export interface AudioRecordingData {
  blob: Blob;
  duration: number;
  mimeType: string;
}

/**
 * Chat state for context or component props
 */
export interface ChatContextType {
  messages: ChatMessage[];
  sessions: ChatSession[];
  currentSessionId: string;
  isLoading: boolean;
  error?: string;
  sendMessage: (payload: ChatMessagePayload) => Promise<void>;
  createSession: () => Promise<string>;
  switchSession: (sessionId: string) => Promise<void>;
}
