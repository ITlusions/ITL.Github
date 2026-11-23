"""Read the failing controls from a Kubescape JSON report so a failed scan can be explained in plain words."""

import json
from pathlib import Path

# AI generated code: GitHub Copilot Claude Haiku 5.5
FAILED_STATUS = 'failed'


class KubescapeReport:
    """Read the controls that failed in one Kubescape JSON report."""

    def __init__(self, path):
        """Store the path of the Kubescape JSON report.

        Args:
            path: Path to the kubescape.json file written by the scan.
        """
        self.path = Path(path)

    def failing_controls(self):
        """Return the failed controls, sorted by control ID.

        Returns:
            A list of dicts with the keys id, name and resources, where resources is the number of failed resources.
            The list is empty when the report does not exist.
        """
        if not self.path.is_file():
            return []
        report = json.loads(self.path.read_text(encoding='utf-8'))
        controls = (report.get('summaryDetails') or {}).get('controls') or {}
        failing = []
        for control_id in sorted(controls):
            control = controls[control_id]
            status = control.get('status')
            if isinstance(status, dict):
                status = status.get('status')
            if status == FAILED_STATUS:
                # Kubescape writes this key with a capital R.
                counters = control.get('ResourceCounters') or {}
                failing.append({
                    'id': control_id,
                    'name': control.get('name', ''),
                    'resources': counters.get('failedResources', 0),
                })
        return failing

    def control_ids(self):
        """Return the IDs of every control that the scan evaluated, whatever its status.

        Returns:
            A set of control IDs. The set is empty when the report does not exist.
        """
        if not self.path.is_file():
            return set()
        report = json.loads(self.path.read_text(encoding='utf-8'))
        return set((report.get('summaryDetails') or {}).get('controls') or {})
