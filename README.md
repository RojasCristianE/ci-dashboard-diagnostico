# 📊 CI Dashboard — Diagnóstico de Perfil Tecnológico

Este repositorio contiene el motor analítico y el dashboard interactivo utilizado por el **Centro de Innovación — INATEC** para la auditoría de capital humano de las startups en el marco del **Hackathon Nicaragua 2026**.

## 🚀 Vista en Vivo
El dashboard interactivo puede visualizarse en:
[https://RojasCristianE.github.io/ci-dashboard-diagnostico/](https://RojasCristianE.github.io/ci-dashboard-diagnostico/)

## 🛠️ Estructura del Proyecto

*   `index.html`: Interfaz del dashboard (Vue/Chart.js/Tailwind).
*   `data/processed/dashboard_data.json`: Datos agregados y anonimizados de los equipos.
*   `src/`: Motor de procesamiento en Python (Limpieza, Scoring, Normalización).
*   `run_pipeline.py`: Orquestador del análisis de datos.
*   `requirements.txt`: Dependencias para ejecutar el pipeline.

## 🔬 Metodología Analítica

El sistema procesa los diagnósticos de perfil tecnológico de los protagonistas para calcular:
1.  **TRL (Technology Readiness Level) v3.0:** Índice de madurez técnica autodiagnosticada.
2.  **ORI (Operational Risk Index) v2.0:** Índice de riesgo basado en logística (hardware), colaboración y dedicación horaria.
3.  **Radar de Competencias:** Visualización de equilibrio de roles (Frontend, Backend, IA, Diseño, Gestión).

## 🔐 Privacidad y Transparencia

En cumplimiento con las políticas de protección de datos, este repositorio **no contiene información de identificación personal (PII)**.
*   Los archivos brutos (`data/respuestas.csv`) han sido excluidos.
*   Los correos electrónicos y teléfonos han sido anonimizados en los conjuntos de datos procesados.
*   El código fuente se comparte para permitir la auditoría del proceso de scoring y normalización de datos.

---
*Centro de Innovación — INATEC Nicaragua*
