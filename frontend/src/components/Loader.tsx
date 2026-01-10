import React from 'react';

export const Loader: React.FC = () => (
  <div className="loader-overlay">
    <div className="spinner"></div>
    <p>Agents are analyzing your brief...</p>
  </div>
);