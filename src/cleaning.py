"""
cleaning.py — Fase 1: Limpieza, normalización y sanitización de datos crudos.

Observatorio de Inteligencia de Datos
Pipeline de Diagnóstico de Perfil Tecnológico
Centro de Innovación — INATEC Nicaragua

Funciones puras que transforman el DataFrame crudo en un DataFrame limpio
listo para feature engineering.
"""
import re
import unicodedata
import logging
from pathlib import Path

import pandas as pd
import numpy as np

from .config import (
    COLUMN_SHORTNAMES,
    SKILL_COLUMNS,
    TEAM_ALIASES,
    TEAM_DISPLAY_NAMES,
    DEPT_NORMALIZE,
    ROLE_MAP,
    EQUIPMENT_SCORES,
    HOURS_MIDPOINTS,
    GIT_SCORES,
    DEPLOY_SCORES,
    COLLAB_SCORES,
)

logger = logging.getLogger(__name__)


# ── Utilidades de texto ────────────────────────────────────────────────────────

def _strip_accents(text: str) -> str:
    """Remueve tildes/diacríticos manteniendo la ñ como 'n'."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def _strip_emojis(text: str) -> str:
    """Remueve emojis y caracteres unicode no-ASCII visibles."""
    # Elimina emojis comunes y variation selectors
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & pictographs
        "\U0001F680-\U0001F6FF"  # Transport & map
        "\U0001F1E0-\U0001F1FF"  # Flags
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed characters
        "\U0000FE0F"              # Variation Selector-16
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text)


def normalize_text(text: str) -> str:
    """Pipeline de normalización de texto: strip → lower → sin emojis → sin tildes."""
    if not isinstance(text, str):
        return ""
    text = text.strip()
    text = text.lower()
    text = _strip_emojis(text)
    text = _strip_accents(text)
    text = re.sub(r"\s+", " ", text)  # Colapsar espacios múltiples
    return text.strip()


# ── Carga y renombramiento ─────────────────────────────────────────────────────

def load_and_rename(csv_path: Path) -> pd.DataFrame:
    """
    Carga el CSV crudo y renombra columnas a nombres cortos estandarizados.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si el número de columnas no coincide.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV no encontrado: {csv_path}")

    df = pd.read_csv(csv_path, encoding="utf-8")

    # Si tiene 21 columnas, omitir 'Marca temporal' y 'Dirección de correo electrónico'
    if len(df.columns) == 21:
        df = df.iloc[:, 2:]

    if len(df.columns) != len(COLUMN_SHORTNAMES):
        raise ValueError(
            f"Desajuste de columnas: CSV tiene {len(df.columns)}, "
            f"se esperaban {len(COLUMN_SHORTNAMES)}.\n"
            f"Columnas del CSV: {list(df.columns)}"
        )

    df.columns = COLUMN_SHORTNAMES
    logger.info(f"CSV cargado: {len(df)} filas, {len(df.columns)} columnas.")
    return df


# ── Normalización de Nombre de Equipo (LLAVE PRIMARIA) ─────────────────────────

def normalize_team_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza la columna 'team_name' usando el diccionario TEAM_ALIASES.
    Agrega 'team_name_display' con la versión legible.
    Reporta variantes no reconocidas.
    """
    df = df.copy()

    # Paso 1: Normalizar texto
    df["_team_raw"] = df["team_name"].copy()  # Guardar original para debugging
    df["team_name"] = df["team_name"].apply(normalize_text)

    # Paso 2: Aplicar alias
    unmatched = set()
    def _resolve_alias(name: str) -> str:
        if name in TEAM_ALIASES:
            return TEAM_ALIASES[name]
        # Intentar sin espacios trailing (ya debería estar limpio, pero por seguridad)
        name_stripped = name.strip()
        if name_stripped in TEAM_ALIASES:
            return TEAM_ALIASES[name_stripped]
        unmatched.add(name)
        return name  # Mantener como está si no hay alias

    df["team_name"] = df["team_name"].apply(_resolve_alias)

    if unmatched:
        logger.warning(
            f"Equipos sin alias definido (se mantienen tal cual): {unmatched}"
        )

    # Paso 3: Agregar nombre display
    df["team_name_display"] = df["team_name"].map(TEAM_DISPLAY_NAMES)
    # Fallback: title case si no hay nombre display definido
    mask_no_display = df["team_name_display"].isna()
    if mask_no_display.any():
        df.loc[mask_no_display, "team_name_display"] = (
            df.loc[mask_no_display, "team_name"].str.title()
        )

    logger.info(
        f"Equipos únicos post-normalización: "
        f"{df['team_name'].nunique()} — {sorted(df['team_name'].unique())}"
    )
    return df


# ── Normalización de Departamentos ─────────────────────────────────────────────

def normalize_departments(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de departamentos para consistencia geográfica."""
    df = df.copy()
    unmatched = set()

    def _norm(dept: str) -> str:
        key = normalize_text(dept)
        if key in DEPT_NORMALIZE:
            return DEPT_NORMALIZE[key]
        if pd.notna(dept) and dept != "":
            unmatched.add(dept)
        return dept

    df["residence_dept"] = df["residence_dept"].apply(_norm)
    if unmatched:
        logger.warning(f"Departamentos no mapeados: {unmatched}")
    return df


# ── Mapeo de Valores Categóricos a Scores Numéricos ───────────────────────────

def map_categorical_to_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte respuestas de texto a valores numéricos para análisis."""
    df = df.copy()

    # Hardware / Logística
    df["equipment_score"] = df["has_equipment"].map(EQUIPMENT_SCORES)

    # Dedicación horaria
    df["hours_midpoint"] = df["weekly_hours"].map(HOURS_MIDPOINTS)

    # Adopción de herramientas (Git)
    df["git_score"] = df["uses_git"].map(GIT_SCORES)

    # Experiencia en Producción (Deploy)
    df["deploy_score"] = df["has_deployed"].map(DEPLOY_SCORES)

    # Experiencia Colaborativa
    df["collab_score"] = df["collab_experience"].map(COLLAB_SCORES)

    # Normalización de Roles
    df["main_role"] = df["main_role"].apply(normalize_text).map(ROLE_MAP).fillna("other")

    return df


# ── Pipeline de Limpieza Completo ──────────────────────────────────────────────

def run_cleaning_pipeline(csv_path: Path) -> pd.DataFrame:
    """Ejecuta todas las fases de limpieza y retorna un DataFrame listo."""
    logger.info("=" * 60)
    logger.info("FASE 1: LIMPIEZA Y NORMALIZACIÓN")
    logger.info("=" * 60)

    df = load_and_rename(csv_path)
    df = normalize_team_names(df)
    df = normalize_departments(df)
    df = map_categorical_to_scores(df)

    # Limpieza final de NAs en skills (coaccionar a 0 si no hay respuesta)
    for col in SKILL_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    logger.info("✓ Limpieza completada con éxito.")
    return df
