from collections import Counter
import json
import csv
from datetime import datetime
from sqlmodel import Session, select
from src.database import engine
from src.models import Team, Protagonist, TeamAlias
from src.config import PATHS
from src.utils import normalize_text
import os
import glob

def get_attendance_data():
    """Escanea los CSV de asistencia en todo el espacio de trabajo y retorna un mapa de equipo -> sesiones asistidas."""
    # Buscar todos los CSVs de asistencia en la raíz del CI
    ci_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = glob.glob(f"{ci_root}/**/*.csv", recursive=True)
    
    attendance_map = {} # team_id -> set of sessions
    
    with Session(engine) as session:
        all_teams = session.exec(select(Team)).all()
        team_lookup = {}
        for t in all_teams:
            team_lookup[normalize_text(t.name)] = t.id
            for alias in t.aliases:
                team_lookup[normalize_text(alias.alias)] = t.id

        total_sessions = 0
        for f_path in files:
            # Filtrar por archivos que realmente sean de asistencia (mayúsculas o minúsculas)
            fname = os.path.basename(f_path).upper()
            if "ASISTENCIA" not in fname: continue
            
            # Evitar archivos de resumen que no tengan la columna 'Equipo'
            total_sessions += 1
            try:
                with open(f_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        raw_team = row.get("Equipo") or row.get("EQUIPO")
                        if raw_team:
                            norm_raw = normalize_text(raw_team)
                            team_id = team_lookup.get(norm_raw)
                            if team_id:
                                if team_id not in attendance_map: attendance_map[team_id] = set()
                                attendance_map[team_id].add(f_path)
            except Exception as e:
                pass # Ignorar errores de encoding o formato en archivos binarios accidentales
                
    print(f"  [✓] Procesadas {total_sessions} fuentes de asistencia detectadas.")
    return attendance_map, total_sessions

def get_mode(data: list) -> str:
    """Retorna el valor más frecuente de una lista."""
    if not data: return "N/A"
    return Counter(data).most_common(1)[0][0]

def calculate_trl(skill_sums: dict, member_count: int, has_deployed_bonus: bool, meth_readiness: dict = None) -> float:
    """Calcula el Technical Readiness Level (TRL) de 0 a 5 (v3.0)."""
    if member_count == 0: return 0.0

    # Pesos equilibrados: 55% Técnica, 45% Madurez/Compromiso
    weights = {
        "skill_programming": 0.15,
        "skill_infra_db": 0.15,
        "skill_ai": 0.15,
        "skill_design": 0.05,
        "english_level": 0.05,
        "meth_autonomy": 0.15,
        "meth_cohesion": 0.15,
        "meth_attendance": 0.15
    }

    score = 0
    # Técnicos
    for key in ["skill_programming", "skill_infra_db", "skill_ai", "skill_design", "english_level"]:
        avg = skill_sums[key] / member_count
        score += avg * weights[key]

    # Madurez
    if meth_readiness:
        score += meth_readiness.get("autonomy", 0) * weights["meth_autonomy"]
        score += meth_readiness.get("cohesion", 0) * weights["meth_cohesion"]
        score += meth_readiness.get("attendance", 0) * weights["meth_attendance"]

    # Bonus Deploy (+5% de la escala = 0.25 ptos)
    if has_deployed_bonus:
        score = min(5.0, score + 0.25)

    # Curva de Eficiencia de Escuadrón (Squad Efficiency Curve)
    # Penaliza la fricción logística o la fragilidad por tamaño de equipo.
    if member_count <= 2:
        efficiency_multiplier = 0.85  # Fragilidad (Bus factor alto)
    elif member_count <= 5:
        efficiency_multiplier = 1.00  # Zona de Oro (Productividad Óptima)
    elif member_count <= 7:
        efficiency_multiplier = 0.90  # Inicio de Fricción
    else:
        efficiency_multiplier = 0.75  # Entropía / Macrocefalia

    return round(score * efficiency_multiplier, 2)

def calculate_ori(infra_risk_score: float, collab_score: float, structural_vulnerability: float) -> dict:
    """
    Calcula el Operational Risk Index (ORI) v2.0.
    Escala 0-100 (donde 100 es riesgo máximo).
    """
    # Pesos ORI v2.0
    # 40% Riesgo Logístico (Hardware/Tiempo)
    # 30% Madurez Colaborativa (Git/Collab)
    # 30% Vulnerabilidad Estructural (Gaps de Roles)
    
    score = (infra_risk_score * 0.4) + (collab_score * 0.3) + (structural_vulnerability * 0.3)
    
    level = "LOW"
    if score >= 60: level = "CRITICAL"
    elif score >= 35: level = "MODERATE"
    
    return {
        "score": round(score, 1),
        "level": level,
        "components": {
            "logistic": round(infra_risk_score, 1),
            "collab": round(collab_score, 1),
            "structural": round(structural_vulnerability, 1)
        }
    }

def run_db_export():
    print("[*] Iniciando exportación consolidada (DB -> JSON)...")
    
    attendance_map, total_sessions = get_attendance_data()
    
    with Session(engine) as session:
        teams = session.exec(select(Team)).all()
        protagonists = session.exec(select(Protagonist)).all()
        
        # Macro Analytics
        macro = {
            "study_center_type": dict(Counter([p.study_center_type for p in protagonists if p.study_center_type])),
            "dept_distribution": dict(Counter([p.residence_dept for p in protagonists if p.residence_dept])),
            "git_usage": dict(Counter([p.uses_git for p in protagonists if p.uses_git])),
            "deploy_experience": dict(Counter([p.has_deployed for p in protagonists if p.has_deployed])),
            "team_cohesion": dict(Counter([p.collab_experience for p in protagonists if p.collab_experience])),
            "tech_curiosity": dict(Counter([p.curiosity_tech for p in protagonists if p.curiosity_tech])),
        }
        
        payload = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_teams": len(teams),
                "total_protagonists": len(protagonists),
                "total_sessions": total_sessions,
                "intelligence_model": "RAND/CI-Nicaragua v2.7"
            },
            "macro_analytics": macro,
            "executive_summary": {
                "critical_risk_teams": 0,
                "teams_missing_backend": 0,
                "high_trl_teams": 0
            },
            "teams": []
        }
        
        for team in teams:
            members = team.members
            n = len(members)
            
            if n == 0:
                payload["teams"].append({
                    "id": team.id,
                    "team_name": team.name,
                    "project_name": team.project_name,
                    "description": team.description,
                    "strategic_metrics": {"trl": 0, "ori": {"score": 0, "level": "N/A"}, "member_count": 0},
                    "no_response": True
                })
                continue
            
            # Agregaciones de Skills
            skill_sums = {
                "skill_programming": sum(m.skill_programming for m in members),
                "skill_infra_db": sum(m.skill_infra_db for m in members),
                "skill_design": sum(m.skill_design for m in members),
                "skill_ai": sum(m.skill_ai for m in members),
                "english_level": sum(m.english_level for m in members)
            }
            
            # Metodológicos / Madurez
            # Cohesión: HHI de departamentos (1 = todos mismo depto, 5 = todos distintos)
            depts = [m.residence_dept for m in members if m.residence_dept]
            dept_counts = Counter(depts)
            hhi = sum((count/n)**2 for count in dept_counts.values())
            cohesion_score = round((1 - hhi) * 5, 2) # 0 = centralizado, 5 = distribuido
            
            # Autonomía: Promedio de scoring interno (basado en git, deploy, learning)
            # (Simplificado para el ejemplo, asumiendo lógica previa de scoring)
            def _get_auto_score(m):
                s = 0
                if "Si" in (m.uses_git or ""): s += 2
                if "varias" in (m.has_deployed or ""): s += 2
                if "IA" in (m.learning_method or ""): s += 1
                return s
            autonomy_avg = round(sum(_get_auto_score(m) for m in members) / n, 2)
            
            # Asistencia
            team_sessions = len(attendance_map.get(team.id, []))
            attendance_score = round((team_sessions / total_sessions) * 5, 2) if total_sessions > 0 else 0
            
            # Strategic Metrics
            has_deployed_bonus = any("Si" in (m.has_deployed or "") for m in members)
            trl = calculate_trl(skill_sums, n, has_deployed_bonus, {"autonomy": autonomy_avg, "cohesion": cohesion_score, "attendance": attendance_score})
            
            # ORI Components
            # Logistic Risk: 100 - (promedio equipo de hardware + tiempo)
            def _get_log_risk(m):
                r = 0
                if "bajo" in (m.has_equipment or "").lower(): r += 30
                if "No tengo" in (m.has_equipment or "").lower(): r += 60
                if "Menos de 5" in (m.weekly_hours or ""): r += 40
                return min(100, r)
            infra_risk = sum(_get_log_risk(m) for m in members) / n
            
            # Collab Risk: 100 - (promedio git + collab experience)
            def _get_collab_risk(m):
                r = 100
                if "Si" in (m.uses_git or ""): r -= 40
                if "acostumbrado" in (m.collab_experience or "").lower(): r -= 40
                return max(0, r)
            collab_risk = sum(_get_collab_risk(m) for m in members) / n
            
            # Structural Vulnerability: Falta de roles clave
            roles = [m.main_role for m in members]
            gaps = []
            struct_vuln = 0
            if "backend" not in roles and "full_stack" not in roles: 
                gaps.append("Missing Backend/Architecture")
                struct_vuln += 50
                payload["executive_summary"]["teams_missing_backend"] += 1
            if "frontend" not in roles and "ux_ui" not in roles and "full_stack" not in roles:
                gaps.append("Missing Frontend/Design")
                struct_vuln += 30
            if "pm_leadership" not in roles and "marketing" not in roles:
                gaps.append("Missing Leadership/Business")
                struct_vuln += 20
            
            ori = calculate_ori(infra_risk, collab_risk, struct_vuln)
            
            # Dispersion (Minimos por skill)
            dispersion = {
                "skill_programming": {"floor": min(m.skill_programming for m in members)},
                "skill_infra_db": {"floor": min(m.skill_infra_db for m in members)},
                "skill_design": {"floor": min(m.skill_design for m in members)},
                "skill_ai": {"floor": min(m.skill_ai for m in members)},
                "english_level": {"floor": min(m.english_level for m in members)},
            }

            team_data = {
                "id": team.id,
                "team_name": team.name,
                "project_name": team.project_name,
                "description": team.description,
                "strategic_metrics": {
                    "trl": trl,
                    "ori": ori,
                    "role_gaps": gaps,
                    "member_count": n,
                    "has_senior_dev": any(m.skill_programming >= 4 or m.skill_infra_db >= 4 for m in members)
                },
                "qualitative_profile": {
                    "academic_origin": get_mode([m.study_center_type for m in members if m.study_center_type]),
                    "learning_style": get_mode([m.learning_method for m in members if m.learning_method]),
                    "territorial_index": "Centralizado" if hhi > 0.7 else "Distribuido",
                    "autonomy_score": autonomy_avg,
                    "cohesion_score": cohesion_score,
                    "attendance_score": attendance_score,
                    "all_institutions": list(set([m.study_center_type for m in members if m.study_center_type])),
                    "all_departments": list(set([m.residence_dept for m in members if m.residence_dept])),
                },
                "averages": {k: round(v/n, 2) for k, v in skill_sums.items()},
                "dispersion": dispersion,
                "role_distribution": dict(Counter(roles)),
                "members": [{
                    "id": m.id,
                    "full_name": m.full_name,
                    "email": m.email,
                    "role": m.main_role,
                    "dept": m.residence_dept,
                    "career": m.career_area,
                    "institution": m.study_center_type,
                    "skills": {
                        "programming": m.skill_programming,
                        "infra_db": m.skill_infra_db,
                        "design": m.skill_design,
                        "ai": m.skill_ai,
                        "english": m.english_level
                    },
                    "flags": {
                        "no_equipment": "No" in (m.has_equipment or ""),
                        "low_time": "Menos de 5" in (m.weekly_hours or "")
                    },
                    "qualitative": {
                        "learning_method": m.learning_method,
                        "has_deployed": m.has_deployed,
                        "uses_git": m.uses_git,
                        "main_obstacle": m.main_obstacle,
                        "collab_experience": m.collab_experience,
                        "curiosity_tech": m.curiosity_tech,
                        "weekly_hours": m.weekly_hours,
                        "autonomy_score": _get_auto_score(m),
                        "attendance_score": 0 # Placeholder
                    }
                } for m in members]
            }
            payload["teams"].append(team_data)
            
        # Guardar JSON final
        output_file = PATHS["llm_context_dir"].parent / "web_dashboard" / "dashboard_data.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            
        print(f"  [✓] JSON Consolidado generado en: {output_file}")

if __name__ == "__main__":
    run_db_export()
