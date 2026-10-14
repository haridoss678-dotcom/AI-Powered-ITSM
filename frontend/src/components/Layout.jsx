import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useEmployee } from '../context/EmployeeContext';
import ConnectionStatus from './ConnectionStatus';
import EmployeeManagerModal from './EmployeeManagerModal';

const navItems = [
  { to: '/self-service', label: 'Employee Self-Service', icon: '💬' },
  { to: '/intake', label: 'Ticket Intake', icon: '🎫' },
  { to: '/self-heal', label: 'Self-Heal Agent', icon: '⚙️' },
  { to: '/knowledge', label: 'Knowledge Base', icon: '📚' },
  { to: '/software', label: 'Software Catalogue', icon: '📦' },
  { to: '/dashboard', label: 'ITSM Dashboard', icon: '📊' },
  { to: '/analysis', label: 'AI Analysis', icon: '🔍' },
];

export default function Layout() {
  const { employeeId, setEmployeeId, selectedEmployee, demoEmployees, error } = useEmployee();
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);

  return (
    <div className="app-shell-container">
      {/* Top Header Bar */}
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-logo">
            <span className="brand-icon">⚡</span>
            <h1>Sorim.AI</h1>
          </div>
          <span className="brand-tag">7-SCREEN ITSM PLATFORM</span>
        </div>

        <div className="header-actions">
          {/* Active Employee Selector & Creator */}
          <div className="header-employee-box">
            <label htmlFor="global-emp-select">Active Employee:</label>
            <select
              id="global-emp-select"
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              aria-label="Active Employee Selector"
            >
              {demoEmployees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.label}
                </option>
              ))}
            </select>
            {selectedEmployee && (
              <span className={`emp-badge ${selectedEmployee.status}`}>
                {selectedEmployee.department} • {selectedEmployee.status.replace('_', ' ')}
              </span>
            )}
            <button
              type="button"
              className="add-emp-btn"
              onClick={() => setShowEmployeeModal(true)}
              title="Register a new employee into MongoDB Atlas"
            >
              + New Employee
            </button>
          </div>

          <ConnectionStatus />
        </div>
      </header>

      {error && (
        <div className="error-banner" style={{ margin: '8px 24px', fontSize: '0.85rem' }}>
          {error}
        </div>
      )}

      {/* Main Body: Left Sidebar + Main Content */}
      <div className="app-layout-body">
        <aside className="app-sidebar" aria-label="Main sidebar navigation">
          <div>
            <div className="sidebar-section-title">ITSM WORKFLOWS</div>
            <nav className="sidebar-nav">
              {navItems.map(({ to, label, icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) => (isActive ? 'sidebar-link active' : 'sidebar-link')}
                >
                  <span className="nav-icon">{icon}</span>
                  <span className="nav-text">{label}</span>
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="sidebar-footer">
            <div className="sidebar-footer-card">
              <span className="footer-title">ENGINEERING SPECS</span>
              <p>PyTorch CPU • MiniLM Embeddings • Persistent ChromaDB • MongoDB Atlas</p>
            </div>
          </div>
        </aside>

        <main className="app-main-content">
          <Outlet />
        </main>
      </div>

      <EmployeeManagerModal
        isOpen={showEmployeeModal}
        onClose={() => setShowEmployeeModal(false)}
      />
    </div>
  );
}
