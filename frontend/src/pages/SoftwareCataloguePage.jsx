import { useEffect, useState } from 'react';
import { createSoftwareRequest, listSoftwareCatalogue, listSoftwareRequests } from '../api/software';
import { useEmployee } from '../context/EmployeeContext';

export default function SoftwareCataloguePage() {
  const { employeeId, setEmployeeId, demoEmployees, selectedEmployee, isValidEmployee } = useEmployee();
  const [catalogue, setCatalogue] = useState([]);
  const [loadingCatalogue, setLoadingCatalogue] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [submitting, setSubmitting] = useState(false);
  const [activeRequest, setActiveRequest] = useState(null);
  const [requestsHistory, setRequestsHistory] = useState([]);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoadingCatalogue(true);
    try {
      const items = await listSoftwareCatalogue();
      setCatalogue(items);
      const history = await listSoftwareRequests({ limit: 10 });
      setRequestsHistory(history.items || []);
    } catch (err) {
      setError('Failed to load software catalogue');
    } finally {
      setLoadingCatalogue(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRequest = async (softwareName) => {
    setSubmitting(true);
    setError(null);
    try {
      const req = await createSoftwareRequest({
        employeeId,
        softwareName,
      });
      setActiveRequest(req);
      const history = await listSoftwareRequests({ limit: 10 });
      setRequestsHistory(history.items || []);
    } catch (err) {
      setError(err.message || 'Software request failed');
    } finally {
      setSubmitting(false);
    }
  };

  const categories = ['all', ...new Set(catalogue.map((c) => c.category))];

  const filteredItems = catalogue.filter((item) => {
    const matchCat = selectedCategory === 'all' || item.category === selectedCategory;
    const matchQuery =
      !searchQuery ||
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchCat && matchQuery;
  });

  return (
    <div className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Screen 5 — Self-Service Provisioning</span>
          <h2>Enterprise Software Catalogue</h2>
        </div>
        <button
          className="secondary-button"
          onClick={() => handleRequest('Visual Studio Code')}
          disabled={submitting}
        >
          {submitting ? 'Provisioning...' : 'Test Scenario D: Request VS Code'}
        </button>
      </div>

      <p style={{ color: '#9fb2cc', marginTop: '6px' }}>
        Request pre-approved enterprise developer and productivity software. The workflow orchestrates ServiceNow service request generation, automated mock package deployment, and postcondition verification.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <div className="employee-picker" style={{ margin: '16px 0' }}>
        <label htmlFor="sw-emp-select">Requester Employee:</label>
        <select
          id="sw-emp-select"
          value={employeeId}
          onChange={(e) => setEmployeeId(e.target.value)}
        >
          {demoEmployees.map((emp) => (
            <option key={emp.id} value={emp.id}>
              {emp.label}
            </option>
          ))}
        </select>
      </div>

      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', margin: '18px 0' }}>
        <input
          type="text"
          placeholder="Search software packages..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            flex: 1,
            minWidth: '220px',
            padding: '10px 14px',
            borderRadius: '10px',
            border: '1px solid rgba(148, 163, 184, 0.3)',
            background: 'rgba(15, 23, 42, 0.75)',
            color: '#fff',
          }}
        />
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {categories.map((cat) => (
            <button
              key={cat}
              className="secondary-button"
              onClick={() => setSelectedCategory(cat)}
              style={{
                textTransform: 'capitalize',
                background: selectedCategory === cat ? '#2563eb' : 'rgba(15, 23, 42, 0.5)',
                borderColor: selectedCategory === cat ? '#60a5fa' : 'rgba(148, 163, 184, 0.2)',
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {activeRequest && (
        <div className="success-banner" style={{ margin: '24px 0' }} role="region" aria-label="Software request details">
          <div className="section-heading" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
              <h3 style={{ margin: 0 }}>Software Request: {activeRequest.software.name}</h3>
              <span className="mock-badge">ServiceNow: {activeRequest.servicenow_ref.number}</span>
            </div>
            <button
              type="button"
              id="close-software-details-btn"
              aria-label="Close software request details"
              onClick={() => setActiveRequest(null)}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(148, 163, 184, 0.3)',
                color: '#f8fafc',
                fontSize: '0.85rem',
                cursor: 'pointer',
                padding: '6px 14px',
                borderRadius: '6px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                fontWeight: 600,
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.18)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)'; }}
            >
              ✕ Close
            </button>
          </div>

          <div className="ticket-detail-grid" style={{ marginTop: '14px' }}>
            <div className="ticket-detail-field">
              <dt>Request ID (Internal)</dt>
              <dd>
                <strong>{activeRequest.software_request_id}</strong>
              </dd>
            </div>
            <div className="ticket-detail-field">
              <dt>ServiceNow Service Request</dt>
              <dd>
                <strong>{activeRequest.servicenow_ref.number}</strong>
              </dd>
            </div>
            <div className="ticket-detail-field">
              <dt>Status</dt>
              <dd>
                <span style={{ color: '#86efac', fontWeight: 'bold' }}>
                  {activeRequest.status.toUpperCase()}
                </span>
              </dd>
            </div>
            <div className="ticket-detail-field">
              <dt>Version</dt>
              <dd>{activeRequest.software.version}</dd>
            </div>
            <div className="ticket-detail-field">
              <dt>Mock Job ID</dt>
              <dd style={{ fontSize: '0.85rem' }}>{activeRequest.provisioning.job_id}</dd>
            </div>
            <div className="ticket-detail-field">
              <dt>Completed Timestamp</dt>
              <dd>{activeRequest.provisioning.completed_at || 'In progress'}</dd>
            </div>
          </div>
          <p style={{ marginTop: '12px', fontSize: '0.9rem', color: '#cbd5e1' }}>
            <em>Note: {activeRequest.provisioning.detail}</em>
          </p>
        </div>
      )}

      {loadingCatalogue ? (
        <div className="analysis-box">Loading approved software catalogue...</div>
      ) : filteredItems.length === 0 ? (
        <div className="analysis-box">No software packages matched your search criteria.</div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '16px',
            marginTop: '16px',
          }}
        >
          {filteredItems.map((item) => (
            <div
              key={item.catalogue_id}
              style={{
                background: 'rgba(15, 23, 42, 0.65)',
                border: '1px solid rgba(148, 163, 184, 0.25)',
                borderRadius: '12px',
                padding: '18px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <h3 style={{ margin: 0, fontSize: '1.15rem' }}>{item.name}</h3>
                  <span
                    style={{
                      fontSize: '0.72rem',
                      background: 'rgba(56, 189, 248, 0.15)',
                      color: '#7dd3fc',
                      padding: '2px 8px',
                      borderRadius: '999px',
                    }}
                  >
                    v{item.version}
                  </span>
                </div>
                <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{item.category}</span>
                <p style={{ margin: '12px 0', fontSize: '0.9rem', color: '#cbd5e1', lineHeight: '1.4' }}>
                  {item.description}
                </p>
              </div>

              <button
                type="button"
                onClick={() => handleRequest(item.name)}
                disabled={submitting}
                style={{
                  background: '#2563eb',
                  color: '#fff',
                  border: 'none',
                  padding: '9px 14px',
                  borderRadius: '8px',
                  cursor: submitting ? 'not-allowed' : 'pointer',
                  fontWeight: '600',
                  marginTop: '10px',
                }}
              >
                {submitting ? 'Requesting...' : `Request ${item.name}`}
              </button>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: '40px' }}>
        <h3>Recent Software Requests</h3>
        {requestsHistory.length === 0 ? (
          <p style={{ color: '#94a3b8', fontStyle: 'italic', marginTop: '10px' }}>
            No software requests submitted yet.
          </p>
        ) : (
          <div style={{ overflowX: 'auto', marginTop: '12px' }}>
            <div className="ticket-table" style={{ minWidth: '780px' }}>
              <div
                className="ticket-table-header"
                style={{
                  gridTemplateColumns: '130px 150px 180px 120px 1fr',
                  gap: '12px',
                  alignItems: 'center',
                }}
              >
                <span>Request ID</span>
                <span>ServiceNow Ref</span>
                <span>Software</span>
                <span>Status</span>
                <span>Requested At</span>
              </div>
              {requestsHistory.map((req) => (
                <div
                  key={req.software_request_id}
                  className="ticket-table-row"
                  style={{
                    gridTemplateColumns: '130px 150px 180px 120px 1fr',
                    gap: '12px',
                    alignItems: 'center',
                  }}
                  onClick={() => setActiveRequest(req)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      setActiveRequest(req);
                    }
                  }}
                  aria-label={`View details for ${req.software_request_id}`}
                >
                  <strong style={{ whiteSpace: 'nowrap' }}>{req.software_request_id}</strong>
                  <span style={{ whiteSpace: 'nowrap' }}>{req.servicenow_ref.number}</span>
                  <span style={{ whiteSpace: 'nowrap' }}>{req.software.name}</span>
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      padding: '3px 8px',
                      borderRadius: '4px',
                      fontSize: '0.82rem',
                      fontWeight: '600',
                      whiteSpace: 'nowrap',
                      background: req.status === 'completed' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(96, 165, 250, 0.15)',
                      color: req.status === 'completed' ? '#86efac' : '#60a5fa',
                      border: req.status === 'completed' ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid rgba(96, 165, 250, 0.3)',
                    }}
                  >
                    {req.status}
                  </span>
                  <time style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: '#cbd5e1' }}>
                    {req.created_at}
                  </time>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
