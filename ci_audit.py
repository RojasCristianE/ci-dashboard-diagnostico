#!/usr/bin/env python3
"""
ci-audit — CI Nicaragua: Audit de Madurez Técnica para Startups
================================================================
Programa de Incubación de Startups de Base Tecnológica
Hackathon Nicaragua 2026 — Centro de Innovación INATEC

Ejecutar en el directorio raíz del proyecto de la startup:

    python ci-audit.py

También disponible vía uvx (desde GitHub):

    uvx --from git+https://github.com/RojasCristianE/ci-dashboard-diagnostico ci-audit

Zero dependencias. Solo necesita Python 3.8+ y git (opcional).
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib import request
from urllib.error import URLError

# ── Configuración ──────────────────────────────────────────────────────────────
# CAMBIAR ESTA URL por la del deployment de Google Apps Script
# (Se obtiene al hacer Deploy > Web App en el editor de Apps Script)
# Dejar vacío para modo dry-run (sin envío)
GOOGLE_APPS_SCRIPT_URL = os.environ.get(
    "CI_AUDIT_ENDPOINT",
    ""  # ← pegar aquí la URL de deployment
)

VERSION = "1.0.0"
TIMEOUT_SECONDS = 30

# ── Métricas y pesos (suman 1.0) ───────────────────────────────────────────────
METRICS = {
    "repo_exists":     {"label": "Repositorio",       "weight": 0.05},
    "git_maturity":    {"label": "Git Madurez",       "weight": 0.15},
    "testing":         {"label": "Testing",           "weight": 0.15},
    "cicd":            {"label": "CI/CD Pipeline",    "weight": 0.15},
    "documentation":   {"label": "Documentación",     "weight": 0.10},
    "security":        {"label": "Seguridad",         "weight": 0.10},
    "structure":       {"label": "Estructura",        "weight": 0.10},
    "deploy_evidence": {"label": "Deploy Evidence",   "weight": 0.10},
    "code_quality":    {"label": "Calidad de Código", "weight": 0.05},
    "dependencies":    {"label": "Dependencias",      "weight": 0.05},
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def bold(text: str) -> str:
    """Negrita ANSI si la terminal lo soporta."""
    if os.environ.get("NO_COLOR") or sys.platform == "win32":
        return text
    return f"\033[1m{text}\033[0m"


def green(text: str) -> str:
    if os.environ.get("NO_COLOR") or sys.platform == "win32":
        return text
    return f"\033[32m{text}\033[0m"


def red(text: str) -> str:
    if os.environ.get("NO_COLOR") or sys.platform == "win32":
        return text
    return f"\033[31m{text}\033[0m"


def yellow(text: str) -> str:
    if os.environ.get("NO_COLOR") or sys.platform == "win32":
        return text
    return f"\033[33m{text}\033[0m"


def bar(score: int, max_score: int = 10) -> str:
    """Barra ASCII de progreso."""
    filled = int(score / max_score * 10)
    blocks = "█" * filled + "░" * (10 - filled)
    return f"{blocks} {score}/{max_score}"


def _run(cmd: list[str], cwd: str | None = None) -> tuple[int, str, str]:
    """Ejecuta un comando y retorna (returncode, stdout, stderr)."""
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10,
            cwd=cwd or os.getcwd(),
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return -1, "", ""


def _git_available() -> bool:
    """¿Hay git instalado y estamos en un repo?"""
    rc, _, _ = _run(["git", "rev-parse", "--git-dir"])
    return rc == 0


EXCLUDE_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__",
               ".mypy_cache", ".pytest_cache", ".tox", ".eggs",
               "dist", "build", ".next", ".nuxt", ".cache",
               "target", ".gradle", ".idea", ".vscode"}


def _files_by_pattern(patterns: list[str]) -> list[Path]:
    """Busca archivos en el árbol que coincidan con patrones glob."""
    cwd = Path.cwd()
    results = []
    for pat in patterns:
        for f in cwd.rglob(pat):
            if any(excl in f.parts for excl in EXCLUDE_DIRS):
                continue
            results.append(f)
    return results


def _count_lines_in_extensions(extensions: tuple[str, ...]) -> int:
    """Cuenta líneas de código en archivos con extensiones dadas."""
    cwd = Path.cwd()
    total = 0
    for ext in extensions:
        for f in cwd.rglob(f"*{ext}"):
            if not f.is_file():
                continue
            if any(excl in f.parts for excl in EXCLUDE_DIRS):
                continue
            try:
                total += len(f.read_text(errors="ignore").splitlines())
            except OSError:
                pass
    return total


# ── Scanner: 10 métricas (0-10 cada una) ──────────────────────────────────────
def scan_repo_exists() -> tuple[int, dict]:
    """¿Existe un repositorio git? ¿Tiene remote?"""
    details = {"has_git": False, "has_remote": False, "remote_url": None}
    rc, _, _ = _run(["git", "rev-parse", "--git-dir"])
    if rc != 0:
        return 0, details  # sin git

    details["has_git"] = True
    _, stdout, _ = _run(["git", "remote", "-v"])
    if "origin" in stdout:
        details["has_remote"] = True
        m = re.search(r"origin\s+(\S+)", stdout)
        if m:
            details["remote_url"] = m.group(1)

    score = 5 if details["has_git"] else 0
    score += 5 if details["has_remote"] else 0
    return score, details


def scan_git_maturity() -> tuple[int, dict]:
    """Frecuencia de commits, branches, contribuidores."""
    if not _git_available():
        return 0, {"commits": 0, "branches": 0, "contributors": 0}

    details = {"commits": 0, "branches": 0, "contributors": 0,
               "last_commit_days_ago": None, "commit_frequency_weekly": 0}

    _, stdout, _ = _run(["git", "log", "--oneline", "--all"])
    commits = stdout.count("\n") + 1 if stdout else 0
    details["commits"] = commits

    _, stdout, _ = _run(["git", "branch", "-a"])
    branches = stdout.count("\n") + 1 if stdout else 0
    details["branches"] = branches

    _, stdout, _ = _run(["git", "shortlog", "-sn", "--all"])
    contributors = stdout.count("\n") + 1 if stdout else 0
    details["contributors"] = contributors

    # Último commit
    _, stdout, _ = _run(["git", "log", "-1", "--format=%ct"])
    if stdout:
        last_ts = int(stdout)
        days_ago = (time.time() - last_ts) / 86400
        details["last_commit_days_ago"] = round(days_ago, 1)

    # Scoring (0-10)
    score = 0
    if commits >= 2:
        score += 2
    if commits >= 10:
        score += 2
    if commits >= 30:
        score += 1
    if branches >= 2:
        score += 2
    if branches >= 4:
        score += 1
    if contributors >= 2:
        score += 2

    details["commit_frequency_weekly"] = round(commits / max(1, (days_ago or 30) / 7), 1)
    return min(10, score), details


def scan_testing() -> tuple[int, dict]:
    """Archivos de test, frameworks de testing detectados."""
    test_files = _files_by_pattern([
        "**/test_*.py", "**/*_test.py", "**/test*.py",
        "**/*.test.js", "**/*.test.ts", "**/*.test.jsx", "**/*.test.tsx",
        "**/*.spec.js", "**/*.spec.ts", "**/*.spec.jsx", "**/*.spec.tsx",
        "**/tests/**", "**/test/**", "**/__tests__/**",
        "**/*Test.java", "**/*Test.kt", "**/*_test.go",
    ])
    test_files = [f for f in test_files if ".git" not in str(f)]

    # Detectar frameworks de test
    frameworks = set()
    cwd = Path.cwd()
    if (cwd / "pytest.ini").exists() or (cwd / "pyproject.toml").exists():
        content = ""
        try:
            content = (cwd / "pyproject.toml").read_text()
        except OSError:
            pass
        if "pytest" in content or (cwd / "pytest.ini").exists():
            frameworks.add("pytest")
    if _files_by_pattern(["jest.config.*", ".jest.*"]):
        frameworks.add("jest")
    if _files_by_pattern(["vitest.config.*"]):
        frameworks.add("vitest")
    if _files_by_pattern(["karma.conf.*"]):
        frameworks.add("karma")
    if _files_by_pattern(["build.gradle*"]) and any(
        "junit" in str(f).lower() for f in _files_by_pattern(["**/*.gradle*"])
    ):
        frameworks.add("junit")

    details = {
        "test_files_count": len(test_files),
        "frameworks": sorted(frameworks),
    }

    score = 0
    if test_files:
        score += min(7, len(test_files))  # hasta 7 puntos por archivos
    if frameworks:
        score += min(3, len(frameworks))  # hasta 3 puntos por frameworks
    return min(10, score), details


def scan_cicd() -> tuple[int, dict]:
    """Pipelines CI/CD, Docker, configs de deploy."""
    cwd = Path.cwd()
    details: dict = {}

    # GitHub Actions
    gh_actions = list(cwd.rglob(".github/workflows/*.yml")) + \
                 list(cwd.rglob(".github/workflows/*.yaml"))
    details["github_actions"] = len(gh_actions)

    # GitLab CI
    gitlab_ci = cwd / ".gitlab-ci.yml"
    details["gitlab_ci"] = gitlab_ci.exists()

    # Docker
    dockerfile = cwd / "Dockerfile"
    docker_compose = cwd / "docker-compose.yml" if (cwd / "docker-compose.yml").exists() else cwd / "docker-compose.yaml"
    details["dockerfile"] = dockerfile.exists()
    details["docker_compose"] = docker_compose.exists()

    # Otros
    makefile = cwd / "Makefile"
    details["makefile"] = makefile.exists()

    # Vercel / Netlify / Railway
    vercel = cwd / "vercel.json"
    netlify = cwd / "netlify.toml"
    railway = cwd / "railway.json"
    details["vercel"] = vercel.exists()
    details["netlify"] = netlify.exists()
    details["railway"] = railway.exists()

    score = 0
    if gh_actions:
        score += min(6, len(gh_actions) * 3)
    if gitlab_ci.exists():
        score += 3
    if dockerfile.exists():
        score += 3
    if docker_compose.exists():
        score += 1
    if makefile.exists() or vercel.exists() or netlify.exists() or railway.exists():
        score += 1
    return min(10, score), details


def scan_documentation() -> tuple[int, dict]:
    """README, docs, arquitectura."""
    cwd = Path.cwd()
    details = {"readme_exists": False, "readme_size": 0, "has_setup": False,
               "docs_dir": False, "architecture_docs": False}

    readme = None
    for name in ["README.md", "README.rst", "README.txt", "README"]:
        candidate = cwd / name
        if candidate.exists():
            readme = candidate
            break

    if readme:
        details["readme_exists"] = True
        try:
            content = readme.read_text(errors="ignore")
            details["readme_size"] = len(content)
            # Buscar secciones clave
            details["has_setup"] = any(
                kw in content.lower()
                for kw in ["install", "instalación", "setup", "configuración",
                            "getting started", "quick start", "quickstart"]
            )
        except OSError:
            pass

    docs_dir = (cwd / "docs").is_dir()
    details["docs_dir"] = docs_dir

    # Detectar docs de arquitectura
    arch_patterns = ["ARCHITECTURE*", "architecture*", "ADR*", "adr*", "DESIGN*"]
    arch_files = _files_by_pattern(arch_patterns)
    details["architecture_docs"] = len(arch_files) > 0

    score = 0
    if details["readme_exists"]:
        score += 3
    if details["has_setup"]:
        score += 3
    if docs_dir:
        score += 2
    if details["architecture_docs"]:
        score += 2
    return min(10, score), details


def scan_security() -> tuple[int, dict]:
    """Secrets hardcodeados, .env.example, .gitignore hygiene."""
    cwd = Path.cwd()
    details = {"hardcoded_secrets": 0, "has_env_example": False,
               "has_gitignore": False, "gitignore_has_env": False}

    # Buscar patrones de secrets hardcodeados
    secret_patterns = [
        r'(?i)(api[_-]?key|apikey|secret|password|passwd|token|auth)\s*[:=]\s*["\'][^\s"\']{8,}["\']',
        r'(?i)(api[_-]?key|apikey|secret|token)\s*=\s*[^\s]{8,}',
    ]
    extensions = (".py", ".js", ".ts", ".jsx", ".tsx", ".dart", ".java", ".kt",
                  ".go", ".rb", ".php", ".env", ".yaml", ".yml", ".json", ".xml")
    for ext in extensions:
        for f in cwd.rglob(f"*{ext}"):
            if any(excl in f.parts for excl in EXCLUDE_DIRS):
                continue
            try:
                content = f.read_text(errors="ignore")
                for pat in secret_patterns:
                    details["hardcoded_secrets"] += len(re.findall(pat, content))
            except OSError:
                pass

    # .env.example
    for name in [".env.example", ".env.sample", ".env.template", ".env.default"]:
        if (cwd / name).exists():
            details["has_env_example"] = True
            break

    # .gitignore
    gitignore = cwd / ".gitignore"
    details["has_gitignore"] = gitignore.exists()
    if gitignore.exists():
        try:
            content = gitignore.read_text(errors="ignore")
            details["gitignore_has_env"] = ".env" in content or "*.env" in content
        except OSError:
            pass

    score = 10
    score -= min(5, details["hardcoded_secrets"])
    if not details["has_gitignore"]:
        score -= 2
    elif not details["gitignore_has_env"]:
        score -= 1
    if not details["has_env_example"]:
        score -= 2
    return max(0, score), details


def scan_structure() -> tuple[int, dict]:
    """Modularidad, separación de concerns, .env.example."""
    cwd = Path.cwd()
    details = {"has_src": False, "has_app": False, "has_api": False,
               "has_config": False, "has_tests": False, "has_docs": False,
               "modular_count": 0}

    indicators = {
        "has_src": ["src"],
        "has_app": ["app", "application"],
        "has_api": ["api", "routes", "controllers"],
        "has_config": ["config", "settings", "configuration"],
        "has_tests": ["tests", "test", "__tests__", "spec"],
        "has_docs": ["docs", "documentation"],
    }
    for key, dirs in indicators.items():
        for d in dirs:
            if (cwd / d).is_dir():
                details[key] = True
                details["modular_count"] += 1
                break

    score = 0
    if details["has_src"] or details["has_app"]:
        score += 4
    if details["has_tests"]:
        score += 2
    if details["has_config"]:
        score += 2
    if details["has_docs"]:
        score += 1
    if details["has_api"]:
        score += 1
    return min(10, score), details


def scan_deploy_evidence() -> tuple[int, dict]:
    """Evidencia de deploy: build outputs, configs de hosting."""
    cwd = Path.cwd()
    details = {"build_dir": False, "dist_dir": False, "out_dir": False,
               "hosting_configs": [], "has_deploy_script": False}

    for d in ["build", "dist", "out", "public", "_site", ".next"]:
        if (cwd / d).is_dir():
            details[f"{d}_dir"] = True

    # Configs de hosting
    hosting_files = {
        "firebase.json": "Firebase",
        "app.yaml": "Google App Engine",
        "Procfile": "Heroku",
        "netlify.toml": "Netlify",
        "vercel.json": "Vercel",
        "railway.json": "Railway",
        "fly.toml": "Fly.io",
        "render.yaml": "Render",
        "docker-compose.yml": "Docker Compose",
        "docker-compose.yaml": "Docker Compose",
        "Dockerfile": "Docker",
    }
    for filename, service in hosting_files.items():
        if (cwd / filename).exists():
            details["hosting_configs"].append(service)

    # Script de deploy
    deploy_scripts = _files_by_pattern(["deploy.sh", "deploy.py", "deploy.ps1",
                                         "scripts/deploy*"])
    details["has_deploy_script"] = len(deploy_scripts) > 0

    has_build = details["build_dir"] or details["dist_dir"] or \
                details["out_dir"] or details.get("_site_dir", False)

    score = 0
    if has_build:
        score += 3
    if details["hosting_configs"]:
        score += min(5, len(details["hosting_configs"]) * 2)
    if details["has_deploy_script"]:
        score += 2
    return min(10, score), details


def scan_code_quality() -> tuple[int, dict]:
    """Linters, formatters, type hints."""
    cwd = Path.cwd()
    details = {"linters": [], "formatters": [], "type_checkers": [], "editorconfig": False}

    linter_map = {
        ".eslintrc.js": "ESLint", ".eslintrc.cjs": "ESLint", ".eslintrc.json": "ESLint",
        ".eslintrc.yaml": "ESLint", ".eslintrc.yml": "ESLint", ".eslintrc": "ESLint",
        "eslint.config.js": "ESLint", "eslint.config.mjs": "ESLint",
        ".pylintrc": "Pylint", ".flake8": "Flake8", ".rubocop.yml": "RuboCop",
    }
    for filename, tool in linter_map.items():
        if (cwd / filename).exists():
            details["linters"].append(tool)

    formatter_map = {
        ".prettierrc": "Prettier", ".prettierrc.json": "Prettier",
        ".prettierrc.yaml": "Prettier", ".prettierrc.yml": "Prettier",
        "prettier.config.js": "Prettier", "prettier.config.mjs": "Prettier",
    }
    for filename, tool in formatter_map.items():
        if (cwd / filename).exists():
            details["formatters"].append(tool)

    # Type checkers
    if (cwd / "tsconfig.json").exists():
        details["type_checkers"].append("TypeScript")
    if (cwd / "pyproject.toml").exists():
        try:
            content = (cwd / "pyproject.toml").read_text()
            if "mypy" in content:
                details["type_checkers"].append("mypy")
        except OSError:
            pass
    if (cwd / "mypy.ini").exists() or (cwd / ".mypy.ini").exists():
        details["type_checkers"].append("mypy")

    details["editorconfig"] = (cwd / ".editorconfig").exists()

    score = 0
    score += min(4, len(details["linters"]) * 2)
    score += min(2, len(details["formatters"]))
    score += min(4, len(details["type_checkers"]) * 2)
    if details["editorconfig"]:
        score += 1
    return min(10, score), details


def scan_dependencies() -> tuple[int, dict]:
    """Archivos de dependencias, lockfiles, versionado."""
    cwd = Path.cwd()
    details = {"files": [], "has_lockfile": False}

    dep_files = {
        "requirements.txt": "pip",
        "pyproject.toml": "Python (pyproject)",
        "setup.py": "Python (setup)",
        "Pipfile": "Pipenv",
        "package.json": "Node.js",
        "Cargo.toml": "Rust",
        "go.mod": "Go",
        "Gemfile": "Ruby",
        "composer.json": "PHP",
        "pubspec.yaml": "Dart/Flutter",
        "build.gradle": "Android/Gradle",
        "build.gradle.kts": "Android/Gradle (Kotlin DSL)",
    }
    for filename, label in dep_files.items():
        if (cwd / filename).exists():
            details["files"].append(label)

    lockfiles = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml",
                 "Pipfile.lock", "poetry.lock", "Cargo.lock", "Gemfile.lock",
                 "composer.lock", "pubspec.lock", "requirements.lock"]
    for lf in lockfiles:
        if (cwd / lf).exists():
            details["has_lockfile"] = True
            break

    score = 0
    if details["files"]:
        score += min(7, len(details["files"]) * 2)
    if details["has_lockfile"]:
        score += 3
    return min(10, score), details


SCANNERS = {
    "repo_exists":     scan_repo_exists,
    "git_maturity":    scan_git_maturity,
    "testing":         scan_testing,
    "cicd":            scan_cicd,
    "documentation":   scan_documentation,
    "security":        scan_security,
    "structure":       scan_structure,
    "deploy_evidence": scan_deploy_evidence,
    "code_quality":    scan_code_quality,
    "dependencies":    scan_dependencies,
}


# ── Cuestionario interactivo ───────────────────────────────────────────────────
def ask_team_info() -> dict:
    """Recolecta información del equipo por prompts interactivos."""
    print(f"\n{bold('🧩 INFORMACIÓN DEL EQUIPO')}")
    print("─" * 50)

    team_name = input("  Nombre del equipo: ").strip()
    project_name = input("  Nombre del proyecto: ").strip()
    repo_url = input("  URL del repositorio (enter si no tiene): ").strip()
    demo_url = input("  URL de demo en vivo (enter si no tiene): ").strip()

    print(f"\n  {bold('Integrantes')} (nombre y rol, enter vacío para terminar):")
    members = []
    i = 1
    while True:
        name = input(f"    #{i} Nombre: ").strip()
        if not name:
            break
        role = input(f"    #{i} Rol (ej. backend, frontend, diseño): ").strip()
        members.append({"name": name, "role": role})
        i += 1

    return {
        "team_name": team_name,
        "project_name": project_name,
        "repo_url": repo_url,
        "demo_url": demo_url,
        "members": members,
    }


# ── POST a Google Sheets ───────────────────────────────────────────────────────
def post_to_sheets(payload: dict) -> bool:
    """Envía el resultado en JSON al endpoint de Google Apps Script.

    Retorna True si el POST fue exitoso (HTTP 2xx/3xx).
    """
    if not GOOGLE_APPS_SCRIPT_URL:
        print(f"\n  {yellow('⚠ Sin endpoint configurado. Modo dry-run.')}")
        print(f"  {yellow('  Seteá CI_AUDIT_ENDPOINT o editar GOOGLE_APPS_SCRIPT_URL en el script.')}")
        return False

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        GOOGLE_APPS_SCRIPT_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            if 200 <= resp.status < 400:
                return True
            print(f"  {red(f'✗ Servidor respondió HTTP {resp.status}')}")
            return False
    except URLError as e:
        print(f"  {red(f'✗ Error de conexión: {e.reason}')}")
        return False


# ── Bloque de código: detección de stacks ─────────────────────────────────────
def detect_tech_stack() -> dict:
    """Detecta el stack de lenguajes principales del proyecto."""
    cwd = Path.cwd()
    lang_counts = {
        "Python": _count_lines_in_extensions((".py",)),
        "JavaScript": _count_lines_in_extensions((".js", ".jsx")),
        "TypeScript": _count_lines_in_extensions((".ts", ".tsx")),
        "Dart": _count_lines_in_extensions((".dart",)),
        "Java": _count_lines_in_extensions((".java",)),
        "Kotlin": _count_lines_in_extensions((".kt",)),
        "Go": _count_lines_in_extensions((".go",)),
        "PHP": _count_lines_in_extensions((".php",)),
        "HTML/CSS": _count_lines_in_extensions((".html", ".css", ".scss", ".sass", ".less")),
    }
    # Filtrar ceros y ordenar
    active = {k: v for k, v in lang_counts.items() if v > 0}
    sorted_langs = sorted(active.items(), key=lambda x: x[1], reverse=True)

    framework_signals = {}
    if (cwd / "pubspec.yaml").exists():
        framework_signals["flutter"] = True
    if list(cwd.rglob("next.config.*")):
        framework_signals["nextjs"] = True
    if list(cwd.rglob("vite.config.*")):
        framework_signals["vite"] = True
    if list(cwd.rglob("manage.py")):
        framework_signals["django"] = True
    if list(cwd.rglob("composer.json")):
        framework_signals["laravel"] = True

    return {
        "primary_language": sorted_langs[0][0] if sorted_langs else "unknown",
        "language_counts": dict(sorted_langs),
        "frameworks_detected": [k for k, v in framework_signals.items() if v],
    }


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{bold('🔍 ci-audit')} v{VERSION}")
    print("CI Nicaragua — Auditoría de Madurez Técnica para Startups")
    print("Hackathon Nicaragua 2026\n")
    print(f"Directorio de trabajo: {Path.cwd()}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    # 1. Cuestionario
    team_info = ask_team_info()

    # 2. Scan automático
    print(f"\n{bold('🔬 ESCANEANDO PROYECTO...')}")
    print("─" * 50)

    scores = {}
    all_details = {}
    composite = 0.0

    for key, scanner_fn in SCANNERS.items():
        meta = METRICS[key]
        raw_score, details = scanner_fn()
        weight = meta["weight"]
        weighted = raw_score * weight
        composite += weighted
        scores[key] = {
            "raw": raw_score,
            "weighted": round(weighted, 2),
            "label": meta["label"],
        }
        all_details[key] = details

        # Mostrar progreso
        icon = "✅" if raw_score >= 7 else "⚠️" if raw_score >= 3 else "❌"
        print(f"  {icon} {meta['label']:<20s} {bar(raw_score)}  (×{weight:.2f} = {weighted:.1f})")

    composite = round(composite * 10, 1)  # escalar 0-10 → 0-100

    # Stack detection
    stack = detect_tech_stack()

    # 3. Resumen
    print(f"\n{bold('📊 RESULTADO')}")
    print("─" * 50)
    tier = "A" if composite >= 75 else "B" if composite >= 50 else "C"
    tier_color = green if tier == "A" else yellow if tier == "B" else red
    print(f"  Score compuesto: {bold(str(composite))}/100")
    print(f"  Tier: {tier_color(f'Tier {tier}')}")
    print(f"  Lenguaje principal: {stack['primary_language']}")
    if stack["frameworks_detected"]:
        print(f"  Frameworks: {', '.join(stack['frameworks_detected'])}")
    print(f"  Código detectado: {sum(stack['language_counts'].values())} líneas")

    # 4. Construir payload
    payload = {
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "team": team_info,
        "scores": scores,
        "composite_score": composite,
        "tier": tier,
        "details": all_details,
        "stack": stack,
        "cwd": str(Path.cwd()),
    }

    # 5. Confirmar y enviar
    print(f"\n{bold('📤 ENVIAR RESULTADOS')}")
    print("─" * 50)

    if GOOGLE_APPS_SCRIPT_URL:
        print(f"  Endpoint: {GOOGLE_APPS_SCRIPT_URL[:60]}...")
    else:
        print(f"  {yellow('Endpoint no configurado — modo dry-run')}")

    confirm = input(f"\n  ¿Enviar resultados? [Y/n]: ").strip().lower()
    if confirm in ("", "y", "yes", "s", "sí", "si"):
        sent = post_to_sheets(payload)
        if sent:
            print(f"\n  {green('✅ Resultados enviados correctamente.')}")
            print(f"  {green('   Gracias por participar en el diagnóstico de madurez.')}")
        else:
            print(f"\n  {yellow('⚠ No se pudo enviar. Revisá la conexión y la URL del endpoint.')}")
            print(f"  {yellow('   Podés volver a ejecutar ci-audit para reintentar.')}")
    else:
        print(f"\n  Envío cancelado. Los resultados no se guardaron.")

    # 6. Guardar localmente
    local_path = Path.cwd() / "ci-audit-result.json"
    try:
        local_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        print(f"  Resultado local guardado en: {local_path.name}")
    except OSError:
        pass

    print()
    return 0 if composite >= 50 else 1


if __name__ == "__main__":
    sys.exit(main())
