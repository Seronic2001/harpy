from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import requests
from harpy.models import ProblemSpec


CPH_DEFAULT_PORTS = [27121, 10045, 10043, 10042]


def dispatch_to_cph(
    spec: ProblemSpec,
    ports: Optional[List[int]] = None,
    timeout: float = 1.0,
) -> Dict[str, object]:
    """
    Sends the problem to CPH (or any Competitive Companion compatible tool)
    via local HTTP POST request.
    """
    ports_to_try = ports or CPH_DEFAULT_PORTS
    payload = spec.to_competitive_companion_dict()

    for port in ports_to_try:
        url = f"http://127.0.0.1:{port}/"
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            if resp.status_code in (200, 201, 204):
                return {
                    "success": True,
                    "port": port,
                    "message": f"Successfully dispatched '{spec.title}' to listener on port {port}",
                }
        except (requests.ConnectionError, requests.Timeout):
            continue
        except Exception as e:
            continue

    return {
        "success": False,
        "ports_tried": ports_to_try,
        "message": "No active CPH or Competitive Companion listener found on ports "
        + ", ".join(map(str, ports_to_try)),
    }


def write_cph_file(
    spec: ProblemSpec,
    solution_path: Path | str,
) -> Path:
    """
    Generates a native CPH configuration file inside `.cph/` directory.
    Format: .cph/.<filename>_<hash>.prob
    This ensures CPH loads test cases even if the HTTP companion was offline.
    """
    sol = Path(solution_path).resolve()
    cph_dir = sol.parent / ".cph"
    cph_dir.mkdir(parents=True, exist_ok=True)

    # Compute hash based on absolute path
    path_hash = hashlib.md5(str(sol).encode("utf-8")).hexdigest()[:16]
    prob_file = cph_dir / f".{sol.name}_{path_hash}.prob"

    timestamp_ms = int(time.time() * 1000)
    tests_payload = []
    for idx, tc in enumerate(spec.testcases):
        tests_payload.append(
            {
                "id": timestamp_ms + idx,
                "input": tc.normalized_input(),
                "expectedOutput": tc.normalized_output() + "\n" if tc.output else "",
            }
        )

    cph_data = {
        "name": spec.title,
        "url": "",
        "interactive": False,
        "memoryLimit": spec.memory_limit_mb,
        "timeLimit": spec.time_limit_ms,
        "srcPath": str(sol),
        "group": "Harpy",
        "tests": tests_payload,
    }

    prob_file.write_text(json.dumps(cph_data, indent=2), encoding="utf-8")
    return prob_file
