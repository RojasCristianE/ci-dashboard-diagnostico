"""
exporter.py — Fase 4b: Exportación del JSON semántico para LLMs.

Observatorio de Inteligencia de Datos
Pipeline de Diagnóstico de Perfil Tecnológico
Centro de Innovación — INATEC Nicaragua

Genera telemetria_capital_humano.json optimizado para consumo por LLM
en la redacción del Informe Think Tank.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import numpy as np

from .config import (
    PIPELINE_VERSION,
    SKILL_COLUMNS,
    SKILL_LABELS,
    COMPOSITE_WEIGHTS,
)

logger = logging.getLogger(__name__)


def _compute_global_summary(
    profiles: list[dict],
    df: pd.DataFrame,
) -> dict:
    """
    Calcula resumen global del programa a partir de los perfiles de equipo.
    """
    total_respondents = len(df)
    total_teams = len(profiles)
    member_counts = [p["member_count"] for p in profiles]

    # Promedios globales de skills
    global_skill_avgs = {}
    for col in SKILL_COLUMNS:
        label = SKILL_LABELS[col]
        global_skill_avgs[label] = round(df[col].astype(float).mean(), 2)

    # Composite score global
    global_composite = 0.0
    for col, weight in COMPOSITE_WEIGHTS.items():
        global_composite += df[col].astype(float).mean() * weight
    global_composite = round(global_composite, 2)

    # Riesgo de infraestructura global
    eq_scores = df["equipment_score"].dropna()
    global_pct_at_risk = round((eq_scores <= 1).sum() / len(eq_scores), 2)

    # Distribución geográfica
    geo_dist = (
        df["residence_dept"]
        .value_counts()
        .to_dict()
    )

    # Distribución de roles global
    role_dist = df["main_role"].value_counts().to_dict()

    # Clasificación de riesgo por equipos
    risk_distribution = {}
    for p in profiles:
        level = p["llm_assessment"]["technical_risk_level"]
        risk_distribution[level] = risk_distribution.get(level, 0) + 1

    # Equipos con flag de roster incompleto
    incomplete_teams = [
        p["team_name_display"]
        for p in profiles
        if "incomplete_roster" in p.get("flags", [])
    ]

    return {
        "total_respondents": total_respondents,
        "total_teams": total_teams,
        "avg_team_size": round(sum(member_counts) / len(member_counts), 1),
        "team_size_range": {
            "min": min(member_counts),
            "max": max(member_counts),
        },
        "global_skill_averages": global_skill_avgs,
        "global_composite_score": global_composite,
        "global_equipment_risk": {
            "pct_at_risk": global_pct_at_risk,
            "total_at_risk": int((eq_scores <= 1).sum()),
            "total_respondents": len(eq_scores),
        },
        "geographic_distribution": geo_dist,
        "role_distribution": role_dist,
        "risk_distribution": risk_distribution,
        "incomplete_roster_teams": incomplete_teams,
    }


def _build_rankings(profiles: list[dict]) -> dict:
    """
    Construye rankings ordenados por diferentes métricas.
    """
    # Por composite score (desc)
    by_cs = sorted(
        profiles,
        key=lambda p: p["competency_profile"]["composite_score"],
        reverse=True,
    )
    ranking_cs = [
        {
            "rank": i + 1,
            "team": p["team_name_display"],
            "composite_score": p["competency_profile"]["composite_score"],
            "risk_level": p["llm_assessment"]["technical_risk_level"],
        }
        for i, p in enumerate(by_cs)
    ]

    # Por riesgo de infraestructura (desc = más riesgo primero)
    by_infra = sorted(
        profiles,
        key=lambda p: p["infrastructure_risk"]["pct_at_risk"],
        reverse=True,
    )
    ranking_infra = [
        {
            "rank": i + 1,
            "team": p["team_name_display"],
            "pct_at_risk": p["infrastructure_risk"]["pct_at_risk"],
            "risk_level": p["infrastructure_risk"]["risk_level"],
        }
        for i, p in enumerate(by_infra)
    ]

    # Por capacidad operativa (desc = más horas primero)
    by_hours = sorted(
        profiles,
        key=lambda p: p["operational_capacity"]["total_weekly_hours"],
        reverse=True,
    )
    ranking_hours = [
        {
            "rank": i + 1,
            "team": p["team_name_display"],
            "total_weekly_hours": p["operational_capacity"]["total_weekly_hours"],
            "avg_weekly_hours": p["operational_capacity"]["avg_weekly_hours"],
            "dedication_level": p["operational_capacity"]["dedication_level"],
        }
        for i, p in enumerate(by_hours)
    ]

    # Por madurez operativa (promedio de los 3 indicadores, desc)
    def _maturity_avg(p):
        m = p["maturity_indicators"]
        return (m["deployment_rate"] + m["git_adoption"] + m["collab_maturity"]) / 3

    by_maturity = sorted(profiles, key=_maturity_avg, reverse=True)
    ranking_maturity = [
        {
            "rank": i + 1,
            "team": p["team_name_display"],
            "deployment_rate": p["maturity_indicators"]["deployment_rate"],
            "git_adoption": p["maturity_indicators"]["git_adoption"],
            "collab_maturity": p["maturity_indicators"]["collab_maturity"],
            "avg_maturity": round(_maturity_avg(p), 2),
        }
        for i, p in enumerate(by_maturity)
    ]

    return {
        "by_composite_score": ranking_cs,
        "by_infrastructure_risk": ranking_infra,
        "by_operational_capacity": ranking_hours,
        "by_maturity": ranking_maturity,
    }


def build_telemetry_payload(
    profiles: list[dict],
    df: pd.DataFrame,
) -> dict:
    """
    Construye el payload JSON completo para consumo LLM.

    Args:
        profiles: Lista de perfiles de equipo.
        df: DataFrame limpio.

    Returns:
        dict listo para serializar como JSON.
    """
    return {
        "meta": {
            "pipeline_version": PIPELINE_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "Diagnóstico de Perfil Tecnológico y Competencias Digitales",
            "context": (
                "Auditoría de capital humano para el Programa de Incubación de "
                "Startups de Base Tecnológica — Hackathon Nicaragua 2026. "
                "Centro de Innovación — INATEC."
            ),
            "normalization_decisions": [
                "Miembros 'AZURA/+Ctrl' (Esther Hernández, Maura Ruiz) asignados a equipo Azura.",
                "Miembro 'Mecani - Asavexi' (Yasser Rugama) fusionado con equipo Asavexi.",
                "Equipos de 1 persona incluidos con flag 'incomplete_roster'.",
            ],
        },
        "global_summary": _compute_global_summary(profiles, df),
        "teams": profiles,
        "rankings": _build_rankings(profiles),
    }


class _NumpyEncoder(json.JSONEncoder):
    """Encoder custom para manejar tipos numpy en la serialización JSON."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        return super().default(obj)


def export_json(payload: dict, output_path: Path):
    """
    Serializa y escribe el payload JSON a disco.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, cls=_NumpyEncoder)

    size_kb = output_path.stat().st_size / 1024
    logger.info(f"  📄 JSON exportado: {output_path.name} ({size_kb:.1f} KB)")


def run_export_pipeline(
    profiles: list[dict],
    df: pd.DataFrame,
    output_dir: Path,
) -> dict:
    """
    Orquesta la construcción y exportación del JSON semántico.

    Returns:
        El payload completo (para uso posterior si se necesita).
    """
    logger.info("=" * 60)
    logger.info("FASE 4b: EXPORTACIÓN JSON SEMÁNTICO")
    logger.info("=" * 60)

    payload = build_telemetry_payload(profiles, df)

    output_path = output_dir / "telemetria_capital_humano.json"
    export_json(payload, output_path)

    # Stats rápidas
    n_teams = len(payload["teams"])
    n_respondents = payload["global_summary"]["total_respondents"]
    risk_dist = payload["global_summary"]["risk_distribution"]

    logger.info(f"\n✓ Telemetría exportada:")
    logger.info(f"  Equipos: {n_teams}")
    logger.info(f"  Respondentes: {n_respondents}")
    logger.info(f"  Distribución de riesgo: {risk_dist}")

    return payload
