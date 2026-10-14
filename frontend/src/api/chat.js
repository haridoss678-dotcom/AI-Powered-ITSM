import { apiFetch } from './http';

export async function sendChatMessage({ employeeId, message, conversationId = null }) {
  return apiFetch('/chat', {
    method: 'POST',
    body: JSON.stringify({
      employee_id: employeeId,
      message,
      conversation_id: conversationId,
    }),
  });
}

export async function listChatRequests({ employeeId, entryType, conversationId, limit = 50, skip = 0 } = {}) {
  const params = new URLSearchParams();
  if (employeeId) params.set('employee_id', employeeId);
  if (entryType) params.set('entry_type', entryType);
  if (conversationId) params.set('conversation_id', conversationId);
  params.set('limit', String(limit));
  params.set('skip', String(skip));
  return apiFetch(`/chat/requests?${params.toString()}`);
}

export async function getChatRequest(requestId) {
  return apiFetch(`/chat/requests/${encodeURIComponent(requestId)}`);
}
