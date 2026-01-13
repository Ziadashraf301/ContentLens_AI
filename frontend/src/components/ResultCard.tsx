import React from 'react';
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

function parseToFragments(text: string) {
  // Very small parser: split into lines and detect headings and lists
  const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  const fragments: React.ReactNode[] = [];
  let currentList: string[] | null = null;

  const flushList = () => {
    if (currentList && currentList.length) {
      fragments.push(<ul key={fragments.length}>{currentList.map((it, i) => <li key={i} dangerouslySetInnerHTML={{ __html: it }} />)}</ul>);
      currentList = null;
    }
  };

  for (const line of lines) {
    if (/^####?\s+/.test(line)) {
      flushList();
      fragments.push(<h4 key={fragments.length}>{line.replace(/^#+\s+/, '')}</h4>);
      continue;
    }
    if (/^\d+\.\s+/.test(line) || /^[-*]\s+/.test(line)) {
      if (!currentList) currentList = [];
      // Convert simple markdown bold to <strong>
      const html = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/^\d+\.\s+/, '');
      currentList.push(html);
      continue;
    }
    // plain paragraph
    flushList();
    fragments.push(<p key={fragments.length} dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>') }} />);
  }
  flushList();
  return fragments;
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
          <h3>💡 Analysis</h3>
          <div className="analysis-formatted">{parseToFragments(data.analysis)}</div>
        </section>
      )}

      {data.recommendation && (
        <section className="recommendation-box">
          <h3>✅ Recommendations</h3>
          <div className="recommendation-list">{parseToFragments(data.recommendation)}</div>
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