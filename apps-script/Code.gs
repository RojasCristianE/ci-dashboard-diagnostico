/**
 * apps-script/Code.gs
 * Google Apps Script — Endpoint receptor de ci-audit
 * ==================================================
 * Acepta POST con JSON del CLI ci-audit y escribe una fila en la hoja "Audit Responses".
 *
 * Instrucciones de despliegue:
 *   1. Creá un Google Sheet. Nombrá la primera hoja "Audit Responses".
 *   2. Agregá encabezados en la fila 1 (ver sección HEADERS más abajo).
 *   3. Abrí Extensiones > Apps Script.
 *   4. Pegá este código y guardalo.
 *   5. Desplegar > Nueva implementación > Tipo: "Aplicación web".
 *   6. Ejecutar como: "Yo", Acceso: "Cualquier persona".
 *   7. Copiá la URL de deployment y pegala en GOOGLE_APPS_SCRIPT_URL en ci_audit.py.
 */

// ── HEADERS esperados en la fila 1 de "Audit Responses" ─────────────────────
// Timestamp | Team | Project | Members | Score | Tier | Repo URL | Demo URL |
// Primary Language | Frameworks | LOC | Git Score | Testing Score | CI/CD Score |
// Docs Score | Security Score | Structure Score | Deploy Score | Quality Score |
// Deps Score | Details JSON | CWD | Client Version

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Audit Responses");

    if (!sheet) {
      return ContentService
        .createTextOutput(JSON.stringify({ ok: false, error: "Sheet 'Audit Responses' not found" }))
        .setMimeType(ContentService.MimeType.JSON);
    }

    const team = payload.team || {};
    const scores = payload.scores || {};
    const stack = payload.stack || {};
    const details = payload.details || {};

    // Aplanar miembros
    const membersStr = (team.members || [])
      .map(m => `${m.name || ""} (${m.role || "?"})`)
      .join("; ");

    // Aplanar scores individuales para columnas
    const s = (key) => (scores[key] && scores[key].raw) || 0;

    // Construir fila
    const row = [
      payload.timestamp || new Date().toISOString(),
      team.team_name || "",
      team.project_name || "",
      membersStr,
      payload.composite_score || 0,
      payload.tier || "?",
      team.repo_url || "",
      team.demo_url || "",
      stack.primary_language || "unknown",
      (stack.frameworks_detected || []).join(", "),
      Object.values(stack.language_counts || {}).reduce((a, b) => a + b, 0),
      s("git_maturity"),
      s("testing"),
      s("cicd"),
      s("documentation"),
      s("security"),
      s("structure"),
      s("deploy_evidence"),
      s("code_quality"),
      s("dependencies"),
      JSON.stringify(details),
      payload.cwd || "",
      payload.version || "",
    ];

    sheet.appendRow(row);

    return ContentService
      .createTextOutput(JSON.stringify({
        ok: true,
        team: team.team_name,
        score: payload.composite_score,
        tier: payload.tier,
      }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet() {
  return ContentService
    .createTextOutput(JSON.stringify({
      ok: true,
      service: "ci-audit endpoint",
      version: "1.0.0",
      instructions: "Send POST with ci-audit JSON payload",
    }))
    .setMimeType(ContentService.MimeType.JSON);
}
