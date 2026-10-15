// Vector Foundry - Dashboard Page
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';

interface Issue {
  number: number;
  title: string;
  body: string;
  html_url: string;
  comments: number;
  labels: Array<{ name: string; color: string }>;
  state: string;
  created_at: string;
  updated_at: string;
  checklist_progress?: { completed: number; total: number };
  readiness_score?: number;
}

interface DashboardState {
  issues: Issue[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  page: number;
  pageSize: number;
}

const PAGE_SIZE = 20;

export function Dashboard() {
  const [state, setState] = useState<DashboardState>({
    issues: [],
    loading: true,
    error: null,
    totalCount: 0,
    page: 1,
    pageSize: PAGE_SIZE,
  });

  const [filters, setFilters] = useState({
    search: '',
    label: '',
    state: 'open',
    sort: 'updated',
    order: 'desc',
  });

  const fetchIssues = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const params = {
        page: state.page,
        per_page: state.pageSize,
        search: filters.search || undefined,
        label: filters.label || undefined,
        state: filters.state,
        sort: filters.sort,
        order: filters.order,
      };

      const response = await apiClient.get<{ issues: Issue[]; total: number }>('/api/v1/issues', params);
      setState(prev => ({
        ...prev,
        issues: response.issues,
        totalCount: response.total,
        loading: false,
      }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        error: err instanceof Error ? err.message : 'Failed to load issues',
        loading: false,
      }));
    }
  };

  useEffect(() => {
    fetchIssues();
  }, [state.page, filters.search, filters.label, filters.state, filters.sort, filters.order]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setState(prev => ({ ...prev, page: 1 }));
  };

  const handleSortChange = (sort: string) => {
    setFilters(prev => ({
      ...prev,
      sort,
      order: prev.sort === sort && prev.order === 'desc' ? 'asc' : 'desc',
    }));
    setState(prev => ({ ...prev, page: 1 }));
  };

  const getProgressColor = (score?: number) => {
    if (score === undefined) return '#94a3b8';
    if (score >= 80) return '#059669';
    if (score >= 60) return '#d97706';
    if (score >= 40) return '#ea580c';
    return '#dc2626';
  };

  const getProgressLabel = (score?: number) => {
    if (score === undefined) return 'Unknown';
    if (score >= 80) return 'Near stabilization';
    if (score >= 60) return 'Active development';
    if (score >= 40) return 'Early stage';
    return 'Blocked / Stalled';
  };

  if (state.loading && state.issues.length === 0) {
    return (
      <div className="loading" role="status" aria-label="Loading issues">
        <div className="spinner" aria-hidden="true"></div>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="error-state">
        <div className="error-state-title">Failed to load issues</div>
        <p>{state.error}</p>
        <button onClick={fetchIssues} className="btn btn-primary" style={{ marginTop: '16px' }}>
          Retry
        </button>
      </div>
    );
  }

  if (state.issues.length === 0) {
    return (
      <div className="empty-state">
        <svg className="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <div className="empty-state-title">No issues found</div>
        <p>Try adjusting your filters or search terms.</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#1e293b', marginBottom: '4px' }}>
            Tracking Issues
          </h1>
          <p style={{ color: '#64748b' }}>
            {state.totalCount} issue{state.totalCount !== 1 ? 's' : ''} from rust-lang/rust
          </p>
        </div>
      </div>

      <form onSubmit={handleSearch} className="card" style={{ marginBottom: '24px', padding: '20px' }}>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ flex: 1, minWidth: '200px' }}>
            <label className="form-label" htmlFor="search">Search</label>
            <input
              id="search"
              type="search"
              className="form-input"
              placeholder="Search titles, bodies..."
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              aria-label="Search issues"
            />
          </div>
          <div className="form-group" style={{ minWidth: '150px' }}>
            <label className="form-label" htmlFor="state">State</label>
            <select
              id="state"
              className="form-input"
              value={filters.state}
              onChange={(e) => { setFilters(prev => ({ ...prev, state: e.target.value })); setState(prev => ({ ...prev, page: 1 })); }}
            >
              <option value="open">Open</option>
              <option value="closed">Closed</option>
              <option value="all">All</option>
            </select>
          </div>
          <div className="form-group" style={{ minWidth: '150px' }}>
            <label className="form-label" htmlFor="sort">Sort by</label>
            <select
              id="sort"
              className="form-input"
              value={filters.sort}
              onChange={(e) => handleSortChange(e.target.value)}
            >
              <option value="updated">Recently updated</option>
              <option value="created">Created date</option>
              <option value="comments">Comments</option>
              <option value="readiness">Readiness score</option>
            </select>
          </div>
        </div>
      </form>

      <div className="card" style={{ overflow: 'hidden' }}>
        <div className="table-container">
          <table className="table" role="table">
            <thead>
              <tr>
                <th style={{ width: '80px' }}>
                  <button
                    onClick={() => handleSortChange('number')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', font: 'inherit', color: 'inherit', display: 'flex', alignItems: 'center', gap: '4px' }}
                  >
                    #
                  </button>
                </th>
                <th>
                  <button
                    onClick={() => handleSortChange('title')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', font: 'inherit', color: 'inherit', display: 'flex', alignItems: 'center', gap: '4px' }}
                  >
                    Title
                  </button>
                </th>
                <th style={{ width: '140px' }}>
                  <button
                    onClick={() => handleSortChange('readiness')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', font: 'inherit', color: 'inherit', display: 'flex', alignItems: 'center', gap: '4px' }}
                  >
                    Readiness
                  </button>
                </th>
                <th style={{ width: '200px' }}>Labels</th>
                <th style={{ width: '120px' }}>
                  <button
                    onClick={() => handleSortChange('comments')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', font: 'inherit', color: 'inherit', display: 'flex', alignItems: 'center', gap: '4px' }}
                  >
                    Comments
                  </button>
                </th>
                <th style={{ width: '160px' }}>
                  <button
                    onClick={() => handleSortChange('updated')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', font: 'inherit', color: 'inherit', display: 'flex', alignItems: 'center', gap: '4px' }}
                  >
                    Updated
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              {state.issues.map((issue) => (
                <tr key={issue.number} style={{ cursor: 'pointer' }}>
                  <td style={{ fontWeight: '600', color: '#334155', fontFamily: 'var(--font-mono)' }}>
                    <Link to={`/issues/${issue.number}`} style={{ color: 'inherit' }}>
                      {issue.number}
                    </Link>
                  </td>
                  <td>
                    <Link to={`/issues/${issue.number}`} style={{ fontWeight: '500', color: '#1e293b' }}>
                      {issue.title}
                    </Link>
                  </td>
                  <td>
                    {issue.readiness_score !== undefined ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{
                          width: '60px',
                          height: '6px',
                          background: '#e2e8f0',
                          borderRadius: '3px',
                          overflow: 'hidden',
                        }}>
                          <div style={{
                            width: `${issue.readiness_score}%`,
                            height: '100%',
                            background: getProgressColor(issue.readiness_score),
                            transition: 'width 0.3s ease',
                          }} />
                        </div>
                        <span style={{ fontSize: '12px', fontWeight: '600', color: getProgressColor(issue.readiness_score) }}>
                          {issue.readiness_score}%
                        </span>
                      </div>
                    ) : (
                      <span className="badge badge-neutral">No analysis</span>
                    )}
                  </td>
                  <td>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {issue.labels.slice(0, 4).map((label) => (
                        <span
                          key={label.name}
                          className="badge"
                          style={{
                            background: `#${label.color}20`,
                            color: `#${label.color}`,
                            borderColor: `#${label.color}40`,
                            fontSize: '11px',
                          }}
                        >
                          {label.name}
                        </span>
                      ))}
                      {issue.labels.length > 4 && (
                        <span className="badge badge-neutral" style={{ fontSize: '11px' }}>
                          +{issue.labels.length - 4}
                        </span>
                      )}
                    </div>
                  </td>
                  <td style={{ color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                    {issue.comments}
                  </td>
                  <td style={{ color: '#64748b', fontSize: '13px' }}>
                    {new Date(issue.updated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {state.totalCount > state.pageSize && (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '12px', padding: '16px', borderTop: '1px solid #e2e8f0' }}>
            <button
              className="btn btn-secondary"
              onClick={() => setState(prev => ({ ...prev, page: prev.page - 1 }))}
              disabled={state.page === 1}
            >
              Previous
            </button>
            <span style={{ color: '#64748b', fontSize: '14px' }}>
              Page {state.page} of {Math.ceil(state.totalCount / state.pageSize)}
            </span>
            <button
              className="btn btn-secondary"
              onClick={() => setState(prev => ({ ...prev, page: prev.page + 1 }))}
              disabled={state.page >= Math.ceil(state.totalCount / state.pageSize)}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}