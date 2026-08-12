#!/usr/bin/env python3
"""
  ╔══════════════════════════════════════════════════════════════╗
  ║  PIPELINE DE DIAGNÓSTICO DE PERFIL TECNOLÓGICO             ║
  ║  Observatorio de Inteligencia de Datos                     ║
  ║  Centro de Innovación — INATEC Nicaragua                   ║
  ╚══════════════════════════════════════════════════════════════╝

  Auditoría de Capital Humano — Hackathon Nicaragua 2026
  Fase 2 del análisis Think Tank.

  Uso:
      python run_pipeline.py
"""
import sys
import logging
from datetime import datetime

from src.config import PATHS, PIPELINE_VERSION
from src.cleaning import run_cleaning_pipeline
from src.features import build_team_profiles
from src.visuals import generate_all_plots
from src.exporter import run_export_pipeline

# ── Configuración de logging ──────────────────────────────────────────────────

def setup_logging():
    """Configura logging a consola con formato legible."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


# ── Pipeline principal ────────────────────────────────────────────────────────

def main() -> int:
    setup_logging()
    logger = logging.getLogger(__name__)

    start_time = datetime.now()

    print(f"\n{'═' * 60}")
    print(f"  DIAGNÓSTICO DE PERFIL TECNOLÓGICO v{PIPELINE_VERSION}")
    print(f"  Observatorio de Inteligencia de Datos — INATEC")
    print(f"  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═' * 60}\n")

    try:
        # ── FASE 1: Limpieza y Normalización ──────────────────────────────
        df_clean = run_cleaning_pipeline(PATHS["raw_csv"])

        # Validación post-limpieza
        assert len(df_clean) > 0, "DataFrame vacío post-limpieza."
        assert "team_name" in df_clean.columns, "Columna 'team_name' no encontrada."
        print(f"\n  ✓ Fase 1 completada: {len(df_clean)} individuos limpios.\n")

        # ── FASES 2-3: Feature Engineering + Team Roll-Up ─────────────────
        profiles = build_team_profiles(df_clean)

        # Validación: suma de miembros = total de filas
        total_members = sum(p["member_count"] for p in profiles)
        assert total_members == len(df_clean), (
            f"Desajuste: {total_members} miembros en perfiles vs "
            f"{len(df_clean)} filas en DataFrame."
        )
        print(f"\n  ✓ Fases 2-3 completadas: {len(profiles)} perfiles de equipo.\n")

        # ── FASE 4a: Visualizaciones ──────────────────────────────────────
        generate_all_plots(profiles, df_clean, PATHS["plots_dir"])
        print(f"\n  ✓ Fase 4a completada: Gráficas en {PATHS['plots_dir']}\n")

        # ── FASE 4b: Exportación JSON ─────────────────────────────────────
        payload = run_export_pipeline(
            profiles, df_clean, PATHS["llm_context_dir"]
        )
        print(f"\n  ✓ Fase 4b completada: JSON en {PATHS['llm_context_dir']}\n")

    except FileNotFoundError as e:
        logger.error(f"\n  ✗ ARCHIVO NO ENCONTRADO: {e}")
        return 1
    except ValueError as e:
        logger.error(f"\n  ✗ ERROR DE VALIDACIÓN: {e}")
        return 1
    except Exception as e:
        logger.error(f"\n  ✗ ERROR INESPERADO: {e}", exc_info=True)
        return 1

    # ── Resumen final ─────────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"{'═' * 60}")
    print(f"  PIPELINE COMPLETADO EXITOSAMENTE")
    print(f"{'─' * 60}")
    print(f"  Individuos procesados:  {len(df_clean)}")
    print(f"  Equipos perfilados:     {len(profiles)}")
    print(f"  Gráficas generadas:     6")
    print(f"  JSON exportado:         telemetria_capital_humano.json")
    print(f"  Tiempo de ejecución:    {elapsed:.2f}s")
    print(f"{'═' * 60}\n")

    # Quick stats por riesgo
    risk_counts = {}
    for p in profiles:
        level = p["llm_assessment"]["technical_risk_level"]
        risk_counts[level] = risk_counts.get(level, 0) + 1

    print("  DISTRIBUCIÓN DE RIESGO TÉCNICO:")
    for level in ["low", "moderate", "high", "critical"]:
        count = risk_counts.get(level, 0)
        emoji = {"low": "🟢", "moderate": "🟡", "high": "🟠", "critical": "🔴"}.get(level, "⚪")
        bar = "█" * count
        print(f"    {emoji} {level:10s}: {count:2d} equipos {bar}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
