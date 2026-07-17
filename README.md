# Dashboard Emitibilidad 2026

Repositorio para la actualización automática del Dashboard de Emitibilidad de Despegar.

## Estructura

```
.github/workflows/   → GitHub Action (cron diario 9 AM Chile)
scripts/             → Pipeline de extracción y construcción
docs/                → Dashboard HTML generado
data/raw/            → CSV comprimido exportado de Metabase
templates/           → Template HTML del dashboard
```

## Ejecución manual

Actions → Dashboard Emitibilidad → Run workflow
