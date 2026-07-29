import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import * as chatService from '../services/chatService';
import { ChatSession } from '../types/chat';
import '../styles/Sidebar.css';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { sessionId: activeSessionId } = useParams<{ sessionId?: string }>();

  const loadSessions = useCallback(async () => {
    try {
      const data = await chatService.fetchChatSessions();
      setSessions(data);
    } catch (err) {
      console.error('Failed to load chat sessions:', err);
    }
  }, []);

  useEffect(() => {
    loadSessions();

    // Listen for session updates from ChatPage
    const handleSessionsUpdate = () => {
      loadSessions();
    };

    window.addEventListener('sessions-changed', handleSessionsUpdate);
    return () => {
      window.removeEventListener('sessions-changed', handleSessionsUpdate);
    };
  }, [loadSessions]);

  const handleNewChat = async () => {
    if (isLoading) return;
    try {
      setIsLoading(true);
      const newId = await chatService.createChatSession();
      await loadSessions();
      navigate(`/chat/${newId}`);
    } catch (err) {
      console.error('Failed to create new chat session:', err);
      alert('Failed to create new session. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSessionClick = (id: string) => {
    navigate(`/chat/${id}`);
  };

  const handleDeleteSession = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this chat session?')) return;
    try {
      await chatService.deleteChatSession(id);
      await loadSessions();
      if (activeSessionId === id) {
        navigate('/');
      }
    } catch (err) {
      console.error('Failed to delete chat session:', err);
    }
  };

  return (
    <div className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        {!collapsed && <h2>SalesLens AI</h2>}
        <button 
          className="sidebar-toggle-btn" 
          onClick={onToggle}
          title={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {collapsed ? '▶' : '◀'}
        </button>
      </div>
      
      <button 
        className="new-session-btn" 
        onClick={handleNewChat}
        disabled={isLoading}
        title="New Session"
      >
        {collapsed ? '＋' : '＋ New Session'}
      </button>

      <div className="sidebar-nav">
        {!collapsed && <div className="sessions-list-header">Recent Chats</div>}
        <div className="sessions-scroll-container">
          {sessions.length === 0 ? (
            !collapsed && <div className="no-sessions-msg">No chats yet.</div>
          ) : (
            sessions.map((session) => (
              <div 
                key={session.id} 
                className={`session-item-container ${activeSessionId === session.id ? 'active' : ''}`}
              >
                <button
                  className="session-link-btn"
                  onClick={() => handleSessionClick(session.id)}
                  title={session.title}
                >
                  <span className="session-icon">💬</span>
                  {!collapsed && (
                    <span className="session-title-text">{session.title}</span>
                  )}
                </button>
                {!collapsed && (
                  <div className="session-actions-wrapper">
                    {session.messageCount > 0 && (
                      <span className="session-msg-count">{session.messageCount}</span>
                    )}
                    <button
                      className="session-delete-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteSession(session.id);
                      }}
                      title="Delete Session"
                    >
                      🗑️
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="user-profile-summary">
          <div className="user-avatar-small">D</div>
          {!collapsed && (
            <div className="user-info-text">
              <span className="user-name-label">Dev User</span>
              <span className="user-role-label">Salesperson</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
