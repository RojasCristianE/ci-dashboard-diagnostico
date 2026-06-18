"""
features.py — Fases 2 y 3: Feature Engineering y Assessment de Equipos.

Observatorio de Inteligencia de Datos
Pipeline de Diagnóstico de Perfil Tecnológico
Centro de Innovación — INATEC Nicaragua

Transforma datos individuales en métricas estratégicas por equipo.
"""
import logging
import pandas as pd
import numpy as np

from .config import SKILL_LABELS, SKILL_COLUMNS

logger = logging.getLogger(__name__)


# ── Fase 2: Métricas de Equipo (Roll-Up) ──────────────────────────────────────

def compute_role_balance(team_df: pd.DataFrame) -> dict:
    """Analiza la distribución de roles y detecta gaps críticos."""
    roles = team_df["main_role"].value_counts().to_dict()

    # Identificar áreas cubiertas
    has_backend = "backend" in roles or "full_stack" in roles
    has_frontend = "frontend" in roles or "full_stack" in roles
    has_ux = "ux_ui" in roles
    has_management = "pm_leadership" in roles or "marketing" in roles

    # Clasificación de equilibrio
    if has_backend and has_frontend and (has_ux or has_management):
        classification = "balanced"
    elif not has_backend:
        classification = "missing_backend"
    elif not has_frontend:
        classification = "missing_frontend"
    else:
        classification = "fragmented"

    return {
        "distribution": roles,
        "classification": classification,
        "has_backend": has_backend,
        "has_frontend": has_frontend,
        "has_management": has_management,
    }


def compute_competency_profile(team_df: pd.DataFrame) -> dict:
    """Calcula promedios y dispersión de habilidades técnicas."""
    averages = {}
    stds = {}
    for col in SKILL_COLUMNS:
        label = SKILL_LABELS[col]
        averages[label] = round(team_df[col].mean(), 2)
        stds[label] = round(team_df[col].std(), 2) if len(team_df) > 1 else 0.0

    # Composite Score (Promedio ponderado del equipo)
    # 30% Backend/Sistemas, 30% Programación, 20% IA, 10% Diseño, 10% Inglés
    cs = (
        team_df["skill_programming"].mean() * 0.30
        + team_df["skill_infra_db"].mean() * 0.30
        + team_df["skill_ai"].mean() * 0.20
        + team_df["skill_design"].mean() * 0.10
        + team_df["english_level"].mean() * 0.10
    )

    return {
        "averages": averages,
        "dispersion": stds,
        "composite_score": round(cs, 2),
    }


def compute_infrastructure_risk(team_df: pd.DataFrame) -> dict:
    """Mide el riesgo logístico (hardware y tiempo)."""
    # Hardware score: 1.0 (óptimo) a 0.0 (crítico)
    avg_hw = team_df["equipment_score"].mean() / 5.0
    # Disponibilidad: porcentaje de gente con > 10h
    avail_pct = (team_df["hours_midpoint"] >= 10).mean()

    # Riesgo logístico inverso (0 = bajo riesgo, 1 = alto riesgo)
    risk_score = 1.0 - (avg_hw * 0.6 + avail_pct * 0.4)

    level = "low"
    if risk_score > 0.6:
        level = "high"
    elif risk_score > 0.3:
        level = "moderate"

    return {
        "score": round(risk_score, 2),
        "level": level,
        "avg_hardware": round(avg_hw, 2),
        "availability_index": round(avail_pct, 2),
    }


def compute_operational_capacity(team_df: pd.DataFrame) -> dict:
    """Calcula el 'combustible' semanal del equipo."""
    total_hours = team_df["hours_midpoint"].sum()
    return {
        "total_weekly_hours": total_hours,
        "avg_hours_per_member": round(total_hours / len(team_df), 1),
    }


def compute_maturity_indicators(team_df: pd.DataFrame) -> dict:
    """Indicadores de madurez técnica (Git, Deploy, Collab)."""
    return {
        "git_adoption": round(team_df["git_score"].mean() / 5.0, 2),
        "deployment_rate": round(team_df["deploy_score"].mean() / 5.0, 2),
        "collab_maturity": round(team_df["collab_score"].mean() / 5.0, 2),
    }


def identify_technical_leader(team_df: pd.DataFrame) -> dict:
    """Identifica al integrante con mayor puntaje técnico."""
    # Score técnico individual: (Prog + Infra) / 2
    tech_scores = (team_df["skill_programming"] + team_df["skill_infra_db"]) / 2.0
    leader_idx = tech_scores.idxmax()
    leader = team_df.loc[leader_idx]

    return {
        "name": leader["full_name"],
        "role": leader["main_role"],
        "tech_score": round(tech_scores.max(), 2),
        "is_senior_profile": tech_scores.max() >= 4.0,
    }


# ── Fase 3: Evaluación Automática (Heurística) ───────────────────────────────

def generate_llm_assessment(
    team_name: str,
    member_count: int,
    role_balance: dict,
    competency: dict,
    infra_risk: dict,
    capacity: dict,
    maturity: dict,
    tech_leader: dict,
    flags: list,
) -> dict:
    """
    Genera un diagnóstico narrativo y nivel de riesgo final.
    Simula el juicio experto del Arquitecto.
    """
    risk_level = "low"
    observations = []

    # 1. Evaluación de Riesgo Estructural
    if member_count < 3:
        risk_level = "high"
        observations.append("Equipo con masa crítica insuficiente (Bus Factor alto).")

    if not role_balance["has_backend"]:
        risk_level = "high"
        observations.append("Hueco crítico en Arquitectura/Backend.")

    # 2. Evaluación de Capacidad
    if capacity["total_weekly_hours"] < 25:
        if risk_level != "critical":
            risk_level = "moderate"
        observations.append("Baja dedicación semanal detectada.")

    # 3. Evaluación de Madurez
    if maturity["git_adoption"] < 0.4:
        observations.append("Riesgo de pérdida de código por falta de uso de Git.")

    # 4. Evaluación de Talento
    if tech_leader["tech_score"] < 3.0:
        if risk_level != "critical":
            risk_level = "high"
        observations.append("Falta de liderazgo técnico con experiencia sólida.")

    # Ajuste final por flags
    if "incomplete_roster" in flags and risk_level == "low":
        risk_level = "moderate"

    # Determinar prioridad de mentoría
    priority = "low"
    if risk_level in ["high", "critical"]:
        priority = "urgent"
    elif risk_level == "moderate":
        priority = "medium"

    return {
        "technical_risk_level": risk_level,
        "mentorship_priority": priority,
        "summary_observations": observations,
    }


def _build_member_list(team_df: pd.DataFrame) -> list[dict]:
    """Serializa la información de los integrantes para el JSON final."""
    members = []
    for _, row in team_df.iterrows():
        members.append({
            "name": row["full_name"],
            "role": row["main_role"],
            "department": row["residence_dept"],
            "skills": {
                "programming": int(row["skill_programming"]),
                "infra_db": int(row["skill_infra_db"]),
                "design": int(row["skill_design"]),
                "ai": int(row["skill_ai"]),
                "english": int(row["english_level"]),
            },
            "autonomy_score": round(
                (row["git_score"] + row["deploy_score"] + row["collab_score"]) / 15.0 * 5, 2
            ),
        })
    return members
