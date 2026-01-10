import React from 'react';
import { AnalysisResponse } from '../types/api';

interface Props { data: AnalysisResponse; }

export const ResultCard: React.FC<Props> = ({ data }) => {
  return (
    <div className="result-card">
      {data.extraction && (
        <section>
          <h3>🔍 Structured Extraction</h3>
          <pre>{JSON.stringify(data.extraction, null, 2)}</pre>
        </section>
      )}
      {data.summary && (
        <section>
          <h3>📝 Executive Summary</h3>
          <p>{data.summary}</p>
        </section>
      )}
      {data.translation && (
        <section className="arabic-text">
          <h3>🌍 Arabic Translation</h3>
          <p dir="rtl">{data.translation}</p>
        </section>
      )}
      {data.analysis && (
        <section className="analysis-box">
          <h3>💡 Strategic Recommendations</h3>
          <p>{data.analysis}</p>
        </section>
      )}
    </div>
  );
};