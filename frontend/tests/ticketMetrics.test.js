import assert from 'node:assert/strict';
import test from 'node:test';
import { summarizeTickets } from '../src/utils/ticketMetrics.js';

test('dashboard metrics are derived from the same persisted ticket records', () => {
  const tickets = [
    { ticket_id: 'TKT-000001', status: 'open', escalated: false, resolution: null },
    { ticket_id: 'TKT-000002', status: 'in_progress', escalated: true, resolution: null },
    { ticket_id: 'TKT-000003', status: 'resolved', escalated: false, resolution: { type: 'automation' } },
    { ticket_id: 'TKT-000004', status: 'resolved', escalated: false, resolution: { type: 'human' } },
    { ticket_id: 'TKT-000005', status: 'closed', escalated: false, resolution: { type: 'automation' } },
  ];

  assert.deepEqual(summarizeTickets(tickets), {
    total: 5,
    open: 2,
    inProgress: 1,
    resolved: 2,
    aiResolved: 2,
    escalated: 1,
  });
});

test('dashboard metrics report zero only for a successfully loaded empty dataset', () => {
  assert.deepEqual(summarizeTickets([]), {
    total: 0,
    open: 0,
    inProgress: 0,
    resolved: 0,
    aiResolved: 0,
    escalated: 0,
  });
  assert.throws(() => summarizeTickets(null), TypeError);
});
