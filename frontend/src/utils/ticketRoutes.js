const TICKET_ID_PATTERN = /^TKT-\d{6,}$/;

export function isValidTicketId(ticketId) {
  return typeof ticketId === 'string' && TICKET_ID_PATTERN.test(ticketId);
}

export function ticketDetailsPath(ticketId) {
  if (!isValidTicketId(ticketId)) {
    throw new Error('A valid ticket ID is required to open ticket details.');
  }
  return `/dashboard/tickets/${encodeURIComponent(ticketId)}`;
}
