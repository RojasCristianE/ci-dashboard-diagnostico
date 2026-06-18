import csv
from sqlmodel import Session, select
from .database import engine, init_db
from .models import Team, TeamAlias, Protagonist
from .utils import normalize_text
from .config import BASE_DIR, DEPT_NORMALIZE, CAREER_MAP, ROLE_MAP
import os

# Mapeo manual de variantes difíciles o fusiones estratégicas
MANUAL_MAPPING = {
    "azura": "mas Ctrl",
    "azura/ctrl": "mas Ctrl",
    "ctrl": "mas Ctrl",
    "mecani asavexi": "Asavexi",
    "mecani": "Asavexi",
    "asavexi": "Asavexi",
    "va d viaje anteriormente nikaroute": "Los Mulukukeños",
    "va daro viaje anteriormente nikaroute": "Los Mulukukeños",
    "va de viaje anteriormente nikaroute": "Los Mulukukeños",
    "los mulukukenos": "Los Mulukukeños",
    "los mulukuquenos": "Los Mulukukeños",
    "va d viaje": "Los Mulukukeños",
    "nicabite fritinder": "Frintinder",
    "nicabite": "Frintinder",
    "fritinder": "Frintinder",
    "nicabuy": "URADEV",
    "uradev": "URADEV",
    "app de comercio online": "NubePleys",
    "rommy asistente de salud virtual": "Delta Innovation's",
    "rommy asistente de salud virtual delta innovations": "Delta Innovation's",
    "delta innovation": "Delta Innovation's",
    "delta innovations": "Delta Innovation's",
    "finny": "Phinn",
    "neofluid 3d": "Power Rangers",
    "neofluit 3d": "Power Rangers",
    "powers rangers": "Power Rangers",
    "nica plus": "Nicaplus",
    "nereon": "Sui",
    "los meros meros": "Nacatamal",
    "chontales noxus": "Chontal Noxus",
    "hackabros": "URADEV",
    "los de la isla": "IslaVoz",
    "kachiiing": "Chontal Noxus",
}

def ingest_teams(session: Session, perfiles_path: str):
    """Puebla la tabla de equipos desde el archivo oficial."""
    print(f"[*] Ingestando equipos oficiales desde {perfiles_path}...")
    with open(perfiles_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            team_name = row["Equipo"].strip()
            team = Team(
                name=team_name,
                project_name=row["Proyecto"].strip(),
                description=row["Descripción del Proyecto"].strip()
            )
            session.add(team)
            session.commit()
            session.refresh(team)
            
            # Crear alias inicial con el nombre normalizado
            alias_norm = normalize_text(team_name)
            alias = TeamAlias(alias=alias_norm, team_id=team.id)
            session.add(alias)
            # print(f"  - Creado alias oficial: {alias_norm} -> {team_name}")
        session.commit()

def setup_aliases(session: Session):
    """Registra los mapeos manuales en la base de datos."""
    print("[*] Configurando alias manuales...")
    for alias_text, target_team_name in MANUAL_MAPPING.items():
        # Buscar el equipo oficial
        statement = select(Team).where(Team.name == target_team_name)
        team = session.exec(statement).first()
        if team:
            norm_alias = normalize_text(alias_text)
            # Evitar duplicados si el alias ya existe
            existing = session.exec(select(TeamAlias).where(TeamAlias.alias == norm_alias)).first()
            if not existing:
                # print(f"  - Registrando alias manual: {norm_alias} -> {target_team_name}")
                session.add(TeamAlias(alias=norm_alias, team_id=team.id))
            else:
                # print(f"  - Alias {norm_alias} ya existe para {existing.team.name}")
                pass
        else:
            print(f"  [!] ERROR: Equipo oficial '{target_team_name}' no encontrado para alias '{alias_text}'")
    session.commit()

def ingest_protagonists(session: Session, responses_path: str):
    """Procesa las respuestas y crea los registros de protagonistas."""
    print(f"[*] Ingestando protagonistas desde {responses_path}...")
    with open(responses_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        
        count = 0
        for row in reader:
            raw_team_name = row[3]
            norm_team_name = normalize_text(raw_team_name)
            
            # Resolver equipo por alias
            statement = select(TeamAlias).where(TeamAlias.alias == norm_team_name)
            alias_record = session.exec(statement).first()
            
            team_id = alias_record.team_id if alias_record else None
            
            if not team_id:
                print(f"  [!] ADVERTENCIA: No se pudo mapear el equipo '{raw_team_name}' (norm: {norm_team_name})")

            # Normalizar Departamento
            raw_dept = row[4]
            norm_dept_key = normalize_text(raw_dept)
            final_dept = DEPT_NORMALIZE.get(norm_dept_key, raw_dept.strip())

            # Normalizar Carrera
            raw_career = row[6]
            norm_career_key = normalize_text(raw_career)
            final_career = CAREER_MAP.get(norm_career_key, raw_career.strip())

            # Normalizar Rol
            raw_role = row[7]
            norm_role_key = normalize_text(raw_role)
            final_role = ROLE_MAP.get(norm_role_key, raw_role.strip())

            protagonist = Protagonist(
                timestamp=row[0],
                email=row[1],
                full_name=row[2],
                team_id=team_id,
                residence_dept=final_dept,
                study_center_type=row[5],
                career_area=final_career,
                main_role=final_role,
                has_equipment=row[8],
                skill_programming=int(row[9]) if row[9].isdigit() else 0,
                skill_infra_db=int(row[10]) if row[10].isdigit() else 0,
                skill_design=int(row[11]) if row[11].isdigit() else 0,
                skill_ai=int(row[12]) if row[12].isdigit() else 0,
                english_level=int(row[13]) if row[13].isdigit() else 0,
                learning_method=row[14],
                has_deployed=row[15],
                uses_git=row[16],
                main_obstacle=row[17],
                collab_experience=row[18],
                curiosity_tech=row[19],
                weekly_hours=row[20]
            )
            session.add(protagonist)
            count += 1
        
        session.commit()
        print(f"  [✓] {count} protagonistas procesados.")

def run_ingestion():
    init_db()
    
    # Rutas relativas a la raíz del repositorio
    root_dir = BASE_DIR
    perfiles_csv = root_dir / "data" / "perfiles.csv"
    responses_csv = root_dir / "data" / "respuestas.csv"
    
    with Session(engine) as session:
        # Limpiar datos previos para asegurar idempotencia en el desarrollo
        from sqlmodel import delete
        session.exec(delete(Protagonist))
        session.exec(delete(TeamAlias))
        session.exec(delete(Team))
        session.commit()
        
        ingest_teams(session, perfiles_csv)
        setup_aliases(session)
        ingest_protagonists(session, responses_csv)

if __name__ == "__main__":
    run_ingestion()
