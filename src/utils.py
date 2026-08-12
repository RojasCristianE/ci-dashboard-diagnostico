import unicodedata
import re

def normalize_text(text: str) -> str:
    """Normaliza texto: lowercase, quita tildes, quita caracteres especiales y espacios extra."""
    if not text:
        return ""
    # Lowercase y strip
    text = text.lower().strip()
    # Quitar tildes
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    # Quitar caracteres especiales excepto espacios y alfanuméricos
    text = re.sub(r"[^a-z0-9\s]", "", text)
    # Colapsar espacios múltiples
    text = re.sub(r"\s+", " ", text)
    return text.strip()
