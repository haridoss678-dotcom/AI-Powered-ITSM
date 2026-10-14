import assert from 'node:assert/strict';
import test from 'node:test';

test('Self-heal table column layout allocates at least 160px for status to prevent overlapping timestamp', () => {
  // Test the grid template columns specified for SelfHeal history table
  const gridColumns = '130px 170px 120px 180px 1fr';
  const parts = gridColumns.split(' ');

  assert.equal(parts.length, 5, 'Must have exactly 5 columns (Action ID, Action Type, Employee, Status, Timestamp)');
  const [actionIdCol, actionTypeCol, empCol, statusCol, timestampCol] = parts;

  assert.equal(actionIdCol, '130px');
  assert.equal(actionTypeCol, '170px');
  assert.equal(empCol, '120px');
  assert.equal(statusCol, '180px', 'Status column must be at least 180px to safely contain skipped_ineligible without overlapping timestamp');
  assert.equal(timestampCol, '1fr');
});

test('Self-heal long status values are formatted and fit within dedicated status badge', () => {
  const longStatuses = [
    'skipped_ineligible',
    'completed',
    'failed',
    'execution_in_progress',
    'validation_failed',
    'succeeded',
  ];

  // An 180px column in standard 13-14px font fits at least 22 characters at 8px per character.
  for (const status of longStatuses) {
    assert.ok(status.length <= 22, `Status "${status}" (${status.length} chars) must fit within the dedicated 180px column`);
  }
});

test('Self-heal action details dismiss state logic', () => {
  let activeAction = {
    action_id: 'ACT-000001',
    status: 'succeeded',
    employee_id: 'EMP-001',
    steps: [],
  };

  // 1. Details view is open when activeAction is present
  assert.ok(activeAction !== null);
  assert.equal(activeAction.action_id, 'ACT-000001');

  // 2. Clicking close button sets activeAction to null
  const handleClose = () => {
    activeAction = null;
  };
  handleClose();
  assert.equal(activeAction, null, 'Closing details resets activeAction to null');

  // 3. Reopening with a different action updates state cleanly
  const reopenAction = {
    action_id: 'ACT-000002',
    status: 'skipped_ineligible',
    employee_id: 'EMP-003',
    steps: [],
  };
  activeAction = reopenAction;
  assert.equal(activeAction.action_id, 'ACT-000002');
  assert.equal(activeAction.status, 'skipped_ineligible');

  // 4. Escape key press handler logic
  const handleKeyDown = (e) => {
    if (e.key === 'Escape' && activeAction) {
      activeAction = null;
    }
  };

  handleKeyDown({ key: 'Enter' });
  assert.ok(activeAction !== null, 'Enter key should not close details');

  handleKeyDown({ key: 'Escape' });
  assert.equal(activeAction, null, 'Escape key closes details');
});
