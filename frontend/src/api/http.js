const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  constructor(message, { status, code } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const payload = isJson ? await response.json() : null;

  if (!response.ok) {
    const message = payload?.error?.message || 'Request failed';
    throw new ApiError(message, { status: response.status, code: payload?.error?.code });
  }

  return payload;
}

export function buildUrl(path) {
  return `${API_BASE_URL}${path}`;
}
