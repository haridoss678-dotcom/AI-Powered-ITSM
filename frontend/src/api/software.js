import { apiFetch } from './http';

export async function listSoftwareCatalogue() {
  return apiFetch('/software/catalogue');
}

export async function getSoftwareCatalogueItem(itemId) {
  return apiFetch(`/software/catalogue/${encodeURIComponent(itemId)}`);
}

export async function createSoftwareRequest({ employeeId, softwareName, requestId = null }) {
  return apiFetch('/software-requests', {
    method: 'POST',
    body: JSON.stringify({
      employee_id: employeeId,
      software_name: softwareName,
      request_id: requestId,
    }),
  });
}

export async function listSoftwareRequests({ status, employeeId, limit = 50, skip = 0 } = {}) {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (employeeId) params.set('employee_id', employeeId);
  params.set('limit', String(limit));
  params.set('skip', String(skip));
  return apiFetch(`/software-requests?${params.toString()}`);
}

export async function getSoftwareRequest(softwareRequestId) {
  return apiFetch(`/software-requests/${encodeURIComponent(softwareRequestId)}`);
}
