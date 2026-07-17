"""
scripts/build_dashboard.py
Preprocesa el CSV raw de emitibilidad y construye el dashboard HTML autocontenido.

Tablas agregadas:
  summary : month x brand x canal x Banco x LOB
  s_prod  : month x brand x canal x Banco x LOB x Producto
  by_day  : day (serie temporal diaria)
  errors  : month x brand x canal x Banco x LOB x error_code x detailed_state

Metricas:
  emit_pct = OK / (OK + ERROR) * 100
  usd_ok   = SUM(amount)     donde state='OK'
  clp_ok   = SUM(amount_CLP) donde state='OK'
"""
import argparse
import gzip
import json
import os
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

TOP_N = 8  # top-N categorias; el resto se agrupa en 'Otros'


def top_n_or_otros(series: pd.Series, n: int = TOP_N) -> pd.Series:
    top = series.value_counts().nlargest(n).index
    return series.where(series.isin(top), other="Otros")


def agg_emit(df: pd.DataFrame, group_cols: list) -> pd.DataFrame:
    return (
        df.groupby(group_cols, dropna=False)
        .agg(
            OK    =("state", lambda x: (x == "OK").sum()),
            ERROR =("state", lambda x: (x == "ERROR").sum()),
            usd_ok=("amount",     lambda x: x[df.loc[x.index, "state"] == "OK"].sum()),
            clp_ok=("amount_CLP", lambda x: x[df.loc[x.index, "state"] == "OK"].sum()),
        )
        .assign(
            total    =lambda d: d["OK"] + d["ERROR"],
            emit_pct =lambda d: np.where(d["total"] > 0, d["OK"] / d["total"] * 100, np.nan),
        )
        .reset_index()
    )


def build(input_path: Path, output_path: Path, run_date: date) -> None:
    print(f"[build] Cargando {input_path} ...")
    with gzip.open(input_path, "rb") as f:
        df = pd.read_csv(f, low_memory=False)
    print(f"[build] Filas raw: {len(df):,}")

    df["reservation_date"] = pd.to_datetime(df["reservation_date"], errors="coerce")
    df["month"] = df["reservation_date"].dt.to_period("M").astype(str)
    df["day"]   = df["reservation_date"].dt.strftime("%Y-%m-%d")

    for col in ("canal", "Banco", "Producto"):
        if col in df.columns:
            df[col] = top_n_or_otros(df[col])

    for col in ("amount", "amount_CLP"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    BASE = ["month", "brand", "canal", "Banco", "LOB"]

    print("[build] Agregando tablas ...")
    summary = agg_emit(df, BASE)
    s_prod  = agg_emit(df, BASE + ["Producto"])
    by_day  = agg_emit(df, ["day"])
    errors  = (
        df[df["state"] == "ERROR"]
        .groupby(BASE + ["error_code", "detailed_state"], dropna=False)
        .size()
        .reset_index(name="n")
    )

    payload = {
        "run_date": run_date.isoformat(),
        "summary":  summary.to_dict(orient="records"),
        "s_prod":   s_prod.to_dict(orient="records"),
        "by_day":   by_day.to_dict(orient="records"),
        "errors":   errors.to_dict(orient="records"),
        "filters": {
            "months":    sorted(df["month"].dropna().unique().tolist()),
            "brands":    sorted(df["brand"].dropna().unique().tolist()),
            "canales":   sorted(df["canal"].dropna().unique().tolist()),
            "bancos":    sorted(df["Banco"].dropna().unique().tolist()),
            "lobs":      sorted(df["LOB"].dropna().unique().tolist()),
            "productos": sorted(df["Producto"].dropna().unique().tolist()) if "Producto" in df.columns else [],
        },
    }
    data_str = json.dumps(payload, ensure_ascii=False, default=str)

    tmpl = Path("templates/dashboard_template.html")
    if tmpl.exists():
        html = tmpl.read_text(encoding="utf-8").replace("__DATA__", data_str)
    else:
        html = (
            f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>Dashboard Emitibilidad {run_date}</title></head><body>"
            f"<script>const EMITIBILIDAD_DATA = {data_str};</script>"
            f"<p>Template no encontrado. Datos embebidos correctamente.</p></body></html>"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"[build] Dashboard escrito -> {output_path} ({output_path.stat().st_size / 1024:.1f} KB)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Construir dashboard HTML de Emitibilidad")
    ap.add_argument("--input",  type=Path, default=Path("data/raw/emitibilidad_raw.csv.gz"))
    ap.add_argument("--output", type=Path, default=Path("docs/Dashboard_Emitibilidad.html"))
    args = ap.parse_args()

    force = os.environ.get("FORCE_DATE", "").strip()
    run_date = date.fromisoformat(force) if force else date.today()
    print(f"[build] Fecha de ejecucion: {run_date}")
    build(args.input, args.output, run_date)


if __name__ == "__main__":
    main()
