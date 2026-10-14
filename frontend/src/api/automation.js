import { apiFetch } from './http';

export async function listAutomationActions({ status, employeeId, limit = 50, skip = 0 } = {}) {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (employeeId) params.set('employee_id', employeeId);
  params.set('limit', String(limit));
  params.set('skip', String(skip));
  return apiFetch(`/automation/actions?${params.toString()}`);
}

export async function executeSelfHeal({ employeeId, actionType, claim = null }) {
  return apiFetch('/automation/execute', {
    method: 'POST',
    body: JSON.stringify({
      employee_id: employeeId,
      action_type: actionType,
      claim,
    }),
  });
}
