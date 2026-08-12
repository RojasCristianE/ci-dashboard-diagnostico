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
    """
    Normaliza 'residence_dept' a nombres de departamento canónicos.
    """
    df = df.copy()
    df["_dept_raw"] = df["residence_dept"].copy()
    normalized = df["residence_dept"].apply(normalize_text)

    unmatched_depts = set()

    def _resolve_dept(name: str) -> str:
        if name in DEPT_NORMALIZE:
            return DEPT_NORMALIZE[name]
        unmatched_depts.add(name)
        return name.title()  # Fallback a title case

    df["residence_dept"] = normalized.apply(_resolve_dept)

    if unmatched_depts:
        logger.warning(
            f"Departamentos sin mapeo (fallback a title case): {unmatched_depts}"
        )

    logger.info(
        f"Departamentos únicos: {sorted(df['residence_dept'].unique())}"
    )
    return df


# ── Normalización de Roles ─────────────────────────────────────────────────────

def normalize_roles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza 'main_role' a categorías limpias usando ROLE_MAP.
    Maneja roles custom con match parcial.
    """
    df = df.copy()
    df["_role_raw"] = df["main_role"].copy()
    normalized = df["main_role"].apply(normalize_text)

    unmatched_roles = set()

    def clean_role_text(s: str) -> str:
        s = s.lower()
        s = re.sub(r'[^a-z0-9]', '', s)
        return s

    def _resolve_role(name: str) -> str:
        clean_name = clean_role_text(name)
        
        # Match exacto en versión limpia
        for key, value in ROLE_MAP.items():
            if clean_role_text(key) == clean_name:
                return value
                
        # Match parcial en versión limpia
        for key, value in ROLE_MAP.items():
            clean_key = clean_role_text(key)
            if clean_key in clean_name or clean_name in clean_key:
                return value
                
        unmatched_roles.add(name)
        return "other"

    df["main_role"] = normalized.apply(_resolve_role)

    if unmatched_roles:
        logger.warning(f"Roles sin mapeo (asignados a 'other'): {unmatched_roles}")

    logger.info(f"Roles únicos: {sorted(df['main_role'].unique())}")
    return df


# ── Codificación de variables ordinales ────────────────────────────────────────

def encode_ordinals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte columnas categóricas a escalas numéricas para cuantificación.
    Agrega columnas _score para cada variable ordinal.
    """
    df = df.copy()

    ordinal_maps = {
        "has_equipment": ("equipment_score", EQUIPMENT_SCORES),
        "weekly_hours": ("hours_midpoint", HOURS_MIDPOINTS),
        "uses_git": ("git_score", GIT_SCORES),
        "has_deployed": ("deploy_score", DEPLOY_SCORES),
        "collab_experience": ("collab_score", COLLAB_SCORES),
    }

    for source_col, (target_col, mapping) in ordinal_maps.items():
        normalized = df[source_col].apply(normalize_text)
        mapped = normalized.map(mapping)

        # Reportar valores no mapeados
        unmapped_mask = mapped.isna() & df[source_col].notna()
        if unmapped_mask.any():
            unmapped_vals = df.loc[unmapped_mask, source_col].unique()
            logger.warning(
                f"Valores sin mapeo en '{source_col}' → NaN: {unmapped_vals}"
            )

        df[target_col] = mapped
        logger.info(
            f"Codificado '{source_col}' → '{target_col}': "
            f"{mapped.notna().sum()}/{len(mapped)} mapeados."
        )

    return df


# ── Validación de rangos numéricos ─────────────────────────────────────────────

def validate_numeric_ranges(df: pd.DataFrame) -> pd.DataFrame:
    """
    Verifica que las columnas de skills estén en rango 0-5.
    Clampea outliers con advertencia.
    """
    df = df.copy()

    for col in SKILL_COLUMNS:
        # Asegurar tipo numérico
        df[col] = pd.to_numeric(df[col], errors="coerce")

        # Detectar NaN (datos faltantes)
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            logger.warning(f"'{col}': {nan_count} valores NaN. Se rellenan con 0.")
            df[col] = df[col].fillna(0)

        # Detectar outliers
        out_of_range = ((df[col] < 0) | (df[col] > 5)).sum()
        if out_of_range > 0:
            logger.warning(
                f"'{col}': {out_of_range} valores fuera de rango [0,5]. Clampeando."
            )
            df[col] = df[col].clip(0, 5)

        df[col] = df[col].astype(int)

    return df


# ── Pipeline completo de limpieza ──────────────────────────────────────────────

def run_cleaning_pipeline(csv_path: Path) -> pd.DataFrame:
    """
    Orquesta todas las funciones de limpieza en secuencia.

    Args:
        csv_path: Ruta al archivo CSV crudo.

    Returns:
        DataFrame limpio y normalizado, listo para feature engineering.
    """
    logger.info("=" * 60)
    logger.info("FASE 1: LIMPIEZA Y NORMALIZACIÓN")
    logger.info("=" * 60)

    # 1. Cargar y renombrar
    df = load_and_rename(csv_path)

    # 2. Normalizar nombre de equipo (llave primaria)
    df = normalize_team_names(df)

    # 3. Normalizar departamentos
    df = normalize_departments(df)

    # 4. Normalizar roles
    df = normalize_roles(df)

    # 5. Codificar variables ordinales
    df = encode_ordinals(df)

    # 6. Validar rangos numéricos
    df = validate_numeric_ranges(df)

    # 7. Limpiar nombre completo (strip de espacios)
    df["full_name"] = df["full_name"].str.strip().str.strip('"')

    logger.info(f"\n✓ Limpieza completa: {len(df)} filas, {len(df.columns)} columnas.")
    logger.info(f"  Equipos: {df['team_name'].nunique()}")
    logger.info(f"  Departamentos: {df['residence_dept'].nunique()}")
    logger.info(f"  Roles: {sorted(df['main_role'].unique())}")

    return df
