/**
 * Chat Service
 * Handles all API requests for chat functionality
 * Backend endpoints will be integrated here
 */

import { ChatMessagePayload, ChatMessageResponse, ChatSession } from '../types/chat';
import { API_BASE_URL } from './api';

/**
 * Send a message to the backend
 * Handles both text and multimodal payloads
 * 
 * @param payload - Message payload with optional file
 * @returns Promise with AI response
 */
export async function sendChatMessage(
  payload: ChatMessagePayload
): Promise<ChatMessageResponse> {
  try {
    // Prepare FormData for file upload support
    const formData = new FormData();
    formData.append('session_id', payload.session_id);
    formData.append('message_type', payload.message_type);
    
    if (payload.text) {
      formData.append('text', payload.text);
    }
    
    if (payload.file) {
      formData.append('file', payload.file);
    }
    
    formData.append('timestamp', payload.timestamp);

    const response = await fetch(`${API_BASE_URL}/api/chat/message`, {
      method: 'POST',
      body: formData,
      // Note: Don't set Content-Type header; browser will set it automatically with boundary
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.message || `Chat error: ${response.statusText}`
      );
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to send chat message:', error);
    throw error;
  }
}

/**
 * Stream chat response using Server-Sent Events (SSE)
 * Optional: Use for real-time streaming responses
 * 
 * @param sessionId - Current session ID
 * @param onChunk - Callback for each streamed text chunk
 * @param onComplete - Callback when stream completes
 */
export async function streamChatResponse(
  sessionId: string,
  onChunk: (chunk: string) => void,
  onComplete: () => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/stream?session_id=${sessionId}`);

    if (!response.ok) {
      throw new Error(`Stream error: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is not readable');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');

      // Process complete lines
      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i];
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          onChunk(data);
        }
      }

      // Keep incomplete line in buffer
      buffer = lines[lines.length - 1];
    }

    // Process final buffer
    if (buffer.startsWith('data: ')) {
      onChunk(buffer.slice(6));
    }

    onComplete();
  } catch (error) {
    console.error('Stream error:', error);
    throw error;
  }
}

/**
 * Create a new chat session
 * 
 * @returns Promise with new session ID
 */
export async function createChatSession(): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Session creation failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.session_id || data.id;
  } catch (error) {
    console.error('Failed to create session:', error);
    throw error;
  }
}

/**
 * Fetch all chat sessions for the user
 * 
 * @returns Promise with array of chat sessions
 */
export async function fetchChatSessions(): Promise<ChatSession[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/sessions`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch sessions: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to fetch sessions:', error);
    return []; // Return empty array on error
  }
}

/**
 * Fetch chat history for a specific session
 * 
 * @param sessionId - ID of the session
 * @returns Promise with array of messages
 */
export async function fetchChatHistory(sessionId: string): Promise<ChatMessageResponse[]> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/chat/sessions/${sessionId}/messages`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch chat history: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to fetch chat history:', error);
    return [];
  }
}

/**
 * Delete a chat session
 * 
 * @param sessionId - ID of the session to delete
 */
export async function deleteChatSession(sessionId: string): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to delete session: ${response.statusText}`);
    }
  } catch (error) {
    console.error('Failed to delete session:', error);
    throw error;
  }
}

/**
 * Clear all messages in a session
 * 
 * @param sessionId - ID of the session
 */
export async function clearChatSession(sessionId: string): Promise<void> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/chat/sessions/${sessionId}/clear`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to clear session: ${response.statusText}`);
    }
  } catch (error) {
    console.error('Failed to clear session:', error);
    throw error;
  }
}

/**
 * Regenerate the last AI response
 * 
 * @param sessionId - ID of the session
 * @returns Promise with regenerated message
 */
export async function regenerateLastResponse(
  sessionId: string
): Promise<ChatMessageResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/sessions/${sessionId}/regenerate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to regenerate response: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to regenerate response:', error);
    throw error;
  }
}
