import { apiFetch } from './http';

export async function listEmployees() {
  return apiFetch('/employees');
}

export async function getEmployee(employeeId) {
  return apiFetch(`/employees/${encodeURIComponent(employeeId)}`);
}

export async function createEmployee(payload) {
  return apiFetch('/employees', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
