import { useEffect, useState } from 'react';
import { fetchHealth } from '../api/health';

export default function ConnectionStatus() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const data = await fetchHealth();
        if (active) {
          setHealth(data);
          setError('');
        }
      } catch (err) {
        if (active) {
          setHealth(null);
          setError(err.message || 'Backend disconnected');
        }
      }
    };

    load();
    const interval = window.setInterval(load, 15000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  const dbOk = health?.checks?.database?.status === 'ok';
  const llmOk = health?.checks?.llm?.status === 'ok';
  const connected = !!health && (health.status === 'ok' || dbOk);

  let label = 'Backend disconnected';
  if (connected) {
    if (health.status === 'ok') {
      label = 'Backend connected';
    } else if (dbOk && !llmOk) {
      label = 'Connected (LLM offline)';
    } else {
      label = 'Connected (Degraded)';
    }
  } else if (error) {
    label = error;
  }

  return (
    <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
      <span className="status-dot" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
