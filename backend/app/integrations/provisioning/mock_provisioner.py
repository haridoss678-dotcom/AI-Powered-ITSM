"""
Sorim.AI — Mock Provisioning Adapter  (integrations/provisioning/mock_provisioner.py)

Simulates safe mock deployment of corporate software packages without modifying the OS.
"""

from __future__ import annotations

import uuid


class MockProvisioner:
    def start_job(self, software_name: str, employee_id: str) -> str:
        return f"JOB-PRV-{uuid.uuid4().hex[:8].upper()}"

    def validate_job(self, job_id: str) -> bool:
        return True


_provisioner = MockProvisioner()


def get_mock_provisioner() -> MockProvisioner:
    return _provisioner
