import assert from 'node:assert/strict';
import test from 'node:test';
import { isValidTicketId, ticketDetailsPath } from '../src/utils/ticketRoutes.js';

test('dashboard ticket detail route uses the public ticket ID', () => {
  assert.equal(ticketDetailsPath('TKT-000041'), '/dashboard/tickets/TKT-000041');
  assert.equal(ticketDetailsPath('TKT-000042'), '/dashboard/tickets/TKT-000042');
  assert.equal(isValidTicketId('TKT-000041'), true);
  assert.equal(isValidTicketId('TKT-000042'), true);
  assert.equal(isValidTicketId('TKT-1000000'), true);
});

test('dashboard ticket detail route rejects invalid or missing IDs', () => {
  for (const ticketId of ['', null, '42', 'TKT-42', 'EMP-000042']) {
    assert.equal(isValidTicketId(ticketId), false);
    assert.throws(() => ticketDetailsPath(ticketId), /valid ticket ID/);
  }
});
