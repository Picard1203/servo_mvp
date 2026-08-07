/* Servo Control — frontend logic (revision 2).
   Same-origin client of the FastAPI backend. Polls /state every second and
   renders it EXACTLY as read, posts commands, refreshes zeros + events on a
   slower cycle. */

"use strict";

const API = "/api/v1";
const POLL_STATE_MS = 1000;
/* Saved positions and the activity feed change rarely, and every poll is a
   whole TCP connection through the MCU relay. Polling them as often as the
   live state tripled the connection rate for almost no benefit. */
const POLL_LISTS_MS = 15000;

/* counts per output degree, display-only (saved-position degrees).
   The backend owns all real motion math. */
const COUNTS_PER_OUTPUT_DEG = 4096 * (44 / 30) / 360;

/* Command soft limits, mirroring the backend (output_min_deg /
   output_max_deg). Displayed position may legitimately read negative when
   the active baseline sits above the current position - that is real
   information and is NOT wrapped: in a multi-turn system -25 and 335 are
   different absolute targets, a full output revolution apart. */
const ANGLE_MIN = -90.0;
const ANGLE_MAX = 90.0;
/* one encoder count at the output: (360/4096) * (30/44) */
const ANGLE_STEP = 0.06;

/* how long a transient notice stays on screen */
const TOAST_MS = 5000;

const $ = (id) => document.getElementById(id);

const state = {
  lastState: null,
  zeros: [],
  selectedZeroId: null,
  acceleration: 50,      /* fixed sensible default; not exposed to the user */
  online: false,
};

/* ---------------- HTTP helpers ---------------- */

async function apiGet(path) {
  const response = await fetch(API + path);
  if (!response.ok) throw await asApiError(response);
  return response.json();
}
async function apiPost(path, body) {
  const response = await fetch(API + path, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) throw await asApiError(response);
  return response.json();
}
async function apiDelete(path) {
  const response = await fetch(API + path, { method: "DELETE" });
  if (!response.ok) throw await asApiError(response);
  return response.json();
}
async function asApiError(response) {
  let detail = response.statusText, reason = "";
  try {
    const d = await response.json();
    reason = d.reason || "";
    if (Array.isArray(d.detail)) {
      /* FastAPI validation error: detail is a list of objects */
      detail = d.detail.map((item) => item.msg || "invalid value").join("; ");
    } else if (d.detail) {
      detail = d.detail;
    }
  } catch (_) { /* non-JSON */ }
  const err = new Error(detail); err.status = response.status; err.reason = reason;
  return err;
}

/* ---------------- status line ---------------- */

function toast(message, level) {
  const host = $("toasts");
  const el = document.createElement("div");
  el.className = "toast" + (level ? " " + level : "");

  const text = document.createElement("span");
  text.textContent = message;
  el.appendChild(text);

  const close = document.createElement("button");
  close.className = "x";
  close.textContent = "\u00d7";
  close.setAttribute("aria-label", "Dismiss");
  el.appendChild(close);

  const bar = document.createElement("i");
  bar.className = "bar";
  bar.style.animation = "drain " + TOAST_MS + "ms linear forwards";
  el.appendChild(bar);

  host.appendChild(el);

  let remaining = TOAST_MS;
  let startedAt = Date.now();
  let timer = setTimeout(dismiss, remaining);
  function dismiss() {
    clearTimeout(timer);
    el.classList.add("out");
    setTimeout(() => el.remove(), 200);
  }
  close.addEventListener("click", dismiss);
  el.addEventListener("mouseenter", () => {
    clearTimeout(timer);
    remaining -= Date.now() - startedAt;   /* keep the real time left */
    el.classList.add("paused");
  });
  el.addEventListener("mouseleave", () => {
    startedAt = Date.now();
    el.classList.remove("paused");
    timer = setTimeout(dismiss, Math.max(400, remaining));
  });
}

function say(message, isError) {
  toast(message, isError ? "warn" : null);
}
function clearNotice() {
  /* a new action makes any pending notice irrelevant - dismiss them now
     instead of waiting out the timer */
  const host = $("toasts");
  if (host) Array.from(host.children).forEach((el) => el.remove());
}
/* ---------- themed modal dialogs (native <dialog>) ---------- */

function askConfirm(title, body, okLabel) {
  return new Promise((resolve) => {
    const dlg = $("confirmDlg");
    $("confirmTitle").textContent = title;
    $("confirmBody").textContent = body;
    $("confirmYes").textContent = okLabel || "Confirm";
    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      cleanup();
      if (dlg.open) dlg.close();
      resolve(value);
    };
    const onYes = () => finish(true);
    const onNo = () => finish(false);
    const onClose = () => finish(false);      /* Esc / backdrop close */
    function cleanup() {
      $("confirmYes").removeEventListener("click", onYes);
      $("confirmNo").removeEventListener("click", onNo);
      dlg.removeEventListener("close", onClose);
    }
    $("confirmYes").addEventListener("click", onYes);
    $("confirmNo").addEventListener("click", onNo);
    dlg.addEventListener("close", onClose);
    dlg.showModal();
    $("confirmYes").focus();
  });
}

function askText(title, body, okLabel) {
  return new Promise((resolve) => {
    const dlg = $("promptDlg");
    const input = $("promptInput");
    $("promptTitle").textContent = title;
    $("promptBody").textContent = body;
    $("promptYes").textContent = okLabel || "Save";
    input.value = "";
    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      cleanup();
      if (dlg.open) dlg.close();
      resolve(value);
    };
    const onYes = () => {
      const text = input.value.trim();
      if (!text) { input.focus(); return; }   /* require a name */
      finish(text);
    };
    const onNo = () => finish(null);
    const onClose = () => finish(null);
    const onKey = (e) => { if (e.key === "Enter") { e.preventDefault(); onYes(); } };
    function cleanup() {
      $("promptYes").removeEventListener("click", onYes);
      $("promptNo").removeEventListener("click", onNo);
      dlg.removeEventListener("close", onClose);
      input.removeEventListener("keydown", onKey);
    }
    $("promptYes").addEventListener("click", onYes);
    $("promptNo").addEventListener("click", onNo);
    dlg.addEventListener("close", onClose);
    input.addEventListener("keydown", onKey);
    dlg.showModal();
    input.focus();
  });
}

function sayError(err) {
  const reasons = {
    locked: "refused — servo is locked",
    moving: "refused — servo is moving",
    step: "refused — angle must be a multiple of 0.1°",
    active_zero: "refused — position is in use as the baseline",
    datum_zero: "refused — the reference cannot be removed",
  };
  say(reasons[err.reason] || ("error: " + err.message), true);
}

/* instant press feedback that reverts */
function flash(el) {
  el.classList.remove("flash");
  void el.offsetWidth;         /* restart the animation */
  el.classList.add("flash");
  setTimeout(() => el.classList.remove("flash"), 400);
}

/* ---------------- state polling + render ---------------- */

async function pollState() {
  try {
    const s = await apiGet("/servo/state");
    state.lastState = s;
    setOnline(true);
    renderState(s);
  } catch (_) { setOnline(false); }
}

function setOnline(online) {
  if (online === state.online) return;
  state.online = online;
  $("conn").classList.toggle("off", !online);
  $("connText").textContent = online ? "ONLINE" : "OFFLINE";
  if (!online) say("connection lost — retrying…", true);
}

function renderState(s) {
  $("posN").textContent = s.output_deg.toFixed(1);
  const pct = Math.min(100, Math.max(0, (s.output_deg / 360) * 100));
  $("posBar").style.width = pct + "%";

  $("vTemp").textContent = s.temperature_c.toFixed(1);
  $("vVolt").textContent = s.voltage_v.toFixed(2);
  $("vCur").textContent = s.current_a.toFixed(2);
  $("vTorq").textContent = s.torque_kgcm.toFixed(1);

  const anyFault = s.overload || s.overcurrent || s.overheat ||
                   s.voltage_fault || s.sensor_fault || s.angle_fault;
  const chip = $("movechip");
  if (anyFault) { chip.className = "chip alarm"; chip.textContent = "FAULT"; }
  else if (s.moving) { chip.className = "chip moving"; chip.textContent = "MOVING"; }
  else if (s.settling) { chip.className = "chip"; chip.textContent = "SETTLING"; }
  else { chip.className = "chip holding"; chip.textContent = "HOLDING"; }

  setFault("fOverload", s.overload);
  setFault("fOvercurrent", s.overcurrent);
  setFault("fOverheat", s.overheat);
  setFault("fVoltage", s.voltage_fault);
  setFault("fSensor", s.sensor_fault);
  setFault("fAngle", s.angle_fault);
  $("mTemp").classList.toggle("alarm", s.overheat);
  $("mVolt").classList.toggle("alarm", s.voltage_fault);
  $("mCur").classList.toggle("alarm", s.overcurrent || s.overload);
  $("recoverwrap").hidden = !s.overload;

  const lock = $("lockCube");
  lock.classList.toggle("locked", s.locked);
  lock.textContent = s.locked ? "Locked" : "Lock";

  const cal = $("calCube");
  cal.classList.toggle("needcal", !s.position_verified);
  cal.textContent = "Calibrate";

  const slot = $("alarmslot");
  if (anyFault) {
    slot.className = "alarmslot alarm";
    slot.textContent = "\u25a0 ALARM \u00b7 " + faultName(s) +
      (s.overload ? " \u2014 torque cut back" : "");
  } else if (!s.position_verified) {
    slot.className = "alarmslot warn";
    slot.textContent =
      "\u25b2 Reference not set \u2014 press CALIBRATE at the physical home";
  } else {
    slot.className = "alarmslot";
    slot.innerHTML = '<span class="okdot"></span> No active alarms';
  }
}

function setFault(id, on) {
  const el = $(id);
  el.classList.toggle("on", on);
  const s = el.querySelector(".s");
  if (on) s.textContent = "TRIP";
  else s.innerHTML = '<span class="okdot"></span>OK';
}

function faultName(s) {
  if (s.overload) return "Overload";
  if (s.overcurrent) return "Overcurrent";
  if (s.overheat) return "Overheat";
  if (s.voltage_fault) return "Voltage fault";
  if (s.sensor_fault) return "Sensor fault";
  if (s.angle_fault) return "Angle fault";
  return "Fault";
}

/* ---------------- zeros (saved positions) ---------------- */

async function pollZeros() {
  try { state.zeros = await apiGet("/zeros"); renderZeros(); }
  catch (_) { /* offline handled by state poll */ }
}

function renderZeros() {
  const list = $("zeroList");
  const active = state.zeros.find((z) => z.is_active) || null;
  const base = active ? active.raw_counts : 0;
  list.innerHTML = "";
  state.zeros
    .filter((z) => !z.is_datum)          /* reference row is not shown */
    .forEach((z) => {
      const row = document.createElement("div");
      row.className = "z" + (z.is_active ? " active" : "") +
        (z.id === state.selectedZeroId ? " selected" : "");
      const deg = (z.raw_counts - base) / COUNTS_PER_OUTPUT_DEG;
      row.innerHTML =
        (z.is_active ? '<span class="zt">Active</span>'
                     : '<span class="spacer"></span>') +
        "<span>" + escapeHtml(z.name) + "</span>" +
        '<span class="deg">' + deg.toFixed(1) + "\u00b0</span>";
      row.onclick = () => { state.selectedZeroId = z.id; renderZeros(); };
      list.appendChild(row);
    });
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/* ---------------- events (recent activity) ---------------- */

const EVENT_LABELS = {
  "servo.move.accepted": "move accepted",
  "servo.move.fine_approach": "fine approach",
  "servo.stop": "stopped",
  "servo.lock.engaged": "locked",
  "servo.lock.released": "unlocked",
  "servo.calibrated": "reference set",
  "servo.fault.recovered": "fault cleared",
  "zero.captured": "position saved",
  "zero.activated": "position used",
  "zero.deleted": "position removed",
  "app.boot": "started",
};

/* backend timestamp is an ISO string ("2026-07-22T14:22:07"); parse as Date,
   fall back to the raw time part if parsing ever fails. */
function eventTime(e) {
  /* backend field is `timestamp` (ISO string); tolerate legacy `timestamp` too */
  const raw = e.timestamp != null ? e.timestamp : e.timestamp;
  const d = new Date(raw);
  if (!isNaN(d.getTime())) {
    return d.toLocaleTimeString("en-GB", { hour12: false });  /* 24-hour */
  }
  return typeof raw === "string" && raw.includes("T")
    ? raw.split("T")[1] : String(raw != null ? raw : "");
}

async function pollEvents() {
  try {
    const data = await apiGet("/system/events?limit=50");
    const list = $("eventList");
    list.innerHTML = "";
    data.events.forEach((e) => {
      const row = document.createElement("div");
      row.className = "ev";
      const label = EVENT_LABELS[e.event] || e.event.split(".").pop();
      row.innerHTML =
        '<span class="tm">' + eventTime(e) + "</span>" +
        '<span class="nm">' + escapeHtml(label) + "</span>" +
        '<span class="ds">' + escapeHtml(e.message || "") + "</span>";
      list.appendChild(row);
    });
  } catch (_) { /* offline handled by state poll */ }
}

/* ---------------- commands ---------------- */

async function doMove() {
  clearNotice();
  const target = parseFloat($("inAngle").value);
  const speed = parseFloat($("inSpeed").value);
  if (!isFinite(target) || !isFinite(speed)) { say("enter a valid angle and speed", true); return; }
  if (target < ANGLE_MIN || target > ANGLE_MAX) {
    say("angle must be between " + ANGLE_MIN.toFixed(0) + "\u00b0 and +" +
        ANGLE_MAX.toFixed(0) + "\u00b0", true);
    return;
  }
  try {
    await apiPost("/servo/move", {
      target_deg: Math.round(target / ANGLE_STEP) * ANGLE_STEP,
      speed_dps: speed,
      acceleration: state.acceleration,
    });
    /* success: no notice */
    pollState();
  } catch (err) { sayError(err); }
}
async function doStop() {
  clearNotice();
  try { await apiPost("/servo/stop"); /* success: no notice */ pollState(); }
  catch (err) { sayError(err); }
}
async function toggleLock() {
  clearNotice();
  const current = state.lastState ? state.lastState.locked : false;
  try {
    await apiPost("/servo/lock", { locked: !current });
    /* success: no notice */
    pollState();
  } catch (err) { sayError(err); }
}
async function doCalibrate() {
  clearNotice();
  const verified = state.lastState && state.lastState.position_verified;
  const body = verified
    ? "Re-set the reference to this physical position? The displayed angle "
      + "will be re-zeroed here."
    : "Is the mechanism at its physical home? The current position becomes "
      + "the reference and the displayed angle is re-zeroed.";
  const ok = await askConfirm("Set reference", body, "Set reference");
  if (!ok) return;
  try {
    await apiPost("/servo/calibrate");
    /* success: no notice */
    pollState(); pollZeros();
  } catch (err) { sayError(err); }
}
async function doRecover() {
  clearNotice();
  try { await apiPost("/servo/recover"); /* success: no notice */ pollState(); }
  catch (err) { sayError(err); }
}
async function doSave() {
  clearNotice();
  const name = await askText("Save position",
    "Name this position so it can be recalled later.", "Save");
  if (!name) return;
  try { await apiPost("/zeros/capture", { name: name }); /* success: no notice */ pollZeros(); }
  catch (err) { sayError(err); }
}
async function doUse() {
  clearNotice();
  if (state.selectedZeroId == null) { say("select a position first", true); return; }
  try { await apiPost("/zeros/" + state.selectedZeroId + "/activate"); /* success: no notice */ pollZeros(); pollState(); }
  catch (err) { sayError(err); }
}
async function doRemove() {
  clearNotice();
  if (state.selectedZeroId == null) { say("select a position first", true); return; }
  const zero = state.zeros.find((z) => z.id === state.selectedZeroId);
  if (zero) {
    const ok = await askConfirm("Remove position",
      'Remove "' + zero.name + '" from saved positions?', "Remove");
    if (!ok) return;
  }
  try { await apiDelete("/zeros/" + state.selectedZeroId); state.selectedZeroId = null; /* success: no notice */ pollZeros(); }
  catch (err) { sayError(err); }
}
function doExport() {
  clearNotice();
  const now = Math.floor(Date.now() / 1000);
  const from = now - 24 * 3600;
  window.location.href = API + "/telemetry/export?from=" + from + "&to=" + now;
  /* success: no notice */
}

/* ---------------- wiring ---------------- */

function nudge(inputId, delta) {
  const input = $(inputId);
  const value = parseFloat(input.value) || 0;
  const stepped = Math.round((value + delta) / ANGLE_STEP) * ANGLE_STEP;
  input.value = stepped.toFixed(2);
}

function bind(id, handler) {
  const el = $(id);
  el.addEventListener("click", () => { flash(el); handler(); });
}

function initUi() {
  $("serverAddr").textContent = window.location.host;

  bind("moveBtn", doMove);
  bind("stopBtn", doStop);
  bind("lockCube", toggleLock);
  bind("calCube", doCalibrate);
  bind("recoverBtn", doRecover);
  bind("saveBtn", doSave);
  bind("useBtn", doUse);
  bind("removeBtn", doRemove);
  bind("exportCube", doExport);

  document.querySelectorAll(".step").forEach((btn) => {
    btn.addEventListener("click", () =>
      nudge(btn.dataset.nudge, parseFloat(btn.dataset.d)));
  });

  $("inAngle").addEventListener("keydown", (e) => { if (e.key === "Enter") doMove(); });
}

function start() {
  initUi();
  pollState(); pollZeros(); pollEvents();
  setInterval(pollState, POLL_STATE_MS);
  setInterval(pollZeros, POLL_LISTS_MS);
  setInterval(pollEvents, POLL_LISTS_MS);
}

document.addEventListener("DOMContentLoaded", start);
