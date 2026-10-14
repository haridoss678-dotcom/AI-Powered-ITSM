import { apiFetch } from './http';

export async function getAuditLogs({ requestId, entityType, entityId, eventType, limit = 50, skip = 0 } = {}) {
  const params = new URLSearchParams();
  if (requestId) params.set('request_id', requestId);
  if (entityType) params.set('entity_type', entityType);
  if (entityId) params.set('entity_id', entityId);
  if (eventType) params.set('event_type', eventType);
  params.set('limit', String(limit));
  params.set('skip', String(skip));
  return apiFetch(`/audit-logs?${params.toString()}`);
}
