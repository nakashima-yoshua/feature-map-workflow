"""Package only the explicit synthetic candidate selection."""
import os
from pathlib import Path
from zipfile import ZipFile

with ZipFile(Path(os.environ["FMW_OUTPUT_DIR"]) / "candidate.zip", "w") as archive:
    for name in ("app.py", "requirements.md"):
        archive.write(name, name)
