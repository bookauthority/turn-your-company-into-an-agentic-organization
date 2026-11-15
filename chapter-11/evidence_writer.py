from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_evidence(evidence: Dict[str, Any], path: Path) -> None:
    """Write the evidence JSON to the given path.

    Ensures the parent directory exists and uses UTF-8 encoding.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=False)
