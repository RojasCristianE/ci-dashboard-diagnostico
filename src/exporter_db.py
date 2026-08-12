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
    ci_root = "/home/cristian/Documentos/UNI/CI"
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

    effective_score = score * efficiency_multiplier

    return round(effective_score, 2)

def calculate_ori(
    equipment_data: list,
    hours_data: list,
    member_count: int,
    trl_score: float,
    git_data: list | None = None,
    deploy_data: list | None = None,
    collab_data: list | None = None,
) -> dict:
    """Calcula el Operational Risk Index (ORI) v2.0.

    Componentes:
      - Riesgo Logístico (40%): Hardware + Dedicación de tiempo.
      - Riesgo de Madurez Colaborativa (30%): Git + Deploy + Colaboración.
      - Vulnerabilidad Estructural (30%): Tamaño de equipo + TRL bajo.

    Changelog v2.0:
      - Incorpora git_data, deploy_data y collab_data para cerrar el punto
        ciego donde un equipo sin prácticas de colaboración podía obtener
        ORI=0 solo por tener laptops.
    """
    total = len(equipment_data)
    if total == 0:
        return {"score": 100, "level": "CRITICAL", "components": {"logistic": 100, "collab": 100, "structural": 100}}

    # ── 1. Riesgo Logístico (Hardware + Tiempo) — 40% ─────────────────────
    no_equipment_count = sum(
        1 for e in equipment_data
        if "teléfono" in e or "dependo de laboratorios" in e
    )
    infra_risk = (no_equipment_count / total) * 100

    low_time_count = sum(1 for h in hours_data if "Menos de 5" in h)
    time_risk = (low_time_count / total) * 100

    logistic_score = 0.6 * infra_risk + 0.4 * time_risk  # 0-100

    # ── 2. Riesgo de Madurez Colaborativa — 30% ──────────────────────────
    collab_risk = 0.0
    if git_data:
        # % del equipo que NO usa Git regularmente
        no_git = sum(
            1 for g in git_data
            if not any(x in (g or "").lower() for x in ["siempre", "todos"])
        )
        collab_risk += (no_git / total) * 40  # 40% del componente

    if deploy_data:
        # % del equipo que NUNCA ha desplegado
        no_deploy = sum(
            1 for d in deploy_data
            if any(x in (d or "").lower() for x in ["no", "nunca", "local", "prototipo"])
        )
        collab_risk += (no_deploy / total) * 35  # 35% del componente

    if collab_data:
        # % del equipo sin experiencia colaborativa multidisciplinaria
        no_collab = sum(
            1 for c in collab_data
            if any(x in (c or "").lower() for x in ["no, nunca", "muy poco"])
        )
        collab_risk += (no_collab / total) * 25  # 25% del componente

    # Si no se proporcionaron datos de colaboración, asignar riesgo neutro (50)
    if git_data is None and deploy_data is None and collab_data is None:
        collab_risk = 50.0

    # ── 3. Vulnerabilidad Estructural — 30% ──────────────────────────────
    structural_score = 0.0

    # Factor de Soledad
    if member_count == 1:
        structural_score += 70
    elif member_count == 2:
        structural_score += 30

    # Factor de Inviabilidad Técnica
    if trl_score < 1.5:
        structural_score += 30
    elif trl_score < 2.25:
        structural_score += 15

    structural_score = min(100.0, structural_score)

    # ── Composición Final ─────────────────────────────────────────────────
    final_score = min(
        100.0,
        round(0.40 * logistic_score + 0.30 * collab_risk + 0.30 * structural_score, 1),
    )

    level = "LOW"
    if final_score > 60:
        level = "CRITICAL"
    elif final_score > 35:
        level = "MODERATE"

    return {
        "score": final_score,
        "level": level,
        "components": {
            "logistic": round(logistic_score, 1),
            "collab": round(collab_risk, 1),
            "structural": round(structural_score, 1),
        },
    }

def detect_role_gaps(role_dist: dict) -> list:
    """Identifica vacíos estructurales en la formación del equipo."""
    gaps = []
    if not role_dist.get("backend") and not role_dist.get("cto") and not role_dist.get("full_stack"):
        gaps.append("Missing Backend/Architecture")
    if not role_dist.get("frontend") and not role_dist.get("ux_ui") and not role_dist.get("full_stack"):
        gaps.append("Missing Frontend/Design")
    if not role_dist.get("pm_leadership") and not role_dist.get("marketing"):
        gaps.append("Missing Leadership/Business")
    return gaps

def calculate_macro_analytics(protagonists: list) -> dict:
    """Calcula indicadores globales del ecosistema."""
    stats = {
        "study_center_type": {},
        "dept_distribution": {},
        "git_usage": {},
        "deploy_experience": {},
        "team_cohesion": {},
        "tech_curiosity": {}
    }
    
    for p in protagonists:
        # Origen Académico
        sc = p.study_center_type or "Unknown"
        stats["study_center_type"][sc] = stats["study_center_type"].get(sc, 0) + 1
        
        # Departamentos
        dept = p.residence_dept or "Unknown"
        stats["dept_distribution"][dept] = stats["dept_distribution"].get(dept, 0) + 1
        
        # Git
        git = p.uses_git or "No Data"
        stats["git_usage"][git] = stats["git_usage"].get(git, 0) + 1
        
        # Deploys
        dep = p.has_deployed or "No Data"
        stats["deploy_experience"][dep] = stats["deploy_experience"].get(dep, 0) + 1
        
        # Cohesión
        coh = p.collab_experience or "No Data"
        stats["team_cohesion"][coh] = stats["team_cohesion"].get(coh, 0) + 1
        
        # Tendencias
        cur = p.curiosity_tech or "Other"
        stats["tech_curiosity"][cur] = stats["tech_curiosity"].get(cur, 0) + 1
        
    return stats

def run_export_db():
    print("[*] Generando Telemetría Think Tank para Dashboard Web...")
    
    attendance_data, total_sess = get_attendance_data()
    
    with Session(engine) as session:
        teams = session.exec(select(Team)).all()
        protagonists = session.exec(select(Protagonist)).all()
        
        dashboard_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_teams": len(teams),
                "total_protagonists": len(protagonists),
                "total_sessions": total_sess,
                "intelligence_model": "RAND/CI-Nicaragua v2.7"
            },
            "macro_analytics": calculate_macro_analytics(protagonists),
            "executive_summary": {
                "critical_risk_teams": 0,
                "teams_missing_backend": 0,
                "high_trl_teams": 0
            },
            "teams": []
        }
        
        for team in teams:
            members = team.members
            # Calcular asistencia del equipo
            attended_sessions = len(attendance_data.get(team.id, set()))
            attendance_score = round((attended_sessions / total_sess) * 5, 2) if total_sess > 0 else 0

            if not members:
                # Incluir equipos sin miembros para visibilidad en el dashboard
                dashboard_data["teams"].append({
                    "id": team.id,
                    "team_name": team.name,
                    "project_name": team.project_name,
                    "description": team.description,
                    "strategic_metrics": {
                        "trl": 0,
                        "ori": {"score": 0, "level": "NO_DATA"},
                        "role_gaps": ["Missing All Roles / Pending Form"],
                        "member_count": 0,
                        "has_senior_dev": False
                    },
                    "qualitative_profile": {
                        "academic_origin": "N/A",
                        "learning_style": "N/A",
                        "territorial_index": "N/A",
                        "attendance_score": attendance_score,
                        "all_institutions": [],
                        "all_departments": []
                    },
                    "averages": {"skill_programming": 0, "skill_infra_db": 0, "skill_design": 0, "skill_ai": 0, "english_level": 0},
                    "role_distribution": {},
                    "members": []
                })
                continue
                
            skill_sums = {"skill_programming": 0, "skill_infra_db": 0, "skill_design": 0, "skill_ai": 0, "english_level": 0}
            skill_vals = {k: [] for k in skill_sums}  # Para dispersión (floor, std)
            role_dist = {}
            equipment_data = []
            hours_data = []
            git_data = []      # ORI v2.0: Madurez colaborativa
            deploy_data = []   # ORI v2.0: Experiencia de deploy
            collab_data = []   # ORI v2.0: Colaboración multidisciplinaria
            
            # Acumuladores cualitativos para el equipo
            academic_types = set()
            learning_styles = []
            depts = set()
            
            # Puntuaciones de madurez (promedios)
            total_autonomy_score = 0
            dept_counts = {}
            
            has_deployed_bonus = False
            member_list = []
            
            for m in members:
                role = m.main_role or "unknown"
                role_dist[role] = role_dist.get(role, 0) + 1
                
                # --- Cálculo de Autonomía Individual (IIO: 0-5) ---
                # Masa Crítica Técnica (40%): Promedio de skills core
                mct_norm = ((m.skill_programming or 0) + (m.skill_infra_db or 0)) / 10.0
                
                # Adopción de Versionamiento (30%): Mapeo de confianza
                git = (m.uses_git or "").lower()
                av = 1.0 if any(x in git for x in ["siempre", "todos"]) else 0.5 if any(x in git for x in ["basico", "veces"]) else 0.0
                
                # Experiencia de Producción (30%): Capacidad de entrega
                dep = (m.has_deployed or "").lower()
                ep = 1.0 if "varias veces" in dep else 0.7 if "al menos una vez" in dep else 0.1 if any(x in dep for x in ["no", "nunca", "local"]) else 0.0
                
                # Fórmula IIO escalada a 5
                m_autonomy = round(5.0 * (0.40 * mct_norm + 0.30 * av + 0.30 * ep), 2)
                total_autonomy_score += m_autonomy

                # Otros datos cualitativos
                if m.study_center_type: academic_types.add(m.study_center_type)
                if m_autonomy >= 3: learning_styles.append("Autosuficiente (Digital/IA)")
                else: learning_styles.append("Tradicional (Académico)")
                
                if m.residence_dept:
                    depts.add(m.residence_dept)
                    dept_counts[m.residence_dept] = dept_counts.get(m.residence_dept, 0) + 1
                
                for sk in skill_sums:
                    val = getattr(m, sk, 0) if sk != "english_level" else m.english_level
                    skill_sums[sk] += val
                    skill_vals[sk].append(val)
                
                if m.has_deployed and ("varias veces" in m.has_deployed or "al menos una vez" in m.has_deployed):
                    has_deployed_bonus = True
                    
                if m.has_equipment: equipment_data.append(m.has_equipment)
                if m.weekly_hours: hours_data.append(m.weekly_hours)
                if m.uses_git: git_data.append(m.uses_git)
                if m.has_deployed: deploy_data.append(m.has_deployed)
                if m.collab_experience: collab_data.append(m.collab_experience)
                
                member_list.append({
                    "id": m.id,
                    "full_name": m.full_name,
                    "email": m.email,
                    "role": m.main_role,
                    "dept": m.residence_dept,
                    "career": m.career_area,
                    "institution": m.study_center_type, # Expandir institución individual
                    "skills": {
                        "programming": m.skill_programming,
                        "infra_db": m.skill_infra_db,
                        "design": m.skill_design,
                        "ai": m.skill_ai,
                        "english": m.english_level
                    },
                    "flags": {
                        "no_equipment": "teléfono" in (m.has_equipment or "") or "laboratorios" in (m.has_equipment or ""),
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
                        "autonomy_score": m_autonomy,
                        "attendance_score": attendance_score # Misma asistencia para todos los del equipo
                    }
                })
            
            n = len(members)
            
            # --- Strategic Metrics ---
            avg_autonomy = round(total_autonomy_score / n, 2)
            
            # Cálculo de Cohesión Territorial Aislada (HHI)
            sum_sq = sum((count / n) ** 2 for count in dept_counts.values()) if n > 0 else 0
            avg_cohesion = round(5.0 * sum_sq, 2)
            
            is_centralized = len(depts) == 1
            
            meth_readiness = {"autonomy": avg_autonomy, "cohesion": avg_cohesion, "attendance": attendance_score}
            trl = calculate_trl(skill_sums, n, has_deployed_bonus, meth_readiness)
            ori = calculate_ori(
                equipment_data, hours_data, n, trl,
                git_data=git_data,
                deploy_data=deploy_data,
                collab_data=collab_data,
            )
            role_gaps = detect_role_gaps(role_dist)
            
            # --- Qualitative Team Profile ---
            territorial_index = f"Centralizado ({list(depts)[0]})" if is_centralized else "Distribuido"
            
            qualitative_profile = {
                "academic_origin": get_mode(list(academic_types)),
                "learning_style": get_mode(learning_styles),
                "territorial_index": territorial_index,
                "autonomy_score": avg_autonomy,
                "cohesion_score": avg_cohesion,
                "attendance_score": attendance_score,
                "all_institutions": list(academic_types),
                "all_departments": list(depts)
            }
            
            # Update Executive Summary
            if ori["level"] == "CRITICAL": dashboard_data["executive_summary"]["critical_risk_teams"] += 1
            if "Missing Backend/Architecture" in role_gaps: dashboard_data["executive_summary"]["teams_missing_backend"] += 1
            if trl >= 65: dashboard_data["executive_summary"]["high_trl_teams"] += 1
            
            team_data = {
                "id": team.id,
                "team_name": team.name,
                "project_name": team.project_name,
                "description": team.description,
                "strategic_metrics": {
                    "trl": trl,
                    "ori": ori,
                    "role_gaps": role_gaps,
                    "member_count": n,
                    "has_senior_dev": has_deployed_bonus
                },
                "qualitative_profile": qualitative_profile,
                "averages": {k: round(v/n, 2) for k, v in skill_sums.items()},
                "dispersion": {
                    k: {
                        "floor": min(vals) if vals else 0,
                        "std": round(float((sum((x - sum(vals)/len(vals))**2 for x in vals) / len(vals))**0.5), 2) if len(vals) > 1 else 0.0,
                    }
                    for k, vals in skill_vals.items()
                },
                "role_distribution": role_dist,
                "members": member_list
            }
            
            dashboard_data["teams"].append(team_data)
            
        # Asegurar directorio y guardar
        output_dir = PATHS["llm_context_dir"].parent / "web_dashboard"
        os.makedirs(output_dir, exist_ok=True)
        output_file = output_dir / "dashboard_data.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
            
        print(f"  [✓] JSON Táctico generado en: {output_file}")

if __name__ == "__main__":
    run_export_db()
