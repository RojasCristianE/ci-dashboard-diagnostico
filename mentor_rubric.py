#!/usr/bin/env python3
"""
mentor-rubric — Rúbrica de Observación del Mentor (40% del Audit Score)
=======================================================================
Programa de Incubación de Startups — Hackathon Nicaragua 2026
Centro de Innovación INATEC

Uso exclusivo: Cristian Rojas (Especialista de Formación Profesional).

Completa una rúbrica de 5 dimensiones (1-5) por equipo, basada en
lo observado durante mentorías 1-1, sesiones generales y Startup Day.

Ejecutar:
    .venv/bin/python mentor_rubric.py

Los resultados se guardan en data/mentor_observations.json.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from sqlmodel import Session, select

from src.database import engine
from src.models import Team

DATA_FILE = Path(__file__).resolve().parent / "data" / "mentor_observations.json"

DIMENSIONS = [
    {
        "key": "stack_coherence",
        "label": "Coherencia Stack↔Producto",
        "question": "¿El stack elegido tiene sentido para lo que quieren construir?",
        "guide": (
            "5: Stack óptimo (ej. Django para marketplace, Flutter para mobile).\n"
            "3: Stack aceptable pero con mejores alternativas.\n"
            "1: Stack inadecuado (ej. WordPress para app real-time).\n"
            "0: No tengo suficiente información para evaluar."
        ),
    },
    {
        "key": "arch_comprehension",
        "label": "Comprensión Arquitectónica",
        "question": "¿Saben explicar cómo fluyen los datos en su app?",
        "guide": (
            "5: Explican con claridad el flujo completo (cliente → API → DB → respuesta).\n"
            "3: Entienden partes pero no el panorama completo.\n"
            "1: No pueden explicar el flujo de datos o dependen del BaaS sin entenderlo.\n"
            "0: No he tenido oportunidad de evaluar esto."
        ),
    },
    {
        "key": "observable_progress",
        "label": "Progreso Observable",
        "question": "¿Avanzaron desde la primera mentoría? ¿Hay commits/demos?",
        "guide": (
            "5: Progreso consistente y visible (commits regulares, demos funcionales).\n"
            "3: Avance moderado, inconsistente.\n"
            "1: Estancados o retrocediendo. Misma demo que hace 2 meses.\n"
            "0: No tengo referencias anteriores para comparar."
        ),
    },
    {
        "key": "feedback_response",
        "label": "Respuesta a Feedback",
        "question": "¿Aplicaron las recomendaciones técnicas de sesiones anteriores?",
        "guide": (
            "5: Implementaron todas o casi todas las recomendaciones.\n"
            "3: Implementaron algunas, ignoraron otras.\n"
            "1: No aplicaron nada del feedback.\n"
            "0: Primera interacción o sin recomendaciones previas."
        ),
    },
    {
        "key": "engagement",
        "label": "Engagement / Participación",
        "question": "¿Asisten a sesiones, participan, son proactivos?",
        "guide": (
            "5: Asistencia perfecta, participan activamente, hacen preguntas.\n"
            "3: Asistencia irregular, participación pasiva.\n"
            "1: Ausentes o desconectados.\n"
            "0: Sin datos de asistencia."
        ),
    },
]


def bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"


def green(text: str) -> str:
    return f"\033[32m{text}\033[0m"


def yellow(text: str) -> str:
    return f"\033[33m{text}\033[0m"


def load_existing() -> dict:
    """Carga observaciones previas si existen."""
    if DATA_FILE.exists():
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"generated_at": None, "teams": {}}


def save_observations(data: dict):
    """Guarda observaciones a disco."""
    data["generated_at"] = datetime.now().isoformat()
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def score_team(team_name: str, project_name: str, existing: dict | None) -> dict:
    """Presenta las 5 dimensiones para un equipo y recolecta puntajes."""
    dim_scores = {}
    existing_scores = (existing or {}).get("dimensions", {})

    for dim in DIMENSIONS:
        key = dim["key"]
        prev = existing_scores.get(key)
        prev_str = f" [previo: {prev}]" if prev is not None else ""

        print(f"\n  {bold(dim['label'])}{prev_str}")
        print(f"  {dim['question']}")
        print(f"  {yellow(dim['guide'])}")

        while True:
            raw = input(f"  Puntaje (0-5, enter para mantener previo): ").strip()
            if not raw and prev is not None:
                dim_scores[key] = prev
                break
            if not raw:
                print(f"  {yellow('Sin puntaje previo — ingresá un valor o 0 para saltar.')}")
                continue
            try:
                val = int(raw)
                if 0 <= val <= 5:
                    dim_scores[key] = val
                    break
                print(f"  {yellow('Ingresá un número entre 0 y 5.')}")
            except ValueError:
                print(f"  {yellow('Ingresá un número válido.')}")

    notes = input(f"\n  Notas adicionales (opcional): ").strip()

    score = sum(dim_scores.values())
    max_score = len(DIMENSIONS) * 5
    normalized = round((score / max_score) * 100, 1) if max_score > 0 else 0

    return {
        "team_name": team_name,
        "project_name": project_name,
        "dimensions": dim_scores,
        "raw_score": score,
        "max_score": max_score,
        "normalized_score": normalized,
        "notes": notes or None,
        "scored_at": datetime.now().isoformat(),
    }


def main():
    print(f"\n{bold('🧠 RÚBRICA DE OBSERVACIÓN DEL MENTOR')}")
    print("Centro de Innovación — Hackathon Nicaragua 2026")
    print(f"Cristian Rojas — Especialista de Formación Profesional\n")

    # Cargar equipos del SQLite
    with Session(engine) as session:
        teams = session.exec(select(Team).order_by(Team.name)).all()

    if not teams:
        print("No se encontraron equipos en la base de datos.")
        return 1

    # Cargar observaciones previas
    data = load_existing()
    prev_teams = data.get("teams", {})

    completed = sum(1 for t in prev_teams.values()
                    if t.get("dimensions") and len(t["dimensions"]) == len(DIMENSIONS))
    print(f"Equipos en el programa: {len(teams)}")
    print(f"Completados: {green(str(completed))}/{len(teams)}")
    print(f"Pendientes: {yellow(str(len(teams) - completed))}\n")

    # Listar equipos
    print(f"{bold('EQUIPOS')} (completados con ✅)")
    for t in teams:
        tid = str(t.id)
        status = "✅" if tid in prev_teams and prev_teams[tid].get("dimensions") else "⬜"
        print(f"  {status} {t.id:2d}. {t.name:<25s} {t.project_name[:50]}")

    print(f"\n{bold('COMANDOS')}")
    print("  <número>  — Evaluar ese equipo")
    print("  all       — Evaluar todos los pendientes en secuencia")
    print("  done      — Guardar y salir")
    print("  reset <n> — Borrar evaluación del equipo n y re-evaluarlo")

    while True:
        cmd = input(f"\n{bold('>')} ").strip()

        if cmd.lower() in ("done", "q", "quit", "exit"):
            save_observations(data)
            completed = sum(1 for t in prev_teams.values()
                            if t.get("dimensions") and len(t["dimensions"]) == len(DIMENSIONS))
            print(f"\n{green(f'✅ {completed}/{len(teams)} equipos evaluados.')}")
            print(f"Datos guardados en: {DATA_FILE}")
            break

        if cmd.lower().startswith("reset "):
            try:
                tid = int(cmd.split()[1])
                if str(tid) in data["teams"]:
                    name = data["teams"][str(tid)]["team_name"]
                    del data["teams"][str(tid)]
                    print(f"  {yellow(f'↺ Evaluación de \"{name}\" borrada.')}")
                else:
                    print(f"  {yellow('Equipo no tiene evaluación previa.')}")
            except (ValueError, IndexError):
                print(f"  {yellow('Uso: reset <número>')}")
            continue

        if cmd.lower() == "all":
            target_teams = [t for t in teams if str(t.id) not in data["teams"] or
                            not data["teams"][str(t.id)].get("dimensions")]
            if not target_teams:
                print(f"  {green('Todos los equipos ya están evaluados.')}")
                continue
            print(f"\n  Evaluando {len(target_teams)} equipos pendientes...\n")
        else:
            try:
                tid = int(cmd)
                team = next((t for t in teams if t.id == tid), None)
                if not team:
                    print(f"  {yellow(f'Equipo {tid} no encontrado.')}")
                    continue
                target_teams = [team]
            except ValueError:
                print(f"  {yellow('Comando no reconocido. Usá un número, \"all\", \"done\", o \"reset\".')}")
                continue

        for team in target_teams:
            tid = str(team.id)
            existing = data["teams"].get(tid)

            print(f"\n  {'─' * 55}")
            print(f"  {bold(f'Equipo #{team.id}: {team.name}')}")
            print(f"  Proyecto: {team.project_name}")
            print(f"  {'─' * 55}")

            data["teams"][tid] = score_team(team.name, team.project_name, existing)
            save_observations(data)
            ns = data["teams"][tid]["normalized_score"]
            print(f"\n  {green(f'✅ {team.name}: {ns}/100')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
