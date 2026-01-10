import React from 'react';
import { ResultCard } from '../components/ResultCard';
import { AnalysisResponse } from '../types/api';

interface Props { data: AnalysisResponse; onReset: () => void; }

export const ResultsPage: React.FC<Props> = ({ data, onReset }) => (
  <div className="page fade-in">
    <button onClick={onReset} className="btn-secondary">← Upload New File</button>
    <ResultCard data={data} />
  </div>
);