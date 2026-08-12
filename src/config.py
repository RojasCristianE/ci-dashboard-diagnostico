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

# ── Columnas de competencias numéricas (0-5) ───────────────────────────────────
SKILL_COLUMNS = [
    "skill_programming",
    "skill_infra_db",
    "skill_design",
    "skill_ai",
    "english_level",
]

# Etiquetas legibles para las skills (para gráficas y JSON)
SKILL_LABELS = {
    "skill_programming": "Programación",
    "skill_infra_db": "Infraestructura / BD",
    "skill_design": "Diseño / Prototipado",
    "skill_ai": "IA Generativa",
    "english_level": "Inglés Técnico",
}

# Pesos para composite score (suma = 1.0)
COMPOSITE_WEIGHTS = {
    "skill_programming": 0.30,
    "skill_infra_db": 0.25,
    "skill_design": 0.15,
    "skill_ai": 0.15,
    "english_level": 0.15,
}

# ── Alias de Equipos (NORMALIZACIÓN CRÍTICA) ───────────────────────────────────
# Mapeo: variante normalizada (lowercase, sin tildes, stripped) → nombre canónico.
# El pipeline aplica strip().lower() y luego busca aquí.
# Decisiones aprobadas:
#   - AZURA/+CTRL → azura
#   - Mecani - Asavexi → asavexi
TEAM_ALIASES = {
    # --- Chontal Noxus / Kachiing! ---
    "chontal noxus": "chontal noxus",
    "chontales noxus": "chontal noxus",
    "kachiing": "chontal noxus",
    "kachiing!": "chontal noxus",
    # --- Va de Viaje / Los Mulukukeños ---
    "va de viaje": "los mulukukenos",
    "va d' viaje": "los mulukukenos",
    "va d' viaje (anteriormente nikaroute+)": "los mulukukenos",
    "va d'aro viaje (anteriormente nikaroute+)": "los mulukukenos",
    "va de viaje (anteriormente nikaroute+)": "los mulukukenos",
    # --- Los Mulukukeños ---
    "los mulukukenos": "los mulukukenos",
    "los mulukuquenos": "los mulukukenos",
    # --- NovaMind / LES Healts ---
    "novamind": "novamind",
    "les healts": "novamind",
    "leshealth": "novamind",
    # --- Azura / mas Ctrl ---
    "azura": "mas ctrl",
    "azura/+ctrl": "mas ctrl",
    "mas ctrl": "mas ctrl",
    "+ctrl": "mas ctrl",
    # --- NexuVida ---
    "nexuvida": "nexuvida",
    "plataforma saas (health tech)": "nexuvida",
    # --- Nica Plus / Nicaplus ---
    "nica plus": "nicaplus",
    "nicaplus": "nicaplus",
    "nica prime": "nicaplus",
    "sitio web de salud comunitaria nicaraguense": "nicaplus",
    # --- VoxLab ---
    "voxlab": "voxlab",
    # --- HatoMaster ---
    "hatomaster": "hatomaster",
    # --- SUI ---
    "sui": "sui",
    "nereon": "sui",
    # --- Phinn ---
    "phinn": "phinn",
    "finny": "phinn",
    # --- Nacatamal / Kira ---
    "nacatamal": "nacatamal",
    "los meros meros": "nacatamal",
    "kira": "nacatamal",
    # --- Asavexi / Mecani ---
    "asavexi": "asavexi",
    "mecani": "asavexi",
    "mecani - asavexi": "asavexi",
    # --- Rommy / Delta Innovations ---
    "rommy": "delta innovations",
    "delta innovations": "delta innovations",
    "delta innovation's": "delta innovations",
    "delta innovation": "delta innovations",
    "roomy asistente de salud virtual": "delta innovations",
    "rommy: asistente de salud virtual": "delta innovations",
    "rommy: asistente de salud virtual (delta innovations)": "delta innovations",
    # --- Power Rangers / NeoFluid3D ---
    "power rangers": "power rangers",
    "neofluid3d": "power rangers",
    "neofluit 3d": "power rangers",
    "neofluid 3d": "power rangers",
    "powers rangers": "power rangers",
    # --- URADEV / NicaBuy / Hackabros ---
    "uradev": "uradev",
    "hackabros": "uradev",
    "nicabuy": "uradev",
    # --- IslaVoz ---
    "islavoz": "islavoz",
    "los de la isla": "islavoz",
    # --- Majingilane / Hogari ---
    "majingilane": "majingilane",
    "hogari": "majingilane",
    # --- Frintinder ---
    "frintinder": "frintinder",
    "fritinder": "frintinder",
    # --- Escenicapp (variantes) ---
    "escenicapp": "escenicapp",
    "escenica": "escenicapp",
    # --- Nicabite (variante de Frintinder) ---
    "nicabite": "frintinder",
    "nicabite / fritinder": "frintinder",
    # --- Otros ---
    "no te aisles": "no te aisles",
    "retina care": "retina care",
    "ruteo": "ruteo",
    "ruta inteligente": "ruteo",
    "nubepleys": "nubepleys",
    "dale click - web marketplace": "nubepleys",
    "plataforma de comercio online": "nubepleys",
    "app de comercio online": "nubepleys",
}

# Nombres display (Title Case) para el JSON y gráficas
TEAM_DISPLAY_NAMES = {
    "chontal noxus": "Chontal Noxus",
    "va de viaje": "Va de Viaje",
    "novamind": "NovaMind",
    "azura": "Azura",
    "+ctrl": "+Ctrl",
    "nexuvida": "NexuVida",
    "nica plus": "Nica Plus",
    "voxlab": "VoxLab",
    "hatomaster": "HatoMaster",
    "los mulukukenos": "Los Mulukukeños",
    "sui": "SUI",
    "finny": "Finny",
    "nereon": "NEREON",
    "los meros meros": "Los Meros Meros",
    "asavexi": "Asavexi",
    "rommy": "Rommy",
    "power rangers": "Power Rangers",
    "hackabros": "Hackabros",
    "nicabite": "Nicabite",
    "delta innovations": "Delta Innovations",
}

# ── Normalización de Departamentos ─────────────────────────────────────────────
# Mapeo de ciudades/cabeceras a nombre de departamento canónico.
DEPT_NORMALIZE = {
    "managua": "Managua",
    "chontales": "Chontales",
    "juigalpa": "Chontales",      # Cabecera de Chontales
    "carazo": "Carazo",
    "jinotepe": "Carazo",         # Cabecera de Carazo
    "granada": "Granada",
    "leon": "León",
    "masaya": "Masaya",
    "rivas": "Rivas",
    "nueva segovia": "Nueva Segovia",
    "madriz": "Madriz",
    "boaco": "Boaco",
    "chinandega": "Chinandega",
    "matagalpa": "Matagalpa",
    "esteli": "Estelí",
    "jinotega": "Jinotega",
    "rio san juan": "Río San Juan",
    "raccn": "RACCN",
    "raccs": "RACCS",
    "bilwi puerto cabezas": "RACCN",
    "puerto cabeza bilwi": "RACCN",
}

# ── Normalización de Roles ─────────────────────────────────────────────────────
# Mapeo: variante normalizada (normalize_text) → etiqueta corta canónica
ROLE_MAP = {
    "desarrollo frontend interfaces web movil": "frontend",
    "desarrollo backend servidores bases de datos logica": "backend",
    "diseno uxui prototipado experiencia de usuario": "ux_ui",
    "marketing negocios y comunicacion": "marketing",
    "gestion de proyectos liderazgo": "pm_leadership",
    "analisis de datos inteligencia artificial": "data_ai",
    # Casos manuales / Otros
    "cto": "cto",
    "branding": "marketing",
    "back y fronted": "full_stack", # Mapeado a full_stack
}

# ── Normalización de Áreas de Carrera ──────────────────────────────────────────
# Mapeo: variante normalizada (normalize_text) → etiqueta corta canónica
CAREER_MAP = {
    "tecnologia informatica y sistemas stem": "tech_systems",
    "tecnologia informatica y sistemas": "tech_systems",
    "ingenierias arquitectura y construccion stem": "engineering",
    "ingenierias arquitectura y construccion": "engineering",
    "ciencias de la salud agropecuarias o biologia stem": "health_sciences",
    "administracion economia y finanzas": "business",
    "comunicacion marketing y medios digitales": "communication",
    "diseno grafico multimedia o artes": "design",
    "oficios tecnicos y servicios": "technical_trades",
    # Casos manuales / Otros
    "simulacion de fluidos de sistemas hidraulicos": "engineering",
    "formacion docencia": "education",
    "ingenieria industrial": "engineering",
}

# Categorías de rol para balance de equipo
ROLE_CATEGORIES_TECH = {"frontend", "backend", "data_ai", "cto", "full_stack"}
ROLE_CATEGORIES_DESIGN = {"ux_ui"}
ROLE_CATEGORIES_BUSINESS = {"marketing", "pm_leadership"}

# ── Mapeos de Escalas Ordinales ────────────────────────────────────────────────

# Equipo de cómputo → escala 0-3
EQUIPMENT_SCORES = {
    "si, tengo pc/laptop y buen internet.": 3,
    "tengo pc/laptop, pero el internet es limitado/inestable.": 2,
    "no tengo equipo propio, dependo de laboratorios o cibercafes.": 1,
    "solo utilizo mi telefono movil / tablet.": 0,
}

EQUIPMENT_LABELS = {
    3: "PC + Internet Estable",
    2: "PC + Internet Limitado",
    1: "Sin Equipo (Cibercafé/Lab)",
    0: "Solo Móvil/Tablet",
}

# Horas semanales → midpoints numéricos
HOURS_MIDPOINTS = {
    "menos de 5 horas a la semana.": 3.0,
    "entre 5 y 10 horas a la semana.": 7.5,
    "entre 10 y 20 horas a la semana.": 15.0,
    "tiempo completo (mas de 20 horas).": 25.0,
}

# Control de versiones → escala 0-2
GIT_SCORES = {
    "si, lo uso en todos mis proyectos.": 2,
    "conozco lo basico, pero no lo uso siempre.": 1,
    "no, guardo mis archivos de forma manual.": 0,
}

# Despliegue → escala 0-2
DEPLOY_SCORES = {
    "si, varias veces.": 2,
    "si, al menos una vez.": 1,
    "no, nunca he pasado de la fase local/prototipo.": 0,
}

# Experiencia colaborativa → escala 0-2
COLLAB_SCORES = {
    "si, estoy acostumbrado a equipos multidisciplinarios.": 2,
    "muy poco, casi siempre trabajo solo o con gente de mi misma carrera.": 1,
    "no, nunca.": 0,
}

# ── Umbrales de clasificación ──────────────────────────────────────────────────

# Riesgo de infraestructura (% de miembros con equipment_score <= 1)
INFRA_RISK_THRESHOLDS = {
    "critical": 0.50,   # >= 50% sin equipo
    "moderate": 0.25,   # >= 25% sin equipo
    # < 25% = "low"
}

# Nivel de dedicación (promedio de horas por miembro)
DEDICATION_THRESHOLDS = {
    "high": 15.0,    # >= 15 horas promedio
    "medium": 7.5,   # >= 7.5 horas promedio
    # < 7.5 = "low"
}

# Umbral para identificar líder técnico
TECH_LEAD_MIN_SKILL = 4  # Al menos 4 en programming O infra_db

# Umbral para equipos con roster incompleto (≤ N personas)
INCOMPLETE_ROSTER_THRESHOLD = 1

# ── Paleta visual (Tema Oscuro Institucional) ──────────────────────────────────
PALETTE = {
    "primary": "#3b82f6",
    "secondary": "#06b6d4",
    "accent": "#f59e0b",
    "danger": "#ef4444",
    "success": "#10b981",
    "neutral": "#6b7280",
    "bg_dark": "#0f172a",
    "bg_card": "#1e293b",
    "text_light": "#e2e8f0",
    "grid": "#334155",
}

# Colores para roles en stacked bar chart
ROLE_COLORS = {
    "backend": "#3b82f6",       # Blue
    "frontend": "#06b6d4",      # Cyan
    "full_stack": "#14b8a6",    # Teal
    "ux_ui": "#a855f7",         # Purple
    "marketing": "#f59e0b",     # Amber
    "pm_leadership": "#10b981", # Emerald
    "data_ai": "#ef4444",       # Red
    "cto": "#ec4899",           # Pink
    "other": "#6b7280",         # Gray
}

# Colores para niveles de riesgo
RISK_COLORS = {
    "low": "#10b981",
    "moderate": "#f59e0b",
    "critical": "#ef4444",
}

DARK_RCPARAMS = {
    "figure.facecolor": "#0f172a",
    "axes.facecolor": "#1e293b",
    "axes.edgecolor": "#334155",
    "axes.labelcolor": "#e2e8f0",
    "text.color": "#e2e8f0",
    "xtick.color": "#94a3b8",
    "ytick.color": "#94a3b8",
    "grid.color": "#334155",
    "grid.alpha": 0.3,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.facecolor": "#0f172a",
    "savefig.pad_inches": 0.3,
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
}
