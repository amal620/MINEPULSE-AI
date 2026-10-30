const $ = (id) => document.getElementById(id);
const API = "";
let latestAnalysis = null;
let currentIncidentId = null;
let toastTimer;

function toast(message) {
  const el = $("toast"); el.textContent = message; el.classList.add("show");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove("show"), 2800);
}
function fmtDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleString();
}
function statusClass(value) {
  const v = (value || "").toUpperCase();
  if (v.includes("CRITICAL") || v === "FAILED" || v === "REJECTED") return "critical";
  if (v.includes("HIGH") || v.includes("WARNING") || v.includes("AWAITING") || v === "IN_PROGRESS") return "warning";
  return "";
}
async function api(path, options={}) {
  const response = await fetch(API + path, {
    headers: {"Content-Type":"application/json", ...(options.headers || {})},
    ...options
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}
function navigate(id) {
  document.querySelectorAll(".view").forEach(v => v.classList.toggle("active", v.id === id));
  document.querySelectorAll(".nav-item").forEach(b => b.classList.toggle("active", b.dataset.target === id));
  const titles = {overview:"Operations overview",operations:"Live operations", "digital-twin":"Digital twin",incidents:"Incident center",observability:"Observability",governance:"Agent governance"};
  $("pageTitle").textContent = titles[id] || id;
  $("sectionName").textContent = id.replace("-", " ").toUpperCase();
  if (id === "incidents") loadIncidents();
  if (id === "observability") loadMonitoring();
  if (id === "governance") loadAgentCards();
}
document.querySelectorAll("[data-target]").forEach(btn => btn.addEventListener("click", () => navigate(btn.dataset.target)));
$("refreshBtn").addEventListener("click", refreshAll);
$("reloadIncidents").addEventListener("click", loadIncidents);
$("reloadMonitoring").addEventListener("click", loadMonitoring);
$("clock").textContent = new Date().toLocaleTimeString();
setInterval(() => $("clock").textContent = new Date().toLocaleTimeString(), 1000);

async function refreshAll() {
  try {
    const data = await api("/api/dashboard");
    const k = data.kpis;
    $("kpiActive").textContent = k.active_incidents;
    $("kpiCritical").textContent = k.critical_incidents;
    $("kpiApprovals").textContent = k.approvals_recorded;
    $("kpiEvents").textContent = k.monitoring_events;
    $("navIncidentCount").textContent = k.active_incidents;
    renderRecentIncidents(data.incidents || []);
  } catch (e) { toast("API connection error: " + e.message); }
}
function renderRecentIncidents(items) {
  const body = $("recentIncidents");
  if (!items.length) { body.innerHTML = '<tr><td colspan="5" class="empty">No incidents yet. Run a sensor analysis to begin.</td></tr>'; return; }
  body.innerHTML = items.map(i => `<tr><td><b>${i.incident_id}</b></td><td>${i.equipment_id}</td><td><span class="severity-pill ${statusClass(i.severity)}">${i.severity}</span></td><td><span class="status-pill ${statusClass(i.status)}">${i.status}</span></td><td>${fmtDate(i.created_at)}</td></tr>`).join("");
}

document.querySelectorAll(".preset").forEach(btn => btn.addEventListener("click", () => {
  const p = btn.dataset.preset;
  const values = p === "normal" ? [55,3,2.4] : p === "warning" ? [86,6,2.1] : [92,12,1.8];
  $("temperature").value = values[0]; $("vibration").value = values[1]; $("speed").value = values[2];
}));
$("analysisForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("runAnalysis"); button.disabled = true; button.textContent = "⟳ Running agents…";
  $("analysisState").innerHTML = "<i></i> RUNNING";
  try {
    const payload = {
      equipment_id: $("equipmentId").value.trim(),
      temperature: Number($("temperature").value),
      vibration: Number($("vibration").value),
      speed: Number($("speed").value),
      simulation_mode: true
    };
    const data = await api("/api/analyze", {method:"POST", body:JSON.stringify(payload)});
    latestAnalysis = data;
    renderAnalysis(data);
    $("analysisState").innerHTML = "<i></i> COMPLETED";
    toast("Multi-agent workflow completed.");
    await refreshAll();
  } catch (e) {
    $("analysisState").textContent = "FAILED"; toast(e.message);
  } finally { button.disabled = false; button.textContent = "▶ Run multi-agent analysis"; }
});
function renderAnalysis(data) {
  const r = data.result || {};
  const sensor = r.sensor_result || {};
  const diagnosis = r.diagnosis_result || {};
  const risk = r.risk_result || {};
  const twin = r.digital_twin_result || {};
  const decision = r.decision_result || {};
  $("analysisEmpty").classList.add("hidden"); $("analysisResult").classList.remove("hidden");
  $("resultRisk").textContent = risk.risk_level || "—";
  $("resultSensor").textContent = sensor.status || "—";
  $("resultTwin").textContent = twin.virtual_status || "—";
  $("resultAnomalies").innerHTML = (sensor.anomalies || []).length ? sensor.anomalies.map(a => `<span class="chip">${a}</span>`).join("") : '<span class="muted">No anomaly detected</span>';
  $("resultCauses").innerHTML = (diagnosis.possible_causes || []).map(c => `<li>${c}</li>`).join("");
  $("resultDiagnosis").textContent = diagnosis.explanation || "";
  $("resultRecommendation").textContent = decision.recommended_option || "—";
  $("resultReason").textContent = decision.recommendation_reason || "";
  $("resultOptions").innerHTML = (decision.options || []).map(o => `<div class="option-item ${o.option_name === decision.recommended_option ? "recommended" : ""}"><b>${o.option_name}</b> · Risk: ${o.operational_risk} · Downtime: ${o.estimated_downtime}</div>`).join("");
  const incident = r.incident_result;
  $("resultIncident").textContent = incident ? `${incident.incident_id} created · ${incident.status} · Human approval required.` : "No high/critical incident generated for this scenario.";
  $("resultCorrelation").textContent = data.correlation_id || data.monitoring_report?.correlation_id || "—";
  $("twinTemp").textContent = `${$("temperature").value} °C`;
  $("twinVibration").textContent = `${$("vibration").value} mm/s`;
  $("twinSpeed").textContent = `${$("speed").value} m/s`;
  $("twinHealth").textContent = twin.health_status || "UNASSESSED";
  $("twinStatus").textContent = twin.virtual_status || "AWAITING DATA";
  $("twinStatus").className = "status-pill " + statusClass(twin.virtual_status);
  if (incident) currentIncidentId = incident.incident_id;
  loadMonitoring();
}
$("copyCorrelation").addEventListener("click", async () => {
  const val = $("resultCorrelation").textContent;
  try { await navigator.clipboard.writeText(val); toast("Correlation ID copied."); } catch { toast(val); }
});

async function loadIncidents() {
  try {
    const items = await api("/api/incidents");
    const body = $("allIncidents");
    if (!items.length) { body.innerHTML = '<tr><td colspan="6" class="empty">No incidents recorded.</td></tr>'; return; }
    body.innerHTML = items.map(i => `<tr>
      <td><b>${i.incident_id}</b></td><td>${i.equipment_id}</td>
      <td><span class="severity-pill ${statusClass(i.severity)}">${i.severity}</span></td>
      <td><span class="status-pill ${statusClass(i.status)}">${i.status}</span></td>
      <td>${i.recommended_action}</td><td><button class="text-btn" data-open-incident="${i.incident_id}">Manage →</button></td>
    </tr>`).join("");
    body.querySelectorAll("[data-open-incident]").forEach(b => b.addEventListener("click", () => openIncident(b.dataset.openIncident)));
  } catch (e) { toast(e.message); }
}
async function openIncident(id) {
  try {
    const data = await api(`/api/incidents/${id}`);
    const i = data.incident; currentIncidentId = id;
    const box = $("incidentDetail"); box.classList.remove("hidden");
    let actionHtml = "";
    if (i.status === "AWAITING_APPROVAL") actionHtml = `<button class="primary-btn" id="approveBtn">Approve intervention</button><button class="secondary-btn" id="rejectBtn">Reject</button>`;
    if (i.status === "APPROVED") actionHtml = `<button class="primary-btn" id="startMaintBtn">Start maintenance</button>`;
    if (i.status === "IN_PROGRESS") actionHtml = `<button class="primary-btn" id="completeMaintBtn">Complete maintenance</button>`;
    if (i.status === "RESOLVED") actionHtml = `<button class="primary-btn" id="closeIncidentBtn">Close incident</button>`;
    box.innerHTML = `<div class="panel-heading"><div><span class="eyebrow">INCIDENT DETAILS</span><h3>${i.incident_id} · ${i.equipment_id}</h3></div><span class="status-pill ${statusClass(i.status)}">${i.status}</span></div>
      <p>${i.description}</p><p><b>Possible causes:</b> ${(i.possible_causes||[]).join(" · ")}</p><p><b>Recommended action:</b> ${i.recommended_action}</p>
      <div class="action-row">${actionHtml}</div><div class="approval-history"><h4>Approval history</h4>${(data.approvals||[]).map(a=>`<p>${a.reviewer} · ${a.decision} · ${a.comment} · ${fmtDate(a.timestamp)}</p>`).join("") || '<p class="muted">No approval record yet.</p>'}</div>`;
    if ($("approveBtn")) $("approveBtn").onclick = () => showApprovalModal(id, "APPROVE");
    if ($("rejectBtn")) $("rejectBtn").onclick = () => showApprovalModal(id, "REJECT");
    if ($("startMaintBtn")) $("startMaintBtn").onclick = () => showMaintenanceModal(id);
    if ($("completeMaintBtn")) $("completeMaintBtn").onclick = () => completeMaintenanceForIncident(id);
    if ($("closeIncidentBtn")) $("closeIncidentBtn").onclick = () => closeIncident(id);
    box.scrollIntoView({behavior:"smooth",block:"nearest"});
  } catch (e) { toast(e.message); }
}
function openModal(html) { $("modalContent").innerHTML = html; $("actionModal").classList.remove("hidden"); }
function closeModal() { $("actionModal").classList.add("hidden"); }
$("modalClose").onclick = closeModal;
$("actionModal").addEventListener("click", e => { if (e.target === $("actionModal")) closeModal(); });
function showApprovalModal(id, decision) {
  openModal(`<h3>${decision === "APPROVE" ? "Approve intervention" : "Reject intervention"}</h3><p>Record the responsible reviewer and decision. This action is stored in the audit history.</p>
    <form id="approvalForm"><label>Supervisor / reviewer<input name="reviewer" required value="Mine Supervisor"></label><label>Comment<textarea name="comment">${decision === "APPROVE" ? "Approved for simulated maintenance." : "Rejected after review."}</textarea></label><button class="primary-btn">Confirm ${decision.toLowerCase()}</button></form>`);
  $("approvalForm").onsubmit = async e => {
    e.preventDefault(); const f = new FormData(e.target);
    try { await api(`/api/incidents/${id}/approval`, {method:"POST",body:JSON.stringify({reviewer:f.get("reviewer"),decision,comment:f.get("comment")})}); closeModal(); toast("Human decision recorded."); await loadIncidents(); await openIncident(id); await refreshAll(); }
    catch(err){toast(err.message);}
  };
}
function showMaintenanceModal(id) {
  openModal(`<h3>Start maintenance</h3><p>Maintenance can only start after a supervisor approves the incident.</p><form id="maintenanceForm"><label>Technician<input name="technician" required value="Technician A"></label><label>Intervention description<textarea name="intervention_description" required>Inspect and repair the conveyor assembly.</textarea></label><button class="primary-btn">Start simulated maintenance</button></form>`);
  $("maintenanceForm").onsubmit = async e => {
    e.preventDefault(); const f=new FormData(e.target);
    try { await api(`/api/incidents/${id}/maintenance`,{method:"POST",body:JSON.stringify({technician:f.get("technician"),intervention_description:f.get("intervention_description")})}); closeModal(); toast("Maintenance started."); await loadIncidents(); await openIncident(id); await refreshAll(); }
    catch(err){toast(err.message);}
  };
}
async function completeMaintenanceForIncident(id) {
  // Find the latest maintenance record through an endpoint added for demo flow.
  try {
    const data = await api(`/api/incidents/${id}/maintenance/latest`, {method:"GET"});
    await api(`/api/maintenance/${data.maintenance_id}/complete`,{method:"POST"});
    const verify = await api(`/api/maintenance/${data.maintenance_id}/verify`,{method:"POST",body:JSON.stringify({equipment_operational:true})});
    toast("Maintenance completed. Simulated verification: " + verify.verification_status);
    await loadIncidents(); await openIncident(id); await refreshAll();
  } catch (e) { toast(e.message); }
}
async function closeIncident(id) {
  try { await api(`/api/incidents/${id}/close`,{method:"POST"}); toast("Incident closed."); await loadIncidents(); await openIncident(id); await refreshAll(); }
  catch(e){toast(e.message);}
}

async function loadMonitoring() {
  try {
    const reports = await api("/api/monitoring/recent?limit=12");
    let events=0, success=0, failed=0;
    reports.forEach(r=>{events+=r.total_events;success+=r.successful_agents;failed+=r.failed_agents;});
    $("obsEvents").textContent=events; $("obsSuccess").textContent=success; $("obsFailed").textContent=failed; $("obsRuns").textContent=reports.length;
    $("monitoringList").innerHTML = reports.length ? reports.map(r=>`<article class="trace-card"><div class="trace-head"><strong class="${r.execution_status==="FAILED"?"bad":"ok"}">${r.execution_status}</strong><code>${r.correlation_id}</code><small>${r.total_events} events · ${r.successful_agents} success · ${r.failed_agents} failed</small></div><div class="trace-events">${r.events.map(e=>`<div class="trace-event"><b>${e.agent_name}</b><small class="${e.status==="FAILED"?"bad":"ok"}">${e.status}</small><small>${e.duration_seconds == null ? "—" : e.duration_seconds+" s"}</small></div>`).join("")}</div></article>`).join("") : '<div class="panel empty">No executions recorded yet. Run an analysis first.</div>';
  } catch(e) { toast(e.message); }
}
async function loadAgentCards() {
  try {
    const cards = await api("/api/governance/agent-cards");
    $("agentCards").innerHTML = cards.map(c=>`<article class="agent-card"><span class="agent-no">${c.id}</span><h3>${c.name}</h3><p>${c.purpose}</p><small>INPUT · ${c.input}</small><p><b>Output:</b> ${c.output}</p><small>CONTROL · ${c.control}</small></article>`).join("");
  } catch(e){toast(e.message);}
}
refreshAll();
