import { useEffect, useState } from 'react';
import { executeSelfHeal, listAutomationActions } from '../api/automation';
import { useEmployee } from '../context/EmployeeContext';

const PRESET_ACTIONS = [
  {
    type: 'password_reset',
    label: 'Scenario B: Password Expiry Self-Heal',
    defaultEmp: 'EMP-001',
    claim: 'My password has expired.',
  },
  {
    type: 'account_unlock',
    label: 'Account Unlock Self-Service',
    defaultEmp: 'EMP-001',
    claim: 'Account is locked after too many attempts.',
  },
  {
    type: 'password_reset',
    label: 'Privileged User Ineligibility Test',
    defaultEmp: 'EMP-003',
    claim: 'Privileged admin password reset attempt.',
  },
  {
    type: 'service_restart',
    label: 'Background Service Restart Simulation',
    defaultEmp: 'EMP-002',
    claim: 'Local background print service is unresponsive.',
  },
  {
    type: 'cache_clearing',
    label: 'Outlook Cache Clearing',
    defaultEmp: 'EMP-002',
    claim: 'Outlook cache synchronization failure.',
  },
  {
    type: 'vpn_status_check',
    label: 'VPN Gateway Status Check',
    defaultEmp: 'EMP-002',
    claim: 'VPN status check simulation.',
  },
];

export default function SelfHealPage() {
  const { employeeId, setEmployeeId, demoEmployees, isValidEmployee } = useEmployee();
  const [selectedActionType, setSelectedActionType] = useState('password_reset');
  const [claim, setClaim] = useState('My password has expired.');
  const [executing, setExecuting] = useState(false);
  const [activeAction, setActiveAction] = useState(null);
  const [actionHistory, setActionHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState(null);

  const loadHistory = async () => {
    setLoadingHistory(true);
    try {
      const res = await listAutomationActions({ limit: 10 });
      setActionHistory(res.items || []);
    } catch (err) {
      // Non-blocking history load
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && activeAction) {
        setActiveAction(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeAction]);

  const handleSelectPreset = (preset) => {
    setSelectedActionType(preset.type);
    setEmployeeId(preset.defaultEmp);
    setClaim(preset.claim);
    setActiveAction(null);
    setError(null);
  };

  const handleExecute = async (e) => {
    e?.preventDefault();
    setExecuting(true);
    setError(null);

    try {
      const res = await executeSelfHeal({
        employeeId,
        actionType: selectedActionType,
        claim,
      });
      setActiveAction(res);
      loadHistory();
    } catch (err) {
      setError(err.message || 'Self-heal execution failed');
      setActiveAction(null);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Screen 3 — Autonomous Remediation</span>
          <h2>Self-Heal Agent</h2>
        </div>
        <button className="secondary-button" onClick={loadHistory} disabled={loadingHistory}>
          {loadingHistory ? 'Refreshing...' : 'Refresh History'}
        </button>
      </div>

      <p style={{ color: '#9fb2cc', marginTop: '6px' }}>
        Complete seven-stage autonomous remediation engine with policy eligibility, mock administrative simulation, postcondition validation, and ServiceNow incident synchronization.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <div style={{ marginTop: '20px' }}>
        <h4>Select Test Scenario:</h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
          {PRESET_ACTIONS.map((preset, idx) => (
            <button
              key={idx}
              className="secondary-button"
              onClick={() => handleSelectPreset(preset)}
              style={{
                borderColor:
                  selectedActionType === preset.type && employeeId === preset.defaultEmp
                    ? '#60a5fa'
                    : 'rgba(148, 163, 184, 0.3)',
                background:
                  selectedActionType === preset.type && employeeId === preset.defaultEmp
                    ? 'rgba(37, 99, 235, 0.25)'
                    : 'rgba(15, 23, 42, 0.75)',
              }}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleExecute} className="ticket-form" style={{ maxWidth: '640px', marginTop: '20px' }}>
        <div className="employee-picker" style={{ margin: 0, maxWidth: '100%' }}>
          <label htmlFor="selfheal-emp-select">Target Employee Account:</label>
          <select
            id="selfheal-emp-select"
            value={employeeId}
            onChange={(e) => setEmployeeId(e.target.value)}
          >
            {demoEmployees.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.label}
              </option>
            ))}
          </select>
        </div>

        <label htmlFor="selfheal-claim">
          Issue Claim / Reason:
          <input
            id="selfheal-claim"
            type="text"
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
            required
          />
        </label>

        <button type="submit" disabled={executing}>
          {executing ? 'Executing Seven-Stage Workflow...' : `Execute Self-Heal: ${selectedActionType}`}
        </button>
      </form>

      {activeAction && (
        <div className="analysis-intake" style={{ marginTop: '30px' }} role="region" aria-label="Self-heal action details">
          <div className="section-heading" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
              <h3 style={{ margin: 0 }}>Execution Outcome: {activeAction.action_id}</h3>
              <span
                style={{
                  padding: '4px 10px',
                  borderRadius: '999px',
                  fontWeight: 'bold',
                  fontSize: '0.85rem',
                  background:
                    activeAction.status === 'succeeded'
                      ? 'rgba(34, 197, 94, 0.2)'
                      : activeAction.status === 'skipped_ineligible'
                      ? 'rgba(234, 179, 8, 0.2)'
                      : 'rgba(239, 68, 68, 0.2)',
                  color:
                    activeAction.status === 'succeeded'
                      ? '#86efac'
                      : activeAction.status === 'skipped_ineligible'
                      ? '#fde047'
                      : '#fca5a5',
                  border:
                    activeAction.status === 'succeeded'
                      ? '1px solid rgba(34, 197, 94, 0.4)'
                      : activeAction.status === 'skipped_ineligible'
                      ? '1px solid rgba(234, 179, 8, 0.4)'
                      : '1px solid rgba(239, 68, 68, 0.4)',
                }}
              >
                Status: {activeAction.status.toUpperCase()}
              </span>
            </div>
            <button
              type="button"
              id="close-selfheal-details-btn"
              aria-label="Close action details"
              onClick={() => setActiveAction(null)}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(148, 163, 184, 0.3)',
                color: '#f8fafc',
                fontSize: '0.85rem',
                cursor: 'pointer',
                padding: '6px 14px',
                borderRadius: '6px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                fontWeight: 600,
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.18)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)'; }}
            >
              ✕ Close
            </button>
          </div>

          <div className="ticket-detail-grid" style={{ marginTop: '16px' }}>
            <div className="ticket-detail-field">
              <dt>Action ID</dt>
              <dd>
                <strong>{activeAction.action_id}</strong>
              </dd>
            </div>
            <div className="ticket-detail-field">
              <dt>Linked Incident</dt>
              <dd>
                <strong>{activeAction.ticket_id || 'N/A'}</strong>
              </dd>
            </div>
            <div className="ticket-detail-field">
              <dt>Employee ID</dt>
              <dd>{activeAction.employee_id}</dd>
            </div>
            <div className="ticket-detail-field">
              <dt>Action Type</dt>
              <dd>{activeAction.action_type}</dd>
            </div>
            <div className="ticket-detail-field">
              <dt>Mode</dt>
              <dd>
                <span className="mock-badge">SIMULATED MOCK</span>
              </dd>
            </div>
            <div className="ticket-detail-field">
              <dt>ServiceNow Sync</dt>
              <dd>{activeAction.servicenow_update?.status} ({activeAction.servicenow_update?.detail})</dd>
            </div>
          </div>

          {activeAction.validation && (
            <div
              style={{
                marginTop: '16px',
                padding: '12px 16px',
                borderRadius: '8px',
                background: activeAction.validation.passed
                  ? 'rgba(20, 83, 45, 0.3)'
                  : 'rgba(127, 29, 29, 0.3)',
                border: activeAction.validation.passed
                  ? '1px solid rgba(74, 222, 128, 0.4)'
                  : '1px solid rgba(248, 113, 113, 0.4)',
              }}
            >
              <strong>Postcondition Validation:</strong>{' '}
              {activeAction.validation.passed ? 'PASSED — ' : 'FAILED — '}
              {activeAction.validation.detail}
            </div>
          )}

          <div style={{ marginTop: '24px' }}>
            <h4>Seven-Stage Workflow Timeline:</h4>
            <div style={{ display: 'grid', gap: '10px', marginTop: '12px' }}>
              {activeAction.steps.map((step, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(148, 163, 184, 0.2)',
                  }}
                >
                  <span
                    style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      display: 'grid',
                      placeItems: 'center',
                      fontSize: '0.8rem',
                      fontWeight: 'bold',
                      background:
                        step.status === 'completed'
                          ? '#16a34a'
                          : step.status === 'skipped'
                          ? '#64748b'
                          : '#dc2626',
                      color: '#fff',
                      flexShrink: 0,
                    }}
                  >
                    {idx + 1}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong style={{ textTransform: 'capitalize' }}>
                        {step.step.replace('_', ' ')}
                      </strong>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          color:
                            step.status === 'completed'
                              ? '#86efac'
                              : step.status === 'skipped'
                              ? '#94a3b8'
                              : '#fca5a5',
                        }}
                      >
                        {step.status.toUpperCase()}
                      </span>
                    </div>
                    <p style={{ margin: '4px 0 0', fontSize: '0.88rem', color: '#cbd5e1' }}>
                      {step.detail}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div style={{ marginTop: '36px' }}>
        <h3>Recent Self-Healing Executions</h3>
        {actionHistory.length === 0 ? (
          <p style={{ color: '#94a3b8', fontStyle: 'italic', marginTop: '10px' }}>
            No self-healing operations executed yet. Trigger a scenario above to test the autonomous workflow.
          </p>
        ) : (
          <div style={{ overflowX: 'auto', marginTop: '12px' }}>
            <div className="ticket-table" style={{ minWidth: '820px' }}>
              <div
                className="ticket-table-header"
                style={{
                  gridTemplateColumns: '130px 170px 120px 180px 1fr',
                  gap: '12px',
                  alignItems: 'center',
                }}
              >
                <span>Action ID</span>
                <span>Action Type</span>
                <span>Employee</span>
                <span>Status</span>
                <span>Timestamp</span>
              </div>
              {actionHistory.map((item) => (
                <div
                  key={item.action_id}
                  className="ticket-table-row"
                  style={{
                    gridTemplateColumns: '130px 170px 120px 180px 1fr',
                    gap: '12px',
                    alignItems: 'center',
                  }}
                  onClick={() => setActiveAction(item)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      setActiveAction(item);
                    }
                  }}
                  aria-label={`View details for ${item.action_id}`}
                >
                  <strong style={{ whiteSpace: 'nowrap' }}>{item.action_id}</strong>
                  <span style={{ whiteSpace: 'nowrap' }}>{item.action_type}</span>
                  <span style={{ whiteSpace: 'nowrap' }}>{item.employee_id}</span>
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '0.82rem',
                      fontWeight: '600',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: '100%',
                      background:
                        item.status === 'succeeded'
                          ? 'rgba(34, 197, 94, 0.15)'
                          : item.status === 'skipped_ineligible'
                          ? 'rgba(234, 179, 8, 0.15)'
                          : 'rgba(239, 68, 68, 0.15)',
                      color:
                        item.status === 'succeeded'
                          ? '#86efac'
                          : item.status === 'skipped_ineligible'
                          ? '#fde047'
                          : '#fca5a5',
                      border:
                        item.status === 'succeeded'
                          ? '1px solid rgba(34, 197, 94, 0.3)'
                          : item.status === 'skipped_ineligible'
                          ? '1px solid rgba(234, 179, 8, 0.3)'
                          : '1px solid rgba(239, 68, 68, 0.3)',
                    }}
                    title={item.status}
                  >
                    {item.status}
                  </span>
                  <time style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: '#cbd5e1' }}>
                    {item.started_at}
                  </time>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
