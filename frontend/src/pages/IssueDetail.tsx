// Vector Foundry - Issue Detail Page
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient } from '../api/client';

interface IssueDetail {
  number: number;
  title: string;
  body: string;
  html_url: string;
  comments: number;
  labels: Array<{ name: string; color: string }>;
  state: string;
  created_at: string;
  updated_at: string;
  author: { login: string; avatar_url: string };
  checklist: Array<{ text: string; completed: boolean; level: number }>;
  analysis: {
    readiness_score: number;
    blocking_dependencies: string[];
    unresolved_questions: Array<{ category: string; question: string }>;
    progress_summary: string;
    last_analyzed: string;
  } | null;
}

interface IssueDetailState {
  issue: IssueDetail | null;
  loading: boolean;
  error: string | null;
}

export function IssueDetail() {
  const { number } = useParams<{ number: string }>();
  const [state, setState] = useState<IssueDetailState>({
    issue: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    if (!number) return;

    const fetchIssue = async () => {
      setState(prev => ({ ...prev, loading: true, error: null }));
      try {
        const issue = await apiClient.get<IssueDetail>(`/api/v1/issues/${number}`);
        setState({ issue, loading: false, error: null });
      } catch (err) {
        setState({
          issue: null,
          loading: false,
          error: err instanceof Error ? err.message : 'Failed to load issue',
        });
      }
    };

    fetchIssue();
  }, [number]);

  const getProgressColor = (score: number) => {
    if (score >= 80) return '#059669';
    if (score >= 60) return '#d97706';
    if (score >= 40) return '#ea580c';
    return '#dc2626';
  };

  const renderChecklist = (items: Array<{ text: string; completed: boolean; level: number }>) => {
    return items.map((item, index) => (
      <div key={index} style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '10px',
        padding: '8px 0',
        paddingLeft: `${item.level * 20}px`,
        borderBottom: '1px solid #f1f5f9',
      }}>
        <input
          type="checkbox"
          checked={item.completed}
          disabled
          style={{ marginTop: '3px', width: '16px', height: '16px', accentColor: '#2563eb' }}
        />
        <span style={{
          color: item.completed ? '#94a3b8' : '#1e293b',
          textDecoration: item.completed ? 'line-through' : 'none',
          fontSize: '14px',
          lineHeight: '1.5',
        }}>
          {item.text}
        </span>
      </div>
    ));
  };

  const renderMarkdown = (text: string) => {
    // Simple markdown rendering for body text
    return text.split('\n').map((line, i) => (
      <p key={i} style={{ marginBottom: '8px', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
        {line}
      </p>
    ));
  };

  if (state.loading) {
    return (
      <div className="loading" role="status" aria-label="Loading issue details">
        <div className="spinner" aria-hidden="true"></div>
      </div>
    );
  }

  if (state.error || !state.issue) {
    return (
      <div className="error-state">
        <div className="error-state-title">Failed to load issue</div>
        <p>{state.error || 'Issue not found'}</p>
        <Link to="/" className="btn btn-primary" style={{ marginTop: '16px', display: 'inline-block' }}>
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const { issue } = state;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <Link to="/" className="btn btn-ghost" style={{ marginBottom: '16px', display: 'inline-flex' }}>
            ← Back to Dashboard
          </Link>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', flexWrap: 'wrap' }}>
            <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#1e293b', flex: 1, minWidth: '200px' }}>
              {issue.title}
            </h1>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <span className={`badge ${issue.state === 'open' ? 'badge-primary' : 'badge-neutral'}`}>
                {issue.state}
              </span>
              <a href={issue.html_url} target="_blank" rel="noopener noreferrer" className="badge badge-neutral" style={{ textDecoration: 'none' }}>
                View on GitHub
              </a>
            </div>
          </div>
          <div style={{ marginTop: '12px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {issue.labels.map((label) => (
              <span
                key={label.name}
                className="badge"
                style={{
                  background: `#${label.color}20`,
                  color: `#${label.color}`,
                  borderColor: `#${label.color}40`,
                }}
              >
                {label.name}
              </span>
            ))}
          </div>
        </div>

        {issue.analysis && (
          <div style={{ textAlign: 'right', minWidth: '180px' }}>
            <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Readiness Score</div>
            <div style={{
              fontSize: '48px',
              fontWeight: '700',
              color: getProgressColor(issue.analysis.readiness_score),
              fontFamily: 'var(--font-mono)',
              lineHeight: 1,
            }}>
              {issue.analysis.readiness_score}%
            </div>
            <div style={{
              width: '100%',
              height: '6px',
              background: '#e2e8f0',
              borderRadius: '3px',
              overflow: 'hidden',
              marginTop: '8px',
            }}>
              <div style={{
                width: `${issue.analysis.readiness_score}%`,
                height: '100%',
                background: getProgressColor(issue.analysis.readiness_score),
              }} />
            </div>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '24px' }}>
        <div>
          <section className="card" style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid #e2e8f0' }}>
              Description
            </h2>
            <div style={{ color: '#334155', fontSize: '14px', lineHeight: '1.7' }}>
              {renderMarkdown(issue.body)}
            </div>
            <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #e2e8f0', display: 'flex', gap: '16px', color: '#64748b', fontSize: '13px' }}>
              <span>Opened by <strong>{issue.author.login}</strong></span>
              <span>Created {new Date(issue.created_at).toLocaleDateString()}</span>
              <span>Updated {new Date(issue.updated_at).toLocaleDateString()}</span>
              <span>{issue.comments} comments</span>
            </div>
          </section>

          <section className="card">
            <h2 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid #e2e8f0' }}>
              Implementation Checklist
            </h2>
            {issue.checklist && issue.checklist.length > 0 ? (
              <div>{renderChecklist(issue.checklist)}</div>
            ) : (
              <div className="empty-state" style={{ padding: '24px' }}>
                <div className="empty-state-title">No checklist found</div>
                <p>This issue doesn't have a structured checklist.</p>
              </div>
            )}
          </section>
        </div>

        <aside>
          {issue.analysis && (
            <>
              <section className="card" style={{ marginBottom: '24px' }}>
                <h2 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid #e2e8f0' }}>
                  Progress Summary
                </h2>
                <div style={{ color: '#334155', fontSize: '14px', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
                  {issue.analysis.progress_summary}
                </div>
                <div style={{ marginTop: '12px', fontSize: '12px', color: '#94a3b8' }}>
                  Last analyzed: {new Date(issue.analysis.last_analyzed).toLocaleString()}
                </div>
              </section>

              {issue.analysis.blocking_dependencies.length > 0 && (
                <section className="card" style={{ marginBottom: '24px' }}>
                  <h2 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid #e2e8f0' }}>
                    Blocking Dependencies
                  </h2>
                  <ul style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {issue.analysis.blocking_dependencies.map((dep, i) => (
                      <li key={i} style={{
                        padding: '10px 12px',
                        background: '#fef2f2',
                        border: '1px solid #fecaca',
                        borderRadius: '8px',
                        color: '#991b1b',
                        fontSize: '13px',
                      }}>
                        {dep}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {issue.analysis.unresolved_questions.length > 0 && (
                <section className="card">
                  <h2 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid #e2e8f0' }}>
                    Unresolved Questions
                  </h2>
                  <ul style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {issue.analysis.unresolved_questions.map((q, i) => (
                      <li key={i}>
                        <div style={{ fontSize: '12px', fontWeight: '600', color: '#d97706', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>
                          {q.category}
                        </div>
                        <div style={{ color: '#334155', fontSize: '14px', lineHeight: '1.5' }}>
                          {q.question}
                        </div>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </>
          )}

          {!issue.analysis && (
            <section className="card">
              <div className="empty-state">
                <div className="empty-state-title">No analysis available</div>
                <p>Run the analysis engine to generate insights for this issue.</p>
                <button className="btn btn-primary" style={{ marginTop: '16px' }}>
                  Generate Analysis
                </button>
              </div>
            </section>
          )}
        </aside>
      </div>
    </div>
  );
}