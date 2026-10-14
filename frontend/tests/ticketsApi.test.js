import assert from 'node:assert/strict';
import test from 'node:test';
import { ApiError } from '../src/api/http.js';
import { analyzeTicket, createTicket, getTicket, listAllTickets, updateTicket } from '../src/api/tickets.js';

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

test('ticket API client reads every page and keeps the selected employee filter', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  const firstPage = Array.from({ length: 200 }, (_, index) => ({
    ticket_id: `TKT-${String(index + 1).padStart(6, '0')}`,
  }));
  globalThis.fetch = async (url) => {
    const requestUrl = new URL(url);
    calls.push(requestUrl);
    if (requestUrl.searchParams.get('skip') === '0') {
      return jsonResponse({ items: firstPage, total: 201, limit: 200, skip: 0 });
    }
    return jsonResponse({
      items: [{ ticket_id: 'TKT-000201' }],
      total: 201,
      limit: 200,
      skip: 200,
    });
  };

  try {
    const result = await listAllTickets({ employeeId: 'EMP-002' });
    assert.equal(result.total, 201);
    assert.equal(result.items.length, 201);
    assert.equal(new Set(result.items.map((ticket) => ticket.ticket_id)).size, 201);
    assert.equal(calls.length, 2);
    assert.equal(calls[0].searchParams.get('employee_id'), 'EMP-002');
    assert.equal(calls[1].searchParams.get('employee_id'), 'EMP-002');
    assert.equal(calls[1].searchParams.get('skip'), '200');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('ticket API client rejects inconsistent or duplicate pages instead of showing false totals', async () => {
  const originalFetch = globalThis.fetch;
  let callCount = 0;
  globalThis.fetch = async () => {
    callCount += 1;
    if (callCount === 1) {
      return jsonResponse({
        items: [{ ticket_id: 'TKT-000001' }],
        total: 2,
        limit: 200,
        skip: 0,
      });
    }
    return jsonResponse({
      items: [{ ticket_id: 'TKT-000001' }],
      total: 2,
      limit: 200,
      skip: 1,
    });
  };

  try {
    await assert.rejects(
      listAllTickets(),
      /Duplicate tickets were returned/,
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('ticket detail API requests the selected stable ticket ID', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  const expectedTicket = { ticket_id: 'TKT-000042', short_description: 'Selected ticket' };
  globalThis.fetch = async (url) => {
    calls.push(new URL(url));
    return jsonResponse(expectedTicket);
  };

  try {
    const ticket = await getTicket('TKT-000042');
    assert.deepEqual(ticket, expectedTicket);
    assert.equal(calls.length, 1);
    assert.equal(calls[0].pathname, '/api/v1/tickets/TKT-000042');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('ticket detail API preserves 404 status and code for a clear not-found state', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => jsonResponse({
    error: { code: 'NOT_FOUND', message: "Ticket 'TKT-999999' was not found.", details: null },
  }, 404);

  try {
    await assert.rejects(
      getTicket('TKT-999999'),
      (error) => error instanceof ApiError
        && error.status === 404
        && error.code === 'NOT_FOUND',
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('analysis API submits an employee message to E-02 without creating a ticket', async () => {
  const originalFetch = globalThis.fetch;
  const expectedRecord = { request_id: 'AIR-000001', outcome: 'analysis_only' };
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url: new URL(url), options };
    return jsonResponse(expectedRecord);
  };

  try {
    const record = await analyzeTicket({
      employee_id: 'EMP-002',
      message: 'I cannot connect to VPN.',
    });
    assert.deepEqual(record, expectedRecord);
    assert.equal(request.url.pathname, '/api/v1/tickets/analyze');
    assert.equal(request.options.method, 'POST');
    assert.deepEqual(JSON.parse(request.options.body), {
      employee_id: 'EMP-002',
      message: 'I cannot connect to VPN.',
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('analysis ticket confirmation sends only the approved request reference', async () => {
  const originalFetch = globalThis.fetch;
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url: new URL(url), options };
    return jsonResponse({ ticket_id: 'TKT-000001' }, 201);
  };

  try {
    await createTicket({
      employee_id: 'EMP-002',
      confirmed: true,
      request_id: 'AIR-000001',
    });
    assert.equal(request.url.pathname, '/api/v1/tickets');
    assert.deepEqual(JSON.parse(request.options.body), {
      employee_id: 'EMP-002',
      confirmed: true,
      request_id: 'AIR-000001',
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('ticket update API sends the selected ID and confirmed patch payload', async () => {
  const originalFetch = globalThis.fetch;
  const expectedTicket = { ticket_id: 'TKT-000042', status: 'in_progress' };
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url: new URL(url), options };
    return jsonResponse(expectedTicket);
  };

  try {
    const result = await updateTicket('TKT-000042', {
      status: 'in_progress',
      work_note: 'Investigating.',
    });
    assert.deepEqual(result, expectedTicket);
    assert.equal(request.url.pathname, '/api/v1/tickets/TKT-000042');
    assert.equal(request.options.method, 'PATCH');
    assert.deepEqual(JSON.parse(request.options.body), {
      status: 'in_progress',
      work_note: 'Investigating.',
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});
