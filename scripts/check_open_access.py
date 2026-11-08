"""Verifica que cada referencia tenga una versión de acceso abierto.

Usa Unpaywall y, cuando el DOI está cerrado, comprueba la URL abierta declarada
en el campo ``url`` del archivo BibTeX.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / "doc" / "refs.bib"
EMAIL = "fireca.tif@unsa.edu.pe"
# Referencias fundacionales exigidas por el alcance, aunque su versión
# editorial sea de pago.
ALLOWED_PAYWALLED = {"karafyllidis1997", "alexandridis2008", "hayakawa2011"}


def head_ok(url: str) -> bool:
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "fireca-TIF/1.0", "Range": "bytes=0-0"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status < 400
    except Exception:
        return False


def main() -> int:
    text = BIB.read_text(encoding="utf-8")
    entries = []
    for block in re.split(r"\n@", text):
        key = re.search(r"\{([^,]+),", block)
        doi = re.search(r"doi\s*=\s*\{([^}]+)\}", block, re.I)
        url = re.search(r"url\s*=\s*\{([^}]+)\}", block, re.I)
        if key and doi:
            entries.append((key.group(1), doi.group(1), url.group(1) if url else ""))
    failures = 0
    for key, doi, url in entries:
        if doi.startswith("10.48550/"):
            is_oa, status = False, "arxiv"
        else:
            try:
                endpoint = (
                    "https://api.unpaywall.org/v2/"
                    + urllib.parse.quote(doi)
                    + f"?email={EMAIL}"
                )
                with urllib.request.urlopen(endpoint, timeout=30) as response:
                    record = json.load(response)
                is_oa = bool(record.get("is_oa"))
                status = record.get("oa_status")
            except Exception:
                is_oa, status = False, "unknown"
        free_url_ok = bool(url) and head_ok(url)
        ok = is_oa or free_url_ok
        allowed = key in ALLOWED_PAYWALLED
        if not ok and not allowed:
            failures += 1
        label = "OK  " if ok else ("EXC " if allowed else "FAIL")
        print(
            f"{label} {key:22s} {doi:38s} "
            f"unpaywall={is_oa} ({status}) url_ok={free_url_ok}"
        )
    print(
        f"\n{len(entries)} referencias, {failures} sin acceso abierto "
        f"({len(ALLOWED_PAYWALLED)} excepciones obligatorias)."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
