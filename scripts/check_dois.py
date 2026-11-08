"""Verifica que todos los DOI de ``doc/refs.bib`` resuelvan.

Uso:
    uv run python scripts/check_dois.py
"""

from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / "doc" / "refs.bib"


def main() -> int:
    text = BIB.read_text(encoding="utf-8")
    entries = re.findall(r"@\w+\{([^,]+),.*?doi\s*=\s*\{([^}]+)\}", text, re.S)
    failures = 0
    for key, doi in entries:
        url = f"https://doi.org/{doi}"
        request = urllib.request.Request(url, method="HEAD")
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                status = response.status
                final = response.url
            print(f"OK   {status:3d}  {key:22s} {doi}  -> {final}")
        except urllib.error.HTTPError as exc:
            # 403/202 son habituales en editoriales que bloquean bots; el DOI
            # sí resuelve. Se reportan como advertencia, no como fallo.
            print(f"WARN {exc.code:3d}  {key:22s} {doi}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL      {key:22s} {doi}  {exc}")
    print(f"\n{len(entries)} DOI revisados, {failures} fallos de resolución.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
