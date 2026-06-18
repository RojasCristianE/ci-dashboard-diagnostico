"""
config.py — Constantes, mapeos y diccionarios de normalización.

Observatorio de Inteligencia de Datos
Pipeline de Diagnóstico de Perfil Tecnológico
Centro de Innovación — INATEC Nicaragua

Versión: 1.0.0
"""
from pathlib import Path

PIPELINE_VERSION = "1.0.0"

# ── Rutas ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
PATHS = {
    "raw_csv": BASE_DIR / "data" / "respuestas.csv",
    "plots_dir": BASE_DIR / "outputs" / "plots",
    "llm_context_dir": BASE_DIR / "outputs" / "llm_context",
}

# ── Nombres cortos de columnas (Mapeo del Formulario de Perfil) ────────────────
COLUMN_SHORTNAMES = [
    "full_name",
    "team_name",
    "residence_dept",
    "study_center_type",
    "career_area",
    "main_role",
    "has_equipment",
    "skill_programming",
    "skill_infra_db",
    "skill_design",
    "skill_ai",
    "english_level",
    "learning_method",
    "has_deployed",
    "uses_git",
    "main_obstacle",
    "collab_experience",
    "curiosity_tech",
    "weekly_hours",
]

SKILL_COLUMNS = [
    "skill_programming",
    "skill_infra_db",
    "skill_design",
    "skill_ai",
    "english_level",
]

SKILL_LABELS = {
    "skill_programming": "Programación",
    "skill_infra_db": "Sistemas/BD",
    "skill_design": "Diseño/Interfaces",
    "skill_ai": "IA Generativa",
    "english_level": "Inglés Técnico",
}

# ── Mapeos de Normalización ───────────────────────────────────────────────────

# Alias de equipos (unifica variaciones de nombres)
TEAM_ALIASES = {
    "azura": "mas_ctrl",
    "azura/ctrl": "mas_ctrl",
    "ctrl": "mas_ctrl",
    "mecani asavexi": "asavexi",
    "va d viaje anteriormente nikaroute": "los_mulukukenos",
    "va de viaje": "los_mulukukenos",
    "los de la isla": "islavoz",
    "los meros meros": "nacatamal",
    "nica plus": "nicaplus",
    "nereon": "sui",
}

TEAM_DISPLAY_NAMES = {
    "asavexi": "Asavexi",
    "los_mulukukenos": "Los Mulukukeños",
    "mas_ctrl": "+Ctrl",
    "fritinder": "Frintinder",
    "uradev": "URADEV",
    "nubepleys": "NubePleys",
    "delta_innovations": "Delta Innovation's",
    "phinn": "Phinn",
    "power_rangers": "Power Rangers",
    "nicaplus": "Nicaplus",
    "sui": "Sui",
    "nacatamal": "Nacatamal",
    "chontal_noxus": "Chontal Noxus",
    "islavoz": "IslaVoz",
}

# Departamentos
DEPT_NORMALIZE = {
    "esteli": "Estelí",
    "leon": "León",
    "chinandega": "Chinandega",
    "managua": "Managua",
    "masaya": "Masaya",
    "granada": "Granada",
    "carazo": "Carazo",
    "rivas": "Rivas",
    "chontales": "Chontales",
    "boaco": "Boaco",
    "madriz": "Madriz",
    "nueva segovia": "Nueva Segovia",
    "matagalpa": "Matagalpa",
    "jinotega": "Jinotega",
    "raccn": "RACCN",
    "raccs": "RACCS",
    "rio san juan": "Río San Juan",
}

# Áreas de carrera
CAREER_MAP = {
    "ingenieria de sistemas": "tech_systems",
    "ingenieria en computacion": "tech_systems",
    "licenciatura en sistemas": "tech_systems",
    "diseno grafico": "design",
    "marketing": "marketing",
    "administracion": "business",
}

# Roles
ROLE_MAP = {
    "desarrollador backend": "backend",
    "desarrollador frontend": "frontend",
    "desarrollador full stack": "full_stack",
    "disenador ux/ui": "ux_ui",
    "marketing / modelo de negocio": "marketing",
    "lider de equipo / gestion": "pm_leadership",
    "especialista en datos / ia": "data_ai",
}

# ── Umbrales y Scores ─────────────────────────────────────────────────────────

INCOMPLETE_ROSTER_THRESHOLD = 2  # Equipos con <= 2 personas son marcados

EQUIPMENT_SCORES = {
    "Sí, cuento con computadora propia con buen rendimiento.": 5,
    "Sí, tengo computadora pero es antigua o de bajo rendimiento.": 3,
    "No tengo computadora propia (uso de un compañero o laboratorio).": 1,
}

HOURS_MIDPOINTS = {
    "Menos de 5 horas a la semana.": 2.5,
    "Entre 5 y 10 horas a la semana.": 7.5,
    "Entre 10 y 20 horas a la semana.": 15,
    "Más de 20 horas a la semana.": 25,
}

GIT_SCORES = {
    "Sí, lo uso en todos mis proyectos.": 5,
    "Conozco lo básico, pero no lo uso siempre.": 3,
    "No, guardo mis archivos de forma manual.": 0,
}

DEPLOY_SCORES = {
    "Sí, varias veces.": 5,
    "Sí, al menos una vez.": 3,
    "No, nunca he pasado de la fase local/prototipo.": 0,
}

COLLAB_SCORES = {
    "Sí, estoy acostumbrado a equipos multidisciplinarios.": 5,
    "Muy poco, casi siempre trabajo solo o con gente de mi misma carrera.": 2,
    "No, nunca.": 0,
}

# ── Visualización (Tema Oscuro) ───────────────────────────────────────────────

PALETTE = {
    "bg_dark": "#020617",
    "bg_card": "#0f172a",
    "primary": "#3b82f6",
    "secondary": "#64748b",
    "accent": "#f59e0b",
    "success": "#10b981",
    "danger": "#ef4444",
    "grid": "#1e293b",
    "text_light": "#f8fafc",
    "neutral": "#94a3b8",
}

ROLE_COLORS = {
    "backend": "#3b82f6",
    "frontend": "#06b6d4",
    "full_stack": "#8b5cf6",
    "ux_ui": "#ec4899",
    "marketing": "#f59e0b",
    "pm_leadership": "#10b981",
    "data_ai": "#f43f5e",
    "other": "#64748b",
}

RISK_COLORS = {
    "low": "#10b981",
    "moderate": "#f59e0b",
    "high": "#f97316",
    "critical": "#ef4444",
}

DARK_RCPARAMS = {
    "axes.facecolor": "#020617",
    "figure.facecolor": "#020617",
    "text.color": "#f8fafc",
    "axes.labelcolor": "#94a3b8",
    "xtick.color": "#64748b",
    "ytick.color": "#64748b",
    "grid.color": "#1e293b",
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.facecolor": "#0f172a",
    "savefig.pad_inches": 0.3,
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
}
