"""
scripts/export_metabase.py
Exporta el card 152536 de Metabase como CSV comprimido (datos raw de emitibilidad).
Autenticacion via METABASE_URL y METABASE_SESSION (secrets de GitHub Actions).
"""
import argparse
import gzip
import json
import os
import sys
from pathlib import Path

import requests


def export_card(url_base: str, session: str, card_id: int, out_path: Path) -> None:
    url = f"{url_base.rstrip('/')}/api/card/{card_id}/query/csv"
    headers = {
        "Content-Type": "application/json",
        "X-Metabase-Session": session,
    }
    body = json.dumps({"parameters": []})

    print(f"[export] Solicitando card {card_id} desde {url_base} ...")
    resp = requests.post(url, headers=headers, data=body, timeout=180)

    if resp.status_code != 200:
        print(f"[export] HTTP {resp.status_code}: {resp.text[:400]}", file=sys.stderr)
        sys.exit(1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out_path, "wb") as f:
        f.write(resp.content)

    print(f"[export] OK - {out_path} ({out_path.stat().st_size / 1024:.1f} KB comprimido)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Exportar card Metabase a CSV.GZ")
    ap.add_argument("--card-id",  type=int,  default=152536)
    ap.add_argument("--out-path", type=Path, default=Path("data/raw/emitibilidad_raw.csv.gz"))
    args = ap.parse_args()

    url_base = os.environ.get("METABASE_URL", "").strip()
    session  = os.environ.get("METABASE_SESSION", "").strip()

    if not url_base or not session:
        print("[export] ERROR: METABASE_URL y METABASE_SESSION deben estar definidos.", file=sys.stderr)
        sys.exit(1)

    export_card(url_base, session, args.card_id, args.out_path)


if __name__ == "__main__":
    main()
