from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    project_name: str
    description: str

    # Relationships
    aliases: List["TeamAlias"] = Relationship(back_populates="team")
    members: List["Protagonist"] = Relationship(back_populates="team")

class TeamAlias(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    alias: str = Field(index=True, unique=True)
    team_id: int = Field(foreign_key="team.id")

    # Relationships
    team: Team = Relationship(back_populates="aliases")

class Protagonist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: str
    email: str = Field(index=True)
    full_name: str
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")
    
    # Context data
    residence_dept: Optional[str] = None
    study_center_type: Optional[str] = None
    career_area: Optional[str] = None
    main_role: Optional[str] = None
    has_equipment: Optional[str] = None
    
    # Skills (0-5)
    skill_programming: int = 0
    skill_infra_db: int = 0
    skill_design: int = 0
    skill_ai: int = 0
    english_level: int = 0
    
    # Qualitative / Behavioral
    learning_method: Optional[str] = None
    has_deployed: Optional[str] = None
    uses_git: Optional[str] = None
    main_obstacle: Optional[str] = None
    collab_experience: Optional[str] = None
    curiosity_tech: Optional[str] = None
    weekly_hours: Optional[str] = None

    # Relationships
    team: Optional[Team] = Relationship(back_populates="members")
