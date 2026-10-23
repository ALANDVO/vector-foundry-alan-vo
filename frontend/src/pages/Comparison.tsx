// Vector Foundry - Comparison Page
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
interface ComparisonIssue {
  number: number;
  title: string;
  labels: Array<{ name: string; color: string }>;
  readiness_score: number | null;
  checklist_progress: { completed: number; total: number };
  blocking_count: number;
  questions_count: number;
  last_analyzed: string | null;
}

interface ComparisonState {
  issues: ComparisonIssue[];
  loading: boolean;
  error: string | null;
}

const DEFAULT_ISSUES = [31844, 43467, 81513, 130703, 63063, 110998, 88581, 43122];

export function Comparison() {
  const [state, setState] = useState<ComparisonState>({
    issues: [],
    loading: true,
    error: null,
  });

  const [selectedNumbers, setSelectedNumbers] = useState<number[]>(DEFAULT_ISSUES.slice(0, 4));
  const [availableIssues, setAvailableIssues] = useState<ComparisonIssue[]>([]);

  const fetchComparison = async () => {
    if (selectedNumbers.length === 0) {
      setState({ issues: [], loading: false, error: null });
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const issues = await apiClient.post<ComparisonIssue[]>('/api/v1/issues/compare', { numbers: selectedNumbers });
      setState({ issues, loading: false, error: null });
    } catch (err) {
      setState({
        issues: [],
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to load comparison',
      });
    }
  };

  const fetchAvailableIssues = async () => {
    try {
      const response = await apiClient.get<{ issues: ComparisonIssue[] }>('/api/v1/issues', { per_page: 100 });
      setAvailableIssues(response.issues);
    } catch {
      // Ignore
    }
  };

  useEffect(() => {
    fetchAvailableIssues();
  }, []);

  useEffect(() => {
    fetchComparison();
  }, [selectedNumbers]);

  const toggleIssue = (number: number) => {
    setSelectedNumbers(prev => {
      if (prev.includes(number)) {
        return prev.filter(n => n !== number);
      }
      if (prev.length >= 6) return prev;
      return [...prev, number];
    });
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return '#94a3b8';
    if (score >= 80) return '#059669';
    if (score >= 60) return '#d97706';
    if (score >= 40) return '#ea580c';
    return '#dc2626';
  };


  const metrics = [
    { key: 'readiness_score', label: 'Readiness Score', format: (v: number | null) => v !== null ? `${v}%` : '—', higherBetter: true },
    { key: 'checklist_progress', label: 'Checklist Progress', format: (v: { completed: number; total: number }) => `${v.completed}/${v.total} (${v.total > 0 ? Math.round(v.completed / v.total * 100) : 0}%)`, higherBetter: true },
    { key: 'blocking_count', label: 'Blocking Dependencies', format: (v: number) => String(v), higherBetter: false },
    { key: 'questions_count', label: 'Unresolved Questions', format: (v: number) => String(v), higherBetter: false },
  ];

  if (state.loading) {
    return (
      <div className="loading" role="status" aria-label="Loading comparison">
        <div className="spinner" aria-hidden="true"></div>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="error-state">
        <div className="error-state-title">Failed to load comparison</div>
        <p>{state.error}</p>
        <button onClick={fetchComparison} className="btn btn-primary" style={{ marginTop: '16px' }}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#1e293b', marginBottom: '4px' }}>
            Feature Comparison
          </h1>
          <p style={{ color: '#64748b' }}>
            Compare stabilization progress across multiple tracking issues
          </p>
        </div>
      </div>

      <section className="card" style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', marginBottom: '16px' }}>
          Select Issues to Compare
        </h2>
        <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '16px' }}>
          Select up to 6 issues. Click an issue to add/remove it from comparison.
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {availableIssues.map((issue) => (
            <button
              key={issue.number}
              onClick={() => toggleIssue(issue.number)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 14px',
                borderRadius: '8px',
                border: `2px solid ${selectedNumbers.includes(issue.number) ? '#2563eb' : '#e2e8f0'}`,
                background: selectedNumbers.includes(issue.number) ? '#dbeafe' : '#ffffff',
                color: selectedNumbers.includes(issue.number) ? '#1d4ed8' : '#334155',
                fontWeight: selectedNumbers.includes(issue.number) ? '600' : '500',
                fontSize: '13px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>#{issue.number}</span>
              <span style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {issue.title}
              </span>
              {issue.readiness_score !== null && (
                <span style={{
                  fontSize: '11px',
                  fontWeight: '600',
                  padding: '2px 6px',
                  borderRadius: '9999px',
                  background: getScoreColor(issue.readiness_score) + '20',
                  color: getScoreColor(issue.readiness_score),
                }}>
                  {issue.readiness_score}%
                </span>
              )}
            </button>
          ))}
        </div>
        {availableIssues.length === 0 && (
          <div className="empty-state" style={{ padding: '24px' }}>
            <p>No issues available. Ensure the backend is running and has ingested data.</p>
          </div>
        )}
      </section>

      {state.issues.length > 0 && (
        <>
          <section className="card" style={{ marginBottom: '24px', overflow: 'hidden' }}>
            <h2 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid #e2e8f0' }}>
              Metrics Comparison
            </h2>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th style={{ width: '200px' }}>Metric</th>
                    {state.issues.map(issue => (
                      <th key={issue.number} style={{ textAlign: 'center', minWidth: '140px' }}>
                        <Link to={`/issues/${issue.number}`} style={{ color: '#1e293b', fontWeight: '600' }}>
                          #{issue.number}
                        </Link>
                        <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '400', marginTop: '2px', maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {issue.title}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {metrics.map((metric) => {
                    const values = state.issues.map(issue => issue[metric.key as keyof ComparisonIssue]);
                    const bestValue = metric.higherBetter
                      ? Math.max(...values.filter(v => v !== null && v !== undefined) as number[])
                      : Math.min(...values.filter(v => v !== null && v !== undefined) as number[]);
                    
                    return (
                      <tr key={metric.key}>
                        <td style={{ fontWeight: '500', color: '#334155' }}>{metric.label}</td>
                        {state.issues.map((issue, i) => {
                          const value = values[i];
                          const isBest = value !== null && value !== undefined && value === bestValue;
                          const formatted = metric.format(value as any);
                          let cellColor = '#334155';
                          if (metric.key === 'readiness_score' && value !== null) {
                            cellColor = getScoreColor(value as number);
                          }
                          return (
                            <td key={issue.number} style={{ textAlign: 'center', fontWeight: isBest ? '700' : '500', color: cellColor }}>
                              {formatted}
                              {isBest && metric.key !== 'blocking_count' && metric.key !== 'questions_count' && (
                                <span style={{ marginLeft: '4px', fontSize: '10px', color: '#059669' }}>★</span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>

          <section className="card">
            <h2 style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid #e2e8f0' }}>
              Readiness Scores
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {state.issues.map((issue) => (
                <div key={issue.number} style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <Link to={`/issues/${issue.number}`} style={{ minWidth: '100px', fontWeight: '600', color: '#1e293b', fontFamily: 'var(--font-mono)' }}>
                    #{issue.number}
                  </Link>
                  <div style={{ flex: 1, maxWidth: '400px' }}>
                    <div style={{
                      height: '12px',
                      background: '#e2e8f0',
                      borderRadius: '6px',
                      overflow: 'hidden',
                    }}>
                      <div style={{
                        width: `${issue.readiness_score || 0}%`,
                        height: '100%',
                        background: getScoreColor(issue.readiness_score),
                        borderRadius: '6px',
                        transition: 'width 0.5s ease',
                      }} />
                    </div>
                  </div>
                  <div style={{ minWidth: '100px', textAlign: 'right', fontWeight: '600', color: getScoreColor(issue.readiness_score) }}>
                    {issue.readiness_score !== null ? `${issue.readiness_score}%` : 'Not analyzed'}
                  </div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #e2e8f0', fontSize: '12px', color: '#94a3b8' }}>
              Higher is better. Scores ≥80 indicate features approaching stabilization readiness.
            </div>
          </section>
        </>
      )}

      {state.issues.length === 0 && !state.loading && (
        <div className="empty-state">
          <div className="empty-state-title">No issues selected</div>
          <p>Select issues from the list above to compare their stabilization progress.</p>
        </div>
      )}
    </div>
  );
}