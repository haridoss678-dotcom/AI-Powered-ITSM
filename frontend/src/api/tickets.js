import { apiFetch } from './http.js';

const PAGE_SIZE = 200;

export async function listTickets({ employeeId, status, limit, skip } = {}) {
  const params = new URLSearchParams();
  if (employeeId) params.set('employee_id', employeeId);
  if (status) params.set('status', status);
  if (limit !== undefined) params.set('limit', String(limit));
  if (skip !== undefined) params.set('skip', String(skip));
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch(`/tickets${query}`);
}

export async function listAllTickets({ employeeId } = {}) {
  const firstPage = await listTickets({ employeeId, limit: PAGE_SIZE, skip: 0 });
  if (!Array.isArray(firstPage?.items) || !Number.isSafeInteger(firstPage.total) || firstPage.total < 0) {
    throw new Error('The ticket list response was invalid.');
  }

  const tickets = [...firstPage.items];
  const expectedTotal = firstPage.total;
  const ticketIds = new Set(tickets.map((ticket) => ticket.ticket_id));

  while (tickets.length < expectedTotal) {
    const page = await listTickets({ employeeId, limit: PAGE_SIZE, skip: tickets.length });
    if (!Array.isArray(page?.items) || page.total !== expectedTotal) {
      throw new Error('Ticket data changed while loading. Refresh the list and try again.');
    }
    if (page.items.length === 0) {
      throw new Error('The ticket list response ended before all tickets were loaded.');
    }

    for (const ticket of page.items) {
      if (ticketIds.has(ticket.ticket_id)) {
        throw new Error('Duplicate tickets were returned while loading. Refresh the list and try again.');
      }
      ticketIds.add(ticket.ticket_id);
      tickets.push(ticket);
    }
  }

  if (tickets.length !== expectedTotal) {
    throw new Error('The ticket list response did not match its reported total.');
  }

  return { items: tickets, total: expectedTotal };
}

export async function getTicket(ticketId) {
  return apiFetch(`/tickets/${encodeURIComponent(ticketId)}`);
}

export async function createTicket(payload) {
  return apiFetch('/tickets', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function analyzeTicket(payload) {
  return apiFetch('/tickets/analyze', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateTicket(ticketId, payload) {
  return apiFetch(`/tickets/${encodeURIComponent(ticketId)}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function createTicketFromRequest({ employeeId, requestId }) {
  return createTicket({
    employee_id: employeeId,
    confirmed: true,
    request_id: requestId,
  });
}

export async function analyzeTicketRequest({ employeeId, message }) {
  return analyzeTicket({
    employee_id: employeeId,
    message,
  });
}

