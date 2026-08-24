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

/* Wires a control, and refuses a second press until the first answers.
 *
 * Every handler below awaits an HTTP round trip that can take up to the
 * Bridge's 10 s timeout. The only feedback was flash()'s 400 ms blink,
 * and success is deliberately silent - so for the remaining nine
 * seconds a command in flight looked exactly like one that had done
 * nothing. The operator pressed again, and the second press opened
 * another connection, spending another of the relay's six W5500 slots.
 * The UI's answer to slowness was feeding its cause (D15, D13).
 *
 * The guard lives here rather than in the handlers because this is the
 * one place all nine are wired, so a tenth added later inherits it.
 * `disabled` is what stops the press: it blocks the event outright
 * rather than relying on the handler to check, and it is what the
 * browser already renders as "not available now".
 *
 * The screen is a mouse-driven operator screen, confirmed 8 August
 * 2026 - so hover affordances are safe here. Revisit if that changes:
 * on a touch screen a tap leaves hover state stuck and the busy
 * styling would have to stand on its own.
 *
 * The guard covers the WHOLE handler, dialogs included, so a second
 * press cannot open a second confirm dialog on top of the first.
 *
 * The slow-command notice is NOT here. It belongs to the request, not
 * to the press: three of these handlers open a dialog first, so a timer
 * started on the click announced "the controller has not answered"
 * while the operator was still reading the confirmation - and the thing
 * that had not answered was the operator. It lives in request(). */
function bind(id, handler) {
  const el = $(id);
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
  bind("exportCube", doExport);

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
