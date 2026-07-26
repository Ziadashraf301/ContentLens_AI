import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ChatPage from './pages/ChatPage';
import MainLayout from './components/MainLayout';
import './styles/MainLayout.css';

const App: React.FC = () => {
  return (
    <Router>
      <MainLayout>
        <Routes>
          {/* Chat Workspace with optional Session ID */}
          <Route path="/chat/:sessionId?" element={<ChatPage />} />
          
          {/* Default redirect to chat */}
          <Route path="/" element={<Navigate to="/chat" replace />} />
          
          {/* Fallback */}
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Routes>
      </MainLayout>
    </Router>
  );
};

export default App;
