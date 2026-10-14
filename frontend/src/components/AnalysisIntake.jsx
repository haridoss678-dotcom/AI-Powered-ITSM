import { useRef, useState } from 'react';
import { analyzeTicket, createTicket } from '../api/tickets';

function AnalysisField({ label, value }) {
  return (
    <div className="ticket-detail-field">
      <dt>{label}</dt>
      <dd>{value === null || value === undefined || value === '' ? 'Not provided' : value}</dd>
    </div>
  );
}

export default function AnalysisIntake({ employeeId, onTicketCreated }) {
  const [message, setMessage] = useState('');
  const [record, setRecord] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const creatingRef = useRef(false);

  const handleAnalyze = async (event) => {
    event.preventDefault();
    setRecord(null);
    setError('');
    setNotice('');
    setConfirmed(false);
    setIsAnalyzing(true);
    try {
      const result = await analyzeTicket({ employee_id: employeeId, message });
      if (!result?.request_id || !result.analysis) {
        throw new Error('The analysis response did not include a reviewable result.');
      }
      setRecord(result);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Unable to analyze this request.';
      if (errMsg.includes('503') || errMsg.includes('unavailable') || errMsg.includes('memory') || errMsg.includes('model_unavailable')) {
        setError(`Local AI model is currently offline (${errMsg}). You can submit an incident ticket directly using the manual form.`);
      } else {
        setError(errMsg);
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleConfirm = async () => {
    if (!record || creatingRef.current || !confirmed) return;
    creatingRef.current = true;
    setError('');
    setNotice('');
    setIsCreating(true);
    try {
      const ticket = await createTicket({
        employee_id: employeeId,
        confirmed: true,
        request_id: record.request_id,
      });
      setNotice(`Ticket ${ticket.ticket_id} (ServiceNow: ${ticket.servicenow_ref?.number}) was created from your reviewed analysis.`);
      setRecord(null);
      setConfirmed(false);
      onTicketCreated?.(ticket);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create the ticket.');
    } finally {
      creatingRef.current = false;
      setIsCreating(false);
    }
  };

  const analysis = record?.analysis;
  const canCreateTicket = Boolean(
    record?.escalation?.ticket_option_available
    && (
      analysis?.intent === 'incident'
      || (analysis?.intent === 'knowledge_question' && record.escalation.required)
    ),
  );

  return (
    <section className="analysis-intake" aria-labelledby="analysis-intake-heading">
      <p className="eyebrow">Local AI analysis</p>
      <h3 id="analysis-intake-heading">Review a request before ticket creation</h3>
      <form className="ticket-form" onSubmit={handleAnalyze}>
        <label>
          Describe the issue or request
          <textarea
            value={message}
            onChange={(event) => {
              setMessage(event.target.value);
              setRecord(null);
              setError('');
              setNotice('');
              setConfirmed(false);
            }}
            maxLength={2000}
            rows={4}
            required
            disabled={isAnalyzing || isCreating}
            placeholder="e.g. I cannot connect to VPN since this morning. Authentication keeps failing."
          />
        </label>
        <button type="submit" disabled={!employeeId || !message.trim() || isAnalyzing || isCreating}>
          {isAnalyzing ? 'Analyzing…' : 'Analyze request'}
        </button>
      </form>

      {isAnalyzing && <p role="status">Analyzing with the configured local model…</p>}
      {error && <div className="error-banner" role="alert">{error}</div>}
      {notice && <div className="success-banner" role="status">{notice}</div>}

      {record && analysis && (
        <div className="analysis-result" aria-live="polite">
          <p>Request {record.request_id} · {record.llm_model_id}</p>
          <dl className="ticket-detail-grid">
            <AnalysisField label="Intent" value={analysis.intent} />
            <AnalysisField label="Category" value={analysis.category} />
            <AnalysisField label="Subcategory" value={analysis.subcategory} />
            <AnalysisField label="Priority" value={analysis.priority} />
            <AnalysisField label="Impact" value={analysis.impact} />
            <AnalysisField label="Urgency" value={analysis.urgency} />
            <AnalysisField label="Assignment group" value={analysis.assignment_group} />
            <AnalysisField label="Summary" value={analysis.summary} />
            <AnalysisField label="Suggested resolution" value={analysis.suggested_resolution} />
            <AnalysisField
              label="Confidence"
              value={record.confidence ? `${Math.round(record.confidence.score * 100)}% — ${record.confidence.level} (${record.confidence.method})` : 'N/A'}
            />
          </dl>
          {record.escalation?.required && (
            <p className="error-banner" role="status">
              Human review recommended: {record.escalation.message || record.escalation.reason}.
            </p>
          )}

          <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid rgba(148, 163, 184, 0.2)' }}>
            <p>Review the classification above. Explicit confirmation is required before ticket creation.</p>
            <label className="checkbox-row" style={{ margin: '10px 0' }}>
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
                disabled={isCreating}
              />
              <span>I confirm this incident ticket should be created in ServiceNow.</span>
            </label>

            {canCreateTicket ? (
              <button
                type="button"
                onClick={handleConfirm}
                disabled={isCreating || isAnalyzing || !confirmed}
                style={{
                  background: confirmed ? '#2563eb' : '#475569',
                  cursor: confirmed ? 'pointer' : 'not-allowed',
                }}
              >
                {isCreating ? 'Creating ticket…' : 'Confirm and create ticket'}
              </button>
            ) : (
              <p role="status">
                {analysis.intent === 'knowledge_question'
                  ? 'No incident ticket is suggested for this knowledge question.'
                  : 'This request requires a workflow that is not available in this phase; no ticket was created.'}
              </p>
            )}

            <button
              type="button"
              className="secondary-button"
              onClick={() => {
                setRecord(null);
                setConfirmed(false);
              }}
              disabled={isCreating}
              style={{ marginLeft: '10px' }}
            >
              Discard analysis
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
