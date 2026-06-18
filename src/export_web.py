import json
from datetime import datetime
from sqlmodel import Session, select
from src.database import engine
from src.models import Team, Protagonist
from src.config import PATHS
import os

def generate_web_json():
    print("[*] Generando JSON comprensivo para Dashboard Web...")
    
    with Session(engine) as session:
        teams = session.exec(select(Team)).all()
        protagonists = session.exec(select(Protagonist)).all()
        
        # Estructura global
        dashboard_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_teams": len(teams),
                "total_protagonists": len(protagonists)
            },
            "teams": []
        }
        
        for team in teams:
            members = team.members
            
            # Si el equipo no tiene miembros, lo inicializamos en 0
            if not members:
                dashboard_data["teams"].append({
                    "id": team.id,
                    "team_name": team.name,
                    "project_name": team.project_name,
                    "description": team.description,
                    "metrics": {
                        "member_count": 0,
                        "skill_averages": {},
                        "role_distribution": {}
                    },
                    "members": []
                })
                continue
                
            # Variables para métricas agregadas
            skill_sums = {
                "programming": 0, "infra_db": 0, "design": 0, "ai": 0, "english": 0
            }
            role_dist = {}
            
            member_list = []
            
            for m in members:
                # Contabilizar roles
                role = m.main_role or "unknown"
                role_dist[role] = role_dist.get(role, 0) + 1
                
                # Sumar skills
                skill_sums["programming"] += m.skill_programming
                skill_sums["infra_db"] += m.skill_infra_db
                skill_sums["design"] += m.skill_design
                skill_sums["ai"] += m.skill_ai
                skill_sums["english"] += m.english_level
                
                # Estructurar al miembro con todos los campos
                member_list.append({
                    "id": m.id,
                    "full_name": m.full_name,
                    "email": m.email,
                    "timestamp": m.timestamp,
                    "context": {
                        "residence_dept": m.residence_dept,
                        "study_center_type": m.study_center_type,
                        "career_area": m.career_area,
                        "main_role": m.main_role,
                        "has_equipment": m.has_equipment
                    },
                    "skills": {
                        "programming": m.skill_programming,
                        "infra_db": m.skill_infra_db,
                        "design": m.skill_design,
                        "ai": m.skill_ai,
                        "english": m.english_level
                    },
                    "qualitative": {
                        "learning_method": m.learning_method,
                        "has_deployed": m.has_deployed,
                        "uses_git": m.uses_git,
                        "main_obstacle": m.main_obstacle,
                        "collab_experience": m.collab_experience,
                        "curiosity_tech": m.curiosity_tech,
                        "weekly_hours": m.weekly_hours
                    }
                })
            
            n = len(members)
            
            # Construir objeto del equipo
            team_data = {
                "id": team.id,
                "team_name": team.name,
                "project_name": team.project_name,
                "description": team.description,
                "metrics": {
                    "member_count": n,
                    "skill_averages": {k: round(v/n, 2) for k, v in skill_sums.items()},
                    "role_distribution": role_dist
                },
                "members": member_list
            }
            
            dashboard_data["teams"].append(team_data)
            
        # Asegurar directorio y guardar
        output_dir = PATHS["llm_context_dir"].parent / "web_dashboard"
        os.makedirs(output_dir, exist_ok=True)
        output_file = output_dir / "dashboard_data.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
            
        print(f"  [✓] JSON para Dashboard generado en: {output_file}")

if __name__ == "__main__":
    generate_web_json()
