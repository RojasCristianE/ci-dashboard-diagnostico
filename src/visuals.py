"""
visuals.py — Fase 4: Visualizaciones con tema oscuro institucional.

Observatorio de Inteligencia de Datos
Pipeline de Diagnóstico de Perfil Tecnológico
Centro de Innovación — INATEC Nicaragua

Genera 6 gráficas PNG de alta calidad (300 DPI) para el Informe Think Tank.
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Backend no-interactivo
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.ticker as mticker

from .config import (
    DARK_RCPARAMS,
    PALETTE,
    ROLE_COLORS,
    RISK_COLORS,
    SKILL_LABELS,
    SKILL_COLUMNS,
)

logger = logging.getLogger(__name__)

# Aplicar tema oscuro globalmente
plt.rcParams.update(DARK_RCPARAMS)


# ── Utilidades ─────────────────────────────────────────────────────────────────

def _save_figure(fig: plt.Figure, output_dir: Path, filename: str):
    """Guarda la figura y cierra."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    fig.savefig(path)
    plt.close(fig)
    logger.info(f"  📊 Guardada: {path.name}")


def _get_sorted_profiles(profiles: list[dict]) -> list[dict]:
    """Ordena perfiles por composite score descendente."""
    return sorted(
        profiles,
        key=lambda p: p["competency_profile"]["composite_score"],
        reverse=True,
    )


# ── 1. Radar Chart de Competencias por Equipo ─────────────────────────────────

def plot_competency_radar(profiles: list[dict], output_dir: Path):
    """
    Grid de mini-radar charts — uno por equipo, 5 ejes de competencia.
    """
    sorted_profiles = _get_sorted_profiles(profiles)
    n = len(sorted_profiles)
    cols = 4
    rows = (n + cols - 1) // cols

    skill_names = list(SKILL_LABELS.values())
    n_skills = len(skill_names)
    angles = np.linspace(0, 2 * np.pi, n_skills, endpoint=False).tolist()
    angles += angles[:1]  # Cerrar el polígono

    fig, axes = plt.subplots(
        rows, cols, figsize=(5 * cols, 5 * rows),
        subplot_kw=dict(projection="polar"),
    )
    axes = np.array(axes).flatten()

    for i, profile in enumerate(sorted_profiles):
        ax = axes[i]
        avgs = profile["competency_profile"]["averages"]
        values = [avgs.get(name, 0) for name in skill_names]
        values += values[:1]

        # Polígono con relleno semi-transparente
        ax.fill(angles, values, alpha=0.25, color=PALETTE["primary"])
        ax.plot(angles, values, color=PALETTE["primary"], linewidth=2)

        # Puntos en cada eje
        ax.scatter(angles[:-1], values[:-1], color=PALETTE["accent"], s=30, zorder=5)

        # Configuración del radar
        ax.set_ylim(0, 5)
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_yticklabels(["1", "2", "3", "4", "5"], size=7, color="#94a3b8")
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(skill_names, size=8, color="#e2e8f0")

        # Fondo del radar
        ax.set_facecolor(PALETTE["bg_card"])
        ax.spines["polar"].set_color(PALETTE["grid"])
        ax.grid(color=PALETTE["grid"], alpha=0.3)

        # Título con composite score
        cs = profile["competency_profile"]["composite_score"]
        risk = profile["llm_assessment"]["technical_risk_level"]
        risk_color = RISK_COLORS.get(risk, PALETTE["neutral"])
        ax.set_title(
            f"{profile['team_name_display']} (CS: {cs})",
            pad=15, fontsize=10, fontweight="bold",
            color=risk_color,
        )

    # Ocultar ejes sobrantes
    for j in range(n, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle(
        "Radar de Competencias por Equipo",
        fontsize=18, fontweight="bold", color=PALETTE["text_light"],
        y=1.02,
    )
    fig.tight_layout()
    _save_figure(fig, output_dir, "radar_competencias_equipos.png")


# ── 2. Heatmap de Competencias ─────────────────────────────────────────────────

def plot_competency_heatmap(profiles: list[dict], output_dir: Path):
    """
    Heatmap: equipos (Y) vs competencias (X), ordenado por composite score.
    """
    sorted_profiles = _get_sorted_profiles(profiles)
    skill_names = list(SKILL_LABELS.values())

    team_names = [p["team_name_display"] for p in sorted_profiles]
    data = []
    for p in sorted_profiles:
        avgs = p["competency_profile"]["averages"]
        data.append([avgs.get(name, 0) for name in skill_names])

    data_array = np.array(data)

    fig, ax = plt.subplots(figsize=(10, max(8, len(team_names) * 0.5)))

    # Heatmap con colormap personalizado
    im = ax.imshow(data_array, aspect="auto", cmap="YlOrRd", vmin=0, vmax=5)

    # Anotaciones
    for i in range(len(team_names)):
        for j in range(len(skill_names)):
            val = data_array[i, j]
            text_color = "#0f172a" if val > 2.5 else "#e2e8f0"
            ax.text(
                j, i, f"{val:.1f}",
                ha="center", va="center",
                fontsize=10, fontweight="bold",
                color=text_color,
            )

    ax.set_xticks(range(len(skill_names)))
    ax.set_xticklabels(skill_names, rotation=30, ha="right", fontsize=10)
    ax.set_yticks(range(len(team_names)))
    ax.set_yticklabels(team_names, fontsize=10)

    # Agregar composite score como texto a la derecha
    for i, p in enumerate(sorted_profiles):
        cs = p["competency_profile"]["composite_score"]
        ax.text(
            len(skill_names) + 0.3, i, f"CS: {cs}",
            ha="left", va="center",
            fontsize=9, color=PALETTE["accent"], fontweight="bold",
        )

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.15)
    cbar.set_label("Promedio (0-5)", color=PALETTE["text_light"])
    cbar.ax.yaxis.set_tick_params(color=PALETTE["text_light"])
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=PALETTE["text_light"])

    ax.set_title(
        "Heatmap de Competencias por Equipo\n(Ordenado por Composite Score)",
        fontsize=14, fontweight="bold", pad=15,
    )

    fig.tight_layout()
    _save_figure(fig, output_dir, "heatmap_competencias.png")


# ── 3. Distribución de Roles (Stacked Bar) ────────────────────────────────────

def plot_role_distribution(profiles: list[dict], output_dir: Path):
    """
    Stacked horizontal bar chart — distribución de roles por equipo.
    """
    sorted_profiles = _get_sorted_profiles(profiles)
    all_roles = sorted(ROLE_COLORS.keys())

    team_names = [p["team_name_display"] for p in sorted_profiles]
    role_data = {role: [] for role in all_roles}

    for p in sorted_profiles:
        dist = p["role_balance"]["distribution"]
        for role in all_roles:
            role_data[role].append(dist.get(role, 0))

    fig, ax = plt.subplots(figsize=(12, max(8, len(team_names) * 0.45)))

    y_pos = np.arange(len(team_names))
    left = np.zeros(len(team_names))

    for role in all_roles:
        values = role_data[role]
        if sum(values) == 0:
            continue  # Skip roles no presentes
        bars = ax.barh(
            y_pos, values, left=left,
            color=ROLE_COLORS.get(role, PALETTE["neutral"]),
            label=role.replace("_", " ").title(),
            edgecolor=PALETTE["bg_dark"], linewidth=0.5,
            height=0.7,
        )
        # Anotación dentro de cada barra si el valor > 0
        for j, (bar, val) in enumerate(zip(bars, values)):
            if val > 0:
                ax.text(
                    left[j] + val / 2, j, str(int(val)),
                    ha="center", va="center",
                    fontsize=9, fontweight="bold", color=PALETTE["text_light"],
                )
        left += np.array(values)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(team_names, fontsize=10)
    ax.set_xlabel("Número de Integrantes", fontsize=11)
    ax.set_title(
        "Distribución de Roles por Equipo",
        fontsize=14, fontweight="bold", pad=15,
    )
    ax.legend(
        loc="lower right", fontsize=9,
        facecolor=PALETTE["bg_card"], edgecolor=PALETTE["grid"],
        labelcolor=PALETTE["text_light"],
    )
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.invert_yaxis()

    fig.tight_layout()
    _save_figure(fig, output_dir, "distribucion_roles_equipos.png")


# ── 4. Mapa de Viabilidad (Bubble Chart) ──────────────────────────────────────

def plot_viability_map(profiles: list[dict], output_dir: Path):
    """
    Bubble chart: X = Composite Score, Y = Total Weekly Hours.
    Size = miembros, Color = risk level.
    """
    fig, ax = plt.subplots(figsize=(14, 10))

    for p in profiles:
        cs = p["competency_profile"]["composite_score"]
        hours = p["operational_capacity"]["total_weekly_hours"]
        members = p["member_count"]
        risk = p["llm_assessment"]["technical_risk_level"]

        color = RISK_COLORS.get(risk, PALETTE["neutral"])
        size = max(members * 120, 80)  # Mínimo visible

        ax.scatter(
            cs, hours, s=size,
            color=color, alpha=0.7,
            edgecolor=PALETTE["text_light"], linewidth=1.5,
            zorder=3,
        )
        ax.annotate(
            p["team_name_display"],
            (cs, hours),
            textcoords="offset points",
            xytext=(8, 8),
            fontsize=9, color=PALETTE["text_light"],
            fontweight="bold",
            arrowprops=dict(arrowstyle="-", color=PALETTE["grid"], lw=0.5),
        )

    # Líneas de referencia
    ax.axvline(x=2.5, color=PALETTE["danger"], linestyle="--", alpha=0.3, label="Umbral CS mínimo")
    ax.axhline(y=30, color=PALETTE["accent"], linestyle="--", alpha=0.3, label="30h/semana equipo")

    # Cuadrantes
    ax.text(1.0, 5, "[CRITICO]\nBajo CS + Baja Dedicacion",
            fontsize=8, color=PALETTE["danger"], alpha=0.5, ha="center")
    ax.text(4.0, 5, "[POTENCIAL]\nAlto CS + Baja Dedicacion",
            fontsize=8, color=PALETTE["accent"], alpha=0.5, ha="center")

    ax.set_xlabel("Composite Score (Promedio Ponderado de Competencias)", fontsize=11)
    ax.set_ylabel("Horas Semanales Totales del Equipo", fontsize=11)
    ax.set_title(
        "Mapa de Viabilidad: Capacidad Técnica vs Dedicación\n"
        "(Tamaño = N° Miembros | Color = Nivel de Riesgo)",
        fontsize=14, fontweight="bold", pad=15,
    )

    # Leyenda de riesgo
    for level, color in RISK_COLORS.items():
        ax.scatter([], [], c=color, s=100, label=f"Riesgo: {level.title()}")
    ax.legend(
        loc="upper left", fontsize=9,
        facecolor=PALETTE["bg_card"], edgecolor=PALETTE["grid"],
        labelcolor=PALETTE["text_light"],
    )

    ax.grid(True, alpha=0.2)
    fig.tight_layout()
    _save_figure(fig, output_dir, "mapa_viabilidad_equipos.png")


# ── 5. Madurez Operativa (Grouped Bar) ────────────────────────────────────────

def plot_operational_maturity(profiles: list[dict], output_dir: Path):
    """
    Grouped bar chart: Git adoption + Deployment rate + Collab maturity por equipo.
    """
    sorted_profiles = _get_sorted_profiles(profiles)

    team_names = [p["team_name_display"] for p in sorted_profiles]
    git_rates = [p["maturity_indicators"]["git_adoption"] * 100 for p in sorted_profiles]
    deploy_rates = [p["maturity_indicators"]["deployment_rate"] * 100 for p in sorted_profiles]
    collab_rates = [p["maturity_indicators"]["collab_maturity"] * 100 for p in sorted_profiles]

    x = np.arange(len(team_names))
    width = 0.25

    fig, ax = plt.subplots(figsize=(14, max(7, len(team_names) * 0.35)))

    bars1 = ax.barh(x - width, git_rates, width,
                    label="Adopción Git", color=PALETTE["primary"], alpha=0.85)
    bars2 = ax.barh(x, deploy_rates, width,
                    label="Tasa de Despliegue", color=PALETTE["accent"], alpha=0.85)
    bars3 = ax.barh(x + width, collab_rates, width,
                    label="Madurez Colaborativa", color=PALETTE["success"], alpha=0.85)

    # Anotaciones de porcentaje
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            w = bar.get_width()
            if w > 5:
                ax.text(
                    w - 2, bar.get_y() + bar.get_height() / 2,
                    f"{w:.0f}%",
                    ha="right", va="center", fontsize=8,
                    color=PALETTE["bg_dark"], fontweight="bold",
                )

    ax.set_yticks(x)
    ax.set_yticklabels(team_names, fontsize=10)
    ax.set_xlabel("Porcentaje del Equipo (%)", fontsize=11)
    ax.set_xlim(0, 110)
    ax.set_title(
        "Indicadores de Madurez Operativa por Equipo",
        fontsize=14, fontweight="bold", pad=15,
    )
    ax.legend(
        loc="lower right", fontsize=9,
        facecolor=PALETTE["bg_card"], edgecolor=PALETTE["grid"],
        labelcolor=PALETTE["text_light"],
    )
    ax.invert_yaxis()

    fig.tight_layout()
    _save_figure(fig, output_dir, "madurez_operativa.png")


# ── 6. Distribución Geográfica ─────────────────────────────────────────────────

def plot_geographic_distribution(df: pd.DataFrame, output_dir: Path):
    """
    Horizontal bar chart: participantes por departamento con equipos anotados.
    """
    dept_counts = df["residence_dept"].value_counts().sort_values(ascending=True)

    # Equipos por departamento
    dept_teams = (
        df.groupby("residence_dept")["team_name_display"]
        .apply(lambda x: ", ".join(sorted(x.unique())))
        .to_dict()
    )

    fig, ax = plt.subplots(figsize=(12, max(6, len(dept_counts) * 0.5)))

    colors = [PALETTE["primary"] if count > 5 else PALETTE["secondary"]
              for count in dept_counts.values]

    bars = ax.barh(
        range(len(dept_counts)), dept_counts.values,
        color=colors, edgecolor=PALETTE["bg_dark"],
        height=0.7, alpha=0.85,
    )

    ax.set_yticks(range(len(dept_counts)))
    ax.set_yticklabels(dept_counts.index, fontsize=10)
    ax.set_xlabel("Número de Participantes", fontsize=11)

    # Anotaciones: conteo + equipos
    for i, (dept, count) in enumerate(dept_counts.items()):
        teams = dept_teams.get(dept, "")
        # Truncar si es muy largo
        if len(teams) > 50:
            teams = teams[:47] + "..."
        ax.text(
            count + 0.3, i, f"{count}  [{teams}]",
            ha="left", va="center", fontsize=8,
            color=PALETTE["text_light"], style="italic",
        )

    ax.set_title(
        "Distribución Geográfica de Participantes\n(por Departamento)",
        fontsize=14, fontweight="bold", pad=15,
    )
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.set_xlim(0, dept_counts.max() + 15)

    fig.tight_layout()
    _save_figure(fig, output_dir, "distribucion_geografica.png")


# ── Orquestador ───────────────────────────────────────────────────────────────

def generate_all_plots(
    profiles: list[dict],
    df: pd.DataFrame,
    output_dir: Path,
):
    """
    Genera todas las visualizaciones del pipeline.

    Args:
        profiles: Lista de perfiles de equipo (output de features.build_team_profiles).
        df: DataFrame limpio (para gráfica geográfica).
        output_dir: Directorio de salida para las imágenes PNG.
    """
    logger.info("=" * 60)
    logger.info("FASE 4a: GENERACIÓN DE VISUALIZACIONES")
    logger.info("=" * 60)

    output_dir.mkdir(parents=True, exist_ok=True)

    plot_competency_radar(profiles, output_dir)
    plot_competency_heatmap(profiles, output_dir)
    plot_role_distribution(profiles, output_dir)
    plot_viability_map(profiles, output_dir)
    plot_operational_maturity(profiles, output_dir)
    plot_geographic_distribution(df, output_dir)

    logger.info(f"\n✓ 6 visualizaciones generadas en: {output_dir}")
