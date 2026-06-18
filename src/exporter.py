"""
exporter.py — Fase 4b: Exportación del JSON semántico para LLMs.

Observatorio de Inteligencia de Datos
Pipeline de Diagnóstico de Perfil Tecnológico
Centro de Innovación — INATEC Nicaragua

Genera telemetria_capital_humano.json optimizado para agentes IA.
"""
import json
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


def run_export_pipeline(
    profiles: list[dict], df: pd.DataFrame, output_dir: Path
) -> dict:
    """
    Consolida la telemetría en un objeto JSON y lo guarda.

    Args:
        profiles: Lista de perfiles de equipo.
        df: DataFrame limpio.
        output_dir: Carpeta de destino.

    Returns:
        Diccionario con el payload exportado.
    """
    logger.info("=" * 60)
    logger.info("FASE 4b: EXPORTACIÓN DE TELEMETRÍA (JSON)")
    logger.info("=" * 60)

    n_teams = len(profiles)
    n_respondents = len(df)

    # Distribución de riesgo global
    risk_counts = {}
    for p in profiles:
        level = p["llm_assessment"]["technical_risk_level"]
        risk_counts[level] = risk_counts.get(level, 0) + 1

    risk_dist = {
        level: f"{count} ({count/n_teams:.1%})"
        for level, count in risk_counts.items()
    }

    payload = {
        "metadata": {
            "project": "Hackathon Nicaragua 2026",
            "module": "Diagnóstico de Perfil Tecnológico",
            "generated_at": datetime.now().isoformat(),
            "pipeline_version": "1.0.0",
            "total_teams": n_teams,
            "total_protagonists": n_respondents,
            "source": "Observatorio de Inteligencia de Datos — INATEC.",
        },
        "global_stats": {
            "risk_distribution": risk_dist,
            "averages": {
                "composite_score": round(
                    df["skill_programming"].mean() * 0.3
                    + df["skill_infra_db"].mean() * 0.3
                    + df["skill_ai"].mean() * 0.2
                    + df["skill_design"].mean() * 0.1
                    + df["english_level"].mean() * 0.1,
                    2,
                ),
            },
            "geographic_distribution": df["residence_dept"].value_counts().to_dict(),
        },
        "teams": profiles,
    }

    # Guardar archivo
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "telemetria_capital_humano.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # Log resumen
    logger.info(f"\n✓ Telemetría exportada:")
    logger.info(f"  Equipos: {n_teams}")
    logger.info(f"  Respondentes: {n_respondents}")
    logger.info(f"  Distribución de riesgo: {risk_dist}")

    return payload
