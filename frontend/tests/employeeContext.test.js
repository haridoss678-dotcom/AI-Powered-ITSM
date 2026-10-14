import assert from 'node:assert/strict';
import test from 'node:test';
import { SUPPORTED_EMPLOYEES, getEmployeeById } from '../src/context/employees.js';
import { analyzeTicketRequest, createTicket, createTicketFromRequest } from '../src/api/tickets.js';

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

test('EmployeeContext provides standard seeded employees EMP-001, EMP-002, EMP-003', () => {
  assert.equal(SUPPORTED_EMPLOYEES.length, 3);
  const ids = SUPPORTED_EMPLOYEES.map((e) => e.employee_id);
  assert.deepEqual(ids, ['EMP-001', 'EMP-002', 'EMP-003']);

  for (const id of ['EMP-001', 'EMP-002', 'EMP-003']) {
    const emp = getEmployeeById(id);
    assert.ok(emp);
    assert.equal(emp.employee_id, id);
    assert.ok(emp.name);
    assert.ok(emp.department);
  }
});

test('EmployeeContext rejects invalid or unknown employee IDs with null', () => {
  assert.equal(getEmployeeById('EMP-999'), null);
  assert.equal(getEmployeeById(''), null);
  assert.equal(getEmployeeById(null), null);
  assert.equal(getEmployeeById(undefined), null);
});

test('analyzeTicketRequest sends the currently active employee ID and does not hardcode EMP-002', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url, body: JSON.parse(options.body) });
    return jsonResponse({
      request_id: 'REQ-123456',
      intent: 'incident',
      classification: {
        category: 'Network',
        subcategory: 'VPN',
        priority: 'P2',
      },
    });
  };

  try {
    // Call with EMP-001
    await analyzeTicketRequest({ employeeId: 'EMP-001', message: 'VPN disconnected' });
    assert.equal(calls.length, 1);
    assert.equal(calls[0].body.employee_id, 'EMP-001');

    // Call with EMP-003
    await analyzeTicketRequest({ employeeId: 'EMP-003', message: 'Keycard not working' });
    assert.equal(calls.length, 2);
    assert.equal(calls[1].body.employee_id, 'EMP-003');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('createTicket and createTicketFromRequest send the currently active employee ID and confirmed flag', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url, body: JSON.parse(options.body) });
    return jsonResponse({
      ticket_id: 'TKT-000003',
      status: 'open',
      requester: { employee_id: calls[calls.length - 1]?.body?.employee_id },
      servicenow_ref: { mode: 'mock', number: 'INC000003' },
    }, 201);
  };

  try {
    await createTicket({
      employee_id: 'EMP-001',
      short_description: 'VPN issue',
      description: 'Cannot connect to corporate network.',
      confirmed: true,
    });
    assert.equal(calls.length, 1);
    assert.equal(calls[0].body.employee_id, 'EMP-001');
    assert.equal(calls[0].body.confirmed, true);
    assert.equal(calls[0].body.short_description, 'VPN issue');

    await createTicketFromRequest({
      employeeId: 'EMP-003',
      requestId: 'REQ-999999',
    });
    assert.equal(calls.length, 2);
    assert.equal(calls[1].body.employee_id, 'EMP-003');
    assert.equal(calls[1].body.confirmed, true);
    assert.equal(calls[1].body.request_id, 'REQ-999999');
  } finally {
    globalThis.fetch = originalFetch;
  }
});
