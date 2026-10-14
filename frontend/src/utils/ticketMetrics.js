const OPEN_STATUSES = new Set(['open', 'in_progress']);
const RESOLVED_STATUSES = new Set(['resolved', 'closed']);

export function summarizeTickets(tickets) {
  if (!Array.isArray(tickets)) {
    throw new TypeError('Ticket metrics require an array of persisted ticket records.');
  }

  return tickets.reduce((summary, ticket) => {
    summary.total += 1;
    if (OPEN_STATUSES.has(ticket.status)) summary.open += 1;
    if (ticket.status === 'in_progress') summary.inProgress += 1;
    if (ticket.status === 'resolved') summary.resolved += 1;
    if (ticket.escalated === true) summary.escalated += 1;
    if (RESOLVED_STATUSES.has(ticket.status) && ticket.resolution?.type === 'automation') {
      summary.aiResolved += 1;
    }
    return summary;
  }, { total: 0, open: 0, inProgress: 0, resolved: 0, aiResolved: 0, escalated: 0 });
}
