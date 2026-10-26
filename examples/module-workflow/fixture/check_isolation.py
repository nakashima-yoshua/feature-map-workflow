"""Real Compose assertions; intentionally fails outside the isolated service."""
import json
import os
import socket
from pathlib import Path

checks = {}
try:
    with Path("app.py").open("a"):
        pass
    checks["source_read_only"] = False
except OSError:
    checks["source_read_only"] = True
checks["no_control_state"] = not Path("/run/state/state.json").exists()
checks["no_other_worker_outputs"] = not Path("/run/results/ai").exists()
checks["no_docker_socket"] = not Path("/var/run/docker.sock").exists()
checks["no_model_credentials"] = not any("KEY" in key or "TOKEN" in key for key in os.environ)
try:
    Path("/run/results/build/package").mkdir()
    checks["cannot_forge_future_result"] = False
except OSError:
    checks["cannot_forge_future_result"] = True
try:
    Path("/run/requests/build").iterdir().__next__()
    checks["cannot_read_worker_requests"] = False
except OSError:
    checks["cannot_read_worker_requests"] = True
with socket.socket() as connection:
    connection.settimeout(1)
    try:
        connection.connect(("1.1.1.1", 80))
        checks["network_isolated"] = False
    except OSError:
        checks["network_isolated"] = True
result = {"status": "passed" if all(checks.values()) else "failed",
          "checks": [{"name": name, "expected": True, "observed": value, "passed": value}
                     for name, value in checks.items()]}
(Path(os.environ["FMW_OUTPUT_DIR"]) / "isolation.json").write_text(json.dumps(result), encoding="utf-8")
raise SystemExit(0 if all(checks.values()) else 1)
