import { useState } from 'react';
import { Link } from 'react-router-dom';
import { analyzeTicketRequest, createTicket, createTicketFromRequest } from '../api/tickets';
import { useEmployee } from '../context/EmployeeContext';

const VPN_BENCHMARK_PROMPT =
  'I cannot connect to VPN since this morning. Authentication keeps failing.';

export default function TicketIntakePage() {
  const { employeeId, setEmployeeId, selectedEmployee, isValidEmployee, demoEmployees, error: employeeError } = useEmployee();
  const [message, setMessage] = useState(VPN_BENCHMARK_PROMPT);
  const [analyzing, setAnalyzing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [modelOffline, setModelOffline] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [createdTicket, setCreatedTicket] = useState(null);
  const [error, setError] = useState(null);

  // Manual fallback fields if AI is offline
  const [manualSummary, setManualSummary] = useState('VPN authentication failure');
  const [manualPriority, setManualPriority] = useState('P2');
  const [manualCategory, setManualCategory] = useState('Network');
  const [manualSubcategory, setManualSubcategory] = useState('VPN');

  const handleAnalyze = async (e, textOverride = null) => {
    e?.preventDefault?.();
    const textToAnalyze = (textOverride || message || '').trim();
    if (!textToAnalyze) return;

    setAnalyzing(true);
    setError(null);
    setCreatedTicket(null);
    setConfirmed(false);
    setModelOffline(false);

    try {
      const data = await analyzeTicketRequest({ employeeId, message: textToAnalyze });
      setAnalysisResult(data);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      if (errMsg.includes('503') || errMsg.includes('unavailable') || errMsg.includes('memory') || errMsg.includes('model_unavailable')) {
        setModelOffline(true);
        setError(`Local AI Model is unavailable for inference (${errMsg}). You can proceed with standard incident intake below.`);
      } else {
        setError(errMsg || 'Failed to analyze ticket request');
      }
      setAnalysisResult(null);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleConfirmCreate = async () => {
    if (!confirmed || submitting || !isValidEmployee) return;

    setSubmitting(true);
    setError(null);

    try {
      let ticket;
      if (analysisResult?.request_id) {
        // AI-analyzed confirmed route (Contract E-03 form a)
        ticket = await createTicketFromRequest({
          employeeId,
          requestId: analysisResult.request_id,
        });
      } else {
        // Direct manual confirmed route (Contract E-03 form b)
        ticket = await createTicket({
          employee_id: employeeId,
          short_description: manualSummary || 'VPN authentication failure',
          description: message,
          confirmed: true,
        });
      }
      setCreatedTicket(ticket);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create confirmed ticket');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setMessage(VPN_BENCHMARK_PROMPT);
    setAnalysisResult(null);
    setModelOffline(false);
    setConfirmed(false);
    setCreatedTicket(null);
    setError(null);
    setManualSummary('VPN authentication failure');
    setManualPriority('P2');
    setManualCategory('Network');
    setManualSubcategory('VPN');
  };

  const analysis = analysisResult?.analysis;

  return (
    <div className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Screen 2 — AI-Assisted Intake</span>
          <h2>Incident Ticket Intake</h2>
        </div>
        <button
          type="button"
          className="secondary-button"
          onClick={handleReset}
          disabled={analyzing || submitting}
          id="intake-reset-btn"
        >
          Reset Scenario
        </button>
      </div>

      <p style={{ color: '#9fb2cc', marginTop: '6px' }}>
        AI-assisted incident triage with mandatory employee review and explicit confirmation before creation.
      </p>

      {employeeError && <div className="error-banner">{employeeError}</div>}
      {error && <div className="error-banner">{error}</div>}

      <div className="employee-picker">
        <label htmlFor="intake-emp-select">Requester Employee Context:</label>
        <select
          id="intake-emp-select"
          value={employeeId}
          onChange={(e) => setEmployeeId(e.target.value)}
        >
          {demoEmployees.map((emp) => (
            <option key={emp.id} value={emp.id}>
              {emp.label}
            </option>
          ))}
        </select>
        {selectedEmployee && (
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
            {selectedEmployee.name} ({selectedEmployee.department})
          </span>
        )}
      </div>

      <form onSubmit={handleAnalyze} className="ticket-form" style={{ maxWidth: '720px' }}>
        <label htmlFor="intake-message">
          Employee Issue Description:
          <textarea
            id="intake-message"
            rows={4}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Describe your technical problem..."
            required
            disabled={analyzing || submitting}
          />
        </label>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            type="submit"
            id="intake-analyze-btn"
            disabled={analyzing || submitting || !message.trim() || !isValidEmployee}
          >
            {analyzing ? 'Analyzing with AI…' : 'Analyse Issue & Propose Classification'}
          </button>
          <button
            type="button"
            className="secondary-button"
            id="intake-preset-vpn-btn"
            onClick={() => {
              setMessage(VPN_BENCHMARK_PROMPT);
              setAnalysisResult(null);
              setCreatedTicket(null);
              setError(null);
              void handleAnalyze(null, VPN_BENCHMARK_PROMPT);
            }}
            disabled={analyzing || submitting}
          >
            {analyzing ? 'Analyzing Scenario…' : 'Run Mandatory VPN Scenario'}
          </button>
        </div>
      </form>

      {/* AI Analysis Proposal Section */}
      {analysis && (
        <div className="analysis-intake" style={{ marginTop: '28px' }}>
          <div className="section-heading">
            <h3>AI Classification Proposal</h3>
            <span className="mock-badge">Ref: {analysisResult.request_id}</span>
          </div>

          <div className="ticket-detail-grid" style={{ marginTop: '16px' }}>
            <div className="ticket-detail-field">
              <dt>Predicted Intent</dt>
              <dd>
                <strong>{analysis.intent}</strong>
              </dd>
            </div>
            <div className="ticket-detail-field">
              <dt>Category / Subcategory</dt>
              <dd>
                {analysis.category} / {analysis.subcategory}
              </dd>
            </div>
            <div className="ticket-detail-field">
              <dt>Priority (Derived)</dt>
              <dd>
                <span
                  style={{
                    color: analysis.priority === 'P1' || analysis.priority === 'P2' ? '#f87171' : '#60a5fa',
                    fontWeight: 'bold',
                  }}
                >
                  {analysis.priority || 'N/A'}
                </span>
              </dd>
            </div>
            <div className="ticket-detail-field">
              <dt>Impact / Urgency</dt>
              <dd>
                {analysis.impact} / {analysis.urgency}
              </dd>
            </div>
            <div className="ticket-detail-field">
              <dt>Assignment Group</dt>
              <dd>{analysis.assignment_group}</dd>
            </div>
            <div className="ticket-detail-field">
              <dt>AI Model</dt>
              <dd>{analysisResult.llm_model_id}</dd>
            </div>
          </div>

          <div style={{ marginTop: '16px' }}>
            <p>
              <strong>Summary:</strong> {analysis.summary}
            </p>
            <p>
              <strong>Suggested Resolution:</strong> {analysis.suggested_resolution || 'N/A'}
            </p>
          </div>

          {!createdTicket && (
            <div
              style={{
                marginTop: '20px',
                padding: '16px',
                background: 'rgba(37, 99, 235, 0.1)',
                borderRadius: '10px',
                border: '1px solid rgba(96, 165, 250, 0.3)',
              }}
            >
              <h4>Mandatory Employee Confirmation</h4>
              <p style={{ color: '#cbd5e1', fontSize: '0.9rem' }}>
                Review the classification details above. The system requires your explicit confirmation before creating the official IT incident and mock ServiceNow record.
              </p>

              <label className="checkbox-row" style={{ marginTop: '12px' }}>
                <input
                  type="checkbox"
                  id="confirm-intake-checkbox"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                />
                <span>I confirm this classification and request ticket submission.</span>
              </label>

              <button
                type="button"
                id="intake-create-btn"
                onClick={handleConfirmCreate}
                disabled={!confirmed || submitting || !isValidEmployee}
                style={{
                  marginTop: '14px',
                  background: confirmed ? '#2563eb' : '#475569',
                  color: '#fff',
                  border: 'none',
                  padding: '10px 18px',
                  borderRadius: '8px',
                  cursor: confirmed ? 'pointer' : 'not-allowed',
                  fontWeight: 'bold',
                }}
              >
                {submitting ? 'Submitting to ServiceNow...' : 'Confirm and Create Incident'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Model Offline Fallback Intake Form */}
      {modelOffline && !analysis && (
        <div
          className="analysis-intake"
          style={{
            marginTop: '28px',
            background: 'rgba(30, 41, 59, 0.7)',
            border: '1px solid rgba(148, 163, 184, 0.3)',
            borderRadius: '12px',
            padding: '20px',
          }}
        >
          <div className="section-heading">
            <h3 style={{ color: '#93c5fd' }}>Standard Incident Intake (Model Offline)</h3>
            <span className="mock-badge" style={{ color: '#fca5a5', borderColor: '#f87171' }}>
              Manual Direct Submission
            </span>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#cbd5e1', marginTop: '6px' }}>
            Even when AI model inference is unavailable, you can submit confirmed IT incidents directly to ServiceNow and MongoDB.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px', marginTop: '14px' }}>
            <label>
              Summary
              <input
                type="text"
                value={manualSummary}
                onChange={(e) => setManualSummary(e.target.value)}
                required
              />
            </label>
            <label>
              Priority
              <select value={manualPriority} onChange={(e) => setManualPriority(e.target.value)}>
                <option value="P1">P1 — Critical (Outage)</option>
                <option value="P2">P2 — High Urgency</option>
                <option value="P3">P3 — Moderate</option>
                <option value="P4">P4 — Low</option>
              </select>
            </label>
            <label>
              Category
              <input
                type="text"
                value={manualCategory}
                onChange={(e) => setManualCategory(e.target.value)}
              />
            </label>
            <label>
              Subcategory
              <input
                type="text"
                value={manualSubcategory}
                onChange={(e) => setManualSubcategory(e.target.value)}
              />
            </label>
          </div>

          {!createdTicket && (
            <div style={{ marginTop: '18px', paddingTop: '14px', borderTop: '1px solid rgba(148, 163, 184, 0.2)' }}>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  id="confirm-manual-checkbox"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                />
                <span>I confirm this incident ticket should be created in ServiceNow.</span>
              </label>

              <button
                type="button"
                id="intake-manual-create-btn"
                onClick={handleConfirmCreate}
                disabled={!confirmed || submitting || !isValidEmployee}
                style={{
                  marginTop: '14px',
                  background: confirmed ? '#2563eb' : '#475569',
                  color: '#fff',
                  border: 'none',
                  padding: '10px 18px',
                  borderRadius: '8px',
                  cursor: confirmed ? 'pointer' : 'not-allowed',
                  fontWeight: 'bold',
                }}
              >
                {submitting ? 'Creating Ticket…' : 'Confirm and Create Incident'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Success Notification */}
      {createdTicket && (
        <div className="success-banner" style={{ marginTop: '24px' }}>
          <h3>Incident Ticket Created Successfully</h3>
          <div className="ticket-detail-grid" style={{ marginTop: '14px' }}>
            <div className="ticket-detail-field">
              <dt>Ticket ID</dt>
              <dd>
                <strong>{createdTicket.ticket_id}</strong>
              </dd>
            </div>
            <div className="ticket-detail-field">
              <dt>ServiceNow Incident Number</dt>
              <dd>
                <strong>{createdTicket.servicenow_ref.number}</strong>
              </dd>
            </div>
            <div className="ticket-detail-field">
              <dt>Status</dt>
              <dd>{createdTicket.status}</dd>
            </div>
            <div className="ticket-detail-field">
              <dt>Priority</dt>
              <dd>{createdTicket.priority}</dd>
            </div>
            <div className="ticket-detail-field">
              <dt>ServiceNow Mode</dt>
              <dd>
                <span className="mock-badge">{createdTicket.servicenow_ref.mode.toUpperCase()}</span>
              </dd>
            </div>
            <div className="ticket-detail-field">
              <dt>ServiceNow Sys ID</dt>
              <dd style={{ fontSize: '0.8rem' }}>{createdTicket.servicenow_ref.sys_id}</dd>
            </div>
          </div>
          <div style={{ marginTop: '18px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <Link className="secondary-button" to={`/dashboard/tickets/${encodeURIComponent(createdTicket.ticket_id)}`} id="view-ticket-link">
              View Ticket Details →
            </Link>
            <Link className="secondary-button" to="/dashboard" id="view-dashboard-link">
              View on Dashboard →
            </Link>
            <Link className="secondary-button" to="/self-service" id="view-selfservice-link">
              View in Self-Service Portal →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
