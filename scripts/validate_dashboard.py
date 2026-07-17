"""
scripts/validate_dashboard.py
Verifica que el HTML generado contiene los marcadores esperados y tiene tamano minimo.
Exit 0 = OK | Exit 1 = fallo (el step de CI queda en rojo).
"""
import argparse
import sys
from pathlib import Path

REQUIRED_MARKERS = [
    "EMITIBILIDAD_DATA",
    "run_date",
    "summary",
    "by_day",
    "errors",
    "emit_pct",
    "filters",
]
MIN_SIZE_KB = 30


def validate(path: Path) -> None:
    if not path.exists():
        print(f"[validate] FAIL: archivo no encontrado -> {path}", file=sys.stderr)
        sys.exit(1)

    size_kb = path.stat().st_size / 1024
    content = path.read_text(encoding="utf-8")
    fails   = []

    if size_kb < MIN_SIZE_KB:
        fails.append(f"archivo demasiado pequeno ({size_kb:.1f} KB < {MIN_SIZE_KB} KB)")

    missing = [m for m in REQUIRED_MARKERS if m not in content]
    if missing:
        fails.append(f"marcadores faltantes: {missing}")

    if fails:
        for f in fails:
            print(f"[validate] FAIL: {f}", file=sys.stderr)
        sys.exit(1)

    print(f"[validate] OK - {path.name} ({size_kb:.1f} KB), {len(REQUIRED_MARKERS)} marcadores presentes.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Validar dashboard HTML")
    ap.add_argument("--path", type=Path, default=Path("docs/Dashboard_Emitibilidad.html"))
    args = ap.parse_args()
    validate(args.path)


if __name__ == "__main__":
    main()
