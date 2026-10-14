import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { createEmployee as apiCreateEmployee, listEmployees } from '../api/employees';
import { DEMO_EMPLOYEES, SUPPORTED_EMPLOYEES, getEmployeeById } from './employees.js';

export { DEMO_EMPLOYEES, SUPPORTED_EMPLOYEES, getEmployeeById };

const STORAGE_KEY = 'sorim_active_employee_id';
const DEFAULT_ID = import.meta.env.VITE_DEMO_EMPLOYEE_ID ?? 'EMP-002';

const EmployeeContext = createContext(null);

function formatEmployee(emp) {
  const id = emp.employee_id || emp.id || emp._id;
  const status = emp.mock_account?.account_status || emp.status || 'active';
  const privileged = emp.mock_account?.privileged ?? emp.privileged ?? false;
  const roleTag = privileged
    ? 'Privileged Admin'
    : status === 'password_expired'
    ? 'Password Expired'
    : 'Standard Employee';

  return {
    id,
    employee_id: id,
    name: emp.name,
    email: emp.email,
    department: emp.department,
    status,
    privileged,
    label: `${id} — ${emp.name} (${roleTag})`,
  };
}

export function EmployeeProvider({ children }) {
  const [employees, setEmployees] = useState(DEMO_EMPLOYEES);
  const [employeeId, setEmployeeIdState] = useState(() => {
    return sessionStorage.getItem(STORAGE_KEY) || DEFAULT_ID;
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const refreshEmployees = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listEmployees();
      if (Array.isArray(data) && data.length > 0) {
        const formatted = data.map(formatEmployee);
        setEmployees(formatted);
      }
    } catch {
      // Graceful fallback to pre-seeded static employees if backend offline
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshEmployees();
  }, [refreshEmployees]);

  const selectedEmployee = employees.find((emp) => emp.id === employeeId) || null;
  const isValidEmployee = Boolean(selectedEmployee);

  const setEmployeeId = (newId) => {
    const trimmed = (newId || '').trim().toUpperCase();
    setEmployeeIdState(trimmed);
    sessionStorage.setItem(STORAGE_KEY, trimmed);

    const match = employees.find((emp) => emp.id === trimmed);
    if (!match && trimmed) {
      setError(`Employee ID '${trimmed}' was not found in the employee directory.`);
    } else {
      setError('');
    }
  };

  const addNewEmployee = async (payload) => {
    const created = await apiCreateEmployee(payload);
    const formatted = formatEmployee(created);
    setEmployees((prev) => {
      const exists = prev.some((e) => e.id === formatted.id);
      return exists ? prev.map((e) => (e.id === formatted.id ? formatted : e)) : [...prev, formatted];
    });
    setEmployeeId(formatted.id);
    return formatted;
  };

  useEffect(() => {
    const match = employees.find((emp) => emp.id === employeeId);
    if (!match && employeeId) {
      setError(`Employee ID '${employeeId}' was not found in the employee directory.`);
    } else {
      setError('');
    }
  }, [employeeId, employees]);

  return (
    <EmployeeContext.Provider
      value={{
        employeeId,
        setEmployeeId,
        selectedEmployee,
        isValidEmployee,
        error,
        employees,
        demoEmployees: employees, // maintains full backwards compatibility with all screens
        refreshEmployees,
        addNewEmployee,
        loadingEmployees: loading,
      }}
    >
      {children}
    </EmployeeContext.Provider>
  );
}

export function useEmployee() {
  const context = useContext(EmployeeContext);
  if (!context) {
    throw new Error('useEmployee must be used within an EmployeeProvider');
  }
  return context;
}
