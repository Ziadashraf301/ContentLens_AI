import React from 'react';
import ReactMarkdown from 'react-markdown';
import { AnalysisResponse } from '../types/api';

interface Props { data: AnalysisResponse; }

function renderJSONSchema(schema: any) {
  if (!schema || !schema.properties) return null;
  const props = schema.properties;
  const required = schema.required || [];

  return (
    <div className="extraction-list">
      {Object.entries(props).map(([name, meta]: any) => (
        <div key={name} className="extraction-item">
          <strong>{name}</strong>
          <div className="extraction-meta">
            <span>type: <em>{meta.type ?? 'unknown'}</em></span>
            {meta.default !== undefined && <span>default: <em>{String(meta.default)}</em></span>}
            {required.includes(name) && <span className="required">required</span>}
          </div>
        </div>
      ))}
    </div>
  );
}

export const ResultCard: React.FC<Props> = ({ data }) => {
  const hasSchema = data.extraction && data.extraction.properties;

  return (
    <div className="result-card">
      {data.extraction && (
        <section>
          <h3>🔍 Structured Extraction</h3>
          {hasSchema ? (
            <>
              {renderJSONSchema(data.extraction)}
              <details>
                <summary>View full JSON</summary>
                <pre>{JSON.stringify(data.extraction, null, 2)}</pre>
              </details>
            </>
          ) : (
            <pre>{JSON.stringify(data.extraction, null, 2)}</pre>
          )}
        </section>
      )}

      {data.summary && (
        <section>
          <h3>📝 Executive Summary</h3>
          <div className="summary-content"><ReactMarkdown>{data.summary}</ReactMarkdown></div>
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
          <h3>💡 Analysis</h3>
          <div className="analysis-formatted"><ReactMarkdown>{data.analysis}</ReactMarkdown></div>
        </section>
      )}

      {data.recommendation && (
        <section className="recommendation-box">
          <h3>✅ Recommendations</h3>
          <div className="recommendation-list"><ReactMarkdown>{data.recommendation}</ReactMarkdown></div>
        </section>
      )}

      {data.ideation && (
        <section className="ideation-box">
          <h3>💡 Campaign Ideas</h3>
          <div className="ideation-list"><ReactMarkdown>{data.ideation}</ReactMarkdown></div>
        </section>
      )}

      {data.copywriting && (
        <section className="copy-box">
          <h3>📄 Copywriting</h3>
          <div className="copy-content"><ReactMarkdown>{data.copywriting}</ReactMarkdown></div>
        </section>
      )}

      {data.compliance && (
        <section className="compliance-box">
          <h3>⚖️ Compliance Check</h3>
          {typeof data.compliance === 'object' ? (
            <div className="compliance-content">
              <p><strong>Status:</strong> {data.compliance.status}</p>
              {data.compliance.issues && data.compliance.issues.length > 0 && (
                <ul>
                  {data.compliance.issues.map((issue: string, i: number) => (
                    <li key={i}>{issue}</li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            <div className="compliance-content"><ReactMarkdown>{data.compliance}</ReactMarkdown></div>
          )}
        </section>
      )}

      {/* Optional per-agent raw output for debugging */}
      {data.agents && (
        <section>
          <h3>🔬 Agent Outputs</h3>
          <pre>{JSON.stringify(data.agents, null, 2)}</pre>
        </section>
      )}
    </div>
  );
};