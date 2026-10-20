from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "index.html"
SCRIPT_PATTERN = re.compile(r"<script(?:\s[^>]*)?>(.*?)</script\s*>", re.IGNORECASE | re.DOTALL)


def main() -> int:
    node = shutil.which("node")
    if node is None:
        raise SystemExit("Node.js is required to validate the inline browser JavaScript.")

    html = HTML_PATH.read_text(encoding="utf-8")
    scripts = SCRIPT_PATTERN.findall(html)
    if len(scripts) != 1:
        raise SystemExit(f"Expected exactly one inline script in {HTML_PATH.name}; found {len(scripts)}.")

    with tempfile.TemporaryDirectory(prefix="janggi-js-check-") as temp_dir:
        script_path = Path(temp_dir) / "browser-inline.js"
        script_path.write_text(scripts[0], encoding="utf-8")
        result = subprocess.run([node, "--check", str(script_path)], check=False)
        if result.returncode:
            return result.returncode

    print("Browser inline JavaScript syntax is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
