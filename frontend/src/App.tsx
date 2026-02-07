import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import ChatPage from './pages/ChatPage';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        {/* Upload/Document Processing Page */}
        <Route path="/upload" element={<UploadPage />} />
        
        {/* Chat Page */}
        <Route path="/chat" element={<ChatPage />} />
        
        {/* Default redirect to chat */}
        <Route path="/" element={<Navigate to="/chat" replace />} />
        
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </Router>
  );
};

export default App;
