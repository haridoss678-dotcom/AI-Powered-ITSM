import { apiFetch } from './http';

export async function getDashboardSummary() {
  return apiFetch('/dashboard/summary');
}
