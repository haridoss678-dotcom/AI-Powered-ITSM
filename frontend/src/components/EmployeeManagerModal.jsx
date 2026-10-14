import { useState } from 'react';
import { useEmployee } from '../context/EmployeeContext';

export default function EmployeeManagerModal({ isOpen, onClose }) {
  const { addNewEmployee } = useEmployee();
  const [form, setForm] = useState({
    employee_id: '',
    name: '',
    email: '',
    department: 'Engineering',
    account_status: 'active',
    privileged: false,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const payload = {
        name: form.name.trim(),
        email: form.email.trim(),
        department: form.department.trim(),
        account_status: form.account_status,
        privileged: form.privileged,
      };
      if (form.employee_id.trim()) {
        payload.employee_id = form.employee_id.trim().toUpperCase();
      }
      await addNewEmployee(payload);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to register employee');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0, 0, 0, 0.75)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '16px',
        backdropFilter: 'blur(4px)',
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="emp-modal-title"
    >
      <div
        className="panel"
        style={{
          maxWidth: '480px',
          width: '100%',
          background: '#0f172a',
          border: '1px solid rgba(96, 165, 250, 0.3)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
        }}
      >
        <div className="section-heading">
          <div>
            <span className="eyebrow">Directory Management</span>
            <h3 id="emp-modal-title" style={{ margin: '4px 0 0' }}>Register New Employee</h3>
          </div>
          <button
            type="button"
            className="secondary-button"
            onClick={onClose}
            style={{ padding: '4px 10px', fontSize: '0.9rem' }}
          >
            ✕
          </button>
        </div>

        <p style={{ fontSize: '0.85rem', color: '#94a3b8', margin: '8px 0 16px' }}>
          Create and persist a canonical employee profile in MongoDB Atlas for end-to-end ticketing, self-heal, and software requests.
        </p>

        {error && <div className="error-banner" style={{ marginBottom: '14px' }}>{error}</div>}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.85rem', gap: '4px' }}>
            <span>Employee ID (Optional, defaults to auto-generated EMP-xxx):</span>
            <input
              type="text"
              placeholder="e.g. EMP-005"
              value={form.employee_id}
              onChange={(e) => setForm({ ...form, employee_id: e.target.value })}
            />
          </label>

          <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.85rem', gap: '4px' }}>
            <span>Full Name: *</span>
            <input
              type="text"
              placeholder="e.g. Alex Morgan"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </label>

          <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.85rem', gap: '4px' }}>
            <span>Corporate Email: *</span>
            <input
              type="email"
              placeholder="e.g. alex.morgan@example.test"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </label>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.85rem', gap: '4px' }}>
              <span>Department:</span>
              <input
                type="text"
                required
                value={form.department}
                onChange={(e) => setForm({ ...form, department: e.target.value })}
              />
            </label>

            <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.85rem', gap: '4px' }}>
              <span>Account Status:</span>
              <select
                value={form.account_status}
                onChange={(e) => setForm({ ...form, account_status: e.target.value })}
              >
                <option value="active">Active</option>
                <option value="password_expired">Password Expired</option>
                <option value="locked">Account Locked</option>
              </select>
            </label>
          </div>

          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '0.85rem',
              marginTop: '4px',
              cursor: 'pointer',
            }}
          >
            <input
              type="checkbox"
              checked={form.privileged}
              onChange={(e) => setForm({ ...form, privileged: e.target.checked })}
            />
            <span>Privileged / Domain Admin Role (Subject to Self-Heal lockout)</span>
          </label>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '14px' }}>
            <button
              type="button"
              className="secondary-button"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !form.name.trim() || !form.email.trim()}
              style={{
                background: '#2563eb',
                color: '#fff',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '8px',
                fontWeight: 'bold',
                cursor: 'pointer',
              }}
            >
              {submitting ? 'Creating...' : 'Register Employee'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
