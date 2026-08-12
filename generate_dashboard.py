#!/usr/bin/env python3
"""
generate_dashboard.py — Dashboard HTML interactivo de Capital Humano.

Observatorio de Inteligencia de Datos
Centro de Innovación — INATEC Nicaragua

Lee el JSON semántico generado por el pipeline y produce un archivo HTML
autocontenido con visualizaciones interactivas por equipo.
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent


def get_template() -> str:
    """Retorna el template HTML completo."""
    return r'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Soberanía de Datos | Centro de Innovación</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #020617; color: #94a3b8; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .tactical-border { border: 1px solid #1e293b; }
        .critical-alert { border-left: 4px solid #ef4444; background: rgba(239, 68, 68, 0.05); }
        .low-risk { border-left: 4px solid #10b981; background: rgba(16, 185, 129, 0.05); }
        .glass-card { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(8px); }
        .trl-gauge { height: 4px; background: #1e293b; border-radius: 2px; }
        .trl-fill { height: 100%; border-radius: 2px; transition: width 1s ease-in-out; }
        th { cursor: pointer; user-select: none; transition: color 0.2s; position: relative; }
        th:hover { color: #3b82f6; }
        th.active-sort { color: #3b82f6; }
        th.active-sort::after { content: ' ↓'; font-size: 0.8em }
        th.active-sort.asc::after { content: ' ↑'; }
        .tab-active { color: #3b82f6; border-bottom: 2px solid #3b82f6; }
        .role-badge { font-size: 9px; padding: 1px 6px; border-radius: 4px; font-weight: bold; border: 1px solid rgba(255,255,255,0.1); }
        .badge-backend { background: #3b82f622; color: #60a5fa; }
        .badge-frontend { background: #06b6d422; color: #22d3ee; }
        .badge-full_stack { background: #14b8a622; color: #2dd4bf; }
        .badge-ux_ui { background: #a855f722; color: #c084fc; }
        .badge-marketing { background: #f59e0b22; color: #fbbf24; }
        .badge-pm_leadership { background: #10b98122; color: #34d399; }
        .badge-data_ai { background: #ef444422; color: #f87171; }
        .badge-cto { background: #ec489922; color: #f472b6; }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-[95%] mx-auto">
        <header class="mb-10 border-b border-slate-800 pb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div>
                <h1 class="text-3xl font-bold text-white">Diagnóstico de Perfil Tecnológico</h1>
                <p class="text-[9px] text-amber-500/70 mono mt-1 uppercase tracking-wider">⚠ Datos autodiagnósticos (self-reported) — No constituyen evaluación objetiva validada</p>
            </div>
            <div class="bg-slate-900 px-4 py-2 tactical-border rounded"><div class="text-[10px] uppercase tracking-tighter text-slate-500">Total de Respuestas</div><div id="stat-protagonists" class="text-xl font-bold text-white mono">--</div></div>
        </header>

        <div id="main-display" class="space-y-8">
            <!-- Bento Grid: Matriz + Macro Ecosistema -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Matriz (Ocupa 2 columnas y 2 filas) -->
                <div class="lg:col-span-2 lg:row-span-2 glass-card tactical-border rounded-xl p-6 relative">
                    <h3 class="text-base font-bold text-slate-300 uppercase tracking-widest mb-6 mono border-b border-slate-800 pb-2">Matriz de Viabilidad de Proyectos</h3>
                    <div style="height: 400px; position: relative;">
                        <!-- Cuadrantes Decorativos -->
                        <div class="absolute inset-0 pointer-events-none" style="z-index: 0; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr;">
                            <!-- Top Left: Alto Riesgo, Bajo TRL -->
                            <div class="border-b border-r border-slate-700/50 bg-red-900/5"></div>
                            <!-- Top Right: Alto Riesgo, Alto TRL -->
                            <div class="border-b border-slate-700/50 bg-orange-900/5"></div>
                            <!-- Bottom Left: Bajo Riesgo, Bajo TRL -->
                            <div class="border-r border-slate-700/50 bg-blue-900/5"></div>
                            <!-- Bottom Right: Bajo Riesgo, Alto TRL -->
                            <div class="bg-emerald-900/5"></div>
                        </div>
                        <canvas id="riskMatrix" style="position: relative; z-index: 10;"></canvas>
                    </div>
                    <!-- Leyenda de Matriz -->
                    <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs bg-slate-900/50 p-4 rounded-lg tactical-border">
                        <div>
                            <div class="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Leyenda</div>
                            <div class="text-slate-300 mb-1"><strong class="text-slate-400">Eje X:</strong> Índice de Madurez <span class="text-[8px] text-amber-500/60">(autodiagnóstico)</span></div>
                            <div class="text-slate-300"><strong class="text-slate-400">Eje Y:</strong> Riesgo Operativo (ORI v2.0 — Logístico + Colaborativo + Estructural)</div>
                        </div>
                        <div>
                            <div class="text-[10px] text-slate-500 uppercase tracking-wider mb-2"></div>
                            <div class="flex items-center gap-2 mb-1"><span class="w-3 h-3 rounded-full bg-emerald-500/60 inline-block"></span> <span class="text-slate-300">TRL Alto</span></div>
                            <div class="flex items-center gap-2 mb-1"><span class="w-3 h-3 rounded-full bg-blue-500/40 inline-block"></span> <span class="text-slate-300">TRL Bajo</span></div>
                        </div>
                    </div>
                </div>

                <!-- Macro Ecosistema Widgets -->
                <div class="glass-card tactical-border rounded-xl p-6 flex flex-col items-center">
                    <h4 class="text-xs uppercase font-bold text-slate-400 mb-4 mono w-full border-b border-slate-800 pb-2">Origen Académico</h4>
                    <div style="height: 240px; width: 100%;"><canvas id="chartAcademic"></canvas></div>
                </div>
                <div class="glass-card tactical-border rounded-xl p-6 flex flex-col items-center">
                    <h4 class="text-xs uppercase font-bold text-slate-400 mb-4 mono w-full border-b border-slate-800 pb-2">Distribución Depto</h4>
                    <div style="height: 240px; width: 100%;"><canvas id="chartDept"></canvas></div>
                </div>
                <div class="glass-card tactical-border rounded-xl p-6 flex flex-col items-center lg:col-span-1">
                    <h4 class="text-xs uppercase font-bold text-slate-400 mb-4 mono w-full border-b border-slate-800 pb-2">Herramientas Control</h4>
                    <div style="height: 240px; width: 100%;"><canvas id="chartGit"></canvas></div>
                </div>
                <div class="glass-card tactical-border rounded-xl p-6">
                    <h4 class="text-xs uppercase font-bold text-slate-400 mb-4 mono border-b border-slate-800 pb-2">Tendencias Tech</h4>
                    <div style="height: 240px;"><canvas id="chartCuriosity"></canvas></div>
                </div>
                <div class="glass-card tactical-border rounded-xl p-6">
                    <h4 class="text-xs uppercase font-bold text-slate-400 mb-4 mono border-b border-slate-800 pb-2">Producción</h4>
                    <div style="height: 240px;"><canvas id="chartDeploy"></canvas></div>
                </div>
            </div>

            <!-- Controles de Tablas y Filtros -->
            <div class="flex flex-col lg:flex-row justify-between items-end gap-6 border-b border-slate-800 pb-4 mt-8">
                <div class="flex gap-8 w-full lg:w-auto">
                    <button onclick="setTab('teams')" id="tab-teams" class="pb-2 px-2 text-xs font-bold uppercase tracking-widest transition-colors tab-active whitespace-nowrap">Proyectos</button>
                    <button onclick="setTab('protagonists')" id="tab-protagonists" class="pb-2 px-2 text-xs font-bold uppercase tracking-widest transition-colors text-slate-600 hover:text-slate-400 whitespace-nowrap">Protagonistas</button>
                </div>
                <div class="w-full lg:w-auto">
                    <input type="text" id="search" placeholder="Buscar equipo, rol, o nombre..." class="w-full sm:w-96 bg-slate-950 border border-slate-800 rounded px-4 py-2 text-white outline-none mono text-xs">
                </div>
            </div>

            <!-- Tabla y Filtros directos -->
            <div class="mt-6">
                <div id="risk-filters" class="flex flex-wrap gap-2 mb-4"></div>
                <div id="table-container" class="glass-card tactical-border rounded-xl overflow-hidden mb-20"></div>
            </div>
        </div>
    </div>

    <!-- Modals -->
    <div id="modal" class="fixed inset-0 bg-slate-950/95 backdrop-blur-md z-50 hidden flex items-center justify-center p-4">
        <div class="bg-slate-900 tactical-border rounded-xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
            <div class="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50"><div id="modal-header"></div><button onclick="closeModal()" class="text-slate-500 hover:text-white text-2xl font-light">&times;</button></div>
            <div id="modal-body" class="p-8 overflow-y-auto"></div>
        </div>
    </div>

    <script>
        const rawData = __TELEMETRY_DATA__;
        let allProtagonists = [];
        let mainChart = null;
        let detailChart = null;
        let macroCharts = {};
        let currentTab = 'teams';
        let currentRiskFilter = null;
        let currentRoleFilter = null;
        let sortState = { teams: { col: 'trl', dir: 'desc' }, protagonists: { col: 'full_name', dir: 'asc' } };
        const ROLE_LABELS = {
            'backend': 'Backend',
            'frontend': 'Frontend',
            'full_stack': 'Full Stack',
            'ux_ui': 'Diseño UX/UI',
            'marketing': 'Marketing / Negocios',
            'pm_leadership': 'Gestión / Liderazgo',
            'data_ai': 'Datos / IA',
            'cto': 'CTO'
        };

        async function init() {
            allProtagonists = rawData.teams.flatMap(t => t.members.map(m => ({ ...m, team_id: t.id, team_name: t.team_name, project_name: t.project_name })));
            document.getElementById('stat-protagonists').innerText = rawData.metadata.total_protagonists;
            renderRiskFilters();
            renderMatrix();
            renderMacroCharts();
            renderContent();
            document.getElementById('search').addEventListener('input', () => renderContent());
        }

        function setTab(tab) {
            currentTab = tab;
            currentRiskFilter = null;
            currentRoleFilter = null;
            ['teams', 'protagonists'].forEach(t => {
                const el = document.getElementById(`tab-${t}`);
                if (el) el.className = t === tab ? 'pb-2 px-2 text-xs font-bold uppercase tracking-widest transition-colors tab-active whitespace-nowrap' : 'pb-2 px-2 text-xs font-bold uppercase tracking-widest transition-colors text-slate-600 hover:text-slate-400 whitespace-nowrap';
            });
            if (tab === 'teams') {
                renderRiskFilters();
            } else {
                renderRoleFilters();
            }
            renderContent();
        }

        function setSort(col) {
            const state = sortState[currentTab];
            if (state.col === col) { state.dir = state.dir === 'asc' ? 'desc' : 'asc'; }
            else { state.col = col; state.dir = 'desc'; }
            renderContent();
        }

        function filterRole(role) {
            currentRoleFilter = role;
            renderContent();
        }

        function renderRoleFilters() {
            const container = document.getElementById('risk-filters');
            const roles = [...new Set(allProtagonists.map(p => p.role))];
            const colorMap = {
                'backend': 'blue',
                'frontend': 'cyan',
                'full_stack': 'teal',
                'ux_ui': 'purple',
                'marketing': 'amber',
                'pm_leadership': 'emerald',
                'data_ai': 'red',
                'cto': 'pink'
            };
            
            container.innerHTML = roles.map(r => {
                const label = ROLE_LABELS[r] || r;
                const color = colorMap[r] || 'slate';
                return `<button onclick="filterRole('${r}')" class="text-[9px] border border-${color}-900/50 bg-${color}-950/20 text-${color}-500 py-1 px-2 rounded uppercase font-bold hover:bg-${color}-950/40">${label}</button>`;
            }).join('') + 
            `<button onclick="filterRole(null)" class="text-[9px] border border-slate-700 bg-slate-800 text-slate-300 py-1 px-2 rounded uppercase font-bold">Limpiar</button>`;
        }

        const RISK_TYPES = {
            FALTA_TELEMETRIA: { label: 'FALTA TELEMETRÍA', color: 'amber' },
            FALTA_HARDWARE: { label: 'FALTA HARDWARE', color: 'red' },
            SIN_LIDER_SISTEMAS: { label: 'SIN LÍDER SISTEMAS', color: 'red' },
            SIN_DISENO_INTERFACES: { label: 'SIN DISEÑO/INTERFACES', color: 'amber' },
            SIN_GESTION: { label: 'SIN GESTIÓN', color: 'amber' },
            SANO: { label: 'SANO / SIN ALERTAS', color: 'emerald' }
        };

        function getTeamRiskKey(t) {
            if (t.no_response || t.strategic_metrics.member_count === 0) {
                return 'FALTA_TELEMETRIA';
            }
            if (t.strategic_metrics.role_gaps && t.strategic_metrics.role_gaps.length === 0) {
                return 'SANO';
            }
            const hasNoEquipment = t.members.some(m => m.flags && m.flags.no_equipment);
            const missingBackend = t.strategic_metrics.role_gaps && t.strategic_metrics.role_gaps.includes("Missing Backend/Architecture");
            if (hasNoEquipment) return 'FALTA_HARDWARE';
            if (missingBackend) return 'SIN_LIDER_SISTEMAS';
            
            const missingFrontend = t.strategic_metrics.role_gaps && t.strategic_metrics.role_gaps.includes("Missing Frontend/Design");
            const missingManagement = t.strategic_metrics.role_gaps && t.strategic_metrics.role_gaps.includes("Missing Leadership/Business");
            if (missingFrontend) return 'SIN_DISENO_INTERFACES';
            if (missingManagement) return 'SIN_GESTION';
            
            return 'SANO';
        }

        function renderRiskFilters() {
            const container = document.getElementById('risk-filters');
            const keys = [...new Set(rawData.teams.map(t => getTeamRiskKey(t)))];
            
            keys.sort((a, b) => {
                if (a === 'FALTA_TELEMETRIA') return 1;
                if (b === 'FALTA_TELEMETRIA') return -1;
                if (a === 'SANO') return -1;
                if (b === 'SANO') return 1;
                return a.localeCompare(b);
            });

            container.innerHTML = keys.map(k => {
                const info = RISK_TYPES[k];
                return `<button onclick="filterRisk('${k}')" class="text-[9px] border border-${info.color}-900/50 bg-${info.color}-950/20 text-${info.color}-500 py-1 px-2 rounded uppercase font-bold hover:bg-${info.color}-950/40">${info.label}</button>`;
            }).join('') + 
            `<button onclick="filterRisk(null)" class="text-[9px] border border-slate-700 bg-slate-800 text-slate-300 py-1 px-2 rounded uppercase font-bold">Limpiar</button>`;
        }

        function filterRisk(lvl) { currentRiskFilter = lvl; renderContent(); }

        function renderMatrix() {
            const ctx = document.getElementById('riskMatrix').getContext('2d');
            const datasets = rawData.teams.filter(t => t.strategic_metrics.member_count > 0).map(t => ({
                label: t.team_name,
                data: [{ x: t.strategic_metrics.trl, y: t.strategic_metrics.ori.score, r: t.strategic_metrics.has_senior_dev ? 10 : 5 }],
                backgroundColor: t.strategic_metrics.ori.level === 'CRITICAL' ? 'rgba(239, 68, 68, 0.6)' : t.strategic_metrics.trl > 3.0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(59, 130, 246, 0.4)',
                borderColor: t.strategic_metrics.ori.level === 'CRITICAL' ? 'rgb(239, 68, 68)' : t.strategic_metrics.trl > 3.0 ? 'rgb(16, 185, 129)' : 'rgb(59, 130, 246)',
                borderWidth: 1
            }));
            if (mainChart) mainChart.destroy();
            mainChart = new Chart(ctx, { 
                type: 'bubble', 
                data: { datasets }, 
                options: { 
                    responsive: true, 
                    maintainAspectRatio: false, 
                    scales: { 
                        x: { 
                            min: 0, 
                            max: 5, 
                            grid: { color: 'rgba(30, 41, 59, 0.5)' },
                            title: { display: true, text: 'Índice de Madurez (Autodiagnóstico)', color: '#94a3b8', font: { family: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace', size: 10 } }
                        }, 
                        y: { 
                            min: 0, 
                            max: 100, 
                            grid: { color: 'rgba(30, 41, 59, 0.5)' },
                            title: { display: true, text: 'Riesgo Operativo (ORI)', color: '#94a3b8', font: { family: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace', size: 10 } }
                        } 
                    }, 
                    plugins: { 
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            titleColor: '#fff',
                            bodyColor: '#cbd5e1',
                            borderColor: '#334155',
                            borderWidth: 1,
                            padding: 10,
                            callbacks: {
                                label: function(context) {
                                    const team = context.dataset.label;
                                    const x = context.parsed.x;
                                    const y = context.parsed.y;
                                    return `${team} | TRL: ${x} | Riesgo: ${y}%`;
                                }
                            }
                        }
                    } 
                } 
            });
        }

        function renderContent() {
            const container = document.getElementById('table-container');
            const search = document.getElementById('search').value.toLowerCase();
            const state = sortState[currentTab];
            
            if (currentTab === 'teams') {
                let filtered = rawData.teams.filter(t => (t.team_name.toLowerCase().includes(search) || t.project_name.toLowerCase().includes(search)) && (!currentRiskFilter || getTeamRiskKey(t) === currentRiskFilter));
                filtered.sort((a, b) => {
                    let vA = state.col === 'trl' ? a.strategic_metrics.trl : state.col === 'ori' ? a.strategic_metrics.ori.score : state.col === 'member_count' ? a.strategic_metrics.member_count : a.team_name.toLowerCase();
                    let vB = state.col === 'trl' ? b.strategic_metrics.trl : state.col === 'ori' ? b.strategic_metrics.ori.score : state.col === 'member_count' ? b.strategic_metrics.member_count : b.team_name.toLowerCase();
                    return state.dir === 'asc' ? (vA > vB ? 1 : -1) : (vA < vB ? 1 : -1);
                });
                renderTeamsTable(filtered, container);
            } else if (currentTab === 'protagonists') {
                let filtered = allProtagonists.filter(p => (p.full_name.toLowerCase().includes(search) || p.team_name.toLowerCase().includes(search) || p.role.toLowerCase().includes(search)) && (!currentRoleFilter || p.role === currentRoleFilter));
                filtered.sort((a, b) => {
                    let vA = a[state.col].toLowerCase();
                    let vB = b[state.col].toLowerCase();
                    return state.dir === 'asc' ? (vA > vB ? 1 : -1) : (vA < vB ? 1 : -1);
                });
                renderProtagonistsTable(filtered, container);
            }
        }

        function getTeamRiskBadge(t) {
            const key = getTeamRiskKey(t);
            const info = RISK_TYPES[key];
            return `<span class="text-[9px] px-2 py-1 rounded font-bold mono bg-${info.color}-950/20 text-${info.color}-500 border border-${info.color}-900/50">${info.label}</span>`;
        }

        function renderTeamsTable(data, container) {
            const state = sortState.teams;
            const getCls = (c) => state.col === c ? `active-sort ${state.dir}` : '';
            container.innerHTML = `<table class="w-full text-left border-collapse"><thead><tr class="bg-slate-900/50 border-b border-slate-800">
                <th onclick="setSort('team_name')" class="px-6 py-4 text-[10px] uppercase font-bold text-slate-500 mono ${getCls('team_name')}">Proyecto / Equipo</th>
                <th onclick="setSort('member_count')" class="px-6 py-4 text-[10px] uppercase font-bold text-slate-500 mono ${getCls('member_count')}">Integrantes</th>
                <th onclick="setSort('trl')" class="px-6 py-4 text-[10px] uppercase font-bold text-slate-500 mono ${getCls('trl')}">Madurez Técnica (0-5)</th>
                <th onclick="setSort('ori')" class="px-6 py-4 text-[10px] uppercase font-bold text-slate-500 mono ${getCls('ori')}">Riesgo Operativo</th>
                </tr></thead>
                <tbody>${data.map(t => `<tr class="border-b border-slate-800/50 hover:bg-slate-900/30 transition-colors cursor-pointer ${t.strategic_metrics.member_count === 0 ? 'opacity-40' : ''}" onclick="showTeamDetail(${t.id})">
                    <td class="px-6 py-4"><div class="font-bold text-white">${t.team_name}</div><div class="text-[10px] text-blue-400 mono">${t.project_name}</div></td>
                    <td class="px-6 py-4 text-xs font-bold text-slate-300 mono">${t.strategic_metrics.member_count}</td>
                    <td class="px-6 py-4"><div class="flex items-center gap-2"><span class="text-xs font-bold text-white mono">${t.strategic_metrics.trl}</span><div class="trl-gauge w-20"><div class="trl-fill bg-blue-500" style="width: ${(t.strategic_metrics.trl / 5) * 100}%"></div></div></div></td>
                    <td class="px-6 py-4">${getTeamRiskBadge(t)}</td>
                    </tr>`).join('')}</tbody></table>`;
        }

        function renderProtagonistsTable(data, container) {
            const state = sortState.protagonists;
            const getCls = (c) => state.col === c ? `active-sort ${state.dir}` : '';
            container.innerHTML = `<table class="w-full text-left border-collapse"><thead><tr class="bg-slate-900/50 border-b border-slate-800">
                <th onclick="setSort('full_name')" class="px-6 py-4 text-[10px] uppercase font-bold text-slate-500 mono ${getCls('full_name')}">Nombre del Protagonista</th>
                <th onclick="setSort('team_name')" class="px-6 py-4 text-[10px] uppercase font-bold text-slate-500 mono ${getCls('team_name')}">Proyecto</th>
                <th onclick="setSort('role')" class="px-6 py-4 text-[10px] uppercase font-bold text-slate-500 mono ${getCls('role')}">Responsabilidad</th>
                </tr></thead>
                <tbody>${data.map(p => `<tr class="border-b border-slate-800/50 hover:bg-slate-900/30 transition-colors cursor-pointer" onclick="showProtagonistDetail(${p.id})">
                    <td class="px-6 py-4"><div class="font-bold text-white">${p.full_name}</div><div class="text-[10px] text-slate-500 uppercase mono">${p.dept}</div></td>
                    <td class="px-6 py-4 text-xs text-blue-400 font-bold">${p.team_name}</td>
                    <td class="px-6 py-4"><span class="role-badge badge-${p.role}">${ROLE_LABELS[p.role] || p.role}</span></td>
                    </tr>`).join('')}</tbody></table>`;
        }

        function renderMacroCharts() {
            const stats = rawData.macro_analytics;
            createChart('chartAcademic', 'doughnut', Object.keys(stats.study_center_type), Object.values(stats.study_center_type), ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']);
            const sortedDept = Object.entries(stats.dept_distribution).sort((a,b) => b[1] - a[1]);
            createChart('chartDept', 'bar', sortedDept.map(x=>x[0]), sortedDept.map(x=>x[1]), '#3b82f6', true);
            createChart('chartGit', 'pie', Object.keys(stats.git_usage), Object.values(stats.git_usage), ['#10b981', '#f59e0b', '#ef4444']);
            const sortedCur = Object.entries(stats.tech_curiosity).sort((a,b) => b[1] - a[1]);
            createChart('chartCuriosity', 'bar', sortedCur.map(x=>x[0]), sortedCur.map(x=>x[1]), '#a855f7', true);
            createChart('chartDeploy', 'bar', Object.keys(stats.deploy_experience), Object.values(stats.deploy_experience), '#06b6d4');
        }

        function createChart(id, type, labels, data, colors, horizontal = false) {
            const ctx = document.getElementById(id).getContext('2d');
            if (macroCharts[id]) macroCharts[id].destroy();
            macroCharts[id] = new Chart(ctx, {
                type: type,
                data: { labels: labels, datasets: [{ data: data, backgroundColor: colors, borderColor: 'rgba(255,255,255,0.05)', borderWidth: 1 }] },
                options: { indexAxis: horizontal ? 'y' : 'x', responsive: true, maintainAspectRatio: false, scales: type === 'bar' ? { x: { grid: { display: false }, ticks: { font: { size: 13 } } }, y: { grid: { color: '#1e293b' }, ticks: { font: { size: 13 } } } } : {}, plugins: { legend: { display: type !== 'bar', position: 'bottom', labels: { boxWidth: 10, font: { size: 13 } } } } }
            });
        }

        function showTeamDetail(id) {
            const t = rawData.teams.find(x => x.id === id);
            document.getElementById('modal-header').innerHTML = `<div><h3 class="text-2xl font-bold text-white">${t.team_name}</h3><p class="text-xs text-blue-500 mono uppercase">${t.project_name}</p></div>`;
            document.getElementById('modal-body').innerHTML = `<div class="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-10">
                <div class="glass-card tactical-border rounded-xl p-8 flex flex-col items-center">
                    <h4 class="text-[10px] uppercase font-bold text-slate-500 mb-6 mono w-full text-center">Perfil de Competencias del Equipo</h4>
                    <div style="width: 100%; max-width: 350px; height: 350px;"><canvas id="teamRadarChart"></canvas></div>
                    <div class="mt-6 flex flex-wrap justify-center gap-2">${Object.entries(t.role_distribution).map(([role, count]) => `<span class="role-badge badge-${role}">${ROLE_LABELS[role] || role} (${count})</span>`).join('')}</div>
                    ${t.dispersion ? `<div class="mt-4 w-full"><div class="text-[8px] text-slate-600 uppercase mono mb-1 text-center">Piso Mínimo del Equipo (Bus Factor)</div><div class="flex flex-wrap justify-center gap-1">${Object.entries(t.dispersion).map(([k, v]) => `<span class="text-[7px] mono px-1.5 py-0.5 rounded ${v.floor <= 1 ? 'bg-red-950/30 text-red-400 border border-red-900/40' : 'bg-slate-800 text-slate-400 border border-slate-700'}">⌊${k.replace('skill_','').replace('english_level','eng')}=${v.floor}⌋</span>`).join('')}</div></div>` : ''}
                </div>
                <div class="space-y-6">
                    <div class="bg-slate-950 p-6 rounded-xl tactical-border">
                        <h4 class="text-[10px] uppercase font-bold text-slate-500 mb-4 mono">Visión de Proyecto</h4>
                        <p class="text-xs text-slate-400 italic">"${t.description}"</p>
 
                        <h4 class="text-[10px] uppercase font-bold text-slate-500 mt-8 mb-4 mono">Análisis Cualitativo y Logística</h4>
                        <div class="space-y-3">
                            <div><span class="text-[10px] text-slate-500 mono block mb-1">Instituciones:</span><div class="flex flex-wrap gap-1">${t.qualitative_profile.all_institutions.map(i => `<span class="text-[8px] font-bold px-1.5 py-0.5 rounded bg-purple-900/30 text-purple-400 border border-purple-900/50 uppercase">${i}</span>`).join('')}</div></div>
                            <div><span class="text-[10px] text-slate-500 mono block mb-1">Departamentos:</span><div class="flex flex-wrap gap-1">${t.qualitative_profile.all_departments.map(d => `<span class="text-[8px] font-bold px-1.5 py-0.5 rounded bg-emerald-900/30 text-emerald-400 border border-emerald-900/50 uppercase">${d}</span>`).join('')}</div></div>
                            <div><span class="text-[10px] text-slate-500 mono block mb-1">Aprendizaje:</span><span class="text-[9px] font-bold px-2 py-0.5 rounded bg-blue-900/30 text-blue-400 border border-blue-900/50 uppercase">${t.qualitative_profile.learning_style}</span></div>
                        </div>
 
                        <div class="mt-8 space-y-2">
                            <div class="text-[9px] uppercase font-bold text-slate-600 mono">Necesidades de Intervención Prioritaria</div>
                            ${t.strategic_metrics.role_gaps.map(g => `<div class="bg-red-950/20 text-red-500 p-2 rounded text-[9px] font-bold mono border border-red-900/30">⚠️ ${g.replace('Missing Backend/Architecture','Falta líder en Sistemas').replace('Missing Frontend/Design','Falta especialista en Interfaces').replace('Missing Leadership/Business','Falta perfil de Gestión')}</div>`).join('')}
                            ${t.strategic_metrics.role_gaps.length === 0 ? '<div class="bg-emerald-950/20 text-emerald-500 p-2 rounded text-[9px] font-bold mono border border-emerald-900/30">✓ EQUIPO BALANCEADO</div>' : ''}
                        </div>
                    </div>
                    <div class="bg-slate-900 p-4 rounded tactical-border flex justify-between items-center">
                        <div><div class="text-[9px] text-slate-600 uppercase mono">Índice de Madurez</div><div class="text-xl font-bold text-white mono">${t.strategic_metrics.trl}</div><div class="text-[7px] text-amber-500/50 mono">AUTODIAGNÓSTICO</div></div>
                        <div><div class="text-[9px] text-slate-600 uppercase mono text-right">Riesgo Operativo (ORI v2.0)</div><div class="text-xs font-bold text-amber-500 mono text-right">${t.strategic_metrics.ori.level === 'CRITICAL' ? 'CRÍTICO' : t.strategic_metrics.ori.level === 'MODERATE' ? 'MODERADO' : 'BAJO'} (${t.strategic_metrics.ori.score})</div>
                        ${t.strategic_metrics.ori.components ? `<div class="text-[7px] text-slate-600 mono text-right mt-1">Log:${t.strategic_metrics.ori.components.logistic} · Col:${t.strategic_metrics.ori.components.collab} · Est:${t.strategic_metrics.ori.components.structural}</div>` : ''}
                        </div>
                    </div>
                </div>
            </div>
            <h4 class="text-[10px] uppercase font-bold text-slate-500 mb-4 mono">Integrantes del Equipo</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">${t.members.map(m => `<div onclick="showProtagonistDetail(${m.id})" class="flex items-center justify-between p-3 bg-slate-800/20 rounded border border-slate-800 hover:border-blue-500/50 cursor-pointer transition-colors group"><div><div class="text-sm font-bold text-slate-300 group-hover:text-white">${m.full_name}</div><span class="role-badge badge-${m.role}">${ROLE_LABELS[m.role] || m.role}</span></div><div class="text-right"><div class="text-[8px] text-slate-600 mono uppercase">${m.institution} | ${m.dept}</div><div class="flex gap-1 justify-end mt-1">${m.flags.no_equipment ? '<span class="text-[7px] text-red-500 font-bold">SIN_EQUIPO</span>' : ''}${m.flags.low_time ? '<span class="text-[7px] text-amber-500 font-bold">BAJA_DISP</span>' : ''}</div></div></div>`).join('')}</div>`;
            setTimeout(() => { renderRadar(document.getElementById('teamRadarChart').getContext('2d'), [t.averages.skill_programming, t.averages.skill_infra_db, t.averages.skill_ai, t.averages.skill_design, t.averages.english_level, t.qualitative_profile.autonomy_score, t.qualitative_profile.cohesion_score, t.qualitative_profile.attendance_score], '#3b82f6', 'rgba(59, 130, 246, 0.2)', ['Programación', 'Sistemas/BD', 'IA Generativa', 'Diseño/Interfaces', 'Inglés Técnico', 'Autonomía', 'Cohesión', 'Asistencia']); }, 50);
            document.getElementById('modal').classList.remove('hidden');
        }

        function showProtagonistDetail(id) {
            const p = allProtagonists.find(x => x.id === id);
            document.getElementById('modal-header').innerHTML = `<div><h3 class="text-2xl font-bold text-white">${p.full_name}</h3><p class="text-xs text-blue-500 mono uppercase">Revisión de Protagonista — ${p.team_name}</p></div>`;
            document.getElementById('modal-body').innerHTML = `<div class="grid grid-cols-1 lg:grid-cols-2 gap-12"><div class="glass-card tactical-border rounded-xl p-8 flex flex-col items-center"><h4 class="text-[10px] uppercase font-bold text-slate-500 mb-6 mono w-full text-center">Perfil de Competencias Individual</h4><div style="width: 100%; max-width: 350px; height: 350px;"><canvas id="protagonistRadarChart"></canvas></div><div class="mt-4 flex flex-col items-center gap-2"><span class="role-badge badge-${p.role} text-sm px-4 py-1">${ROLE_LABELS[p.role] || p.role}</span><div class="text-[10px] text-slate-400 mono uppercase">${p.institution} | ${p.dept}</div></div></div><div class="space-y-6"><div class="bg-slate-950 p-6 rounded-xl tactical-border"><h4 class="text-[10px] uppercase font-bold text-slate-500 mb-4 mono">Análisis Cualitativo</h4><div class="space-y-4"><div><div class="text-[10px] text-slate-600 uppercase">Obstáculo Identificado</div><div class="text-xs text-red-400 font-bold leading-tight">${p.qualitative.main_obstacle}</div></div><div><div class="text-[10px] text-slate-600 uppercase">Método de Aprendizaje</div><div class="text-xs text-slate-300 italic">${p.qualitative.learning_method}</div></div><div><div class="text-[10px] text-slate-600 uppercase">Puestas en Producción</div><div class="text-xs text-white font-bold">${p.qualitative.has_deployed.replace('varias veces','Varias veces').replace('al menos una vez','Al menos una vez').replace('no, nunca','Sin experiencia previa')}</div></div><div class="grid grid-cols-2 gap-4 pt-4 border-t border-slate-800"><div class="p-3 rounded bg-slate-900 border border-slate-800"><div class="text-[9px] text-slate-600 uppercase">Uso de Git</div><div class="text-xs text-white font-bold">${p.qualitative.uses_git.replace('si, lo uso','Uso frecuente').replace('conozco lo basico','Básico').replace('no, guardo','Manual')}</div></div><div class="p-3 rounded bg-slate-900 border border-slate-800"><div class="text-[9px] text-slate-600 uppercase">Dedicación</div><div class="text-xs text-white font-bold">${p.qualitative.weekly_hours}</div></div></div></div></div><div class="flex gap-4">${p.flags.no_equipment ? '<div class="flex-1 bg-red-950/20 border border-red-900/50 p-4 rounded text-center"><div class="text-xs text-red-500 font-bold">Sin Equipo Propio</div></div>' : ''}${p.flags.low_time ? '<div class="flex-1 bg-amber-950/20 border border-amber-900/50 p-4 rounded text-center"><div class="text-xs text-amber-500 font-bold">Baja Disponibilidad</div></div>' : ''}</div><button onclick="showTeamDetail(${p.team_id})" class="w-full py-3 bg-slate-800 hover:bg-slate-700 text-xs font-bold uppercase tracking-widest rounded transition-colors tactical-border">Regresar al Equipo</button></div></div>`;
            setTimeout(() => { renderRadar(document.getElementById('protagonistRadarChart').getContext('2d'), [p.skills.programming, p.skills.infra_db, p.skills.ai, p.skills.design, p.skills.english, p.qualitative.autonomy_score, p.qualitative.attendance_score], '#10b981', 'rgba(16, 185, 129, 0.2)', ['Programación', 'Sistemas/BD', 'IA Generativa', 'Diseño/Interfaces', 'Inglés Técnico', 'Autonomía', 'Asistencia']); }, 50);
            document.getElementById('modal').classList.remove('hidden');
        }

        function renderRadar(ctx, data, color, bgColor, labels) {
            if (detailChart) detailChart.destroy();
            detailChart = new Chart(ctx, { type: 'radar', data: { labels: labels, datasets: [{ data, backgroundColor: bgColor, borderColor: color, pointBackgroundColor: color, pointBorderColor: '#fff', borderWidth: 2 }] }, options: { responsive: true,
          maintainAspectRatio: false, scales: { r: { min: 0, max: 5, beginAtZero: true, grid: { color: 'rgba(51, 65, 85, 0.4)' }, angleLines: { color: 'rgba(51, 65, 85, 0.4)' }, pointLabels: {
          color: '#64748b', font: { size: 8, family: 'JetBrains Mono' } }, ticks: { display: false, stepSize: 1 } } }, plugins: { legend: { display: false } } } });
        }


        function closeModal() { document.getElementById('modal').classList.add('hidden'); }
        init();
    </script>
</body>
</html>'''


def _normalize_team_name(name: str) -> str:
    """Normaliza un nombre de equipo para comparación."""
    import re
    n = name.lower().strip()
    n = re.split(r'[/:\(]', n)[0].strip()
    n = re.sub(r'[^a-z0-9áéíóúñü\s]', '', n).strip()
    return n


def _inject_missing_architecture_teams(data: dict) -> dict:
    """Inyecta equipos del diagnóstico de arquitectura que no respondieron
    el diagnóstico individual como entradas placeholder 'no_response'."""
    import csv
    import re

    arch_csv = (
        BASE_DIR.parent.parent.parent
        / "Documentos"
        / "Formularios_Maestros"
        / "Diagnóstico de Arquitectura y Plan de Desarrollo (Respuestas).csv"
    )
    if not arch_csv.exists():
        logger.warning(f"⚠ CSV de arquitectura no encontrado: {arch_csv}")
        return data

    # Read architecture teams
    with open(arch_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        arch_teams = []
        for row in reader:
            name = row.get("Nombre de la Startup / Proyecto", "").strip()
            leader = row.get(
                "Nombre completo del Líder Técnico o desarrollador principal del equipo", ""
            ).strip()
            if name:
                arch_teams.append({"display": name, "leader": leader})

    # Build set of existing telemetry team names (normalized)
    existing = set()
    for t in data["teams"]:
        existing.add(_normalize_team_name(t.get("team_name", "")))
        if t.get("project_name"):
            existing.add(_normalize_team_name(t.get("project_name", "")))

    # Identify truly missing teams
    injected = 0
    exclude_projects = {"mediscan", "miempleo", "rommy", "milpagrow", "mipagrow"}
    for at in arch_teams:
        norm = _normalize_team_name(at["display"])
        if norm in exclude_projects:
            continue
        # Check if already matched (exact or prefix)
        matched = False
        for ex in existing:
            if ex == norm or (len(ex) >= 5 and len(norm) >= 5 and ex[:5] == norm[:5]):
                matched = True
                break
            # Special case: "Va D' Viaje" -> "va de viaje"
            if "viaje" in ex and "viaje" in norm:
                matched = True
                break
        if not matched:
            # Create placeholder team matching the dashboard_data schema
            placeholder = {
                "id": len(data["teams"]) + 1,
                "team_name": norm,
                "team_name_display": at["display"],
                "project_name": at["display"],
                "description": "Equipo pendiente de completar diagnóstico individual.",
                "no_response": True,
                "strategic_metrics": {
                    "trl": 1.0,
                    "ori": {
                        "score": 100.0,
                        "level": "CRITICAL"
                    },
                    "role_gaps": ["Missing All Roles / Pending Form"],
                    "member_count": 0,
                    "has_senior_dev": False
                },
                "qualitative_profile": {
                    "academic_origin": "N/A",
                    "learning_style": "N/A",
                    "territorial_index": "N/A",
                    "autonomy_score": 0.0,
                    "cohesion_score": 0.0,
                    "attendance_score": 0.0,
                    "all_institutions": [],
                    "all_departments": []
                },
                "averages": {
                    "skill_programming": 0.0,
                    "skill_infra_db": 0.0,
                    "skill_design": 0.0,
                    "skill_ai": 0.0,
                    "english_level": 0.0
                },
                "role_distribution": {},
                "members": []
            }
            data["teams"].append(placeholder)
            existing.add(norm)
            injected += 1

    if injected > 0:
        logger.info(f"  +{injected} equipos inyectados desde diagnóstico de arquitectura (sin respuesta individual)")

    return data


def main():
    """Genera el dashboard HTML autocontenido."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    json_path = BASE_DIR / "outputs" / "web_dashboard" / "dashboard_data.json"
    if not json_path.exists():
        logger.error(f"❌ No se encontró el JSON: {json_path}")
        logger.error("   Ejecutá primero el pipeline: python run_pipeline.py")
        return

    logger.info(f"📊 Leyendo datos: {json_path.name}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Inyectar equipos del diagnóstico de arquitectura que no respondieron
    data = _inject_missing_architecture_teams(data)

    # Obtener template y embeder datos
    template = get_template()
    json_str = json.dumps(data, ensure_ascii=False)
    # Escapar </script> para evitar romper el HTML parser
    json_str = json_str.replace("</", "<\\/")
    html = template.replace("__TELEMETRY_DATA__", json_str)

    # Escribir output
    output_path = BASE_DIR / "outputs" / "dashboard.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    n_active = len([t for t in data["teams"] if not t.get("no_response")])
    n_pending = len([t for t in data["teams"] if t.get("no_response")])
    n_members = sum(len(t.get("members", [])) for t in data["teams"] if not t.get("no_response"))
    size_kb = output_path.stat().st_size / 1024

    logger.info(f"✓ Dashboard generado: {output_path}")
    logger.info(f"  {n_active} equipos con datos + {n_pending} pendientes · {n_members} participantes · {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
