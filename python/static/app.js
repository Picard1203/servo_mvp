/* Servo Control — frontend logic (revision 3).
   Same-origin client of the FastAPI backend. Receives live state, zeros,
   and events through a single SSE stream (/api/v1/stream); posts commands
   over individual HTTP requests. Replaces the three-connection polling
   model (revision 2) to stay within the W5500's 6-socket ceiling. */

"use strict";

const API = "/api/v1";


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

/* How many consecutive failures before the UI declares a problem.
 *
 * At one poll per second this is about three seconds. A single lost
 * answer is ordinary traffic, not a fault: reacting to one made the
 * connection banner flash "connection lost" and the position blink to
 * "--" while everything was in fact working, which reads as a broken
 * machine to an operator who is not a programmer.
 *
 * This paces what is DISPLAYED. It does not soften what is reported -
 * the API still says reading_valid false the moment a read fails, per
 * ADR-0008. A real stall lasts ten seconds and still shows plainly. */
const FAILURES_BEFORE_ALARM = 3;

/* How long a command may go unanswered before the UI says so.
 *
 * A servo_read can take up to the Bridge's 10 s timeout, and the only
 * feedback used to be a 400 ms flash - so for the following nine
 * seconds a working command looked exactly like one that did nothing,
 * and the operator pressed again (D15). Well short of the timeout, so
 * the notice arrives while they are still deciding whether to. */
const SLOW_COMMAND_MS = 2500;

const $ = (id) => document.getElementById(id);

const state = {
  lastState: null,
  zeros: [],
  selectedZeroId: null,
  acceleration: 50,      /* fixed sensible default; not exposed to the user */
  online: false,
  streamFailures: 0,     /* consecutive SSE connection errors */
  readFailures: 0,       /* consecutive invalid servo readings */
  lastKnownDeg: null,    /* last position actually measured */
  lastMeasured: null,    /* last state the servo actually answered */
};

/* ---------------- HTTP helpers ---------------- */

/* Reason code for a failure that never reached the backend at all.
   Not a backend code - the backend cannot report that it was never
   asked. Kept alongside them so every failure path carries a reason
   and sayError() has one shape to handle. */
const UNREACHABLE = "unreachable";

/* Single door for every request, because the interesting failure
   happens before there is a response to read.
 *
 * fetch() REJECTS when the connection itself fails - refused, dropped,
 * or stalled. asApiError() is never reached, so err.reason was
 * undefined and sayError() fell through to the browser's own words:
 * "error: Failed to fetch". That is the single most likely failure in
 * this system - the relay has six W5500 slots and refuses politely
 * when they are spent (D13, measured at 5 refusals in 10 back-to-back
 * requests) - and it produced the least intelligible message in the
 * whole UI. The end users are not programmers. */
/* `notify` says whether a slow answer is worth telling the operator
   about. Commands: yes - they pressed something and are waiting. Polls:
   no - they run every second in the background, and a poll that takes
   2.5 s is the UI's problem, not theirs. Announcing those would put a
   toast on screen nobody asked for. */
async function request(path, init, notify) {
  let dismissSlow = null;
  const slow = notify ? setTimeout(() => {
    dismissSlow = say("still working — the controller has not answered yet",
                      false);
  }, SLOW_COMMAND_MS) : null;
  try {
    let response;
    try {
      response = await fetch(API + path, init);
    } catch (_) {
      const err = new Error("the controller did not answer");
      err.status = 0;
      err.reason = UNREACHABLE;
      throw err;
    }
    if (!response.ok) throw await asApiError(response);
    return await response.json();
  } finally {
    /* clearTimeout only cancels a notice that has not appeared yet. One
       that HAS appeared must be taken down, or the screen goes on
       saying the controller has not answered while the servo is
       visibly moving - and success is deliberately silent, so nothing
       else would contradict it. */
    if (slow !== null) clearTimeout(slow);
    if (dismissSlow) dismissSlow();
  }
}

async function apiGet(path) {
  return request(path, undefined, false);
}
async function apiPost(path, body) {
  return request(path, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  }, true);
}
async function apiDelete(path) {
  return request(path, { method: "DELETE" }, true);
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
  /* handed back so a notice that has been superseded can be taken down
     rather than left to run out its timer (the slow-command notice). */
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

  return dismiss;
}

function say(message, isError) {
  return toast(message, isError ? "warn" : null);
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

/* Refusals whose wording is ours: the backend's phrasing for these is
   written for a developer, and the operator gains nothing from it. */
const REFUSALS = {
  locked: "refused — servo is locked",
  moving: "refused — servo is moving",
  active_zero: "refused — position is in use as the baseline",
  datum_zero: "refused — the reference cannot be removed",
  invalid_reading: "refused — the servo did not answer, so its position "
                 + "is not known",
  unreachable: "the controller is busy or did not answer — wait a moment "
             + "and try again",
};

/* Refusals that carry a NUMBER derived from configuration. Their
   message is the backend's to write, because a copy here goes stale
   the moment the configuration is retuned - which is exactly what
   happened: this mapped `step` to a hardcoded "multiple of 0.1°" while
   config.py and motion_service.py enforced 0.06° (D21). The correct
   figure travelled all the way from config.py and was discarded on
   arrival. */
const BACKEND_WORDED = ["step", "out_of_travel"];

function sayError(err) {
  if (BACKEND_WORDED.indexOf(err.reason) !== -1) {
    say("refused — " + err.message, true);
    return;
  }
  const refusal = REFUSALS[err.reason];
  if (refusal) { say(refusal, true); return; }
  /* No reason code. Three outcomes, kept distinct because they call for
     different things from the operator: try again, tell someone, or
     stop. Never the browser's own text (D14). */
  if (!err.status) {
    say(REFUSALS[UNREACHABLE], true);
  } else if (err.status >= 500) {
    say("the controller reported a fault — " + err.message, true);
  } else {
    say("refused — " + err.message, true);
  }
}

/* instant press feedback that reverts */
function flash(el) {
  el.classList.remove("flash");
  void el.offsetWidth;         /* restart the animation */
  el.classList.add("flash");
  setTimeout(() => el.classList.remove("flash"), 400);
}

/* ---------------- SSE stream + on-demand fetches ---------------- */

/* The single persistent connection that replaces the three polling
   timers. EventSource handles reconnection automatically; its retry
   interval defaults to ~3 s which is appropriate for this relay.
   One connection per operator instead of three cuts socket demand 3x
   against the W5500's hard 6-socket ceiling (ADR-0009). */
let eventSource = null;

function connectStream() {
  if (eventSource !== null) {
    eventSource.close();
  }
  eventSource = new EventSource(API + "/stream");

  eventSource.addEventListener("state", function (msg) {
    try {
      const s = JSON.parse(msg.data);
      state.lastState = s;
      state.streamFailures = 0;
      setOnline(true);
      renderState(s);
    } catch (_) { /* malformed event — next one arrives in ~1 s */ }
  });

  eventSource.addEventListener("zeros", function (msg) {
    try {
      state.zeros = JSON.parse(msg.data);
      renderZeros();
    } catch (_) { /* next push arrives in ~15 s */ }
  });

  eventSource.addEventListener("events", function (msg) {
    try {
      renderEvents(JSON.parse(msg.data));
    } catch (_) { /* next push arrives in ~15 s */ }
  });

  eventSource.onopen = function () {
    state.streamFailures = 0;
    setOnline(true);
  };

  eventSource.onerror = function () {
    state.streamFailures += 1;
    if (state.streamFailures >= FAILURES_BEFORE_ALARM) {
      setOnline(false);
    }
    /* EventSource reconnects automatically */
  };
}

/* On-demand fetch — used after write commands where the operator
   expects immediate feedback (zero list changes). The SSE stream
   delivers regular updates; this is for the gap between a write and
   the next scheduled push. */
async function fetchZeros() {
  try { state.zeros = await apiGet("/zeros"); renderZeros(); }
  catch (_) { /* stream will deliver zeros shortly; ignore */ }
}

function setOnline(online) {
  if (online === state.online) return;
  state.online = online;
  $("conn").classList.toggle("off", !online);
  $("connText").textContent = online ? "ONLINE" : "OFFLINE";
  if (!online) say("connection lost — retrying…", true);
}

function renderState(s) {
  // output_deg is null when the servo did not answer. Never show that as
  // a number of its own: a failed read arrives as count 0, which is
  // indistinguishable from the bottom of travel, and the operator
  // commands moves from what this readout says.
  //
  // A single failed read holds the last MEASURED position rather than
  // blanking, because one blip is not a fault. After
  // FAILURES_BEFORE_ALARM in a row the position is genuinely unknown and
  // says so.
  const measured = s.reading_valid && s.output_deg !== null;
  if (measured) {
    state.readFailures = 0;
    state.lastKnownDeg = s.output_deg;
    state.lastMeasured = s;
  } else {
    state.readFailures += 1;
  }
  const known = measured || ((state.readFailures < FAILURES_BEFORE_ALARM)
                             && (state.lastKnownDeg !== null));
  const deg = measured ? s.output_deg : state.lastKnownDeg;
  $("posN").textContent = known ? deg.toFixed(1) : "—";
  const pct = known ? Math.min(100, Math.max(0, (deg / 360) * 100)) : 0;
  $("posBar").style.width = pct + "%";
  /* An empty track is what a genuine reading at the datum looks like,
     so collapsing the bar to 0 on an unknown read says "at zero" in
     exactly the way the numeric readout is careful not to. The track
     itself has to show that it is not reporting. */
  $("posTrack").classList.toggle("unknown", !known);

  // Everything below this line describes the SERVO, and on a failed read
  // the servo described nothing. temperature, voltage, current and
  // torque arrive as 0.0 from the empty snapshot, and `moving` and the
  // six fault flags arrive as false - so an unanswered read used to
  // render "0.00 V" and "HOLDING" with every lamp reading OK, next to a
  // position that honestly said unknown. It looked like a servo that had
  // lost power while sitting still and healthy, and none of it was
  // measured (D16).
  //
  // The API now sends null for the four readings. Rendering follows the
  // position's own pacing rather than inventing a second rule: hold the
  // last MEASURED values through a blip, blank once the reading is
  // genuinely unknown. D9 is what two definitions of one baseline cost.
  const shown = measured ? s : (known ? state.lastMeasured : null);
  const num = (value, places) =>
    (shown && value !== null && value !== undefined)
      ? value.toFixed(places) : "—";

  $("vTemp").textContent = num(shown && shown.temperature_c, 1);
  $("vVolt").textContent = num(shown && shown.voltage_v, 2);
  $("vCur").textContent = num(shown && shown.current_a, 2);
  $("vTorq").textContent = num(shown && shown.torque_kgcm, 1);

  const anyFault = !!shown && (shown.overload || shown.overcurrent ||
                   shown.overheat || shown.voltage_fault ||
                   shown.sensor_fault || shown.angle_fault);
  const chip = $("movechip");
  if (!shown) { chip.className = "chip"; chip.textContent = "—"; }
  else if (anyFault) { chip.className = "chip alarm"; chip.textContent = "FAULT"; }
  else if (shown.moving) { chip.className = "chip moving"; chip.textContent = "MOVING"; }
  else if (s.settling) { chip.className = "chip"; chip.textContent = "SETTLING"; }
  else { chip.className = "chip holding"; chip.textContent = "HOLDING"; }

  /* null, not false: "no fault reported" and "nothing was reported" are
     different things, and a green OK lamp is a claim either way. */
  const flag = (name) => shown ? shown[name] : null;
  setFault("fOverload", flag("overload"));
  setFault("fOvercurrent", flag("overcurrent"));
  setFault("fOverheat", flag("overheat"));
  setFault("fVoltage", flag("voltage_fault"));
  setFault("fSensor", flag("sensor_fault"));
  setFault("fAngle", flag("angle_fault"));
  $("mTemp").classList.toggle("alarm", flag("overheat") === true);
  $("mVolt").classList.toggle("alarm", flag("voltage_fault") === true);
  $("mCur").classList.toggle("alarm",
                             flag("overcurrent") === true ||
                             flag("overload") === true);
  $("recoverwrap").hidden = flag("overload") !== true;

  const lock = $("lockCube");
  lock.classList.toggle("locked", s.locked);
  lock.textContent = s.locked ? "Locked" : "Lock";

  const cal = $("calCube");
  cal.classList.toggle("needcal", !s.position_verified);
  cal.textContent = "Calibrate";

  const slot = $("alarmslot");
  if (anyFault) {
    slot.className = "alarmslot alarm";
    slot.textContent = "\u25a0 ALARM \u00b7 " + faultName(shown) +
      (shown.overload ? " \u2014 torque cut back" : "");
  } else if (!known) {
    // Ranks above the unverified warning: an unset reference means the
    // shown angle may be wrong, a lost reading means there is no angle.
    slot.className = "alarmslot warn";
    slot.textContent =
      "\u25b2 Position unknown \u2014 the servo did not answer the last read";
  } else if (!s.position_verified) {
    slot.className = "alarmslot warn";
    slot.textContent =
      "\u25b2 Reference not set \u2014 press CALIBRATE at the physical home";
  } else {
    slot.className = "alarmslot";
    slot.innerHTML = '<span class="okdot"></span> No active alarms';
  }
}

/* `on` is true, false, or null for "the servo did not report".
   A green OK dot is a claim about the hardware; it must not be shown
   for a read that never answered (D16). */
function setFault(id, on) {
  const el = $(id);
  el.classList.toggle("on", on === true);
  el.classList.toggle("unknown", on === null);
  const s = el.querySelector(".s");
  if (on === true) s.textContent = "TRIP";
  else if (on === null) s.textContent = "—";
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
  "telemetry.exported": "export delivered",
};

/* backend timestamp is an ISO string ("2026-07-22T14:22:07"); parse as Date,
   fall back to the raw time part if parsing ever fails. */
function eventTime(e) {
  const raw = e.timestamp;
  const d = new Date(raw);
  if (!isNaN(d.getTime())) {
    return d.toLocaleTimeString("en-GB", { hour12: false });  /* 24-hour */
  }
  return typeof raw === "string" && raw.includes("T")
    ? raw.split("T")[1] : String(raw != null ? raw : "");
}

/* Renders the events list from data pushed by the SSE stream.
   The data shape matches EventListResponse: { events: [...] }. */
function renderEvents(data) {
  const items = data.events || data;
  const list = $("eventList");
  list.innerHTML = "";
  items.forEach((e) => {
    const row = document.createElement("div");
    row.className = "ev";
    const label = EVENT_LABELS[e.event] || e.event.split(".").pop();
    row.innerHTML =
      '<span class="tm">' + eventTime(e) + "</span>" +
      '<span class="nm">' + escapeHtml(label) + "</span>" +
      '<span class="ds">' + escapeHtml(e.message || "") + "</span>";
    list.appendChild(row);
  });
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
  } catch (err) { sayError(err); }
}
async function doStop() {
  clearNotice();
  try { await apiPost("/servo/stop"); /* success: no notice */ }
  catch (err) { sayError(err); }
}
async function toggleLock() {
  clearNotice();
  const current = state.lastState ? state.lastState.locked : false;
  try {
    await apiPost("/servo/lock", { locked: !current });
    /* success: no notice */
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
    fetchZeros();
  } catch (err) { sayError(err); }
}
async function doRecover() {
  clearNotice();
  try { await apiPost("/servo/recover"); /* success: no notice */ }
  catch (err) { sayError(err); }
}
async function doSave() {
  clearNotice();
  const name = await askText("Save position",
    "Name this position so it can be recalled later.", "Save");
  if (!name) return;
  try { await apiPost("/zeros/capture", { name: name }); /* success: no notice */ fetchZeros(); }
  catch (err) { sayError(err); }
}
async function doUse() {
  clearNotice();
  if (state.selectedZeroId == null) { say("select a position first", true); return; }
  try { await apiPost("/zeros/" + state.selectedZeroId + "/activate"); /* success: no notice */ fetchZeros(); }
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
  try { await apiDelete("/zeros/" + state.selectedZeroId); state.selectedZeroId = null; /* success: no notice */ fetchZeros(); }
  catch (err) { sayError(err); }
}
function formatLocalDatetimeInput(date) {
  const pad = (n) => String(n).padStart(2, "0");
  const y = date.getFullYear();
  const m = pad(date.getMonth() + 1);
  const d = pad(date.getDate());
  const hh = pad(date.getHours());
  const mm = pad(date.getMinutes());
  return `${y}-${m}-${d}T${hh}:${mm}`;
}

function setExportPreset(rangeKey) {
  const now = new Date();
  let past = new Date(now);
  if (rangeKey === "1h") past.setHours(past.getHours() - 1);
  else if (rangeKey === "6h") past.setHours(past.getHours() - 6);
  else if (rangeKey === "24h") past.setHours(past.getHours() - 24);
  else if (rangeKey === "7d") past.setDate(past.getDate() - 7);

  const fromEl = $("exportFrom");
  const toEl = $("exportTo");
  if (fromEl && toEl) {
    fromEl.value = formatLocalDatetimeInput(past);
    toEl.value = formatLocalDatetimeInput(now);
  }

  document.querySelectorAll(".preset-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.range === rangeKey);
  });
}

function parseBinaryTelemetry(buffer) {
  const view = new DataView(buffer);
  if (buffer.byteLength < 12) return [];
  const baseTs = view.getFloat64(0, true);
  const count = view.getUint32(8, true);

  const samples = [];
  let offset = 12;
  for (let i = 0; i < count && offset + 18 <= buffer.byteLength; i++) {
    const rawCounts = view.getUint16(offset, true);
    const outputDeg = view.getInt16(offset + 2, true) / 100.0;
    const tempC = view.getInt16(offset + 4, true) / 100.0;
    const voltageV = view.getUint16(offset + 6, true) / 100.0;
    const currentA = view.getUint16(offset + 8, true) / 100.0;
    const torque = view.getInt16(offset + 10, true) / 100.0;
    const flags = view.getUint8(offset + 12);
    const dtMs = view.getUint32(offset + 13, true);
    offset += 18;

    samples.push({
      timestamp: baseTs + (dtMs / 1000.0),
      raw_counts: rawCounts,
      output_deg: outputDeg,
      temperature_c: tempC,
      voltage_v: voltageV,
      current_a: currentA,
      torque_kgcm: torque,
      moving: (flags & 1) !== 0,
      locked: (flags & 2) !== 0,
      overload: (flags & 4) !== 0,
      overcurrent: (flags & 8) !== 0,
      overheat: (flags & 16) !== 0,
      voltage_fault: (flags & 32) !== 0,
      sensor_fault: (flags & 64) !== 0,
      angle_fault: (flags & 128) !== 0,
    });
  }
  return samples;
}

function crc32(strOrUint8) {
  let table = window._crc32Table;
  if (!table) {
    table = new Uint32Array(256);
    for (let i = 0; i < 256; i++) {
      let c = i;
      for (let k = 0; k < 8; k++) {
        c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
      }
      table[i] = c;
    }
    window._crc32Table = table;
  }
  let crc = -1;
  const process = (data) => {
    const bytes = typeof data === "string" ? new TextEncoder().encode(data) : data;
    for (let i = 0; i < bytes.length; i++) {
      crc = (crc >>> 8) ^ table[(crc ^ bytes[i]) & 0xff];
    }
  };
  if (Array.isArray(strOrUint8)) {
    for (const chunk of strOrUint8) process(chunk);
  } else {
    process(strOrUint8);
  }
  return (crc ^ (-1)) >>> 0;
}

/* Raw DEFLATE (no zlib/gzip wrapper) - exactly what a ZIP local file
   header's compression-method-8 entry expects. Native browser API, no
   library. */
async function deflateRaw(bytes) {
  const cs = new CompressionStream("deflate-raw");
  const writer = cs.writable.getWriter();
  writer.write(bytes);
  writer.close();
  return new Uint8Array(await new Response(cs.readable).arrayBuffer());
}

/* entries: array of [filename, content]. `content` may be a string,
   Uint8Array/ArrayBuffer, array of chunks (as before) - OR a zero-arg
   function that PRODUCES the content when called. Day-sheet content is
   passed as a function so only one day's uncompressed XML string exists
   in memory at a time: built, compressed, written, then eligible for GC
   before the next one is built - a 30-day export no longer needs the
   whole range's raw text resident at once (board/browser-measured: 5 days
   uncompressed hit 475MB and 15 days exhausted a 4GB heap before this). */
async function createZipArchive(entries) {
  const enc = new TextEncoder();
  const fileEntries = [];
  let offset = 0;
  const parts = [];

  for (const [filename, contentOrFn] of entries) {
    const content = typeof contentOrFn === "function" ? contentOrFn() : contentOrFn;
    const filenameBytes = enc.encode(filename);

    let rawBytes;
    if (Array.isArray(content)) {
      let total = 0;
      const chunks = content.map((c) => {
        const b = typeof c === "string" ? enc.encode(c) : c;
        total += b.length;
        return b;
      });
      rawBytes = new Uint8Array(total);
      let o = 0;
      for (const b of chunks) { rawBytes.set(b, o); o += b.length; }
    } else {
      rawBytes = typeof content === "string" ? enc.encode(content) : new Uint8Array(content);
    }

    const crc = crc32(rawBytes);
    const uncompressedSize = rawBytes.length;
    const compressed = await deflateRaw(rawBytes);
    const compressedSize = compressed.length;

    const lh = new ArrayBuffer(30 + filenameBytes.length);
    const v = new DataView(lh);
    v.setUint32(0, 0x04034b50, true);
    v.setUint16(4, 20, true);
    v.setUint16(6, 0, true);
    v.setUint16(8, 8, true);          /* compression method: deflate */
    v.setUint16(10, 0, true);
    v.setUint16(12, 0, true);
    v.setUint32(14, crc, true);
    v.setUint32(18, compressedSize, true);
    v.setUint32(22, uncompressedSize, true);
    v.setUint16(26, filenameBytes.length, true);
    v.setUint16(28, 0, true);

    const lhArr = new Uint8Array(lh);
    lhArr.set(filenameBytes, 30);

    fileEntries.push({ filenameBytes, crc, compressedSize, uncompressedSize, offset });
    parts.push(lhArr, compressed);
    offset += lhArr.length + compressedSize;
  }

  const cdStart = offset;
  for (const entry of fileEntries) {
    const cd = new ArrayBuffer(46 + entry.filenameBytes.length);
    const v = new DataView(cd);
    v.setUint32(0, 0x02014b50, true);
    v.setUint16(4, 20, true);
    v.setUint16(6, 20, true);
    v.setUint16(8, 8, true);          /* compression method: deflate */
    v.setUint16(10, 0, true);
    v.setUint16(12, 0, true);
    v.setUint16(14, 0, true);
    v.setUint32(16, entry.crc, true);
    v.setUint32(20, entry.compressedSize, true);
    v.setUint32(24, entry.uncompressedSize, true);
    v.setUint16(28, entry.filenameBytes.length, true);
    v.setUint16(30, 0, true);
    v.setUint16(32, 0, true);
    v.setUint16(34, 0, true);
    v.setUint16(36, 0, true);
    v.setUint32(38, 0, true);
    v.setUint32(42, entry.offset, true);

    const cdArr = new Uint8Array(cd);
    cdArr.set(entry.filenameBytes, 46);

    parts.push(cdArr);
    offset += cdArr.length;
  }

  const cdSize = offset - cdStart;
  const eocd = new ArrayBuffer(22);
  const ev = new DataView(eocd);
  ev.setUint32(0, 0x06054b50, true);
  ev.setUint16(4, 0, true);
  ev.setUint16(6, 0, true);
  ev.setUint16(8, fileEntries.length, true);
  ev.setUint16(10, fileEntries.length, true);
  ev.setUint32(12, cdSize, true);
  ev.setUint32(16, cdStart, true);
  ev.setUint16(20, 0, true);

  parts.push(new Uint8Array(eocd));
  return new Blob(parts, { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
}

/* Charts read from a bounded, downsampled block on a hidden ChartData
   sheet, never from the raw day sheets - each cell there is a formula
   pointing at the exact day-sheet cell it was picked from (min-max
   binning, see minMaxDownsampleRefs), so the chart is genuinely fetching
   from the day sheets, live, without holding one giant series. */
const CHART_DOWNSAMPLE_MAX_POINTS = 2000;
const DAY_SHEET_COLS = { output_deg: "C", temperature_c: "D", voltage_v: "E",
                         current_a: "F", torque_kgcm: "G", interval: "I" };

function groupSamplesByDay(samples) {
  const days = [];
  const index = new Map();
  for (const s of samples) {
    const dateStr = new Date(s.timestamp * 1000).toISOString().slice(0, 10);
    let day = index.get(dateStr);
    if (!day) {
      day = { dateStr, samples: [] };
      index.set(dateStr, day);
      days.push(day);
    }
    day.samples.push(s);
  }
  return days;
}

/* Attaches interval-since-previous-sample to each sample in place, and
   returns the peak/sustained figures - computed once, over the FULL
   dataset, never the downsampled one (R5: numbers are never downsampled,
   only the charted series is). */
function computeStatsAndIntervals(samples) {
  let prevTs = null, stallCount = 0, maxInterval = 0.0;
  let peakTorque = 0.0, peakCurrent = 0.0, maxTemp = -999.0, minTemp = 999.0;
  let minVoltage = 999.0, maxVoltage = 0.0, minAngle = 999.0, maxAngle = -999.0;
  const faultCounts = { overload: 0, overcurrent: 0, overheat: 0, voltage: 0, sensor: 0, angle: 0 };
  samples.forEach((s) => {
    const interval = prevTs !== null ? Math.round((s.timestamp - prevTs) * 1000) / 1000 : 0.0;
    s.interval = interval;
    prevTs = s.timestamp;
    maxInterval = Math.max(maxInterval, interval);
    if (interval >= 9.0) stallCount++;
    peakTorque = Math.max(peakTorque, s.torque_kgcm);
    peakCurrent = Math.max(peakCurrent, s.current_a);
    maxTemp = Math.max(maxTemp, s.temperature_c);
    minTemp = Math.min(minTemp, s.temperature_c);
    minVoltage = Math.min(minVoltage, s.voltage_v);
    maxVoltage = Math.max(maxVoltage, s.voltage_v);
    minAngle = Math.min(minAngle, s.output_deg);
    maxAngle = Math.max(maxAngle, s.output_deg);
    if (s.overload) faultCounts.overload++;
    if (s.overcurrent) faultCounts.overcurrent++;
    if (s.overheat) faultCounts.overheat++;
    if (s.voltage_fault) faultCounts.voltage++;
    if (s.sensor_fault) faultCounts.sensor++;
    if (s.angle_fault) faultCounts.angle++;
  });
  if (samples.length === 0) {
    maxTemp = minTemp = minVoltage = maxVoltage = minAngle = maxAngle = 0.0;
  }
  return { stallCount, maxInterval, peakTorque, peakCurrent, maxTemp, minTemp,
           minVoltage, maxVoltage, minAngle, maxAngle, faultCounts };
}

/* Min-max binning over the flattened (day, row) sequence: for each bin,
   keeps the highest and lowest sample of `field` - preserves spikes and
   faults, which matter more here than a smooth-looking average would.
   Returns refs {dayIdx, row}, in ascending row order, ready to become
   formula cells. */
function minMaxDownsampleRefs(days, field) {
  const flat = [];
  days.forEach((day, dayIdx) => {
    day.samples.forEach((s, i) => flat.push({ value: s[field], ts: s.timestamp, dayIdx, row: i + 2 }));
  });
  const n = flat.length;
  if (n === 0) return [];
  if (n <= CHART_DOWNSAMPLE_MAX_POINTS) return flat;
  const bins = Math.max(1, Math.floor(CHART_DOWNSAMPLE_MAX_POINTS / 2));
  const binSize = Math.ceil(n / bins);
  const picked = [];
  for (let start = 0; start < n; start += binSize) {
    const end = Math.min(n, start + binSize);
    let lo = flat[start], hi = flat[start];
    for (let i = start; i < end; i++) {
      if (flat[i].value < lo.value) lo = flat[i];
      if (flat[i].value > hi.value) hi = flat[i];
    }
    if (lo === hi) picked.push(lo);
    else if (lo.row <= hi.row) picked.push(lo, hi);
    else picked.push(hi, lo);
  }
  return picked;
}

function dayCellRef(days, ref, colLetter) {
  return `'${days[ref.dayIdx].dateStr}'!${colLetter}${ref.row}`;
}

/* Excel stores dates as a serial number: days since 1899-12-30, fractional
   part is time-of-day. 25569 is the number of days between that epoch and
   the Unix epoch (1970-01-01) - the standard conversion constant. Storing
   this instead of a spelled-out ISO text string (which needed its own
   verbose inlineStr XML wrapper) is both smaller AND a real Excel date -
   sortable/filterable natively, not a lookalike string. */
function excelSerialDate(unixSeconds) {
  return unixSeconds / 86400 + 25569;
}

/* Same bit layout export_binary_stream already uses server-side
   (telemetry_service.py) - one encoding, not a second one invented here. */
function packFlags(s) {
  return (s.moving ? 1 : 0) | (s.locked ? 2 : 0) | (s.overload ? 4 : 0) |
    (s.overcurrent ? 8 : 0) | (s.overheat ? 16 : 0) | (s.voltage_fault ? 32 : 0) |
    (s.sensor_fault ? 64 : 0) | (s.angle_fault ? 128 : 0);
}

const RAW_HEADERS = [
  "Timestamp", "Raw Counts", "Output Angle (deg)", "Temperature (C)",
  "Voltage (V)", "Current (A)", "Torque (kg.cm)", "Flags (bit0=moving,1=locked,2=overload,3=overcurrent,4=overheat,5=voltage,6=sensor,7=angle)",
  "Interval (s)"
];
const RAW_COLS = ["A","B","C","D","E","F","G","H","I"];
const TIMESTAMP_COL = "A";

/* One worksheet per day, full resolution - this is the raw form; nothing
   downsamples it, and there is no row cap, so a day is always well under
   Excel's 1,048,576-row ceiling regardless of range length or sample rate.
   Values rounded to 2 decimals: the sensor data itself is only ever
   accurate to that (see telemetry_service.py's *100-then-int packing) -
   writing more digits is false precision, not more information. */
function makeDaySheetXml(day) {
  const hRowXml = `<row r="1" ht="20" customHeight="1">` +
    RAW_HEADERS.map((h, i) => `<c r="${RAW_COLS[i]}1" t="inlineStr" s="1"><is><t>${h}</t></is></c>`).join("") +
    `</row>`;
  let body = "";
  day.samples.forEach((s, idx) => {
    const r = idx + 2;
    body += `<row r="${r}">` +
      `<c r="A${r}" s="2"><v>${excelSerialDate(s.timestamp)}</v></c>` +
      `<c r="B${r}"><v>${s.raw_counts}</v></c>` +
      `<c r="C${r}"><v>${Math.round(s.output_deg * 100) / 100}</v></c>` +
      `<c r="D${r}"><v>${Math.round(s.temperature_c * 100) / 100}</v></c>` +
      `<c r="E${r}"><v>${Math.round(s.voltage_v * 100) / 100}</v></c>` +
      `<c r="F${r}"><v>${Math.round(s.current_a * 100) / 100}</v></c>` +
      `<c r="G${r}"><v>${Math.round(s.torque_kgcm * 100) / 100}</v></c>` +
      `<c r="H${r}"><v>${packFlags(s)}</v></c>` +
      `<c r="I${r}"><v>${Math.round(s.interval * 1000) / 1000}</v></c>` +
      `</row>`;
  });
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n` +
    `<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">\n` +
    `<sheetData>${hRowXml}${body}</sheetData>\n</worksheet>`;
}

const CHART_FIELDS = [
  { key: "output_deg", title: "Measured Output Angle", axis: "Degrees (deg)", color: "FF9900" },
  { key: "torque_kgcm", title: "Shaft Torque Load", axis: "kg.cm", color: "FF9900" },
  { key: "current_a", title: "Electrical Current Draw", axis: "Amperes", color: "7077A1" },
  { key: "temperature_c", title: "Motor Temperature", axis: "Celsius", color: "C0392B" },
  { key: "voltage_v", title: "Supply Voltage", axis: "Volts", color: "4A7C59" },
  { key: "interval", title: "Sampler Interval Jitter", axis: "Seconds", color: "7077A1" },
];

/* Builds the hidden ChartData sheet: one (timestamp, value) formula-cell
   pair of columns per chart field, each cell a live reference into a day
   sheet - not a value, so editing a day sheet updates the chart. Bounded
   to CHART_DOWNSAMPLE_MAX_POINTS rows per field regardless of range. */
function makeChartDataSheetXml(days) {
  const colPairs = CHART_FIELDS.map((_, i) => [
    RAW_COLS[i * 2] || String.fromCharCode(65 + i * 2),
    RAW_COLS[i * 2 + 1] || String.fromCharCode(65 + i * 2 + 1),
  ]);
  let maxRows = 0;
  const perField = CHART_FIELDS.map((f) => {
    const refs = minMaxDownsampleRefs(days, f.key === "interval" ? "interval" : f.key);
    maxRows = Math.max(maxRows, refs.length);
    return refs;
  });

  let hRow = `<row r="1">`;
  CHART_FIELDS.forEach((f, i) => {
    const [tsCol, valCol] = colPairs[i];
    hRow += `<c r="${tsCol}1" t="inlineStr"><is><t>${f.title} - time</t></is></c>` +
            `<c r="${valCol}1" t="inlineStr"><is><t>${f.title}</t></is></c>`;
  });
  hRow += `</row>`;

  let body = "";
  for (let r = 0; r < maxRows; r++) {
    const rowN = r + 2;
    let rowXml = `<row r="${rowN}">`;
    CHART_FIELDS.forEach((f, i) => {
      const refs = perField[i];
      if (r >= refs.length) return;
      const ref = refs[r];
      const valCol = f.key === "interval" ? DAY_SHEET_COLS.interval : DAY_SHEET_COLS[f.key];
      const [tsColOut, valColOut] = colPairs[i];
      /* Formula AND cached value on every cell - real Excel output never
         ships a formula alone (confirmed against a reference file), and
         a renderer that doesn't recalculate on open (some OnlyOffice/
         LibreOffice paths) would otherwise show these blank. */
      /* Cached value must match what the day-sheet cell actually holds
         (an Excel serial date now, not raw Unix seconds) - otherwise the
         cache and the live formula would disagree the moment anything
         recalculates. */
      rowXml += `<c r="${tsColOut}${rowN}" s="2"><f>${dayCellRef(days, ref, TIMESTAMP_COL)}</f><v>${excelSerialDate(ref.ts)}</v></c>` +
                `<c r="${valColOut}${rowN}"><f>${dayCellRef(days, ref, valCol)}</f><v>${ref.value}</v></c>`;
    });
    rowXml += `</row>`;
    body += rowXml;
  }

  return {
    xml: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n` +
      `<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">\n` +
      `<sheetData>${hRow}${body}</sheetData>\n</worksheet>`,
    colPairs,
    maxRows,
    perField,
  };
}

/* Real, verified OOXML chart structure - generated with XlsxWriter and
   unzipped to confirm the exact schema, not guessed from documentation
   (the previous session's version of this function was never written at
   all: every call to makeChartXml/makeDrawingXml threw ReferenceError). */
function numCacheXml(values) {
  const pts = values.map((v, i) => `<c:pt idx="${i}"><c:v>${v}</c:v></c:pt>`).join("");
  return `<c:numCache><c:formatCode>General</c:formatCode><c:ptCount val="${values.length}"/>${pts}</c:numCache>`;
}

function makeChartXml(title, axisTitle, seriesName, colorHex, catFormula, valFormula,
                      catCache, valCache) {
  /* Cache embedded alongside the reference, matching real Excel output -
     a renderer that shows the chart before/without resolving cross-sheet
     formulas (some OnlyOffice/LibreOffice paths) still has something
     correct to draw. */
  const catCacheXml = catCache ? numCacheXml(catCache) : "";
  const valCacheXml = valCache ? numCacheXml(valCache) : "";
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<c:chart>
<c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr/></a:pPr><a:r><a:rPr lang="en-US"/><a:t>${title}</a:t></a:r></a:p></c:rich></c:tx><c:layout/></c:title>
<c:plotArea><c:layout/>
<c:lineChart><c:grouping val="standard"/>
<c:ser><c:idx val="0"/><c:order val="0"/><c:tx><c:v>${seriesName}</c:v></c:tx>
<c:spPr><a:ln><a:solidFill><a:srgbClr val="${colorHex}"/></a:solidFill></a:ln></c:spPr>
<c:marker><c:symbol val="none"/></c:marker>
<c:cat><c:numRef><c:f>${catFormula}</c:f>${catCacheXml}</c:numRef></c:cat>
<c:val><c:numRef><c:f>${valFormula}</c:f>${valCacheXml}</c:numRef></c:val>
</c:ser>
<c:axId val="111111111"/><c:axId val="222222222"/>
</c:lineChart>
<c:catAx><c:axId val="111111111"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:delete val="0"/><c:axPos val="b"/><c:crossAx val="222222222"/></c:catAx>
<c:valAx><c:axId val="222222222"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:delete val="0"/><c:axPos val="l"/><c:crossAx val="111111111"/><c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>${axisTitle}</a:t></a:r></a:p></c:rich></c:tx></c:title></c:valAx>
</c:plotArea>
<c:legend><c:legendPos val="b"/></c:legend>
<c:plotVisOnly val="1"/>
</c:chart>
</c:chartSpace>`;
}

/* Anchors: [{rId, fromCol, fromRow, toCol, toRow}]. One drawing part can
   anchor several charts on the same sheet - used to lay all 6 charts on
   the Overview sheet in a 2-column grid. */
function makeDrawingXml(anchors) {
  const frames = anchors.map((a, i) =>
    `<xdr:twoCellAnchor><xdr:from><xdr:col>${a.fromCol}</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>${a.fromRow}</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:from><xdr:to><xdr:col>${a.toCol}</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>${a.toRow}</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:to><xdr:graphicFrame macro=""><xdr:nvGraphicFramePr><xdr:cNvPr id="${i + 2}" name="Chart ${i + 1}"/><xdr:cNvGraphicFramePr/></xdr:nvGraphicFramePr><xdr:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/></xdr:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart"><c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" r:id="${a.rId}"/></a:graphicData></a:graphic></xdr:graphicFrame><xdr:clientData/></xdr:twoCellAnchor>`
  ).join("");
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n` +
    `<xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/spreadsheetml/2006/spreadsheetDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">\n` +
    `${frames}\n</xdr:wsDr>`;
}

function makeOverviewSheetXml(days, samples, stats) {
  const dtStart = new Date(samples[0]?.timestamp * 1000 || 0).toISOString().replace("T", " ").slice(0, 16) + " UTC";
  const dtEnd = new Date(samples[samples.length - 1]?.timestamp * 1000 || 0).toISOString().replace("T", " ").slice(0, 16) + " UTC";
  const totalFaults = Object.values(stats.faultCounts).reduce((a, b) => a + b, 0);
  const rows = [
    ["Total samples", String(samples.length)],
    ["Days covered", String(days.length)],
    ["Window start", dtStart],
    ["Window end", dtEnd],
    ["Physical range", `${stats.minAngle.toFixed(2)} to ${stats.maxAngle.toFixed(2)} deg`],
    ["Peak torque", `${stats.peakTorque.toFixed(2)} kg.cm`],
    ["Peak current", `${stats.peakCurrent.toFixed(2)} A`],
    ["Temperature range", `${stats.minTemp.toFixed(1)} - ${stats.maxTemp.toFixed(1)} C`],
    ["Voltage range", `${stats.minVoltage.toFixed(2)} - ${stats.maxVoltage.toFixed(2)} V`],
    ["Sampler stalls (>= 9s gap)", String(stats.stallCount)],
    ["Max sampler interval", `${stats.maxInterval.toFixed(3)} s`],
    ["Fault trips (any type)", String(totalFaults)],
  ];
  let body = `<row r="1"><c r="A1" t="inlineStr"><is><t>Servo Telemetry Export - Summary</t></is></c></row>`;
  rows.forEach(([k, v], idx) => {
    const r = idx + 3;
    body += `<row r="${r}"><c r="A${r}" t="inlineStr"><is><t>${k}</t></is></c>` +
            `<c r="B${r}" t="inlineStr"><is><t>${v}</t></is></c></row>`;
  });
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n` +
    `<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">\n` +
    `<sheetData>${body}</sheetData>\n<drawing r:id="rId1"/>\n</worksheet>`;
}

async function generateExcelXlsxZip(samples, fromTs, toTs) {
  const stats = computeStatsAndIntervals(samples);
  const days = groupSamplesByDay(samples);
  const chartData = makeChartDataSheetXml(days);
  const overviewXml = makeOverviewSheetXml(days, samples, stats);
  /* Day-sheet XML is NOT built here - each is built lazily, one at a
     time, inside the filesMap entries below, so createZipArchive can
     compress and discard one day's text before building the next
     rather than holding every day's raw XML in memory simultaneously. */

  const chartXmls = CHART_FIELDS.map((f, i) => {
    const [tsCol, valCol] = chartData.colPairs[i];
    const lastRow = chartData.maxRows + 1;
    const refs = chartData.perField[i];
    return makeChartXml(f.title, f.axis, f.title, f.color,
                        `ChartData!$${tsCol}$2:$${tsCol}$${lastRow}`,
                        `ChartData!$${valCol}$2:$${valCol}$${lastRow}`,
                        refs.map((r) => excelSerialDate(r.ts)), refs.map((r) => r.value));
  });
  const drawing1Xml = makeDrawingXml(
    chartXmls.map((_, i) => ({ rId: `rId${i + 1}`, fromCol: (i % 2) * 8, fromRow: 1 + Math.floor(i / 2) * 15,
                               toCol: (i % 2) * 8 + 7, toRow: 1 + Math.floor(i / 2) * 15 + 14 })));

  const stylesXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="1">
  <numFmt numFmtId="164" formatCode="yyyy-mm-dd hh:mm:ss"/>
</numFmts>
<fonts count="2">
  <font><sz val="10"/><name val="Calibri"/></font>
  <font><b/><sz val="10"/><name val="Calibri"/></font>
</fonts>
<fills count="1"><fill><patternFill patternType="none"/></fill></fills>
<borders count="1"><border/></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="3">
  <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
  <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>
  <xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
</cellXfs>
</styleSheet>`;

  /* Sheet order: Overview (charts), ChartData (hidden, formula-fed),
     then one sheet per day. Workbook-level rIds and part filenames are
     assigned in that order, 1-based. */
  const daySheetCount = days.length;
  const overviewSheetNum = 1;
  const chartDataSheetNum = 2;
  const firstDaySheetNum = 3;

  const contentTypeOverrides = [
    `<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>`,
    `<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>`,
  ];
  for (let i = 1; i <= 2 + daySheetCount; i++) {
    contentTypeOverrides.push(`<Override PartName="/xl/worksheets/sheet${i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`);
  }
  contentTypeOverrides.push(`<Override PartName="/xl/drawings/drawing1.xml" ContentType="application/vnd.openxmlformats-officedocument.drawing+xml"/>`);
  chartXmls.forEach((_, i) => contentTypeOverrides.push(`<Override PartName="/xl/charts/chart${i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.chart+xml"/>`));

  const workbookSheets = [
    `<sheet name="Overview" sheetId="1" r:id="rId${overviewSheetNum}"/>`,
    `<sheet name="ChartData" sheetId="2" r:id="rId${chartDataSheetNum}" state="hidden"/>`,
  ];
  days.forEach((d, i) => {
    workbookSheets.push(`<sheet name="${d.dateStr}" sheetId="${3 + i}" r:id="rId${firstDaySheetNum + i}"/>`);
  });

  const workbookRels = [];
  for (let i = 1; i <= 2 + daySheetCount; i++) {
    workbookRels.push(`<Relationship Id="rId${i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${i}.xml"/>`);
  }
  workbookRels.push(`<Relationship Id="rId${3 + daySheetCount}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>`);

  const fileEntries = [
    ["[Content_Types].xml", `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n` +
      `<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n` +
      `<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n` +
      `<Default Extension="xml" ContentType="application/xml"/>\n` +
      contentTypeOverrides.join("\n") + `\n</Types>`],
    ["_rels/.rels", `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>`],
    ["xl/workbook.xml", `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n` +
      `<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">\n` +
      `<sheets>\n${workbookSheets.join("\n")}\n</sheets>\n` +
      /* ChartData's cells are formulas with no cached <v> - force a full
         recalc on open so they (and the charts reading them) are
         populated immediately, not left blank until manual recalc. */
      `<calcPr calcId="0" fullCalcOnLoad="1"/>\n</workbook>`],
    ["xl/_rels/workbook.xml.rels", `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n` +
      `<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n` +
      workbookRels.join("\n") + `\n</Relationships>`],
    [`xl/worksheets/_rels/sheet${overviewSheetNum}.xml.rels`, `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing1.xml"/>
</Relationships>`],
    ["xl/drawings/_rels/drawing1.xml.rels", `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n` +
      `<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n` +
      chartXmls.map((_, i) => `<Relationship Id="rId${i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="../charts/chart${i + 1}.xml"/>`).join("\n") +
      `\n</Relationships>`],
    ["xl/styles.xml", stylesXml],
    [`xl/worksheets/sheet${overviewSheetNum}.xml`, overviewXml],
    [`xl/worksheets/sheet${chartDataSheetNum}.xml`, chartData.xml],
    ["xl/drawings/drawing1.xml", drawing1Xml],
  ];
  days.forEach((d, i) => {
    fileEntries.push([`xl/worksheets/sheet${firstDaySheetNum + i}.xml`, () => makeDaySheetXml(d)]);
  });
  chartXmls.forEach((xml, i) => {
    fileEntries.push([`xl/charts/chart${i + 1}.xml`, xml]);
  });

  return await createZipArchive(fileEntries);
}

async function doExport() {
  clearNotice();
  const fromEl = $("exportFrom");
  const toEl = $("exportTo");

  let fromTs = 0;
  let toTs = Math.floor(Date.now() / 1000);

  if (fromEl && fromEl.value) {
    const d = new Date(fromEl.value);
    if (!isNaN(d.getTime())) fromTs = Math.floor(d.getTime() / 1000);
  } else {
    fromTs = toTs - 24 * 3600;
  }

  if (toEl && toEl.value) {
    const d = new Date(toEl.value);
    if (!isNaN(d.getTime())) toTs = Math.floor(d.getTime() / 1000);
  }

  if (fromTs >= toTs) {
    sayError(new Error("Start time must be earlier than end time"));
    return;
  }

  const btn = $("exportBtn");
  const fillEl = $("exportFill");
  const labelEl = $("exportLabel");
  const origText = labelEl.textContent;

  btn.classList.add("exporting");
  btn.disabled = true;
  fillEl.style.width = "0%";
  labelEl.textContent = "Downloading stream…";

  try {
    const url = API + "/telemetry/binary?from=" + fromTs + "&to=" + toTs;
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Export failed with HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const chunks = [];
    let receivedBytes = 0;
    let totalUncompressedBytes = Math.max(1, (toTs - fromTs) * 18 + 12);

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      receivedBytes += value.length;

      if (chunks.length === 1 && value.length >= 12) {
        const view = new DataView(value.buffer, value.byteOffset, value.byteLength);
        const sampleCount = view.getUint32(8, true);
        if (sampleCount > 0) {
          totalUncompressedBytes = (sampleCount * 18) + 12;
        }
      }

      const recKb = Math.round(receivedBytes / 1024);
      const totKb = Math.round(totalUncompressedBytes / 1024);
      const pct = Math.min(85, Math.round((receivedBytes / totalUncompressedBytes) * 85));

      labelEl.textContent = "Downloaded " + recKb + " / " + totKb + " KB (" + pct + "%)";
      fillEl.style.width = pct + "%";
    }

    labelEl.textContent = "Compiling .xlsx workbook…";
    fillEl.style.width = "90%";

    const totalLen = chunks.reduce((acc, c) => acc + c.length, 0);
    const fullBuffer = new Uint8Array(totalLen);
    let offset = 0;
    for (const chunk of chunks) {
      fullBuffer.set(chunk, offset);
      offset += chunk.length;
    }

    const samples = parseBinaryTelemetry(fullBuffer.buffer);
    const xlsxBlob = await generateExcelXlsxZip(samples, fromTs, toTs);

    fillEl.style.width = "100%";
    labelEl.textContent = "Saving file…";

    const downloadUrl = window.URL.createObjectURL(xlsxBlob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = downloadUrl;

    const fromDateStr = new Date(fromTs * 1000).toISOString().slice(0, 10);
    const toDateStr = new Date(toTs * 1000).toISOString().slice(0, 10);
    a.download = `servo_telemetry_${fromDateStr}_to_${toDateStr}.xlsx`;

    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(downloadUrl);
    a.remove();
  } catch (err) {
    sayError(err);
  } finally {
    btn.classList.remove("exporting");
    btn.disabled = false;
    labelEl.textContent = origText;
  }
}

function nudge(inputId, delta) {
  const input = $(inputId);
  const value = parseFloat(input.value) || 0;
  const stepped = Math.round((value + delta) / ANGLE_STEP) * ANGLE_STEP;
  input.value = stepped.toFixed(2);
}

function bind(id, handler) {
  const el = $(id);
  if (!el) return;
  let inFlight = false;
  el.addEventListener("click", async () => {
    if (inFlight) return;              /* the second press never leaves */
    inFlight = true;
    el.disabled = true;
    el.classList.add("busy");
    flash(el);
    try {
      await handler();
    } finally {
      el.disabled = false;
      el.classList.remove("busy");
      inFlight = false;
    }
  });
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
  bind("exportBtn", doExport);

  setExportPreset("24h");
  document.querySelectorAll(".preset-btn").forEach((btn) => {
    btn.addEventListener("click", () => setExportPreset(btn.dataset.range));
  });

  document.querySelectorAll(".step").forEach((btn) => {
    btn.addEventListener("click", () =>
      nudge(btn.dataset.nudge, parseFloat(btn.dataset.d)));
  });

  /* Enter in the angle field is the tenth entry point, and it must go
     through the SAME guard as the button - it was the one path that
     escaped it. keydown auto-repeats, so holding Enter streamed moves
     onto the wire and spent a W5500 slot per repeat: the keyboard
     reproduced D15 exactly while the mouse was fixed. */
  $("inAngle").addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); $("moveBtn").click(); }
  });
}

function start() {
  initUi();
  connectStream();
}

document.addEventListener("DOMContentLoaded", start);
