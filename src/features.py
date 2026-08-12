"""
features.py — Fases 2-3: Feature Engineering, Team Roll-Up y Líder Técnico.

Observatorio de Inteligencia de Datos
Pipeline de Diagnóstico de Perfil Tecnológico
Centro de Innovación — INATEC Nicaragua

Agrupa individuos por equipo y calcula métricas colectivas de viabilidad.
"""
import logging
from typing import Any

import pandas as pd
import numpy as np

from .config import (
    SKILL_COLUMNS,
    SKILL_LABELS,
    COMPOSITE_WEIGHTS,
    ROLE_CATEGORIES_TECH,
    ROLE_CATEGORIES_DESIGN,
    ROLE_CATEGORIES_BUSINESS,
    ROLE_COLORS,
    EQUIPMENT_LABELS,
    TEAM_DISPLAY_NAMES,
    INFRA_RISK_THRESHOLDS,
    DEDICATION_THRESHOLDS,
    TECH_LEAD_MIN_SKILL,
    INCOMPLETE_ROSTER_THRESHOLD,
)

logger = logging.getLogger(__name__)


# ── Balance de Roles ───────────────────────────────────────────────────────────

def compute_role_balance(group: pd.DataFrame) -> dict:
    """
    Analiza la distribución de roles dentro de un equipo.

    Returns:
        dict con distribution, classification, y flags.
    """
    role_counts = group["main_role"].value_counts().to_dict()

    # Contar por categoría
    n_tech = sum(role_counts.get(r, 0) for r in ROLE_CATEGORIES_TECH)
    n_design = sum(role_counts.get(r, 0) for r in ROLE_CATEGORIES_DESIGN)
    n_business = sum(role_counts.get(r, 0) for r in ROLE_CATEGORIES_BUSINESS)
    n_total = len(group)

    flags = []

    # Verificar roles mínimos viables
    has_backend = role_counts.get("backend", 0) > 0 or role_counts.get("cto", 0) > 0 or role_counts.get("full_stack", 0) > 0
    has_frontend = role_counts.get("frontend", 0) > 0 or role_counts.get("full_stack", 0) > 0
    has_business = n_business > 0

    if not has_backend:
        flags.append("ZERO_BACKEND")
    if not has_frontend:
        flags.append("ZERO_FRONTEND")
    if not has_business:
        flags.append("ZERO_BUSINESS")

    # Clasificación
    if has_backend and has_frontend and has_business:
        classification = "balanced"
    elif n_total > 0 and n_tech / n_total >= 0.66 and not has_business:
        classification = "tech_heavy"
    elif n_total > 0 and (n_design + n_business) / n_total >= 0.66 and not has_backend:
        classification = "design_heavy"
    elif n_total == 1:
        classification = "solo"
    else:
        classification = "unbalanced"

    return {
        "distribution": role_counts,
        "counts_by_category": {
            "tech": n_tech,
            "design": n_design,
            "business": n_business,
        },
        "classification": classification,
        "flags": flags,
    }


# ── Termómetro de Competencias ─────────────────────────────────────────────────

def compute_competency_profile(group: pd.DataFrame) -> dict:
    """
    Calcula estadísticas de competencias del equipo.

    Returns:
        dict con averages, peaks, floors, skill_gaps, y composite_score.
    """
    averages = {}
    peaks = {}
    floors = {}
    skill_gaps = {}

    for col in SKILL_COLUMNS:
        label = SKILL_LABELS[col]
        vals = group[col].astype(float)
        avg = round(vals.mean(), 2)
        mx = int(vals.max())
        mn = int(vals.min())

        averages[label] = avg
        peaks[label] = mx
        floors[label] = mn
        skill_gaps[label] = mx - mn

    # Composite score ponderado
    composite = 0.0
    for col, weight in COMPOSITE_WEIGHTS.items():
        composite += group[col].astype(float).mean() * weight
    composite = round(composite, 2)

    return {
        "averages": averages,
        "peaks": peaks,
        "floors": floors,
        "skill_gaps": skill_gaps,
        "composite_score": composite,
    }


# ── Riesgo de Infraestructura ──────────────────────────────────────────────────

def compute_infrastructure_risk(group: pd.DataFrame) -> dict:
    """
    Evalúa el riesgo de infraestructura del equipo basado en equipamiento.

    Returns:
        dict con avg_equipment_score, pct_at_risk, risk_level, y detalles.
    """
    scores = group["equipment_score"].dropna()

    if len(scores) == 0:
        return {
            "avg_equipment_score": 0,
            "pct_at_risk": 1.0,
            "risk_level": "critical",
            "member_details": [],
        }

    avg_score = round(scores.mean(), 2)
    at_risk = (scores <= 1).sum()  # Cibercafé o solo móvil
    pct_at_risk = round(at_risk / len(scores), 2)

    if pct_at_risk >= INFRA_RISK_THRESHOLDS["critical"]:
        risk_level = "critical"
    elif pct_at_risk >= INFRA_RISK_THRESHOLDS["moderate"]:
        risk_level = "moderate"
    else:
        risk_level = "low"

    # Detalles por miembro (para el JSON)
    member_details = []
    for _, row in group.iterrows():
        eq_score = row.get("equipment_score", np.nan)
        eq_label = EQUIPMENT_LABELS.get(
            int(eq_score) if pd.notna(eq_score) else -1,
            "Desconocido"
        )
        member_details.append({
            "name": row["full_name"],
            "equipment_score": int(eq_score) if pd.notna(eq_score) else None,
            "equipment_label": eq_label,
        })

    return {
        "avg_equipment_score": avg_score,
        "pct_at_risk": pct_at_risk,
        "risk_level": risk_level,
        "member_details": member_details,
    }


# ── Capacidad Operativa ───────────────────────────────────────────────────────

def compute_operational_capacity(group: pd.DataFrame) -> dict:
    """
    Sumariza las horas semanales dedicadas por el equipo.

    Returns:
        dict con total_weekly_hours, avg_weekly_hours, pct_fulltime, dedication_level.
    """
    hours = group["hours_midpoint"].dropna()

    if len(hours) == 0:
        return {
            "total_weekly_hours": 0,
            "avg_weekly_hours": 0,
            "pct_fulltime": 0,
            "dedication_level": "low",
        }

    total = round(hours.sum(), 1)
    avg = round(hours.mean(), 1)
    pct_fulltime = round((hours >= 25).sum() / len(hours), 2)

    if avg >= DEDICATION_THRESHOLDS["high"]:
        dedication_level = "high"
    elif avg >= DEDICATION_THRESHOLDS["medium"]:
        dedication_level = "medium"
    else:
        dedication_level = "low"

    return {
        "total_weekly_hours": total,
        "avg_weekly_hours": avg,
        "pct_fulltime": pct_fulltime,
        "dedication_level": dedication_level,
    }


# ── Indicadores de Madurez ─────────────────────────────────────────────────────

def compute_maturity_indicators(group: pd.DataFrame) -> dict:
    """
    Calcula tasas de despliegue, adopción Git y madurez de colaboración.

    Returns:
        dict con deployment_rate, git_adoption, collab_maturity.
    """
    n = len(group)
    if n == 0:
        return {"deployment_rate": 0, "git_adoption": 0, "collab_maturity": 0}

    # Deploy: score >= 1 significa "ha desplegado al menos una vez"
    deploy = group["deploy_score"].dropna()
    deployment_rate = round((deploy >= 1).sum() / n, 2)

    # Git: score == 2 significa "lo usa en todos sus proyectos"
    git = group["git_score"].dropna()
    git_adoption = round((git == 2).sum() / n, 2)

    # Collab: score == 2 significa "acostumbrado a equipos multidisciplinarios"
    collab = group["collab_score"].dropna()
    collab_maturity = round((collab == 2).sum() / n, 2)

    return {
        "deployment_rate": deployment_rate,
        "git_adoption": git_adoption,
        "collab_maturity": collab_maturity,
    }


# ── Líder Técnico Real (Fase 3) ───────────────────────────────────────────────

def identify_technical_leader(group: pd.DataFrame) -> dict:
    """
    Identifica al miembro con los scores técnicos más altos dentro del equipo.

    El "Arquitecto Real" es quien tiene skill_programming >= 4 OR skill_infra_db >= 4,
    rankeado por la suma (programming + infra_db) descendente.

    Returns:
        dict con name, declared_role, skills, is_declared_pm,
        y flag si no hay líder técnico claro.
    """
    # Filtrar candidatos
    candidates = group[
        (group["skill_programming"] >= TECH_LEAD_MIN_SKILL) |
        (group["skill_infra_db"] >= TECH_LEAD_MIN_SKILL)
    ].copy()

    if candidates.empty:
        # Nadie cumple el umbral — reportar al mejor disponible
        group_sorted = group.copy()
        group_sorted["_tech_sum"] = (
            group_sorted["skill_programming"] + group_sorted["skill_infra_db"]
        )
        best = group_sorted.sort_values("_tech_sum", ascending=False).iloc[0]

        return {
            "name": best["full_name"],
            "declared_role": best["main_role"],
            "skills": {
                "programming": int(best["skill_programming"]),
                "infra_db": int(best["skill_infra_db"]),
                "design": int(best["skill_design"]),
                "ai": int(best["skill_ai"]),
                "english": int(best["english_level"]),
            },
            "tech_sum": int(best["skill_programming"] + best["skill_infra_db"]),
            "is_declared_pm": best["main_role"] in ("pm_leadership", "marketing"),
            "flag": "NO_CLEAR_TECH_LEAD",
        }

    # Rankear candidatos
    candidates["_tech_sum"] = (
        candidates["skill_programming"] + candidates["skill_infra_db"]
    )
    leader = candidates.sort_values("_tech_sum", ascending=False).iloc[0]

    return {
        "name": leader["full_name"],
        "declared_role": leader["main_role"],
        "skills": {
            "programming": int(leader["skill_programming"]),
            "infra_db": int(leader["skill_infra_db"]),
            "design": int(leader["skill_design"]),
            "ai": int(leader["skill_ai"]),
            "english": int(leader["english_level"]),
        },
        "tech_sum": int(leader["skill_programming"] + leader["skill_infra_db"]),
        "is_declared_pm": leader["main_role"] in ("pm_leadership", "marketing"),
        "flag": None,
    }


# ── Assessment automático para LLM ────────────────────────────────────────────

def generate_llm_assessment(
    team_name: str,
    member_count: int,
    role_balance: dict,
    competency: dict,
    infra_risk: dict,
    capacity: dict,
    maturity: dict,
    tech_leader: dict,
    flags: list[str],
) -> dict:
    """
    Genera strings de fortalezas, debilidades y recomendación
    basados en las métricas calculadas, para consumo directo del LLM.
    """
    strengths = []
    weaknesses = []
    risk_level = "low"

    # --- Competencias ---
    cs = competency["composite_score"]
    if cs >= 3.5:
        strengths.append(
            f"Composite Score alto ({cs}/5.0) — equipo con base técnica sólida."
        )
    elif cs >= 2.5:
        strengths.append(f"Composite Score medio ({cs}/5.0) — capacidad funcional.")
    else:
        weaknesses.append(
            f"Composite Score bajo ({cs}/5.0) — brecha técnica significativa."
        )
        risk_level = "moderate"

    # --- Picos de excelencia ---
    for skill, val in competency["peaks"].items():
        if val >= 5:
            strengths.append(f"Excelencia en {skill} (pico 5/5).")

    # --- Brechas internas ---
    for skill, gap in competency["skill_gaps"].items():
        if gap >= 4:
            weaknesses.append(
                f"Brecha interna extrema en {skill} (gap de {gap} puntos)."
            )

    # --- Balance de roles ---
    if role_balance["classification"] == "balanced":
        strengths.append("Equipo balanceado con cobertura de roles técnicos y negocio.")
    elif role_balance["classification"] == "tech_heavy":
        weaknesses.append(
            "Equipo sesgado hacia perfiles técnicos sin cobertura de negocio."
        )
    elif role_balance["classification"] == "design_heavy":
        weaknesses.append(
            "Equipo sesgado hacia diseño/negocio sin capacidad de desarrollo backend."
        )
        risk_level = "high"
    elif role_balance["classification"] == "solo":
        weaknesses.append("Equipo de una sola persona — capacidad operativa limitada.")
        risk_level = "high"

    for flag in role_balance.get("flags", []):
        if flag == "ZERO_BACKEND":
            weaknesses.append("Sin ningún perfil Backend — riesgo de no poder ejecutar.")
        elif flag == "ZERO_FRONTEND":
            weaknesses.append("Sin perfil Frontend declarado.")

    # --- Infraestructura ---
    if infra_risk["risk_level"] == "critical":
        weaknesses.append(
            f"Riesgo de infraestructura CRÍTICO: {int(infra_risk['pct_at_risk']*100)}% "
            f"del equipo sin equipo propio."
        )
        risk_level = "critical"
    elif infra_risk["risk_level"] == "moderate":
        weaknesses.append(
            f"Riesgo de infraestructura moderado: {int(infra_risk['pct_at_risk']*100)}% "
            f"del equipo con acceso limitado."
        )
        if risk_level == "low":
            risk_level = "moderate"

    # --- Capacidad operativa ---
    if capacity["dedication_level"] == "high":
        strengths.append(
            f"Alta dedicación: {capacity['avg_weekly_hours']}h/semana promedio."
        )
    elif capacity["dedication_level"] == "low":
        weaknesses.append(
            f"Baja dedicación: solo {capacity['avg_weekly_hours']}h/semana promedio."
        )

    # --- Madurez ---
    if maturity["git_adoption"] >= 0.8:
        strengths.append(
            f"Alta adopción de Git ({int(maturity['git_adoption']*100)}%)."
        )
    elif maturity["git_adoption"] <= 0.3:
        weaknesses.append(
            f"Muy baja adopción de Git ({int(maturity['git_adoption']*100)}%) — "
            f"riesgo de colaboración."
        )

    if maturity["deployment_rate"] >= 0.5:
        strengths.append(
            f"Experiencia en despliegue ({int(maturity['deployment_rate']*100)}% "
            f"han publicado)."
        )
    elif maturity["deployment_rate"] == 0:
        weaknesses.append("Nadie en el equipo ha desplegado una aplicación.")

    # --- Líder técnico ---
    if tech_leader.get("flag") == "NO_CLEAR_TECH_LEAD":
        weaknesses.append(
            f"Sin líder técnico claro (nadie con skill >= {TECH_LEAD_MIN_SKILL}). "
            f"Mejor candidato: {tech_leader['name']} "
            f"(prog: {tech_leader['skills']['programming']}, "
            f"infra: {tech_leader['skills']['infra_db']})."
        )
        if risk_level in ("low", "moderate"):
            risk_level = "high"
    else:
        strengths.append(
            f"Líder técnico identificado: {tech_leader['name']} "
            f"(prog: {tech_leader['skills']['programming']}, "
            f"infra: {tech_leader['skills']['infra_db']})."
        )

    # --- Flags generales ---
    if "incomplete_roster" in flags:
        weaknesses.append(
            "Roster incompleto — solo un miembro registrado en este formulario."
        )

    # --- Generar recomendación ---
    if risk_level == "critical":
        recommendation = (
            "RIESGO CRÍTICO. Se recomienda Mentoría Preventiva con "
            "Recomendación de Pivoteo o asignación de mentoría intensiva."
        )
    elif risk_level == "high":
        recommendation = (
            "RIESGO ALTO. Requiere intervención directa del programa de "
            "mentorías para cubrir brechas fundamentales."
        )
    elif risk_level == "moderate":
        recommendation = (
            "RIESGO MODERADO. Viable con mentoría técnica focalizado "
            "en las debilidades identificadas."
        )
    else:
        recommendation = (
            "RIESGO BAJO. Equipo con capacidad de ejecución. "
            "Mentoría orientada a escalabilidad y refinamiento."
        )

    return {
        "strengths": strengths if strengths else ["Sin fortalezas destacadas."],
        "critical_weaknesses": weaknesses if weaknesses else ["Sin debilidades críticas."],
        "technical_risk_level": risk_level,
        "recommendation": recommendation,
    }


# ── Construcción de Perfiles de Equipo ─────────────────────────────────────────

def _build_member_list(group: pd.DataFrame) -> list[dict]:
    """Construye la lista de miembros con sus datos individuales."""
    members = []
    for _, row in group.iterrows():
        members.append({
            "name": row["full_name"],
            "role": row["main_role"],
            "department": row["residence_dept"],
            "study_center": row.get("study_center_type", ""),
            "career_area": row.get("career_area", ""),
            "skills": {
                "programming": int(row["skill_programming"]),
                "infra_db": int(row["skill_infra_db"]),
                "design": int(row["skill_design"]),
                "ai": int(row["skill_ai"]),
                "english": int(row["english_level"]),
            },
            "equipment_score": (
                int(row["equipment_score"])
                if pd.notna(row.get("equipment_score"))
                else None
            ),
            "weekly_hours": (
                float(row["hours_midpoint"])
                if pd.notna(row.get("hours_midpoint"))
                else None
            ),
            "git_score": (
                int(row["git_score"])
                if pd.notna(row.get("git_score"))
                else None
            ),
            "deploy_score": (
                int(row["deploy_score"])
                if pd.notna(row.get("deploy_score"))
                else None
            ),
            "collab_score": (
                int(row["collab_score"])
                if pd.notna(row.get("collab_score"))
                else None
            ),
            "learning_method": row.get("learning_method", ""),
            "main_obstacle": row.get("main_obstacle", ""),
            "curiosity_tech": row.get("curiosity_tech", ""),
        })
    return members


def build_team_profiles(df: pd.DataFrame) -> list[dict]:
    """
    Orquesta todas las funciones de feature engineering por equipo.

    Args:
        df: DataFrame limpio post-Phase 1.

    Returns:
        Lista de diccionarios, uno por equipo, con toda la telemetría.
    """
    logger.info("=" * 60)
    logger.info("FASES 2-3: FEATURE ENGINEERING + TEAM ROLL-UP")
    logger.info("=" * 60)

    profiles = []

    for team_name, group in df.groupby("team_name"):
        member_count = len(group)
        display_name = TEAM_DISPLAY_NAMES.get(team_name, team_name.title())

        # Flags del equipo
        team_flags = []
        if member_count <= INCOMPLETE_ROSTER_THRESHOLD:
            team_flags.append("incomplete_roster")

        # Calcular todas las métricas
        role_balance = compute_role_balance(group)
        competency = compute_competency_profile(group)
        infra_risk = compute_infrastructure_risk(group)
        capacity = compute_operational_capacity(group)
        maturity = compute_maturity_indicators(group)
        tech_leader = identify_technical_leader(group)
        members = _build_member_list(group)

        # Assessment automático
        assessment = generate_llm_assessment(
            team_name=team_name,
            member_count=member_count,
            role_balance=role_balance,
            competency=competency,
            infra_risk=infra_risk,
            capacity=capacity,
            maturity=maturity,
            tech_leader=tech_leader,
            flags=team_flags,
        )

        profile = {
            "team_name": team_name,
            "team_name_display": display_name,
            "member_count": member_count,
            "flags": team_flags,
            "members": members,
            "role_balance": role_balance,
            "competency_profile": competency,
            "infrastructure_risk": infra_risk,
            "operational_capacity": capacity,
            "maturity_indicators": maturity,
            "technical_leader": tech_leader,
            "llm_assessment": assessment,
        }

        profiles.append(profile)

        # Log resumen
        risk_emoji = {
            "low": "🟢", "moderate": "🟡", "high": "🟠", "critical": "🔴"
        }
        emoji = risk_emoji.get(assessment["technical_risk_level"], "⚪")
        logger.info(
            f"  {emoji} {display_name:20s} | {member_count} miembros | "
            f"CS: {competency['composite_score']:.2f} | "
            f"Roles: {role_balance['classification']:12s} | "
            f"Riesgo: {assessment['technical_risk_level']}"
        )

    # Ordenar por composite score descendente
    profiles.sort(key=lambda p: p["competency_profile"]["composite_score"], reverse=True)

    logger.info(f"\n✓ {len(profiles)} perfiles de equipo generados.")
    return profiles
