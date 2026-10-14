export const DEMO_EMPLOYEES = [
  {
    id: 'EMP-001',
    employee_id: 'EMP-001',
    name: 'Demo Employee One',
    email: 'emp001@example.test',
    department: 'Finance',
    status: 'password_expired',
    privileged: false,
    label: 'EMP-001 — Demo Employee One (Password Expired)',
  },
  {
    id: 'EMP-002',
    employee_id: 'EMP-002',
    name: 'Demo Employee Two',
    email: 'emp002@example.test',
    department: 'Operations',
    status: 'active',
    privileged: false,
    label: 'EMP-002 — Demo Employee Two (Standard Employee)',
  },
  {
    id: 'EMP-003',
    employee_id: 'EMP-003',
    name: 'Demo Employee Three',
    email: 'emp003@example.test',
    department: 'IT',
    status: 'active',
    privileged: true,
    label: 'EMP-003 — Demo Employee Three (Privileged Admin)',
  },
];

export const SUPPORTED_EMPLOYEES = DEMO_EMPLOYEES;

export function getEmployeeById(id) {
  if (!id) return null;
  return DEMO_EMPLOYEES.find((emp) => emp.id === id || emp.employee_id === id) || null;
}
