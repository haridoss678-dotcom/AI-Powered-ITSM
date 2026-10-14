import { useCallback, useEffect, useState } from 'react';
import { listChatRequests } from '../api/chat';
import { listAllTickets } from '../api/tickets';
import AnalysisIntake from '../components/AnalysisIntake';
import { useEmployee } from '../context/EmployeeContext';

export default function AIAnalysisPage() {
  const { employeeId, setEmployeeId, demoEmployees } = useEmployee();
  const [activeTab, setActiveTab] = useState('records'); // 'records' | 'test'
  const [dataType, setDataType] = useState('ai_telemetry'); // 'ai_telemetry' | 'tickets'
  const [filterEmp, setFilterEmp] = useState('all'); // 'all' | employeeId

  const [aiRecords, setAiRecords] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [selectedTicket, setSelectedTicket] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [aiRes, tktRes] = await Promise.all([
        listChatRequests({ limit: 50 }).catch((e) => {
          throw new Error(`AI Telemetry API error: ${e.message}`);
        }),
        listAllTickets().catch((e) => {
          throw new Error(`Tickets API error: ${e.message}`);
        }),
      ]);

      const loadedAi = aiRes.items || [];
      const loadedTkts = tktRes.items || [];

      setAiRecords(loadedAi);
      setTickets(loadedTkts);

      if (loadedAi.length > 0 && !selectedRecord) {
        setSelectedRecord(loadedAi[0]);
      }
      if (loadedTkts.length > 0 && !selectedTicket) {
        setSelectedTicket(loadedTkts[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load telemetry data from backend.');
    } finally {
      setLoading(false);
    }
  }, [selectedRecord, selectedTicket]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const filteredAiRecords = aiRecords.filter((r) => {
    if (filterEmp === 'all') return true;
    return r.employee_id === filterEmp;
  });

  const filteredTickets = tickets.filter((t) => {
    if (filterEmp === 'all') return true;
    return t.requester?.employee_id === filterEmp;
  });

  const analysis = selectedRecord?.analysis;

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Screen 7 — Model Inspection & Explainability</span>
          <h2>AI Analysis Inspector</h2>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button
            className="secondary-button"
            onClick={() => setActiveTab('records')}
            style={{
              background: activeTab === 'records' ? '#2563eb' : 'rgba(15, 23, 42, 0.5)',
              borderColor: activeTab === 'records' ? '#60a5fa' : 'rgba(148, 163, 184, 0.2)',
            }}
          >
            Persisted Records ({aiRecords.length} AI • {tickets.length} Tickets)
          </button>
          <button
            className="secondary-button"
            onClick={() => setActiveTab('test')}
            style={{
              background: activeTab === 'test' ? '#2563eb' : 'rgba(15, 23, 42, 0.5)',
              borderColor: activeTab === 'test' ? '#60a5fa' : 'rgba(148, 163, 184, 0.2)',
            }}
          >
            Ad-Hoc Analysis Form
          </button>
        </div>
      </div>

      <p style={{ color: '#9fb2cc', marginTop: '6px' }}>
        Inspect full classification telemetry, signal rules explainability, heuristic confidence calculations, and downstream workflow linkages for every transaction.
      </p>

      {error && <div className="error-banner" role="alert">{error}</div>}

      {activeTab === 'test' ? (
        <div style={{ marginTop: '20px' }}>
          <div className="employee-picker">
            <label htmlFor="ai-test-emp">Employee Context:</label>
            <select
              id="ai-test-emp"
              value={employeeId}
              onChange={(event) => setEmployeeId(event.target.value)}
            >
              {demoEmployees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.label}
                </option>
              ))}
            </select>
          </div>
          <AnalysisIntake key={employeeId} employeeId={employeeId} />
        </div>
      ) : (
        <div style={{ marginTop: '20px' }}>
          {/* Controls: Data Category & Employee Filter */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
              padding: '12px 16px',
              background: 'rgba(15, 23, 42, 0.6)',
              borderRadius: '10px',
              border: '1px solid rgba(148, 163, 184, 0.15)',
              marginBottom: '16px',
            }}
          >
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span style={{ fontSize: '0.82rem', color: '#94a3b8', fontWeight: 'bold' }}>View Dataset:</span>
              <button
                type="button"
                className="secondary-button"
                onClick={() => setDataType('ai_telemetry')}
                style={{
                  padding: '4px 10px',
                  fontSize: '0.8rem',
                  background: dataType === 'ai_telemetry' ? '#2563eb' : 'transparent',
                  borderColor: dataType === 'ai_telemetry' ? '#60a5fa' : 'rgba(148, 163, 184, 0.3)',
                }}
              >
                AI Telemetry ({filteredAiRecords.length})
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={() => setDataType('tickets')}
                style={{
                  padding: '4px 10px',
                  fontSize: '0.8rem',
                  background: dataType === 'tickets' ? '#2563eb' : 'transparent',
                  borderColor: dataType === 'tickets' ? '#60a5fa' : 'rgba(148, 163, 184, 0.3)',
                }}
              >
                Incident Tickets ({filteredTickets.length})
              </button>
            </div>

            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <label htmlFor="ai-filter-emp" style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                Filter Employee:
              </label>
              <select
                id="ai-filter-emp"
                value={filterEmp}
                onChange={(e) => setFilterEmp(e.target.value)}
                style={{
                  fontSize: '0.8rem',
                  padding: '4px 8px',
                  borderRadius: '6px',
                  background: '#1e293b',
                  color: '#fff',
                  border: '1px solid rgba(148, 163, 184, 0.3)',
                }}
              >
                <option value="all">All Employees (Global)</option>
                {demoEmployees.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.id} — {e.name}
                  </option>
                ))}
              </select>

              <button
                className="secondary-button"
                onClick={loadData}
                disabled={loading}
                style={{ padding: '4px 12px', fontSize: '0.8rem' }}
              >
                {loading ? 'Refreshing…' : 'Refresh Data'}
              </button>
            </div>
          </div>

          {loading ? (
            <div className="analysis-box">Loading records from MongoDB Atlas…</div>
          ) : dataType === 'ai_telemetry' ? (
            /* AI TELEMETRY VIEW */
            filteredAiRecords.length === 0 ? (
              <div className="analysis-box">
                No AI analysis records found for the selected filter. Run the Ticket Intake scenario or submit a chat request to generate telemetry.
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'minmax(280px, 1fr) minmax(400px, 2fr)', gap: '20px' }}>
                {/* List column */}
                <div style={{ maxHeight: '600px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {filteredAiRecords.map((r) => (
                    <button
                      key={r.request_id}
                      className="ticket-table-row"
                      onClick={() => setSelectedRecord(r)}
                      style={{
                        padding: '12px',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'flex-start',
                        gap: '4px',
                        cursor: 'pointer',
                        textAlign: 'left',
                        borderColor: selectedRecord?.request_id === r.request_id ? '#60a5fa' : 'rgba(148, 163, 184, 0.2)',
                        background:
                          selectedRecord?.request_id === r.request_id
                            ? 'rgba(37, 99, 235, 0.2)'
                            : 'rgba(15, 23, 42, 0.5)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                        <strong style={{ color: '#7dd3fc' }}>{r.request_id}</strong>
                        <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{r.outcome}</span>
                      </div>
                      <span style={{ fontSize: '0.82rem', color: '#cbd5e1', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', width: '100%' }}>
                        {r.message}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                        {r.employee_id} • {r.created_at?.slice(11, 19)}
                      </span>
                    </button>
                  ))}
                </div>

                {/* Detail column */}
                {selectedRecord && (
                  <div
                    style={{
                      background: 'rgba(15, 23, 42, 0.7)',
                      border: '1px solid rgba(148, 163, 184, 0.25)',
                      borderRadius: '12px',
                      padding: '20px',
                      maxHeight: '600px',
                      overflowY: 'auto',
                    }}
                  >
                    <div className="section-heading">
                      <div>
                        <span className="eyebrow">{selectedRecord.entry_type?.toUpperCase()} TRANSACTION</span>
                        <h3 style={{ margin: '4px 0' }}>{selectedRecord.request_id}</h3>
                      </div>
                      <span className="mock-badge">Model: {selectedRecord.llm_model_id}</span>
                    </div>

                    <div style={{ marginTop: '12px' }}>
                      <dt style={{ color: '#9fb2cc', fontSize: '0.85rem' }}>Original Employee Input:</dt>
                      <dd style={{ margin: '4px 0 0', padding: '10px 14px', borderRadius: '8px', background: 'rgba(0, 0, 0, 0.25)', fontStyle: 'italic', color: '#f1f5f9' }}>
                        "{selectedRecord.message}"
                      </dd>
                    </div>

                    {analysis && (
                      <div style={{ marginTop: '20px' }}>
                        <h4 style={{ margin: '0 0 10px', color: '#93c5fd' }}>Classification & Rules Telemetry</h4>
                        <div className="ticket-detail-grid">
                          <div className="ticket-detail-field">
                            <dt>Intent</dt>
                            <dd><strong>{analysis.intent}</strong></dd>
                          </div>
                          <div className="ticket-detail-field">
                            <dt>Category</dt>
                            <dd>{analysis.category}</dd>
                          </div>
                          <div className="ticket-detail-field">
                            <dt>Subcategory</dt>
                            <dd>{analysis.subcategory}</dd>
                          </div>
                          <div className="ticket-detail-field">
                            <dt>Priority</dt>
                            <dd style={{ color: '#f87171', fontWeight: 'bold' }}>{analysis.priority || 'N/A'}</dd>
                          </div>
                          <div className="ticket-detail-field">
                            <dt>Impact / Urgency</dt>
                            <dd>{analysis.impact || 'N/A'} / {analysis.urgency || 'N/A'}</dd>
                          </div>
                          <div className="ticket-detail-field">
                            <dt>Assignment Group</dt>
                            <dd>{analysis.assignment_group || 'N/A'}</dd>
                          </div>
                        </div>

                        <div style={{ marginTop: '14px' }}>
                          <p style={{ margin: '4px 0' }}><strong>Summary:</strong> {analysis.summary}</p>
                          <p style={{ margin: '4px 0' }}><strong>Suggested Resolution:</strong> {analysis.suggested_resolution || 'N/A'}</p>
                        </div>

                        {analysis.signals && (
                          <div style={{ marginTop: '14px', padding: '10px 14px', borderRadius: '8px', background: 'rgba(37, 99, 235, 0.1)', border: '1px solid rgba(96, 165, 250, 0.2)' }}>
                            <strong>Explainability Signals:</strong>
                            <div style={{ fontSize: '0.85rem', color: '#cbd5e1', marginTop: '4px' }}>
                              <span>LLM Propose: {analysis.signals.llm_impact || 'none'} / {analysis.signals.llm_urgency || 'none'}</span>
                              {analysis.signals.urgency_rule_hit && (
                                <span style={{ marginLeft: '12px', color: '#fde047' }}>Rule Hit: "{analysis.signals.urgency_rule_hit}"</span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {selectedRecord.confidence && (
                      <div style={{ marginTop: '20px' }}>
                        <h4 style={{ margin: '0 0 10px', color: '#93c5fd' }}>Confidence Breakdown</h4>
                        <div className="ticket-detail-grid">
                          <div className="ticket-detail-field">
                            <dt>Overall Score</dt>
                            <dd><strong>{(selectedRecord.confidence.score * 100).toFixed(0)}% ({selectedRecord.confidence.level})</strong></dd>
                          </div>
                          <div className="ticket-detail-field">
                            <dt>Threshold</dt>
                            <dd>{(selectedRecord.confidence.threshold * 100).toFixed(0)}%</dd>
                          </div>
                          <div className="ticket-detail-field">
                            <dt>Taxonomy Agreement</dt>
                            <dd>
                              {selectedRecord.confidence.components.classification_agreement !== null
                                ? `${(selectedRecord.confidence.components.classification_agreement * 100).toFixed(0)}%`
                                : 'N/A'}
                            </dd>
                          </div>
                          <div className="ticket-detail-field">
                            <dt>Retrieval Top Score</dt>
                            <dd>
                              {selectedRecord.confidence.components.retrieval_top_score !== null
                                ? `${(selectedRecord.confidence.components.retrieval_top_score * 100).toFixed(1)}%`
                                : 'N/A'}
                            </dd>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Downstream Entity References */}
                    <div style={{ marginTop: '20px' }}>
                      <h4 style={{ margin: '0 0 10px', color: '#93c5fd' }}>Workflow Outcomes & References</h4>
                      <div className="ticket-detail-grid">
                        <div className="ticket-detail-field">
                          <dt>Outcome State</dt>
                          <dd><strong>{selectedRecord.outcome}</strong></dd>
                        </div>
                        <div className="ticket-detail-field">
                          <dt>Linked Incident</dt>
                          <dd>{selectedRecord.ticket_id || selectedRecord.ticket?.ticket_id || 'None'}</dd>
                        </div>
                        <div className="ticket-detail-field">
                          <dt>Linked Automation</dt>
                          <dd>{selectedRecord.automation_action_id || selectedRecord.automation?.action_id || 'None'}</dd>
                        </div>
                        <div className="ticket-detail-field">
                          <dt>Linked Software Req</dt>
                          <dd>{selectedRecord.software_request_id || selectedRecord.software_request?.software_request_id || 'None'}</dd>
                        </div>
                      </div>
                    </div>

                    {selectedRecord.timings_ms && (
                      <div style={{ marginTop: '16px', fontSize: '0.8rem', color: '#94a3b8' }}>
                        Latency Breakdown: Analysis: {selectedRecord.timings_ms.analysis ?? '—'} ms | Retrieval: {selectedRecord.timings_ms.retrieval ?? '—'} ms | Generation: {selectedRecord.timings_ms.generation ?? '—'} ms | Total: {selectedRecord.timings_ms.total ?? '—'} ms
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          ) : (
            /* INCIDENT TICKETS VIEW */
            filteredTickets.length === 0 ? (
              <div className="analysis-box">
                No incident tickets found for the selected filter. Create a ticket in Self-Service or Ticket Intake.
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'minmax(280px, 1fr) minmax(400px, 2fr)', gap: '20px' }}>
                {/* List column */}
                <div style={{ maxHeight: '600px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {filteredTickets.map((t) => (
                    <button
                      key={t.ticket_id}
                      className="ticket-table-row"
                      onClick={() => setSelectedTicket(t)}
                      style={{
                        padding: '12px',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'flex-start',
                        gap: '4px',
                        cursor: 'pointer',
                        textAlign: 'left',
                        borderColor: selectedTicket?.ticket_id === t.ticket_id ? '#60a5fa' : 'rgba(148, 163, 184, 0.2)',
                        background:
                          selectedTicket?.ticket_id === t.ticket_id
                            ? 'rgba(37, 99, 235, 0.2)'
                            : 'rgba(15, 23, 42, 0.5)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                        <strong style={{ color: '#7dd3fc' }}>{t.ticket_id}</strong>
                        <span
                          style={{
                            fontSize: '0.72rem',
                            fontWeight: 'bold',
                            color: t.priority === 'P1' || t.priority === 'P2' ? '#f87171' : '#60a5fa',
                          }}
                        >
                          {t.priority} • {t.status}
                        </span>
                      </div>
                      <span style={{ fontSize: '0.82rem', color: '#cbd5e1', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', width: '100%' }}>
                        {t.short_description}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                        {t.requester?.name} ({t.requester?.employee_id}) • {t.created_at?.slice(11, 19)}
                      </span>
                    </button>
                  ))}
                </div>

                {/* Ticket Detail column */}
                {selectedTicket && (
                  <div
                    style={{
                      background: 'rgba(15, 23, 42, 0.7)',
                      border: '1px solid rgba(148, 163, 184, 0.25)',
                      borderRadius: '12px',
                      padding: '20px',
                      maxHeight: '600px',
                      overflowY: 'auto',
                    }}
                  >
                    <div className="section-heading">
                      <div>
                        <span className="eyebrow">PERSISTED INCIDENT TICKET</span>
                        <h3 style={{ margin: '4px 0' }}>{selectedTicket.ticket_id}</h3>
                      </div>
                      <span className="mock-badge">
                        SNOW: {selectedTicket.servicenow_ref?.number || 'INC-MOCK'}
                      </span>
                    </div>

                    <div style={{ marginTop: '12px' }}>
                      <dt style={{ color: '#9fb2cc', fontSize: '0.85rem' }}>Issue Description:</dt>
                      <dd style={{ margin: '4px 0 0', padding: '10px 14px', borderRadius: '8px', background: 'rgba(0, 0, 0, 0.25)', color: '#f1f5f9' }}>
                        {selectedTicket.description || selectedTicket.short_description}
                      </dd>
                    </div>

                    <div style={{ marginTop: '20px' }}>
                      <h4 style={{ margin: '0 0 10px', color: '#93c5fd' }}>Incident Attributes & Routing</h4>
                      <div className="ticket-detail-grid">
                        <div className="ticket-detail-field">
                          <dt>Status</dt>
                          <dd><strong>{selectedTicket.status}</strong></dd>
                        </div>
                        <div className="ticket-detail-field">
                          <dt>Priority</dt>
                          <dd style={{ color: '#f87171', fontWeight: 'bold' }}>{selectedTicket.priority}</dd>
                        </div>
                        <div className="ticket-detail-field">
                          <dt>Category</dt>
                          <dd>{selectedTicket.category} / {selectedTicket.subcategory}</dd>
                        </div>
                        <div className="ticket-detail-field">
                          <dt>Assignment Group</dt>
                          <dd>{selectedTicket.assignment_group}</dd>
                        </div>
                        <div className="ticket-detail-field">
                          <dt>Impact / Urgency</dt>
                          <dd>{selectedTicket.impact} / {selectedTicket.urgency}</dd>
                        </div>
                        <div className="ticket-detail-field">
                          <dt>Requester</dt>
                          <dd>{selectedTicket.requester?.name} ({selectedTicket.requester?.employee_id})</dd>
                        </div>
                      </div>

                      {selectedTicket.suggested_resolution && (
                        <div style={{ marginTop: '14px' }}>
                          <p style={{ margin: '4px 0' }}><strong>Suggested Resolution:</strong> {selectedTicket.suggested_resolution}</p>
                        </div>
                      )}

                      <div style={{ marginTop: '14px', padding: '10px 14px', borderRadius: '8px', background: 'rgba(37, 99, 235, 0.1)', border: '1px solid rgba(96, 165, 250, 0.2)' }}>
                        <strong>ServiceNow Synchronization:</strong>
                        <div style={{ fontSize: '0.85rem', color: '#cbd5e1', marginTop: '4px' }}>
                          <span>Record Number: <strong>{selectedTicket.servicenow_ref?.number || 'INC-MOCK'}</strong></span>
                          <span style={{ marginLeft: '12px' }}>Sys ID: <code>{selectedTicket.servicenow_ref?.sys_id || 'N/A'}</code></span>
                          <span style={{ marginLeft: '12px' }}>Source: <code>{selectedTicket.source}</code></span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          )}
        </div>
      )}
    </section>
  );
}
