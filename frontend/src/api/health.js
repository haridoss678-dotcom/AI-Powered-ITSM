const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`, {
    headers: { 'Content-Type': 'application/json' },
  });
  if (response.headers.get('content-type')?.includes('application/json')) {
    const data = await response.json();
    return { ...data, httpStatus: response.status };
  }
  throw new Error('Health check failed');
}
