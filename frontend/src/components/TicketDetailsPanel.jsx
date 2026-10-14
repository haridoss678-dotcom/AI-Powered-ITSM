import { useEffect, useState } from 'react';
import { ApiError } from '../api/http.js';
import { getTicket, updateTicket } from '../api/tickets';
import { isValidTicketId } from '../utils/ticketRoutes';

function display(value) {
  return value === null || value === undefined || value === '' ? 'Not provided' : value;
}

function DetailField({ label, value }) {
  return (
    <div className="ticket-detail-field">
      <dt>{label}</dt>
      <dd>{display(value)}</dd>
    </div>
  );
}

const NEXT_STATUSES = {
  open: ['in_progress', 'resolved'],
  in_progress: ['resolved'],
  resolved: ['closed', 'in_progress'],
  closed: [],
};

export default function TicketDetailsPanel({ ticketId, onClose, allowUpdates = false }) {
  const [ticket, setTicket] = useState(null);
  const [loadedTicketId, setLoadedTicketId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('');
  const [workNote, setWorkNote] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState('');
  const [updateMessage, setUpdateMessage] = useState('');

  useEffect(() => {
    let active = true;
    setLoadedTicketId(ticketId ?? null);
    setTicket(null);
    setLoading(true);
    setError('');
    setStatus('');
    setWorkNote('');
    setUpdateError('');
    setUpdateMessage('');

    if (!isValidTicketId(ticketId)) {
      setError(ticketId ? 'The ticket ID is invalid.' : 'A ticket ID is required to view details.');
      setLoading(false);
      return () => {
        active = false;
      };
    }

    getTicket(ticketId)
      .then((result) => {
        if (!active) return;
        if (!result || result.ticket_id !== ticketId) {
          setError('The ticket details response did not match the requested ticket.');
          return;
        }
        setTicket(result);
      })
      .catch((err) => {
        if (!active) return;
        if (err instanceof ApiError && err.status === 404) {
          setError(`Ticket ${ticketId} was not found.`);
          return;
        }
        setError(err instanceof Error ? err.message : 'Unable to load ticket details.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [ticketId]);

  useEffect(() => {
    if (!onClose) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const visibleTicket = loadedTicketId === ticketId ? ticket : null;
  const visibleLoading = loadedTicketId !== ticketId || loading;
  const visibleError = loadedTicketId === ticketId ? error : '';

  const handleUpdate = async (event) => {
    event.preventDefault();
    setUpdateError('');
    setUpdateMessage('');
    const payload = {};
    if (status) payload.status = status;
    if (workNote.trim()) payload.work_note = workNote.trim();
    if (Object.keys(payload).length === 0) {
      setUpdateError('Choose a status change or enter a work note.');
      return;
    }

    setIsUpdating(true);
    try {
      const result = await updateTicket(ticketId, payload);
      if (!result || result.ticket_id !== ticketId) {
        setUpdateError('The ticket update response did not match the requested ticket.');
        return;
      }
      setTicket(result);
      setStatus('');
      setWorkNote('');
      setUpdateMessage('Ticket updated successfully.');
    } catch (err) {
      setUpdateError(err instanceof Error ? err.message : 'Unable to update ticket.');
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <section className="ticket-details" aria-labelledby="ticket-details-heading" aria-live="polite">
      <div className="section-heading">
        <h3 id="ticket-details-heading">Ticket details</h3>
        {onClose && (
          <button type="button" className="secondary-button" onClick={onClose}>
            Close details
          </button>
        )}
      </div>
      {visibleLoading && <p role="status">Loading ticket details…</p>}
      {visibleError && <div className="error-banner" role="alert">{visibleError}</div>}
      {visibleTicket && (
        <>
          <h4>{visibleTicket.ticket_id}: {visibleTicket.short_description}</h4>
          {visibleTicket.servicenow_ref?.mode === 'mock' && (
            <span className="mock-badge" aria-label="ServiceNow mock integration">MOCK</span>
          )}
          <p className="ticket-description">{display(visibleTicket.description)}</p>
          <dl className="ticket-detail-grid">
            <DetailField label="Ticket ID" value={visibleTicket.ticket_id} />
            <DetailField label="Status" value={visibleTicket.status} />
            <DetailField label="Priority" value={visibleTicket.priority} />
            <DetailField label="Category" value={visibleTicket.category} />
            <DetailField label="Subcategory" value={visibleTicket.subcategory} />
            <DetailField label="Assignment group" value={visibleTicket.assignment_group} />
            <DetailField label="Impact" value={visibleTicket.impact} />
            <DetailField label="Urgency" value={visibleTicket.urgency} />
            <DetailField label="Requester" value={visibleTicket.requester?.employee_id} />
            <DetailField label="Suggested resolution" value={visibleTicket.suggested_resolution} />
            <DetailField label="Escalated" value={visibleTicket.escalated === true ? 'Yes' : visibleTicket.escalated === false ? 'No' : null} />
            <DetailField label="Escalation reason" value={visibleTicket.escalation_reason} />
            <DetailField label="Created" value={visibleTicket.created_at} />
            <DetailField label="Updated" value={visibleTicket.updated_at} />
            <DetailField label="Resolution type" value={visibleTicket.resolution?.type} />
            <DetailField label="Resolved at" value={visibleTicket.resolution?.resolved_at} />
            <DetailField label="Resolution notes" value={visibleTicket.resolution?.notes} />
            <DetailField label="ServiceNow mode" value={visibleTicket.servicenow_ref?.mode} />
            <DetailField label="ServiceNow record" value={visibleTicket.servicenow_ref?.record_type} />
            <DetailField label="ServiceNow number" value={visibleTicket.servicenow_ref?.number} />
            <DetailField label="ServiceNow sys_id" value={visibleTicket.servicenow_ref?.sys_id} />
          </dl>
          {allowUpdates && (
            <form className="ticket-update-form" onSubmit={handleUpdate}>
              <h4>Update ticket</h4>
              <label>
                Status transition
                <select value={status} onChange={(event) => setStatus(event.target.value)}>
                  <option value="">No status change</option>
                  {NEXT_STATUSES[visibleTicket.status]?.map((nextStatus) => (
                    <option key={nextStatus} value={nextStatus}>{nextStatus}</option>
                  ))}
                </select>
              </label>
              <label>
                Work note
                <textarea
                  value={workNote}
                  onChange={(event) => setWorkNote(event.target.value)}
                  maxLength={1000}
                  rows={3}
                />
              </label>
              <button type="submit" disabled={isUpdating || (!status && !workNote.trim())}>
                {isUpdating ? 'Updating…' : 'Save update'}
              </button>
              {updateError && <div className="error-banner" role="alert">{updateError}</div>}
              {updateMessage && <p className="success-banner" role="status">{updateMessage}</p>}
            </form>
          )}
        </>
      )}
    </section>
  );
}
