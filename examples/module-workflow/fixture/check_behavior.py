"""Specification-derived expectation; retained native per-check observations."""
import json
import os
from pathlib import Path
from app import value

observed = value()
passed = type(observed) is int and observed == 2
result = {"requirement": "REQ-VALUE", "status": "passed" if passed else "failed",
          "checks": [{"name": "returns the specified integer", "expected": 2,
                      "observed": observed, "passed": passed}],
          "limitations": ["Synthetic Python behavior only; no DB, UI or customer acceptance."]}
(Path(os.environ["FMW_OUTPUT_DIR"]) / "result.json").write_text(json.dumps(result), encoding="utf-8")
raise SystemExit(0 if passed else 1)
