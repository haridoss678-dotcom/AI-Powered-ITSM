import { useCallback, useEffect, useState } from 'react';
import { listChatRequests, sendChatMessage } from '../api/chat';
import { createTicket, createTicketFromRequest } from '../api/tickets';

const PRESET_PROMPTS = [
  { label: 'Scenario A: VPN Incident', text: 'I cannot connect to VPN since this morning. Authentication keeps failing.' },
  { label: 'Scenario B: Password Expiry', text: 'My password has expired.' },
  { label: 'Scenario C: Outlook RAG', text: 'How do I troubleshoot Outlook synchronization?' },
  { label: 'Scenario D: Software Request', text: 'I need Visual Studio Code installed on my laptop.' },
  { label: 'Scenario E: Unsupported Question', text: 'Can you recommend lunch options around the office?' },
];

export default function ChatPanel({ employeeId, onTicketCreated, onOpenTicketForm }) {
  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: 'Hello! I am Sorim.AI, your IT Helpdesk Virtual Assistant. How can I assist you with technical issues, software requests, or troubleshooting today?',
      created_at: new Date().toLocaleTimeString(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [lastFailedMessage, setLastFailedMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Explicit confirmation state per request
  const [confirmingId, setConfirmingId] = useState(null);
  const [confirmedChecks, setConfirmedChecks] = useState({});

  // History state
  const [showHistory, setShowHistory] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Load chat history from backend
  const loadChatHistory = useCallback(async () => {
    if (!employeeId) return;
    setLoadingHistory(true);
    try {
      const res = await listChatRequests({ employeeId, limit: 15 });
      setChatHistory(res.items || []);
    } catch {
      // Non-blocking history load
    } finally {
      setLoadingHistory(false);
    }
  }, [employeeId]);

  useEffect(() => {
    void loadChatHistory();
  }, [loadChatHistory]);

  const handleSend = async (textToSend) => {
    const text = textToSend || inputMessage;
    if (!text.trim()) return;

    const userMsg = {
      sender: 'user',
      text,
      created_at: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setLastFailedMessage('');
    setLoading(true);
    setError(null);

    try {
      const chatRecord = await sendChatMessage({
        employeeId,
        message: text,
      });

      const assistantMsg = {
        sender: 'assistant',
        text: chatRecord.answer || 'I have analyzed your request.',
        record: chatRecord,
        created_at: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      void loadChatHistory();
    } catch (err) {
      setLastFailedMessage(text);
      setError(err instanceof Error ? err.message : 'Failed to send message to AI assistant');
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: `Error: ${err instanceof Error ? err.message : 'Unable to process your request.'}`,
          isError: true,
          created_at: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckboxToggle = (requestId) => {
    setConfirmedChecks((prev) => ({
      ...prev,
      [requestId]: !prev[requestId],
    }));
  };

  const handleConfirmTicket = async (record, isManual = false) => {
    const reqId = record.request_id;
    setConfirmingId(reqId);
    setError(null);
    try {
      let ticket;
      if (isManual) {
        // Direct creation from answered query
        ticket = await createTicket({
          employee_id: employeeId,
          confirmed: true,
          short_description: record.analysis?.summary || record.message || 'Escalated chat request',
          description: record.message || 'Created from virtual assistant chat',
        });
      } else {
        // Confirmed from incident proposal or escalation
        ticket = await createTicketFromRequest({
          employeeId,
          requestId: reqId,
        });
      }

      if (onTicketCreated) onTicketCreated(ticket);

      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: `Incident ticket ${ticket.ticket_id} has been created successfully (ServiceNow: ${ticket.servicenow_ref.number}) with priority ${ticket.priority}. Our support team will follow up shortly.`,
          createdTicket: ticket,
          created_at: new Date().toLocaleTimeString(),
        },
      ]);
      void loadChatHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create confirmed ticket');
    } finally {
      setConfirmingId(null);
    }
  };

  return (
    <div
      style={{
        background: 'rgba(15, 23, 42, 0.65)',
        border: '1px solid rgba(148, 163, 184, 0.25)',
        borderRadius: '16px',
        padding: '20px',
        marginTop: '16px',
      }}
    >
      {/* 1. Header with Actions & Create Ticket Option */}
      <div
        className="section-heading"
        style={{
          borderBottom: '1px solid rgba(148, 163, 184, 0.2)',
          paddingBottom: '14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '10px',
        }}
      >
        <div>
          <h3 style={{ margin: 0, color: '#93c5fd' }}>Sorim.AI Virtual Assistant</h3>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
            Multi-intent routing: RAG Knowledge • Incident Classification • Self-Heal • Software Provisioning
          </span>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span className="mock-badge">Identity: {employeeId}</span>
          <button
            type="button"
            className="secondary-button"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
            onClick={() => setShowHistory((prev) => !prev)}
          >
            {showHistory ? 'Hide History' : `History (${chatHistory.length})`}
          </button>
          {onOpenTicketForm && (
            <button
              type="button"
              className="primary-button"
              style={{
                fontSize: '0.8rem',
                padding: '6px 14px',
                background: '#2563eb',
                color: '#fff',
                border: 'none',
                borderRadius: '8px',
                fontWeight: 'bold',
                cursor: 'pointer',
              }}
              onClick={onOpenTicketForm}
            >
              + Create Ticket
            </button>
          )}
        </div>
      </div>

      {/* 2. Past AI Requests / History Drawer */}
      {showHistory && (
        <div
          style={{
            margin: '14px 0',
            padding: '14px',
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(96, 165, 250, 0.3)',
            borderRadius: '10px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <strong style={{ fontSize: '0.85rem', color: '#93c5fd' }}>Recent AI Requests (Backend Persisted)</strong>
            <button
              type="button"
              className="secondary-button"
              style={{ fontSize: '0.75rem', padding: '3px 8px' }}
              onClick={loadChatHistory}
              disabled={loadingHistory}
            >
              {loadingHistory ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
          {chatHistory.length === 0 ? (
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: 0 }}>No past requests found for {employeeId}.</p>
          ) : (
            <div style={{ maxHeight: '180px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {chatHistory.map((item) => (
                <div
                  key={item.request_id}
                  style={{
                    padding: '8px 10px',
                    background: 'rgba(30, 41, 59, 0.6)',
                    borderRadius: '6px',
                    fontSize: '0.8rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: '10px',
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', overflow: 'hidden' }}>
                    <strong style={{ color: '#7dd3fc' }}>{item.request_id}</strong>
                    <span style={{ color: '#cbd5e1', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                      {item.message}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexShrink: 0 }}>
                    <span className="mock-badge" style={{ fontSize: '0.7rem' }}>
                      {item.outcome}
                    </span>
                    {item.ticket_id && (
                      <span style={{ fontSize: '0.72rem', color: '#86efac', fontWeight: 'bold' }}>
                        {item.ticket_id}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 3. Quick Scenario Presets */}
      <div style={{ marginTop: '12px' }}>
        <span style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>Quick demo scenarios:</span>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
          {PRESET_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              className="secondary-button"
              style={{ fontSize: '0.78rem', padding: '6px 10px' }}
              onClick={() => handleSend(p.text)}
              disabled={loading}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* 4. Error Banner with Retry Button */}
      {error && (
        <div className="error-banner" style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{error}</span>
          {lastFailedMessage && (
            <button
              type="button"
              className="secondary-button"
              style={{ fontSize: '0.75rem', padding: '4px 8px' }}
              onClick={() => handleSend(lastFailedMessage)}
              disabled={loading}
            >
              Retry
            </button>
          )}
        </div>
      )}

      {/* 5. Chat Transcript */}
      <div
        style={{
          marginTop: '16px',
          maxHeight: '480px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
          paddingRight: '6px',
        }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '88%',
              background:
                msg.sender === 'user'
                  ? 'rgba(37, 99, 235, 0.35)'
                  : msg.isError
                  ? 'rgba(127, 29, 29, 0.35)'
                  : 'rgba(30, 41, 59, 0.8)',
              border:
                msg.sender === 'user'
                  ? '1px solid rgba(96, 165, 250, 0.4)'
                  : '1px solid rgba(148, 163, 184, 0.25)',
              borderRadius: '12px',
              padding: '14px 16px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', marginBottom: '6px' }}>
              <strong style={{ fontSize: '0.85rem', color: msg.sender === 'user' ? '#93c5fd' : '#7dd3fc' }}>
                {msg.sender === 'user' ? 'You' : 'Sorim.AI Assistant'}
              </strong>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{msg.created_at}</span>
            </div>

            <p style={{ margin: 0, fontSize: '0.95rem', lineHeight: '1.5', whiteSpace: 'pre-wrap' }}>
              {msg.text}
            </p>

            {/* AI Record Details Card */}
            {msg.record && (
              <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid rgba(148, 163, 184, 0.2)' }}>
                {/* Intent & Classification Badges */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '8px' }}>
                  {msg.record.analysis?.intent && (
                    <span className="mock-badge" style={{ textTransform: 'capitalize' }}>
                      Intent: {msg.record.analysis.intent.replace('_', ' ')}
                    </span>
                  )}
                  {msg.record.analysis?.category && (
                    <span className="mock-badge">
                      {msg.record.analysis.category} / {msg.record.analysis.subcategory || 'General'}
                    </span>
                  )}
                  {msg.record.confidence && (
                    <span
                      style={{
                        fontSize: '0.75rem',
                        padding: '2px 8px',
                        borderRadius: '999px',
                        background: 'rgba(34, 197, 94, 0.15)',
                        color: '#86efac',
                        border: '1px solid rgba(34, 197, 94, 0.3)',
                      }}
                    >
                      Confidence: {(msg.record.confidence.score * 100).toFixed(0)}% ({msg.record.confidence.level})
                    </span>
                  )}
                </div>

                {/* Suggested Resolution Box */}
                {msg.record.analysis?.suggested_resolution && (
                  <div
                    style={{
                      background: 'rgba(37, 99, 235, 0.1)',
                      border: '1px solid rgba(96, 165, 250, 0.25)',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      marginBottom: '10px',
                      fontSize: '0.85rem',
                    }}
                  >
                    <strong style={{ color: '#93c5fd' }}>Suggested Resolution: </strong>
                    <span style={{ color: '#e2e8f0' }}>{msg.record.analysis.suggested_resolution}</span>
                  </div>
                )}

                {/* 1. Proposed Incident Card (ticket_suggested) */}
                {msg.record.outcome === 'ticket_suggested' && msg.record.analysis && (
                  <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '14px', borderRadius: '8px', border: '1px solid rgba(248, 113, 113, 0.3)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong style={{ color: '#f87171' }}>
                        Proposed Incident: {msg.record.analysis.priority}
                      </strong>
                      <span className="mock-badge">{msg.record.analysis.assignment_group}</span>
                    </div>
                    <div style={{ margin: '8px 0', fontSize: '0.85rem', color: '#cbd5e1' }}>
                      <p style={{ margin: '2px 0' }}><strong>Summary:</strong> {msg.record.analysis.summary}</p>
                      <p style={{ margin: '2px 0' }}><strong>Impact:</strong> {msg.record.analysis.impact} | <strong>Urgency:</strong> {msg.record.analysis.urgency}</p>
                    </div>

                    <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgba(148, 163, 184, 0.15)' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer', color: '#f1f5f9' }}>
                        <input
                          type="checkbox"
                          checked={Boolean(confirmedChecks[msg.record.request_id])}
                          onChange={() => handleCheckboxToggle(msg.record.request_id)}
                        />
                        I confirm this incident ticket should be created in ServiceNow.
                      </label>

                      <button
                        type="button"
                        onClick={() => handleConfirmTicket(msg.record)}
                        disabled={confirmingId === msg.record.request_id || !confirmedChecks[msg.record.request_id]}
                        style={{
                          marginTop: '10px',
                          background: confirmedChecks[msg.record.request_id] ? '#2563eb' : 'rgba(37, 99, 235, 0.4)',
                          color: '#fff',
                          border: 'none',
                          padding: '8px 16px',
                          borderRadius: '6px',
                          cursor: confirmedChecks[msg.record.request_id] ? 'pointer' : 'not-allowed',
                          fontWeight: 'bold',
                          fontSize: '0.85rem',
                        }}
                      >
                        {confirmingId === msg.record.request_id ? 'Creating Ticket…' : 'Create Confirmed Incident Ticket'}
                      </button>
                    </div>
                  </div>
                )}

                {/* 2. Insufficient Knowledge / Escalation Card */}
                {(msg.record.outcome === 'insufficient_knowledge' || msg.record.escalation?.required) && (
                  <div style={{ background: 'rgba(127, 29, 29, 0.25)', padding: '14px', borderRadius: '8px', border: '1px solid rgba(248, 113, 113, 0.4)' }}>
                    <strong style={{ color: '#fca5a5' }}>
                      Human Support Escalation Recommended
                    </strong>
                    <p style={{ fontSize: '0.85rem', color: '#e2e8f0', margin: '6px 0' }}>
                      {msg.record.escalation?.message || 'Knowledge base evidence is insufficient to resolve this request automatically.'}
                    </p>

                    <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgba(248, 113, 113, 0.2)' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer', color: '#f1f5f9' }}>
                        <input
                          type="checkbox"
                          checked={Boolean(confirmedChecks[msg.record.request_id])}
                          onChange={() => handleCheckboxToggle(msg.record.request_id)}
                        />
                        I confirm escalating this issue to an IT support specialist.
                      </label>

                      <button
                        type="button"
                        onClick={() => handleConfirmTicket(msg.record)}
                        disabled={confirmingId === msg.record.request_id || !confirmedChecks[msg.record.request_id]}
                        style={{
                          marginTop: '10px',
                          background: confirmedChecks[msg.record.request_id] ? '#dc2626' : 'rgba(220, 38, 38, 0.4)',
                          color: '#fff',
                          border: 'none',
                          padding: '8px 16px',
                          borderRadius: '6px',
                          cursor: confirmedChecks[msg.record.request_id] ? 'pointer' : 'not-allowed',
                          fontWeight: 'bold',
                          fontSize: '0.85rem',
                        }}
                      >
                        {confirmingId === msg.record.request_id ? 'Escalating…' : 'Create Escalation Ticket'}
                      </button>
                    </div>
                  </div>
                )}

                {/* 3. Knowledge Question Answered — Option to Still Create Ticket */}
                {msg.record.outcome === 'answered' && !msg.record.escalation?.required && (
                  <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'flex-end' }}>
                    <button
                      type="button"
                      className="secondary-button"
                      style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                      onClick={() => handleConfirmTicket(msg.record, true)}
                      disabled={confirmingId === msg.record.request_id}
                    >
                      {confirmingId === msg.record.request_id ? 'Submitting…' : 'Did this not help? Create an Incident Ticket'}
                    </button>
                  </div>
                )}

                {/* 4. Autonomous Remediation Timeline */}
                {msg.record.automation && (
                  <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(148, 163, 184, 0.2)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong style={{ color: msg.record.automation.status === 'succeeded' ? '#86efac' : '#fca5a5' }}>
                        Autonomous Remediation: {msg.record.automation.status.toUpperCase()}
                      </strong>
                      <span className="mock-badge">{msg.record.automation.action_id}</span>
                    </div>
                    <p style={{ margin: '6px 0', fontSize: '0.85rem', color: '#cbd5e1' }}>
                      Linked Incident: {msg.record.automation.ticket_id} | Validation: {msg.record.automation.validation?.passed ? 'PASSED' : 'N/A'}
                    </p>
                  </div>
                )}

                {/* 5. Software Request Details */}
                {msg.record.software_request && (
                  <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(148, 163, 184, 0.2)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong style={{ color: '#86efac' }}>
                        Software Provisioned: {msg.record.software_request.software.name}
                      </strong>
                      <span className="mock-badge">ServiceNow: {msg.record.software_request.servicenow_ref.number}</span>
                    </div>
                    <p style={{ margin: '6px 0', fontSize: '0.85rem', color: '#cbd5e1' }}>
                      Status: {msg.record.software_request.status} | Job ID: {msg.record.software_request.provisioning.job_id}
                    </p>
                  </div>
                )}

                {/* 6. Knowledge Citations */}
                {msg.record.sources && msg.record.sources.length > 0 && (
                  <div style={{ marginTop: '10px' }}>
                    <span style={{ fontSize: '0.78rem', color: '#93c5fd', fontWeight: 'bold' }}>
                      Knowledge Sources & Citations ({msg.record.sources.length}):
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                      {msg.record.sources.map((s, sIdx) => (
                        <span
                          key={sIdx}
                          style={{
                            fontSize: '0.75rem',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            background: s.cited ? 'rgba(37, 99, 235, 0.3)' : 'rgba(15, 23, 42, 0.6)',
                            border: s.cited ? '1px solid #60a5fa' : '1px solid rgba(148, 163, 184, 0.2)',
                            color: s.cited ? '#93c5fd' : '#cbd5e1',
                          }}
                          title={s.excerpt}
                        >
                          [{sIdx + 1}] {s.title} ({s.category})
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div style={{ alignSelf: 'flex-start', color: '#93c5fd', fontStyle: 'italic', fontSize: '0.9rem' }}>
            Sorim.AI is analyzing your request and retrieving knowledge sources...
          </div>
        )}
      </div>

      {/* 6. Message Input & Send Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        style={{ display: 'flex', gap: '10px', marginTop: '16px' }}
      >
        <input
          type="text"
          placeholder="Describe your issue, ask a question, or request software..."
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          style={{
            flex: 1,
            padding: '12px 14px',
            borderRadius: '10px',
            border: '1px solid rgba(148, 163, 184, 0.3)',
            background: 'rgba(15, 23, 42, 0.8)',
            color: '#fff',
            font: 'inherit',
          }}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !inputMessage.trim()}
          style={{
            background: '#2563eb',
            color: '#fff',
            border: 'none',
            padding: '12px 22px',
            borderRadius: '10px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontWeight: 'bold',
          }}
        >
          {loading ? 'Sending…' : 'Send'}
        </button>
      </form>
    </div>
  );
}
