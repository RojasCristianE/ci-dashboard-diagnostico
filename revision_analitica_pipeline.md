# 🔬 Revisión Analítica del Pipeline de Diagnóstico de Perfil Tecnológico

> **Clasificación:** Auditoría Metodológica — Senior Data Science Review  
> **Objeto:** Pipeline `diagnostico-perfil-tecnologico` v1.0.0  
> **Datos Analizados:** ~82 individuos, ~24 startups  
> **Fecha:** 2026-06-17

---

## 1. Sesgos y Debilidades Metodológicas

### 1.1 — El Problema Fundamental: Datos Autodiagnósticos (Self-Reported)

El pipeline entero descansa sobre **una sola fuente de verdad: encuestas autodiagnósticas**. Esto introduce tres distorsiones simultáneas que se amplifican mutuamente:

#### A) Efecto Dunning-Kruger Estructural

Las escalas de competencia (`skill_programming`, `skill_infra_db`, etc.) van de 0 a 5 y son **completamente subjetivas**. No existe rúbrica de anclaje publicada que defina qué significa concretamente un "3" vs un "4" en programación.

**Consecuencia directa:** Los participantes con menor competencia real tienden a sobrereportarse (Dunning-Kruger), mientras que los más competentes tienden a ser más conservadores. Esto genera una **compresión artificial hacia la media** (compresión de rango) que hace que el `composite_score` subestime la varianza real entre equipos.

- El `composite_score` ([features.py:L116-L128](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/features.py#L116-L128)) pondera promedios de estos datos inflados como si fueran mediciones objetivas.
- El `TRL` ([exporter_db.py:L59-L104](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/exporter_db.py#L59-L104)) usa los mismos promedios como 55% de su peso. **Un TRL de 3.2 basado en autoevaluación no tiene la misma validez que un TRL basado en entregables observados.**

> [!CAUTION]
> **Severidad: ALTA.** El nombre "TRL" (Technology Readiness Level) implícitamente comunica que fue medido con un instrumento validado, como los TRL de la NASA. Usar esta etiqueta para un índice derivado de autoevaluación es **metrología engañosa** ante un comité directivo que no conoce la cadena de origen del dato.

#### B) Sesgo de Deseabilidad Social

En un programa competitivo de incubación, los participantes tienen incentivos para inflar sus respuestas. Si perciben que el diagnóstico influye en asignación de recursos o permanencia en el programa, las respuestas se sesgan hacia lo que creen que es "la respuesta correcta".

- Las preguntas de equipo (`uses_git`, `has_deployed`, `collab_experience`) son particularmente vulnerables: "¿Usas Git?" en un programa tech tiene una respuesta socialmente obvia.
- Las horas semanales (`weekly_hours`) son notoriamente no-confiables en encuestas. El midpoint de "Tiempo completo (>20 horas)" se mapea a 25.0 ([config.py:L267](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/config.py#L267)), pero la distribución real de horas de un estudiante que dice "tiempo completo" puede variar enormemente.

#### C) Non-Response Bias (Sesgo de No-Respuesta)

De 24 startups, el pipeline detecta y marca equipos que "no respondieron" inyectándolos con TRL=1.0 y ORI=100 ([generate_dashboard.py:L543-L577](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/generate_dashboard.py#L543-L577)). Pero los equipos que **sí respondieron** podrían no estar completos: si 3 de 5 miembros responden, los promedios de equipo reflejan solo al subgrupo que tuvo disponibilidad o motivación para responder.

**No hay mecanismo para detectar respuestas parciales dentro de un equipo con datos.** El pipeline asume que si un equipo tiene `n` respuestas, esos `n` son la totalidad del equipo.

---

### 1.2 — Normalización de Roles: Determinismo Rígido

El mapeo de roles ([config.py:L209-L220](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/config.py#L209-L220)) tiene solo **9 entradas** en `ROLE_MAP`. La función `_resolve_role` en [cleaning.py:L203-L218](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/cleaning.py#L203-L218) usa un match parcial alfanumérico como fallback.

**Sesgos identificados:**

| Problema | Ejemplo | Impacto |
|---|---|---|
| **Colapso de multi-rol** | Un participante que escribe "Backend y algo de DevOps" se mapea solo a `backend`. El componente DevOps se pierde. | Subestimación de coverage real |
| **Match parcial ambiguo** | Si alguien escribe "Diseño de bases de datos", el match parcial podría devolver `ux_ui` (por "diseño") en vez de `backend`/`data_ai` | Clasificación errónea silenciosa |
| **Forzar a `other`** | Roles legítimos pero no previstos (QA, DevOps, Mobile Dev, Technical Writer) se descartan a `other` | Invisible en análisis de balance |
| **`full_stack` subrepresentado** | Solo una entrada lo mapea: `"back y fronted"`. Un participante que diga "Desarrollo web completo" no matchearía | Role gaps fantasma |

> [!WARNING]
> El match parcial bidireccional (`clean_key in clean_name or clean_name in clean_key`) es particularmente peligroso: si alguien escribe solo "datos", matchea con `"analisis de datos inteligencia artificial"` → `data_ai`, lo cual puede ser incorrecto si se refería a "entrada de datos".

---

## 2. Errores de Agregación y Métricas Engañosas

### 2.1 — El Problema del Promedio Simple

El pipeline usa **promedios simples (`mean()`) de forma ubicua** para consolidar skills individuales a nivel de equipo:

- [features.py:L107](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/features.py#L107): `avg = round(vals.mean(), 2)`
- [exporter_db.py:L386](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/exporter_db.py#L386): `"averages": {k: round(v/n, 2) for k, v in skill_sums.items()}`

**Escenario crítico — Enmascaramiento por Talento Outlier:**

| Miembro | Programming | Infra/BD |
|---|---|---|
| Alice (CTO) | 5 | 5 |
| Bob | 1 | 0 |
| Carol | 1 | 1 |
| **Promedio** | **2.33** | **2.00** |

Ante Dirección, este equipo reporta un composite score ~2.2 y aparece como "capacidad funcional" en el assessment ([features.py:L344-L345](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/features.py#L344-L345)). **En realidad, tiene un Bus Factor de 1:** si Alice se va, el equipo tiene competencia efectiva ~0.5.

> [!IMPORTANT]  
> **El promedio oculta la distribución.** Con N=3-4 (tamaño típico de estos equipos), un solo outlier mueve el promedio 1-2 puntos. La mediana, el percentil 25, o el mínimo (floor) son más informativos para evaluar riesgo operativo.

El pipeline **sí calcula `floors`** ([features.py:L113](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/features.py#L113)), pero estos **no se usan** en el cálculo del TRL ni del ORI. Son datos muertos en el JSON que nadie consume.

### 2.2 — Horas Totales vs. Horas Promedio: Métrica Contradicente

La `operational_capacity` calcula tanto `total_weekly_hours` como `avg_weekly_hours` ([features.py:L202-L203](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/features.py#L202-L203)). Pero el `dedication_level` se decide solo por el promedio.

Un equipo de 6 personas con promedio de 7.5h/semana tiene **45 horas totales** — más capacidad bruta que un equipo de 2 con promedio de 15h/semana (30 horas totales). Sin embargo, el primero se clasifica como "medium" y el segundo como "high".

### 2.3 — El Composite Score: Pesos Arbitrarios Sin Validación

Los pesos en `COMPOSITE_WEIGHTS` ([config.py:L63-L70](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/config.py#L63-L70)):

```python
COMPOSITE_WEIGHTS = {
    "skill_programming": 0.30,
    "skill_infra_db": 0.25,
    "skill_design": 0.15,
    "skill_ai": 0.15,
    "english_level": 0.15,
}
```

Estos pesos son **decisiones de diseño, no resultados empíricos**. No existe validación cruzada que demuestre que programación debería pesar el doble que diseño para predecir el éxito de una startup. Dado que los proyectos son diversos (health-tech, e-commerce, educación), un peso fijo es inherentemente inadecuado:

- Un proyecto de UX/marketplace podría necesitar más peso en diseño.
- Un proyecto de IA generativa necesita más peso en `skill_ai`.

Al usar pesos fijos, se introduce un **sesgo implícito que favorece equipos tech-heavy y penaliza equipos design/business-driven**, independientemente de si la naturaleza de su proyecto lo justifica.

---

## 3. Robustez de las Heurísticas de Riesgo

### 3.1 — TRL: La Ilusión de Precisión

El TRL v3.0 ([exporter_db.py:L59-L104](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/exporter_db.py#L59-L104)) es un índice compuesto de 8 componentes:

```
55% Skills Técnicos (self-reported)
15% Autonomía (derivada de Git + Deploy + Skills)
15% Cohesión Territorial (HHI geográfico)  
15% Asistencia (CSV scanning)
```

**Puntos ciegos identificados:**

#### A) Cohesión Territorial como Proxy de Rendimiento

La "Cohesión" se calcula con un [índice HHI](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/exporter_db.py#L344-L345) (Herfindahl-Hirschman) sobre distribución geográfica de los miembros. Un equipo donde todos viven en Managua obtiene HHI=1.0 → Cohesión=5.0, lo cual **bonifica su TRL**.

**El problema:** La cercanía geográfica no implica cohesión real. Un equipo remoto con buenas prácticas de colaboración asíncrona puede superar a uno presencial con mala comunicación. Además, penalizar la dispersión geográfica introduce un **sesgo territorial contra equipos de departamentos rurales** (RACCN, Río San Juan, Jinotega), que es exactamente la población que un programa de incubación nacional debería proteger.

#### B) Efficiency Multiplier como Dogma

La "Curva de Eficiencia de Escuadrón" ([exporter_db.py:L93-L100](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/exporter_db.py#L93-L100)):

```python
if member_count <= 2:  efficiency_multiplier = 0.85  # Fragilidad
elif member_count <= 5: efficiency_multiplier = 1.00  # Zona de Oro
elif member_count <= 7: efficiency_multiplier = 0.90  # Fricción
else:                   efficiency_multiplier = 0.75  # Entropía
```

Esto es una **prescripción normativa, no una observación empírica**. Un equipo de 2 personas altamente competentes recibe un **15% de penalización** en TRL por el solo hecho de ser dos. Un equipo de 5 mediocres recibe factor 1.0. Los umbrales son steps discretos sin gradiente: un equipo de 5 tiene TRL × 1.0 pero un equipo de 6 tiene TRL × 0.90, una caída del 10% por un solo miembro adicional.

#### C) Deploy Bonus: Impacto Desproporcionado

El bonus de deploy (+0.25 si al menos un miembro ha deployado) es **binario y no proporcional**. Si 1 de 5 ha deployado una vez, el equipo recibe el mismo bonus que si 5 de 5 han deployado múltiples veces.

### 3.2 — ORI: Riesgo Operativo con Puntos Ciegos Severos

El ORI ([exporter_db.py:L106-L137](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/exporter_db.py#L106-L137)) tiene la estructura más peligrosa del pipeline:

#### Edge Cases Críticos (Falsos Negativos):

| Escenario | ORI Real | ORI Calculado | Causa |
|---|---|---|---|
| Equipo de 4, todos con PC+internet, pero `composite_score` = 1.0 y nadie ha deployado | **Alto** (no pueden ejecutar) | **0** (Bajo) | ORI no mide competencia técnica excepto indirectamente vía TRL penalty |
| Equipo balanceado en roles pero todos reportan <5h/semana | **Alto** (no hay bandwidth) | **~40** (Moderado) | `low_time_count` solo cuenta "Menos de 5h", no el rango "5-10h" que también puede ser insuficiente |
| Equipo donde nadie usa Git y nadie ha collaborado en equipo | **Alto** (riesgo de colapso en fase de integración) | **0** (Bajo) si tienen PC y dicen dedicar >5h | ORI no incorpora **ningún indicador de madurez de colaboración** |

#### Edge Cases Críticos (Falsos Positivos):

| Escenario | ORI Real | ORI Calculado | Causa |
|---|---|---|---|
| Equipo de 2 personas, ambas sénior (5/5 en todo), usan Git, han deployado, PC propia | **Bajo** (viables pero frágiles) | **15-20** (Moderado → bordering) | Structural penalty de +15 por ser 2 personas, sin importar competencia |
| Equipo de 1 persona con TRL bajo pero es un serial entrepreneur con track record | **Moderado** | **55** (Crítico) | +35 por soledad + +20 por TRL bajo = alarm total |

> [!CAUTION]
> **El ORI nunca detecta el riesgo de "equipo que no puede integrar código"** porque no mide Git ni colaboración. Un equipo donde 4 de 4 guardan archivos manualmente y jamás han trabajado en equipo tiene ORI=0 si todos tienen laptop y dicen dedicar >5h. **Este es el punto ciego más peligroso del pipeline.**

### 3.3 — Role Gaps: Reglas Demasiado Binarias

La función `detect_role_gaps` ([exporter_db.py:L139-L148](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/src/exporter_db.py#L139-L148)) solo verifica presencia/ausencia:

```python
if not role_dist.get("backend") and not role_dist.get("cto") and not role_dist.get("full_stack"):
    gaps.append("Missing Backend/Architecture")
```

**No mide la calidad del rol.** Un equipo con un "backend" que tiene `skill_programming=1` y `skill_infra_db=0` pasa el filtro sin alerta. El role gap **se basa en lo que la persona declaró ser, no en lo que puede hacer**. Combinado con el sesgo de deseabilidad social del punto 1.1.B, un participante puede declararse "backend" por haber hecho un tutorial de HTML.

---

## 4. Visualización e Interpretación Directiva

### 4.1 — La Matriz Bubble Chart: Ilusión de Cuadrantes

La matriz TRL vs ORI ([generate_dashboard.py:L281-L332](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/generate_dashboard.py#L281-L332)) posiciona equipos en cuatro cuadrantes con **colores de semáforo** (verde = bueno, rojo = malo). Esta visualización tiene tres problemas graves para un comité directivo:

1. **Falsa dicotomía:** Los cuadrantes se dividen en TRL=2.5 y ORI=50, pero estos umbrales no son puntos de inflexión validados. Un equipo en TRL=2.4 vs TRL=2.6 puede tener una diferencia de décimas en autoevaluación, pero visualmente uno cae en "zona roja" y otro en "zona verde".

2. **Tamaño de burbuja engañoso:** El radio se define como `has_senior_dev ? 10 : 5`. Esto crea una diferencia visual de área de **4×** (πr² = 78.5 vs 314.2), comunicando que los equipos con deploy son dramáticamente "más grandes" o "mejores", cuando la variable solo indica si alguien ha deployado algo alguna vez.

3. **Resolución insuficiente:** Con ~24 equipos en un espacio 5×100, hay alto riesgo de **oclusión** (burbujas superpuestas) que oculta equipos del comité.

### 4.2 — Radar Charts: La Trampa del Polígono

Los radar charts del modal de detalle usan 7-8 ejes ([generate_dashboard.py:L452](file:///home/webmaster/Documentos/Cristian/UNI/CI/05%20Mayo/04_Proyectos/diagnostico-perfil-tecnologico/generate_dashboard.py#L452)) que mezclan escalas de naturaleza diferente:

- Skills (0-5, self-reported, ordinal)
- Autonomía (0-5, derivado, continuo)  
- Cohesión (0-5, HHI geográfico, continuo)
- Asistencia (0-5, datos observados, continuo)

**El área del polígono radar depende del orden de los ejes**, y un comité directivo interpretará visualmente "polígono más grande = mejor equipo". Pero un equipo con Cohesión=5 (todos del mismo departamento) y Asistencia=5 puede tener un polígono enorme con Skills=1, creando la ilusión de competencia.

### 4.3 — Labels de Riesgo como Sentencias

Los badges del dashboard (`SANO / SIN ALERTAS`, `FALTA HARDWARE`, `SIN LÍDER SISTEMAS`) son **categóricos y absolutos**. No hay gradientes ni probabilidades. Un comité directivo tenderá a:

- **Descartar** equipos con badge `FALTA HARDWARE` sin verificar si esa "falta" es un solo miembro de 5 que usa su móvil pero no es crítico para el desarrollo.
- **Sobre-confiar** en equipos marcados `SANO / SIN ALERTAS`, asumiendo que están libres de riesgo, cuando en realidad "sin alertas" solo significa que ninguna de las ~5 reglas heurísticas se disparó.

### 4.4 — Métricas que Generan Falsas Expectativas

| Métrica | Falsa Expectativa | Realidad |
|---|---|---|
| `composite_score` alto | "Este equipo puede entregar un MVP" | Solo miden que creen saber programar, no que puedan |
| `git_adoption = 80%` | "Equipo maduro con CI/CD" | Solo significa que dicen usar Git, no que lo usen correctamente ni con branching/PRs |
| `deployment_rate = 50%` | "Han puesto cosas en producción" | Un deploy de un sitio HTML estático en Netlify cuenta igual que un sistema distribuido en AWS |
| `dedication_level = high` | "Están dedicados al proyecto" | Solo reportaron >15h/semana, que es probablemente aspiracional, no factual |

---

## 5. Resumen de Hallazgos por Prioridad

### 🔴 Críticos (Pueden generar decisiones directivas incorrectas)

1. **Metrología engañosa del TRL:** El nombre sugiere un estándar validado; es un índice ad-hoc de autoevaluación. Renombrarlo o documentar explícitamente sus limitaciones en el dashboard.
2. **ORI no mide madurez de colaboración:** Un equipo sin Git, sin deploy, sin experiencia colaborativa puede aparecer con ORI=0 si tiene laptops. Incorporar `git_score`, `deploy_score` y `collab_score` al cálculo del ORI.
3. **Promedio simple oculta Bus Factor:** El `composite_score` y los promedios del dashboard pueden hacer que un equipo con 1 experto y 3 principiantes parezca viable. Agregar `floor` (mínimo del equipo) y desviación estándar como métricas visibles.

### 🟡 Importantes (Sesgan la interpretación pero no la invalidan)

4. **Cohesión territorial como proxy:** Penalizar equipos geográficamente dispersos no tiene soporte empírico y discrimina contra participantes rurales.
5. **Pesos del composite_score arbitrarios:** Sin validación cruzada contra outcomes reales, la jerarquía de pesos es una opinión, no un modelo.
6. **Role gaps basados en autodeclaración:** Verificar competencia real, no solo label declarado.

### 🟢 Mejorables (Refinamientos de presentación)

7. **Efecto Dunning-Kruger:** Documentar en el dashboard que las skills son autodiagnósticas, no evaluaciones objetivas.
8. **Radar charts con escalas mixtas:** Separar datos observados (asistencia) de datos self-reported (skills) en visualizaciones diferentes, o al menos etiquetarlos visualmente.
9. **Badges categóricos sin gradiente:** Agregar intensidad/severidad numérica junto al badge cualitativo.

---

> [!NOTE]
> Esta revisión analiza el sistema como instrumento de medición y toma de decisiones. Todos los hallazgos son evaluables empíricamente. La recomendación principal es: **nunca presentar datos autodiagnósticos como si fueran mediciones objetivas, y siempre acompañar indicadores compuestos con sus intervalos de confianza o, al mínimo, con los datos de dispersión (min, max, std) que ya se calculan pero no se muestran.**
