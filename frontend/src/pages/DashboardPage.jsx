import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getDashboardSummary } from '../api/dashboard';
import { listAllTickets } from '../api/tickets';
import { summarizeTickets } from '../utils/ticketMetrics';
import { ticketDetailsPath } from '../utils/ticketRoutes';

export default function DashboardPage() {
  const [tickets, setTickets] = useState([]);
  const [summary, setSummary] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [ticketResult, summaryResult] = await Promise.all([
        listAllTickets().catch(() => ({ items: [] })),
        getDashboardSummary().catch(() => null),
      ]);

      setTickets(ticketResult.items || []);
      setStats(summarizeTickets(ticketResult.items || []));
      setSummary(summaryResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load dashboard data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  // Derived metrics connecting backend summary with fallback
  const totalTickets = summary?.tickets?.total ?? stats?.total ?? 0;
  const openTickets = summary?.tickets?.open ?? stats?.open ?? 0;
  const aiResolvedTickets = summary?.tickets?.ai_resolved ?? stats?.aiResolved ?? 0;
  const escalatedTickets = summary?.tickets?.escalated ?? stats?.escalated ?? 0;
  const inProgressTickets = stats?.inProgress ?? 0;

  const swTotal = summary?.software_requests?.total ?? 0;
  const swCompleted = summary?.software_requests?.by_status?.completed ?? 0;
  const swProvisioning = summary?.software_requests?.by_status?.provisioning ?? 0;

  const autoTotal = summary?.automation?.total_actions ?? 0;
  const autoSucceeded = summary?.automation?.by_status?.succeeded ?? 0;
  const autoFailed = summary?.automation?.by_status?.failed ?? 0;

  const aiTotal = summary?.ai_requests?.total ?? 0;

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Screen 6 — Real-Time Operations</span>
          <h2>ITSM Dashboard</h2>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {summary?.servicenow_mode && (
            <span className="mock-badge">ServiceNow: {summary.servicenow_mode.toUpperCase()}</span>
          )}
          <button
            type="button"
            className="secondary-button"
            onClick={() => void loadDashboard()}
            disabled={loading}
          >
            {loading ? 'Refreshing…' : 'Refresh Dashboard'}
          </button>
        </div>
      </div>

      {error && <div className="error-banner" role="alert">{error}</div>}
      {!error && loading && <p role="status">Loading dashboard metrics…</p>}

      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
        <div className="stat-card">
          <strong>{loading ? '—' : totalTickets}</strong>
          <span>Total Incidents</span>
          <small>{openTickets} currently open</small>
        </div>

        <div className="stat-card" style={{ background: 'rgba(34, 197, 94, 0.1)', borderColor: 'rgba(34, 197, 94, 0.3)' }}>
          <strong style={{ color: '#86efac' }}>{loading ? '—' : aiResolvedTickets}</strong>
          <span>AI-Resolved</span>
          <small>Autonomous self-heal</small>
        </div>

        <div className="stat-card" style={{ background: 'rgba(239, 68, 68, 0.1)', borderColor: 'rgba(239, 68, 68, 0.3)' }}>
          <strong style={{ color: '#fca5a5' }}>{loading ? '—' : escalatedTickets}</strong>
          <span>Escalated</span>
          <small>Human review required</small>
        </div>

        <div className="stat-card">
          <strong>{loading ? '—' : inProgressTickets}</strong>
          <span>In Progress</span>
          <small>Active remediation</small>
        </div>

        <div className="stat-card" style={{ background: 'rgba(56, 189, 248, 0.1)', borderColor: 'rgba(56, 189, 248, 0.3)' }}>
          <strong style={{ color: '#7dd3fc' }}>{loading ? '—' : swTotal}</strong>
          <span>Software Requests</span>
          <small>{swCompleted} completed • {swProvisioning} active</small>
        </div>

        <div className="stat-card" style={{ background: 'rgba(168, 85, 247, 0.1)', borderColor: 'rgba(168, 85, 247, 0.3)' }}>
          <strong style={{ color: '#d8b4fe' }}>{loading ? '—' : autoTotal}</strong>
          <span>Self-Heal Actions</span>
          <small>{autoSucceeded} succeeded • {autoFailed} failed</small>
        </div>

        <div className="stat-card">
          <strong>{loading ? '—' : aiTotal}</strong>
          <span>AI Requests Handled</span>
          <small>RAG & Analysis</small>
        </div>
      </div>

      <div className="ticket-list" style={{ marginTop: '36px' }}>
        <div className="section-heading">
          <h3>Recent Incidents</h3>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>{tickets.length} total persisted records</span>
        </div>

        {error && <p>Ticket data is unavailable until the request succeeds.</p>}
        {!error && !loading && tickets.length === 0 && <p>No persisted tickets found.</p>}
        {!error && !loading && tickets.length > 0 && (
          <div className="ticket-table" aria-label="Dashboard tickets">
            <div className="ticket-table-header dashboard-ticket-row">
              <span>Ticket</span><span>Summary</span><span>Status</span><span>Priority</span><span>Assignment group</span><span>Created</span><span>Action</span>
            </div>
            {tickets.map((ticket) => (
              <Link
                className="ticket-table-row dashboard-ticket-row"
                key={ticket.ticket_id}
                to={ticketDetailsPath(ticket.ticket_id)}
                aria-label={`View details for ticket ${ticket.ticket_id}`}
              >
                <strong>{ticket.ticket_id}</strong>
                <span>{ticket.short_description}</span>
                <span style={{ textTransform: 'capitalize' }}>{ticket.status}</span>
                <span style={{ fontWeight: 'bold' }}>{ticket.priority}</span>
                <span>{ticket.assignment_group}</span>
                <time dateTime={ticket.created_at}>{ticket.created_at}</time>
                <span className="ticket-action-label">View details →</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
