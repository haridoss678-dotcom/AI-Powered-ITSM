import { useCallback, useEffect, useRef, useState } from 'react';
import { createTicket, listAllTickets } from '../api/tickets';
import AnalysisIntake from '../components/AnalysisIntake';
import ChatPanel from '../components/ChatPanel';
import TicketDetailsPanel from '../components/TicketDetailsPanel';
import { useEmployee } from '../context/EmployeeContext';

const EMPTY_FORM = { confirmed: false, short_description: '', description: '' };

function display(value) {
  return value === null || value === undefined || value === '' ? 'Not provided' : value;
}

export default function EmployeeSelfServicePage() {
  const { employeeId, setEmployeeId, selectedEmployee, isValidEmployee, demoEmployees } = useEmployee();
  const [activeTab, setActiveTab] = useState('assistant'); // 'assistant' | 'create'
  const [createMode, setCreateMode] = useState('review'); // 'review' | 'manual'
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [tickets, setTickets] = useState([]);
  const [selectedTicketId, setSelectedTicketId] = useState(null);
  const [success, setSuccess] = useState('');
  const [formError, setFormError] = useState('');
  const [listError, setListError] = useState('');
  const [isLoadingTickets, setIsLoadingTickets] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const requestSequence = useRef(0);

  const loadTickets = useCallback(async () => {
    const requestId = ++requestSequence.current;
    if (!isValidEmployee) {
      setTickets([]);
      setListError(`Employee ID '${employeeId}' is not recognized. Please choose a valid employee context.`);
      setIsLoadingTickets(false);
      return;
    }

    setIsLoadingTickets(true);
    setListError('');
    try {
      const result = await listAllTickets({ employeeId });
      if (requestId === requestSequence.current) setTickets(result.items);
    } catch (err) {
      if (requestId === requestSequence.current) {
        setTickets([]);
        setListError(err instanceof Error ? err.message : 'Unable to load tickets.');
      }
    } finally {
      if (requestId === requestSequence.current) setIsLoadingTickets(false);
    }
  }, [employeeId, isValidEmployee]);

  // Reload tickets whenever employeeId changes
  useEffect(() => {
    setTickets([]);
    setSelectedTicketId(null);
    setSuccess('');
    setFormError('');
    setListError('');
    setForm({ ...EMPTY_FORM });
    void loadTickets();
    return () => {
      requestSequence.current += 1;
    };
  }, [loadTickets, employeeId]);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({
      ...current,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError('');
    setSuccess('');
    setIsSubmitting(true);
    try {
      const created = await createTicket({ ...form, employee_id: employeeId });
      setSuccess(`Ticket ${created.ticket_id} (ServiceNow: ${created.servicenow_ref?.number}) was created successfully.`);
      setForm({ ...EMPTY_FORM });
      setSelectedTicketId(created.ticket_id);
      await loadTickets();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Unable to create the ticket.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Screen 1 — Self-Service Portal</span>
          <h2>Employee Self-Service</h2>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            type="button"
            className="secondary-button"
            onClick={() => setActiveTab('assistant')}
            style={{
              background: activeTab === 'assistant' ? '#2563eb' : 'rgba(15, 23, 42, 0.5)',
              borderColor: activeTab === 'assistant' ? '#60a5fa' : 'rgba(148, 163, 184, 0.2)',
            }}
          >
            Virtual Assistant (Chat)
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={() => setActiveTab('create')}
            style={{
              background: activeTab === 'create' ? '#2563eb' : 'rgba(15, 23, 42, 0.5)',
              borderColor: activeTab === 'create' ? '#60a5fa' : 'rgba(148, 163, 184, 0.2)',
              fontWeight: 'bold',
            }}
          >
            + Create Ticket
          </button>
        </div>
      </div>

      <div className="employee-picker">
        <label htmlFor="self-service-emp">Active Employee Identity:</label>
        <select
          id="self-service-emp"
          value={employeeId}
          onChange={(e) => setEmployeeId(e.target.value)}
          aria-label="Employee ID"
        >
          {demoEmployees.map((emp) => (
            <option key={emp.id} value={emp.id}>
              {emp.label}
            </option>
          ))}
        </select>
        {selectedEmployee && (
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
            {selectedEmployee.name} ({selectedEmployee.department}) — Account: {selectedEmployee.status.replace('_', ' ')}
          </span>
        )}
      </div>

      {activeTab === 'assistant' ? (
        <ChatPanel
          employeeId={employeeId}
          onTicketCreated={(ticket) => {
            setSuccess(`Ticket ${ticket.ticket_id} (ServiceNow: ${ticket.servicenow_ref?.number}) was created successfully.`);
            setSelectedTicketId(ticket.ticket_id);
            void loadTickets();
          }}
          onOpenTicketForm={() => setActiveTab('create')}
        />
      ) : (
        <div style={{ marginTop: '20px' }}>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            <button
              type="button"
              className="secondary-button"
              onClick={() => setCreateMode('review')}
              style={{
                fontSize: '0.85rem',
                background: createMode === 'review' ? 'rgba(37, 99, 235, 0.3)' : 'rgba(15, 23, 42, 0.5)',
                borderColor: createMode === 'review' ? '#60a5fa' : 'rgba(148, 163, 184, 0.2)',
              }}
            >
              Option 1: AI-Assisted Classification Review
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={() => setCreateMode('manual')}
              style={{
                fontSize: '0.85rem',
                background: createMode === 'manual' ? 'rgba(37, 99, 235, 0.3)' : 'rgba(15, 23, 42, 0.5)',
                borderColor: createMode === 'manual' ? '#60a5fa' : 'rgba(148, 163, 184, 0.2)',
              }}
            >
              Option 2: Direct Manual Form
            </button>
          </div>

          {createMode === 'review' ? (
            <AnalysisIntake
              key={employeeId}
              employeeId={employeeId}
              onTicketCreated={(ticket) => {
                setSuccess(`Ticket ${ticket.ticket_id} (ServiceNow: ${ticket.servicenow_ref?.number}) was created successfully from your reviewed analysis.`);
                setSelectedTicketId(ticket.ticket_id);
                void loadTickets();
              }}
            />
          ) : (
            <form className="ticket-form" onSubmit={handleSubmit} style={{ marginTop: '12px' }}>
              <h4>Manual Incident Ticket Creation</h4>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem', margin: '4px 0 16px' }}>
                Create a ticket directly without pre-classification. Explicit employee confirmation is required.
              </p>

              <label>
                Short description
                <input
                  name="short_description"
                  value={form.short_description}
                  onChange={handleChange}
                  placeholder="e.g. VPN authentication failure"
                  required
                />
              </label>

              <label>
                Description
                <textarea
                  name="description"
                  value={form.description}
                  onChange={handleChange}
                  placeholder="Detailed description of your issue..."
                  rows={4}
                  required
                />
              </label>

              <label className="checkbox-row" style={{ marginTop: '10px' }}>
                <input type="checkbox" name="confirmed" checked={form.confirmed} onChange={handleChange} />
                I confirm this incident ticket should be created in ServiceNow.
              </label>

              <button
                type="submit"
                disabled={isSubmitting || !form.confirmed || !isValidEmployee}
                style={{ marginTop: '12px' }}
              >
                {isSubmitting ? 'Creating ticket…' : 'Submit Confirmed Incident Ticket'}
              </button>
            </form>
          )}
        </div>
      )}

      {formError && <div className="error-banner" role="alert" style={{ marginTop: '16px' }}>{formError}</div>}
      {success && <div className="success-banner" role="status" style={{ marginTop: '16px' }}>{success}</div>}

      <div className="ticket-list" style={{ marginTop: '36px' }}>
        <div className="section-heading">
          <div>
            <h3>My Persisted Tickets & Requests</h3>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
              Filtered for employee {employeeId} • Synchronized with MongoDB and ServiceNow mock adapter
            </span>
          </div>
          <button
            type="button"
            className="secondary-button"
            onClick={() => void loadTickets()}
            disabled={isLoadingTickets || !isValidEmployee}
          >
            {isLoadingTickets ? 'Loading…' : 'Refresh list'}
          </button>
        </div>

        {isLoadingTickets && <p role="status">Loading tickets…</p>}
        {listError && (
          <div className="error-banner" role="alert">
            <p>{listError}</p>
            <button type="button" className="secondary-button" onClick={() => void loadTickets()} disabled={isLoadingTickets}>
              Retry
            </button>
          </div>
        )}
        {!isLoadingTickets && !listError && tickets.length === 0 && <p>No tickets found for {employeeId}.</p>}
        {!isLoadingTickets && !listError && tickets.length > 0 && (
          <div className="ticket-table" aria-label="Your persisted tickets">
            <div className="ticket-table-header self-service-ticket-row">
              <span>Ticket ID</span><span>Summary</span><span>Status</span><span>Priority</span><span>ServiceNow Ref</span><span>Created</span>
            </div>
            {tickets.map((ticket) => (
              <button
                type="button"
                className="ticket-table-row self-service-ticket-row"
                key={ticket.ticket_id}
                onClick={() => setSelectedTicketId(ticket.ticket_id)}
              >
                <strong>{display(ticket.ticket_id)}</strong>
                <span>{display(ticket.short_description)}</span>
                <span style={{ textTransform: 'capitalize' }}>{display(ticket.status)}</span>
                <span style={{ fontWeight: 'bold', color: ticket.priority === 'P1' || ticket.priority === 'P2' ? '#f87171' : '#60a5fa' }}>
                  {display(ticket.priority)}
                </span>
                <span style={{ color: '#93c5fd' }}>{display(ticket.servicenow_ref?.number || '—')}</span>
                <time dateTime={ticket.created_at}>{display(ticket.created_at)}</time>
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedTicketId && (
        <TicketDetailsPanel ticketId={selectedTicketId} onClose={() => setSelectedTicketId(null)} />
      )}
    </section>
  );
}
