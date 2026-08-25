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
  wasLocked: false,      /* edge-detects the lock RELEASE, for the
                            isolated-but-just-unlocked nudge */
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
  // Deliberately not a strict mirror of "locked"'s wording: naming the
  // state without the remedy leaves the operator in it with no way out
  // in view (D12's lesson - a state they can enter and not leave).
  isolated: "refused — motor is isolated; un-isolate to move",
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
  $("posN").textContent = known ? deg.toFixed(2) : "—";

  /* Scaled against the REACHABLE range the server just sent
     (output_min_deg/output_max_deg), not a fixed /360. Travel here is
     -90..+90 from a mid-travel datum, not a full turn: the old /360
     math rendered every negative angle as 0% (indistinguishable from
     resting at the datum) and never filled the positive half past a
     quarter of the bar - found while building the target marker, which
     needed a scale that actually matched reachable travel. Falls back
     to the client's own mirrored limits only if a state payload is
     somehow missing the range (older cached response). */
  const rangeMin = (typeof s.output_min_deg === "number") ? s.output_min_deg : ANGLE_MIN;
  const rangeMax = (typeof s.output_max_deg === "number") ? s.output_max_deg : ANGLE_MAX;
  const rangeSpan = (rangeMax - rangeMin) || 1;
  const toRangePct = (angle) =>
    Math.min(100, Math.max(0, ((angle - rangeMin) / rangeSpan) * 100));

  const pct = known ? toRangePct(deg) : 0;
  $("posBar").style.width = pct + "%";
  /* An empty track is what a genuine reading at the datum looks like,
     so collapsing the bar to 0 on an unknown read says "at zero" in
     exactly the way the numeric readout is careful not to. The track
     itself has to show that it is not reporting. */
  $("posTrack").classList.toggle("unknown", !known);

  // Target: independent of reading_valid - a target is still known when
  // the servo goes silent (unlike SERVO below, which mirrors the
  // measured position exactly). Never fabricated as 0.0 (D16 shape).
  const hasTarget = s.target_deg !== null && s.target_deg !== undefined;
  const marker = $("targetMarker");
  if (hasTarget) {
    marker.style.left = toRangePct(s.target_deg) + "%";
    marker.classList.add("show");
    marker.classList.toggle("stale", !!s.target_stale);
  } else {
    marker.classList.remove("show");
  }
  const targetItem = $("targetItem");
  $("targetVal").textContent = hasTarget
    ? s.target_deg.toFixed(2) + "°" + (s.target_stale ? " · STOPPED" : "")
    : "—";
  targetItem.classList.toggle("stale", !!s.target_stale);

  // Delta: the whole point of showing a target is seeing this number
  // without doing the subtraction by eye - blank whenever either side
  // is unknown, never computed against a fabricated value.
  const hasDelta = known && hasTarget;
  const deltaVal = hasDelta ? (s.target_deg - deg) : null;
  $("deltaVal").textContent = hasDelta
    ? (deltaVal > 0 ? "+" : "") + deltaVal.toFixed(2) + "°"
    : "—";
  $("deltaItem").classList.toggle("stale", !!s.target_stale);

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

  // Servo (pre-ratio) angle follows the measured position exactly - same
  // "shown" snapshot, same blanking pacing as temp/voltage/current/torque
  // above. It is a debug value, not an operator control.
  const servoText = num(shown && shown.servo_deg, 1);
  $("servoVal").textContent = servoText === "—" ? "—" : servoText + "°";

  // D25: a fault that WAS reported must not vanish just because the
  // reading has since gone unknown - before this, three failed reads
  // blanked `shown` to null, `anyFault` collapsed to false with it, and
  // the alarm banner + recover control both disappeared while the servo
  // was, as far as anyone knew, still overloaded. Deliberately
  // asymmetric with D16's rule, not a relaxation of it: a reported TRUE
  // (a real trip) is sticky and survives the reading going unknown; a
  // reported FALSE (healthy) is not carried forward past the known-
  // window - claiming "still OK" from stale data is exactly what D16
  // exists to prevent. Cleared only by a later fresh read that itself
  // reports the fault gone.
  const stickyFlag = (name) => {
    if (measured) return s[name];
    if (state.lastMeasured && state.lastMeasured[name] === true) return true;
    return known ? (shown ? shown[name] : null) : null;
  };
  const stickyFaults = {};
  for (const field of FAULT_FIELDS) stickyFaults[field.key] = stickyFlag(field.key);
  const faultIsStale = !measured &&
    FAULT_FIELDS.some((field) => stickyFaults[field.key] === true);

  const anyFault = FAULT_FIELDS.some((field) => stickyFaults[field.key] === true);
  const chip = $("movechip");
  // FAULT outranks everything (D25: an alarm must never vanish).
  // ISOLATED outranks MOVING/SETTLING/HOLDING: with drive torque cut,
  // "HOLDING" would assert the servo is actively holding position, when
  // friction (and, once fitted, the physical lock) is what's actually
  // doing that - the same shape of screen/reality gap D9 was about.
  if (!shown && !anyFault) { chip.className = "chip"; chip.textContent = "—"; }
  else if (anyFault) { chip.className = "chip alarm"; chip.textContent = "FAULT"; }
  else if (s.isolated) { chip.className = "chip isolated"; chip.textContent = "ISOLATED"; }
  else if (shown.moving) { chip.className = "chip moving"; chip.textContent = "MOVING"; }
  else if (s.settling) { chip.className = "chip"; chip.textContent = "SETTLING"; }
  else { chip.className = "chip holding"; chip.textContent = "HOLDING"; }

  /* null, not false: "no fault reported" and "nothing was reported" are
     different things, and a green OK lamp is a claim either way. */
  setFault("fOverload", stickyFaults.overload);
  setFault("fOvercurrent", stickyFaults.overcurrent);
  setFault("fOverheat", stickyFaults.overheat);
  setFault("fVoltage", stickyFaults.voltage_fault);
  setFault("fSensor", stickyFaults.sensor_fault);
  setFault("fAngle", stickyFaults.angle_fault);
  $("mTemp").classList.toggle("alarm", stickyFaults.overheat === true);
  $("mVolt").classList.toggle("alarm", stickyFaults.voltage_fault === true);
  $("mCur").classList.toggle("alarm",
                             stickyFaults.overcurrent === true ||
                             stickyFaults.overload === true);

  // Recover is genuinely unable to work without a known position -
  // MotionService.recover() re-commands the current position, and there
  // isn't one. Visible-but-disabled with the reason stated (D15's own
  // pattern for a control that must refuse) teaches the operator "still
  // wrong, can't act yet" - hidden would teach "the alarm is over",
  // which is exactly the false signal D25 is about.
  const recoverWrap = $("recoverwrap");
  const recoverBtn = $("recoverBtn");
  recoverWrap.hidden = stickyFaults.overload !== true;
  // Recover re-commands the present position, which needs drive torque -
  // meaningless while isolated. Same D15/D25 pattern as the position-
  // unknown case: visible, disabled, reason stated on the control itself.
  recoverBtn.disabled = !known || s.isolated;
  recoverBtn.title = s.isolated
    ? "Motor is isolated - un-isolate to recover"
    : known ? ""
    : "Position unknown - recover needs a known position to re-command";

  const lock = $("lockCube");
  lock.classList.toggle("locked", s.locked);
  lock.textContent = s.locked ? "Locked" : "Lock";
  if (!s.locked && s.isolated) {
    // The moment un-locking meets its actual limit: the operator just
    // freed movement, but the motor still won't move. Fires only on the
    // RELEASE edge, not every render, or it would repeat on every ~1s
    // poll for as long as both states hold.
    if (state.wasLocked) {
      say("Lock released — motor is still isolated; un-isolate to move.");
    }
  }
  state.wasLocked = s.locked;

  const cal = $("calCube");
  cal.classList.toggle("needcal", !s.position_verified);
  cal.textContent = "Calibrate";

  const iso = $("isoCube");
  iso.classList.toggle("isolated", s.isolated);
  iso.textContent = s.isolated ? "Isolated" : "Isolate";
  $("isoHint").textContent = "auto-isolates after " +
    Math.round(s.isolation_idle_timeout_s / 60) + " min locked";

  const slot = $("alarmslot");
  if (anyFault) {
    slot.className = "alarmslot alarm";
    slot.textContent = "\u25a0 ALARM \u00b7 " + faultName(stickyFaults) +
      (stickyFaults.overload ? " \u2014 torque cut back" : "") +
      (faultIsStale ? " (last known \u2014 position unknown)" : "");
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

/* The one list of fault flag -> label. faultName() (live event line, one
   name) and the export's decoded Faults column (all active names) both
   read this instead of each stating the mapping independently. */
const FAULT_FIELDS = [
  { key: "overload", label: "Overload" },
  { key: "overcurrent", label: "Overcurrent" },
  { key: "overheat", label: "Overheat" },
  { key: "voltage_fault", label: "Voltage fault" },
  { key: "sensor_fault", label: "Sensor fault" },
  { key: "angle_fault", label: "Angle fault" },
];

function faultName(s) {
  const hit = FAULT_FIELDS.find((f) => s[f.key]);
  return hit ? hit.label : "Fault";
}

/* Export use: every active fault, not just the first - a forensic
   reviewer of an unattended run needs to know all of them, not the
   single-line summary the live event log shows. "" (blank) when none,
   read the same way the Faults column reads: absence is normal. */
function decodedFaultNames(s) {
  return FAULT_FIELDS.filter((f) => s[f.key]).map((f) => f.label).join(", ");
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
        '<span class="deg">' + deg.toFixed(2) + "\u00b0</span>";
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
    /* Sent exactly as typed - the backend enforces the step (D32) and
       says so in its own words; silently rewriting it here would hide
       the correction from the operator instead of explaining it. */
    await apiPost("/servo/move", {
      target_deg: target,
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
async function toggleIsolate() {
  clearNotice();
  const current = state.lastState ? state.lastState.isolated : false;
  const next = !current;
  try {
    await apiPost("/servo/isolate", { isolated: next });
    // Deliberately NOT the usual "success: no notice" pattern: the
    // physical lock is manual and unsensed, so the software never knows
    // whether it's actually engaged either way - every isolate action
    // needs this reminder, not just the auto-triggered one.
    say(next
      ? "Motor isolated — physical lock is manual, confirm it's engaged."
      : "Motor isolation released.");
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

/* Mirrors SAMPLE_STRUCT/HEADER_STRUCT in telemetry_service.py exactly -
   a twin path; both sides move together, and this comment is the third
   statement of the format alongside the Python struct string and its
   own comment (a stale copy of this exact comment once disagreed with
   the real struct, see BACKLOG.md). Header is 16 bytes: base timestamp
   (f64), sample count (u32), servo-degrees-per-output-degree ratio
   (f32, signed by direction) - the one authoritative gear-ratio
   constant, received as data rather than restated as a second,
   hardcoded copy (ANGLE_STEP below is the OTHER angle constant this
   project already keeps in one place only). Sample is 20 bytes; byte 17
   is target_valid_flags, not a plain bool - bit0 is target_valid, bit1
   is motor isolation, sharing the byte rather than widening the sample
   (the flags byte at offset 12 has none left). */
const SERVO_RATIO_OFFSET = 12;
const HEADER_BYTES = 16;
const SAMPLE_BYTES = 20;

function parseBinaryTelemetry(buffer) {
  const view = new DataView(buffer);
  if (buffer.byteLength < HEADER_BYTES) return { samples: [], servoRatio: null };
  const baseTs = view.getFloat64(0, true);
  const count = view.getUint32(8, true);
  const servoRatio = view.getFloat32(SERVO_RATIO_OFFSET, true);

  const samples = [];
  let offset = HEADER_BYTES;
  for (let i = 0; i < count && offset + SAMPLE_BYTES <= buffer.byteLength; i++) {
    const rawCounts = view.getUint16(offset, true);
    const outputDeg = view.getInt16(offset + 2, true) / 100.0;
    const tempC = view.getInt16(offset + 4, true) / 100.0;
    const voltageV = view.getUint16(offset + 6, true) / 100.0;
    const currentA = view.getUint16(offset + 8, true) / 100.0;
    const torque = view.getInt16(offset + 10, true) / 100.0;
    const flags = view.getUint8(offset + 12);
    const dtMs = view.getUint32(offset + 13, true);
    const targetValidFlags = view.getUint8(offset + 17);
    const targetValid = (targetValidFlags & 1) !== 0;
    const isolated = (targetValidFlags & 2) !== 0;
    /* null, not 0.0, when no target was in effect - same rule as every
       other "did not answer" field in this contract (D16's shape). */
    const targetDeg = targetValid ? view.getInt16(offset + 18, true) / 100.0 : null;
    offset += SAMPLE_BYTES;

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
      target_deg: targetDeg,
      isolated: isolated,
      /* Servo (pre-ratio) angle is a pure function of output_deg and the
         one ratio carried in the header - computed here, not stored a
         second time on the wire or in the export (see BACKLOG.md R5). */
      servo_deg: servoRatio ? outputDeg * servoRatio : null,
    });
  }
  return { samples, servoRatio };
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
  /* Blob.stream().pipeThrough() instead of manually driving a writer:
     the earlier version called writer.write()/writer.close() without
     awaiting either, a real race that let the read side start before
     writing finished on some inputs - reproduced live, 23 August 2026:
     openpyxl rejected a real board-generated file with "Bad CRC-32 for
     [Content_Types].xml" even though it was the file's first, smallest
     entry. pipeThrough's spec-guaranteed backpressure/completion
     handling removes the race entirely rather than papering over one
     symptom of it. */
  const stream = new Blob([bytes]).stream().pipeThrough(new CompressionStream("deflate-raw"));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

/* entries: array of [filename, content]. `content` may be a string,
   Uint8Array/ArrayBuffer, array of chunks (as before) - OR a zero-arg
   function that PRODUCES the content when called. Day-sheet content is
   passed as a function so only one day's uncompressed XML string exists
   in memory at a time: built, compressed, written, then eligible for GC
   before the next one is built - a 30-day export no longer needs the
   whole range's raw text resident at once (board/browser-measured: 5 days
   uncompressed hit 475MB and 15 days exhausted a 4GB heap before this). */
async function createZipArchive(entries, onProgress) {
  const enc = new TextEncoder();
  const fileEntries = [];
  let offset = 0;
  const parts = [];
  let done = 0;

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
    done += 1;
    if (onProgress) onProgress(done, entries.length, filename);
  }

  const cdStart = offset;
  for (const entry of fileEntries) {
    const cd = new ArrayBuffer(46 + entry.filenameBytes.length);
    const v = new DataView(cd);
    v.setUint32(0, 0x02014b50, true);
    v.setUint16(4, 20, true);         /* version made by */
    v.setUint16(6, 20, true);         /* version needed to extract */
    v.setUint16(8, 0, true);          /* general purpose bit flag - was
                                          swapped with compression method
                                          below (real bug, reproduced live
                                          23 August 2026: every reader that
                                          honors the central directory,
                                          including openpyxl/zipfile and
                                          OnlyOffice, read flag=8 "data
                                          descriptor follows" and rejected
                                          the whole file; unzip's more
                                          lenient path masked it) */
    v.setUint16(10, 8, true);         /* compression method: deflate */
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
const DAY_SHEET_COLS = { output_deg: "C", servo_deg: "D", target_deg: "E",
                         temperature_c: "F", voltage_v: "G", current_a: "H",
                         torque_kgcm: "I", interval: "M" };

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

/* Per-day rows for the Overview table - "which day ran hot, which day
   stalled" (operator's ask: richer content than one whole-range number
   per stat). Derivable from data already grouped by day; no schema
   change, no new sampling. `days` already groups samples per calendar
   day (groupSamplesByDay), so this is one more pass over what is
   already in memory, not a second query. */
function computeDailyStats(days) {
  return days.map((day) => {
    const samples = day.samples;
    let peakTorque = 0, peakCurrent = 0, minTemp = 999, maxTemp = -999,
        minVoltage = 999, maxVoltage = 0, stallCount = 0, movingCount = 0,
        isolatedCount = 0,
        angleTravelled = 0, prevAngle = null, prevTs = null;
    samples.forEach((s) => {
      peakTorque = Math.max(peakTorque, s.torque_kgcm);
      peakCurrent = Math.max(peakCurrent, s.current_a);
      minTemp = Math.min(minTemp, s.temperature_c);
      maxTemp = Math.max(maxTemp, s.temperature_c);
      minVoltage = Math.min(minVoltage, s.voltage_v);
      maxVoltage = Math.max(maxVoltage, s.voltage_v);
      if (s.moving) movingCount += 1;
      if (s.isolated) isolatedCount += 1;
      if (prevTs !== null && (s.timestamp - prevTs) >= 9.0) stallCount += 1;
      if (prevAngle !== null) angleTravelled += Math.abs(s.output_deg - prevAngle);
      prevAngle = s.output_deg;
      prevTs = s.timestamp;
    });
    if (samples.length === 0) { minTemp = maxTemp = minVoltage = maxVoltage = 0; }
    return {
      dateStr: day.dateStr, count: samples.length,
      movingPct: samples.length ? (movingCount / samples.length) * 100 : 0,
      isolatedPct: samples.length ? (isolatedCount / samples.length) * 100 : 0,
      angleTravelled, peakTorque, peakCurrent, minTemp, maxTemp,
      minVoltage, maxVoltage, stallCount,
    };
  });
}

/* Min-max binning over the flattened (day, row) sequence, IN TIME ORDER:
   for each bin, keeps the highest and lowest sample of `field` -
   preserves spikes and faults, which matter more here than a smooth-
   looking average would. Returns refs {dayIdx, row, value, ts}, ascending
   row order, ready to become formula cells.
   opts.skipNull drops samples where the field is null/undefined before
   binning - needed for target_deg, which is null until a move is ever
   commanded; without it, null would compare as 0 in the min/max picks
   and silently fabricate a target that was never set (D16 shape). */
function minMaxDownsampleRefs(days, field, opts) {
  const skipNull = !!(opts && opts.skipNull);
  const flat = [];
  days.forEach((day, dayIdx) => {
    day.samples.forEach((s, i) => {
      const value = s[field];
      if (skipNull && (value === null || value === undefined)) return;
      flat.push({ value, ts: s.timestamp, dayIdx, row: i + 2 });
    });
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

/* Same min-max binning, but over the sequence sorted by OUTPUT ANGLE
   rather than time - for the angle-correlated charts (mechanical team's
   request: see how a field relates to position, not to when it was
   sampled). Returns refs {dayIdx, row, value, angle}, ascending angle. */
function angleSortedDownsampleRefs(days, field) {
  const flat = [];
  days.forEach((day, dayIdx) => {
    day.samples.forEach((s, i) => {
      if (s.output_deg === null || s.output_deg === undefined) return;
      flat.push({ value: s[field], angle: s.output_deg, dayIdx, row: i + 2 });
    });
  });
  flat.sort((a, b) => a.angle - b.angle);
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
    // Ordered by ANGLE (the x-axis here), not original row index - the
    // time-sorted version above can order by row because row order IS
    // time order; that shortcut doesn't hold once the sequence has been
    // re-sorted by angle.
    if (lo === hi) picked.push(lo);
    else if (lo.angle <= hi.angle) picked.push(lo, hi);
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

const RAW_HEADERS = [
  "Timestamp", "Raw Counts", "Output Angle (deg)", "Servo Angle (deg)",
  "Target Angle (deg)", "Temperature (C)", "Voltage (V)", "Current (A)",
  "Torque (kg.cm)", "Moving", "Locked", "Faults", "Interval (s)", "Isolated"
];
// Isolated is APPENDED as column N, never inserted earlier: DAY_SHEET_COLS
// below hardcodes "M" for interval, which feeds every chart formula via
// dayCellRef() - a mid-table insert would silently shift it and break
// every chart built from this sheet.
const RAW_COLS = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N"];
const TIMESTAMP_COL = "A";

/* Explicit widths for every column - the previous version had none at
   all, so every column (not just the date) sat at Excel's default and
   the timestamp rendered as `########` (BACKLOG.md R5). Units are
   Excel's own "characters of the default font" measure. */
const DAY_SHEET_COL_WIDTHS_XML =
  `<cols>` +
  `<col min="1" max="1" width="20" customWidth="1"/>` +   // Timestamp
  `<col min="2" max="2" width="12" customWidth="1"/>` +   // Raw Counts
  // The 3 angle columns and Temperature/Torque are sized for their OWN
  // header text ("Output/Servo/Target Angle (deg)", "Temperature (C)"),
  // not just the data - a value fits in half this width, but a header
  // clipped mid-word is the same unreadable-column defect this section
  // exists to fix (found rendering a real preview, not assumed fixed).
  `<col min="3" max="5" width="20" customWidth="1"/>` +   // the 3 angles
  `<col min="6" max="6" width="17" customWidth="1"/>` +   // Temperature (C)
  `<col min="7" max="8" width="12" customWidth="1"/>` +   // Voltage/Current
  `<col min="9" max="9" width="15" customWidth="1"/>` +   // Torque (kg.cm)
  `<col min="10" max="11" width="9" customWidth="1"/>` +  // Moving/Locked
  `<col min="12" max="12" width="26" customWidth="1"/>` + // Faults (can list several)
  `<col min="13" max="14" width="13" customWidth="1"/>` + // Interval (s)/Isolated
  `</cols>`;

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
    const hasServo = s.servo_deg !== null && s.servo_deg !== undefined;
    const hasTarget = s.target_deg !== null && s.target_deg !== undefined;
    const faults = decodedFaultNames(s);
    /* Row-level style only - no per-cell stamps, confirmed to still
       render (see stylesXml's comment) - what matters at millions of
       rows is one attribute per row, not nine. A fault row takes
       priority over plain banding, mirroring the live UI's fault lamps
       (style.css .fault.on) taking priority over the ordinary look. */
    const rowStyle = faults ? 4 : (idx % 2 === 1 ? 3 : null);
    const rowAttrs = rowStyle !== null ? ` s="${rowStyle}" customFormat="1"` : "";
    body += `<row r="${r}"${rowAttrs}>` +
      `<c r="A${r}" s="2"><v>${excelSerialDate(s.timestamp)}</v></c>` +
      `<c r="B${r}"><v>${s.raw_counts}</v></c>` +
      `<c r="C${r}"><v>${Math.round(s.output_deg * 100) / 100}</v></c>` +
      (hasServo ? `<c r="D${r}"><v>${Math.round(s.servo_deg * 100) / 100}</v></c>` : "") +
      (hasTarget ? `<c r="E${r}"><v>${Math.round(s.target_deg * 100) / 100}</v></c>` : "") +
      `<c r="F${r}"><v>${Math.round(s.temperature_c * 100) / 100}</v></c>` +
      `<c r="G${r}"><v>${Math.round(s.voltage_v * 100) / 100}</v></c>` +
      `<c r="H${r}"><v>${Math.round(s.current_a * 100) / 100}</v></c>` +
      `<c r="I${r}"><v>${Math.round(s.torque_kgcm * 100) / 100}</v></c>` +
      (s.moving ? `<c r="J${r}" t="inlineStr"><is><t>Yes</t></is></c>` : "") +
      (s.locked ? `<c r="K${r}" t="inlineStr"><is><t>Yes</t></is></c>` : "") +
      (faults ? `<c r="L${r}" t="inlineStr"><is><t>${faults}</t></is></c>` : "") +
      `<c r="M${r}"><v>${Math.round(s.interval * 1000) / 1000}</v></c>` +
      (s.isolated ? `<c r="N${r}" t="inlineStr"><is><t>Yes</t></is></c>` : "") +
      `</row>`;
  });
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n` +
    `<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">\n` +
    `${DAY_SHEET_COL_WIDTHS_XML}\n<sheetData>${hRowXml}${body}</sheetData>\n</worksheet>`;
}

/* Every TIME-based chart series this workbook can show, one place, so
   there is a single list of "what gets charted against time" rather than
   a second one drifting out of sync with ChartData's column allocation.
   target_deg is skipNull: it doesn't exist until a move is commanded,
   and letting the downsample treat a missing target as 0 would chart a
   target that was never set (D16 shape). */
const TIME_SERIES = [
  { key: "output_deg", title: "Measured Output Angle", axis: "Degrees (deg)", color: "FF9900" },
  { key: "torque_kgcm", title: "Shaft Torque Load", axis: "kg.cm", color: "FF9900" },
  { key: "current_a", title: "Electrical Current Draw", axis: "Amperes", color: "7077A1" },
  { key: "temperature_c", title: "Motor Temperature", axis: "Celsius", color: "C0392B" },
  { key: "voltage_v", title: "Supply Voltage", axis: "Volts", color: "4A7C59" },
  { key: "interval", title: "Sampler Interval Jitter", axis: "Seconds", color: "7077A1" },
  { key: "servo_deg", title: "Servo Shaft Angle (pre-ratio)", axis: "Degrees (deg)", color: "BB88BB" },
  { key: "target_deg", title: "Target Angle", axis: "Degrees (deg)", color: "8888BB", skipNull: true },
];

/* Angle-correlated charts, mechanical team's request: how a field
   relates to POSITION, not to when it was sampled. x is output_deg
   (the mechanism's own travel), sorted ascending - see
   angleSortedDownsampleRefs. Colors match each field's own TIME_SERIES
   entry above, so the time chart and its angle-correlated counterpart
   read as the same fact, not two unrelated colors. */
const ANGLE_SERIES = [
  { key: "torque_kgcm", title: "Torque vs Angle", axis: "kg.cm", color: "FF9900" },
  { key: "current_a", title: "Current vs Angle", axis: "Amperes", color: "7077A1" },
  { key: "temperature_c", title: "Temperature vs Angle", axis: "Celsius", color: "C0392B" },
  { key: "voltage_v", title: "Voltage vs Angle", axis: "Volts", color: "4A7C59" },
];

/* Fixed Overview cells the operator types a range into - typed once,
   in one recognisable place, so ChartData's formulas below can hardcode
   the reference (see makeOverviewSheetXml for the labelled cells). */
const RANGE_FROM_CELL = "Overview!$C$2";
const RANGE_TO_CELL = "Overview!$C$3";

/* Wraps a value formula so it disappears (NA(), which Excel line/scatter
   charts render as a gap, not a zero) whenever its own sample falls
   outside the operator-typed range - the mechanism the typed range
   selector runs on. tsRef is always the day-sheet TIMESTAMP cell for
   THIS row, even when the column being computed is the angle x-value:
   gating by real time, not by the angle re-sort, is what "the operator's
   range" has to mean. */
function gatedFormula(tsRef, valueRef) {
  return `IF(AND(${tsRef}&gt;=${RANGE_FROM_CELL},${tsRef}&lt;=${RANGE_TO_CELL}),${valueRef},NA())`;
}

/* Builds the hidden ChartData sheet: one (x, y) formula-cell pair of
   columns per series above (TIME_SERIES then ANGLE_SERIES), each cell a
   live reference into a day sheet, gated by the typed range - not a
   plain value, so editing a day sheet OR the range updates the charts.
   Bounded to CHART_DOWNSAMPLE_MAX_POINTS rows per field regardless of
   range length. 12 series today = 24 columns, comfortably inside A..Z -
   this stops being true past 13 series and would need double-letter
   columns; noted here since nothing else enforces it. */
function makeChartDataSheetXml(days) {
  const allSeries = [
    ...TIME_SERIES.map((f) => Object.assign({ mode: "time" }, f)),
    ...ANGLE_SERIES.map((f) => Object.assign({ mode: "angle" }, f)),
  ];
  const colPairs = allSeries.map((_, i) => [
    String.fromCharCode(65 + i * 2), String.fromCharCode(65 + i * 2 + 1),
  ]);
  let maxRows = 0;
  const perField = allSeries.map((f) => {
    const refs = f.mode === "angle"
      ? angleSortedDownsampleRefs(days, f.key)
      : minMaxDownsampleRefs(days, f.key, { skipNull: !!f.skipNull });
    maxRows = Math.max(maxRows, refs.length);
    return refs;
  });

  let hRow = `<row r="1">`;
  allSeries.forEach((f, i) => {
    const [xCol, yCol] = colPairs[i];
    const xLabel = f.mode === "angle" ? `${f.title} - angle` : `${f.title} - time`;
    hRow += `<c r="${xCol}1" t="inlineStr"><is><t>${xLabel}</t></is></c>` +
            `<c r="${yCol}1" t="inlineStr"><is><t>${f.title}</t></is></c>`;
  });
  hRow += `</row>`;

  let body = "";
  for (let r = 0; r < maxRows; r++) {
    const rowN = r + 2;
    let rowXml = `<row r="${rowN}">`;
    allSeries.forEach((f, i) => {
      const refs = perField[i];
      if (r >= refs.length) return;
      const ref = refs[r];
      const tsRef = dayCellRef(days, ref, TIMESTAMP_COL);
      const [xColOut, yColOut] = colPairs[i];
      const yValRef = dayCellRef(days, ref, DAY_SHEET_COLS[f.key]);
      /* Formula AND cached value on every cell - real Excel output never
         ships a formula alone (confirmed against a reference file), and
         a renderer that doesn't recalculate on open (some OnlyOffice/
         LibreOffice paths) would otherwise show these blank. Cached
         value is the UNGATED value: at generation time every sample is
         inside the default (full-export) range, so cache and live
         formula agree until the operator actually edits the range -
         which needs a recalc to show regardless (see the OnlyOffice
         gate on the range selector itself). */
      if (f.mode === "angle") {
        const xValRef = dayCellRef(days, ref, DAY_SHEET_COLS.output_deg);
        rowXml += `<c r="${xColOut}${rowN}"><f>${gatedFormula(tsRef, xValRef)}</f><v>${ref.angle}</v></c>` +
                  `<c r="${yColOut}${rowN}"><f>${gatedFormula(tsRef, yValRef)}</f><v>${ref.value}</v></c>`;
      } else {
        rowXml += `<c r="${xColOut}${rowN}" s="2"><f>${gatedFormula(tsRef, tsRef)}</f><v>${excelSerialDate(ref.ts)}</v></c>` +
                  `<c r="${yColOut}${rowN}"><f>${gatedFormula(tsRef, yValRef)}</f><v>${ref.value}</v></c>`;
      }
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
    allSeries,
  };
}

/* Real, verified OOXML chart structures - both generated with XlsxWriter
   and unzipped to confirm the exact schema, not guessed from
   documentation (the line-chart shape was verified 23 Aug; the scatter
   shape, needed this session for a genuinely numeric x-axis, the same
   way - see BACKLOG.md R5, the lesson that cost a corrupted-file defect
   was "verify against a reference, don't guess a second time"). */
function numCacheXml(values) {
  const pts = values.map((v, i) => `<c:pt idx="${i}"><c:v>${v}</c:v></c:pt>`).join("");
  return `<c:numCache><c:formatCode>General</c:formatCode><c:ptCount val="${values.length}"/>${pts}</c:numCache>`;
}

function titleXml(text, vertical) {
  const bodyPr = vertical ? `<a:bodyPr rot="-5400000" vert="horz"/>` : `<a:bodyPr/>`;
  return `<c:title><c:tx><c:rich>${bodyPr}<a:lstStyle/><a:p><a:pPr><a:defRPr/></a:pPr><a:r><a:rPr lang="en-US"/><a:t>${text}</a:t></a:r></a:p></c:rich></c:tx><c:layout/></c:title>`;
}

/* A category axis with an EXPLICIT tick-label skip, computed by us from
   the actual point count - not c:dateAx's "auto" spacing. c:dateAx was
   tried first (verified against a reference, rendered cleanly there) and
   still made this WORSE on a real board export: LibreOffice's automatic
   interval picked a per-second tick across a full hour of real (denser,
   less uniform) data, producing the same illegible label smear it was
   meant to fix. Trusting the renderer's heuristic on data we hadn't
   actually tested it against was the mistake - we already know exactly
   how many points are in this series, so we pick the interval ourselves
   and verified THIS shape against a reference at real scale (2000
   points) before shipping it, the same rigor as everything else in this
   file that touches OOXML. */
function catAxXml(axId, crossAxId, tickLblSkip) {
  /* -45deg labels (rot="-2700000", OOXML angle units are 1/60000 deg) -
     even with a dozen labels instead of hundreds, horizontal labels on
     a chart this narrow still touch/overlap edge to edge. Diagonal was
     the original layout before this session's changes; restored on
     request, verified against a real reference (this exact txPr shape)
     rather than reassembled from memory. */
  const txPr = `<c:txPr><a:bodyPr rot="-2700000" vert="horz"/><a:lstStyle/><a:p><a:pPr><a:defRPr baseline="0"/></a:pPr><a:endParaRPr lang="en-US"/></a:p></c:txPr>`;
  return `<c:catAx><c:axId val="${axId}"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:delete val="0"/><c:axPos val="b"/><c:numFmt formatCode="mm-dd hh:mm" sourceLinked="0"/><c:tickLblPos val="nextTo"/>${txPr}<c:crossAx val="${crossAxId}"/><c:crosses val="autoZero"/><c:lblAlgn val="ctr"/><c:lblOffset val="100"/><c:tickLblSkip val="${tickLblSkip}"/></c:catAx>`;
}

/* Aim for roughly a dozen visible labels regardless of how many points
   actually feed the chart - readable at the smallest range (1 hour) and
   the largest (30 days) alike, without depending on a renderer's own
   auto-spacing guess. */
function tickSkipFor(pointCount) {
  return Math.max(1, Math.ceil(pointCount / 12));
}

/* One <c:ser> block, shared by the line-chart (c:cat/c:val) and the
   scatter-chart (c:xVal/c:yVal) builders below - same series shape,
   different tag names, per the real OOXML schema for each chart type. */
function seriesXml(idx, tagX, tagY, name, colorHex, xFormula, yFormula, xCache, yCache) {
  const xCacheXml = xCache ? numCacheXml(xCache) : "";
  const yCacheXml = yCache ? numCacheXml(yCache) : "";
  return `<c:ser><c:idx val="${idx}"/><c:order val="${idx}"/><c:tx><c:v>${name}</c:v></c:tx>` +
    `<c:spPr><a:ln><a:solidFill><a:srgbClr val="${colorHex}"/></a:solidFill></a:ln></c:spPr>` +
    `<c:marker><c:symbol val="none"/></c:marker>` +
    `<c:${tagX}><c:numRef><c:f>${xFormula}</c:f>${xCacheXml}</c:numRef></c:${tagX}>` +
    `<c:${tagY}><c:numRef><c:f>${yFormula}</c:f>${yCacheXml}</c:numRef></c:${tagY}>` +
    `</c:ser>`;
}

/* Time-series line chart. seriesSpecs is a list so the same builder
   covers both a single-field chart (every entry below except one) and
   the Measured-vs-Target overlay (two series, one chart) without a
   second, near-duplicate chart function. */
function makeChartXml(title, axisTitle, seriesSpecs, pointCount) {
  const seriesXmls = seriesSpecs.map((s, i) =>
    seriesXml(i, "cat", "val", s.seriesName, s.colorHex, s.catFormula, s.valFormula,
             s.catCache, s.valCache)).join("");
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<c:chart>
${titleXml(title, false)}
<c:plotArea><c:layout/>
<c:lineChart><c:grouping val="standard"/>
${seriesXmls}
<c:axId val="111111111"/><c:axId val="222222222"/>
</c:lineChart>
${catAxXml("111111111", "222222222", tickSkipFor(pointCount))}
<c:valAx><c:axId val="222222222"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:delete val="0"/><c:axPos val="l"/><c:crossAx val="111111111"/>${titleXml(axisTitle, true)}</c:valAx>
</c:plotArea>
<c:legend><c:legendPos val="b"/></c:legend>
<c:plotVisOnly val="1"/>
<c:dispBlanksAs val="gap"/>
</c:chart>
</c:chartSpace>`;
}

/* Angle-correlated chart: a genuinely numeric x-axis (output angle),
   which c:lineChart's category axis cannot give - a category axis
   assumes evenly-spaced ordinal categories, wrong for angle values that
   aren't evenly sampled. c:scatterChart with scatterStyle="lineMarker"
   and markers suppressed is Excel's own shape for an XY line (verified
   against a real XlsxWriter-generated file, same rigor as the line
   chart above), with TWO value axes (c:valAx/c:valAx, not catAx/valAx). */
function makeScatterChartXml(title, xAxisTitle, yAxisTitle, seriesName, colorHex,
                             xFormula, yFormula, xCache, yCache) {
  const ser = seriesXml(0, "xVal", "yVal", seriesName, colorHex,
                        xFormula, yFormula, xCache, yCache);
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<c:chart>
${titleXml(title, false)}
<c:plotArea><c:layout/>
<c:scatterChart><c:scatterStyle val="lineMarker"/>
${ser}
<c:axId val="333333333"/><c:axId val="444444444"/>
</c:scatterChart>
<c:valAx><c:axId val="333333333"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:delete val="0"/><c:axPos val="b"/><c:crossAx val="444444444"/><c:crossBetween val="midCat"/>${titleXml(xAxisTitle, false)}</c:valAx>
<c:valAx><c:axId val="444444444"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:delete val="0"/><c:axPos val="l"/><c:crossAx val="333333333"/><c:crossBetween val="midCat"/>${titleXml(yAxisTitle, true)}</c:valAx>
</c:plotArea>
<c:legend><c:legendPos val="b"/></c:legend>
<c:plotVisOnly val="1"/>
<c:dispBlanksAs val="gap"/>
</c:chart>
</c:chartSpace>`;
}

/* Anchors: [{rId, fromCol, fromRow, toCol, toRow}]. One drawing part can
   anchor several charts on the same sheet - used to lay every chart on
   the Overview sheet in a 2-column grid, however many there are. */
function makeDrawingXml(anchors) {
  const frames = anchors.map((a, i) =>
    `<xdr:twoCellAnchor><xdr:from><xdr:col>${a.fromCol}</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>${a.fromRow}</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:from><xdr:to><xdr:col>${a.toCol}</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>${a.toRow}</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:to><xdr:graphicFrame macro=""><xdr:nvGraphicFramePr><xdr:cNvPr id="${i + 2}" name="Chart ${i + 1}"/><xdr:cNvGraphicFramePr/></xdr:nvGraphicFramePr><xdr:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/></xdr:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart"><c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" r:id="${a.rId}"/></a:graphicData></a:graphic></xdr:graphicFrame><xdr:clientData/></xdr:twoCellAnchor>`
  ).join("");
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n` +
    `<xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/spreadsheetml/2006/spreadsheetDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">\n` +
    `${frames}\n</xdr:wsDr>`;
}

/* Charts are anchored starting at row index 1 (row 2), column index 3
   (column D) - see generateExcelXlsxZip's drawing1Xml. Text content in
   columns A:C never collides with them regardless of row; the per-day
   table below is deliberately placed past the LAST chart's bottom edge
   so it can use the full row width without the drawing layer sitting
   over it. Kept as named constants so a future chart-count change (this
   session went from 6 charts to 13) has one place to update, not a
   number re-derived by eye. */
const CHART_GRID_COLS = 2;
const CHART_ROW_HEIGHT = 15;
function chartGridBottomRow(chartCount) {
  return 1 + Math.ceil(chartCount / CHART_GRID_COLS) * CHART_ROW_HEIGHT + 14;
}

function makeOverviewSheetXml(days, samples, stats, fromTs, toTs, chartCount) {
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
  /* Title band spans A1:F1 (not just A1) so the tangerine fill backs
     the whole title rather than clipping where column A's own width
     ends - a styled band that stops under the text it's meant to
     frame reads as a bug, found rendering a real preview. */
  let body = `<row r="1" ht="24" customHeight="1">` +
    `<c r="A1" t="inlineStr" s="5"><is><t>Servo Telemetry Export - Summary</t></is></c>` +
    `<c r="B1" s="5"/><c r="C1" s="5"/><c r="D1" s="5"/><c r="E1" s="5"/><c r="F1" s="5"/>` +
    `</row>`;
  /* The typed range selector - two cells the operator edits directly,
     same date-time style (s="2") the day sheets already use. Fixed at
     C2/C3 (RANGE_FROM_CELL/RANGE_TO_CELL) so every ChartData formula can
     hardcode the reference. Defaults to the full exported range, so a
     fresh export already shows everything without editing anything. */
  body += `<row r="2"><c r="A2" t="inlineStr" s="6"><is><t>Chart range - From</t></is></c>` +
          `<c r="C2" s="2"><v>${excelSerialDate(fromTs)}</v></c></row>`;
  body += `<row r="3"><c r="A3" t="inlineStr" s="6"><is><t>Chart range - To</t></is></c>` +
          `<c r="C3" s="2"><v>${excelSerialDate(toTs)}</v></c></row>`;
  body += `<row r="4"><c r="A4" t="inlineStr"><is><t>Edit the two dates above to narrow every chart to that window - defaults to the full export.</t></is></c></row>`;
  rows.forEach(([k, v], idx) => {
    const r = idx + 6;
    body += `<row r="${r}"><c r="A${r}" t="inlineStr" s="6"><is><t>${k}</t></is></c>` +
            `<c r="B${r}" t="inlineStr"><is><t>${v}</t></is></c></row>`;
  });

  /* Per-day table: which day ran hot, which day stalled - one row per
     day, placed below the chart drawing's bottom edge so the full
     column width is free to use. */
  const dailyStats = computeDailyStats(days);
  const dailyHeaders = ["Day", "Samples", "Moving %", "Angle Travelled (deg)",
                        "Peak Torque (kg.cm)", "Peak Current (A)",
                        "Temp Range (C)", "Voltage Range (V)", "Stalls (>=9s)",
                        "Isolated %"];
  // Appended at the end, not inserted after "Moving %" - every column
  // letter above is hardcoded into the row-population code below, so a
  // mid-table insert would silently shift them (the same trap the day
  // sheets' own column letters already warn about).
  const dailyCols = ["A","B","C","D","E","F","G","H","I","J"];
  const tableTop = chartGridBottomRow(chartCount) + 4;
  body += `<row r="${tableTop - 1}"><c r="A${tableTop - 1}" t="inlineStr" s="6"><is><t>Per-day summary</t></is></c></row>`;
  body += `<row r="${tableTop}" ht="20" customHeight="1">` +
    dailyHeaders.map((h, i) => `<c r="${dailyCols[i]}${tableTop}" t="inlineStr" s="1"><is><t>${h}</t></is></c>`).join("") +
    `</row>`;
  dailyStats.forEach((d, idx) => {
    const r = tableTop + 1 + idx;
    const rowAttrs = (idx % 2 === 1) ? ` s="3" customFormat="1"` : "";
    body += `<row r="${r}"${rowAttrs}>` +
      `<c r="A${r}" t="inlineStr"><is><t>${d.dateStr}</t></is></c>` +
      `<c r="B${r}"><v>${d.count}</v></c>` +
      `<c r="C${r}"><v>${Math.round(d.movingPct * 10) / 10}</v></c>` +
      `<c r="D${r}"><v>${Math.round(d.angleTravelled * 100) / 100}</v></c>` +
      `<c r="E${r}"><v>${Math.round(d.peakTorque * 100) / 100}</v></c>` +
      `<c r="F${r}"><v>${Math.round(d.peakCurrent * 100) / 100}</v></c>` +
      `<c r="G${r}" t="inlineStr"><is><t>${d.minTemp.toFixed(1)} - ${d.maxTemp.toFixed(1)}</t></is></c>` +
      `<c r="H${r}" t="inlineStr"><is><t>${d.minVoltage.toFixed(2)} - ${d.maxVoltage.toFixed(2)}</t></is></c>` +
      `<c r="I${r}"><v>${d.stallCount}</v></c>` +
      `<c r="J${r}"><v>${Math.round(d.isolatedPct * 10) / 10}</v></c>` +
      `</row>`;
  });

  /* Same defect this session already found and fixed on the day sheets
     (BACKLOG.md R5): a date/number cell too narrow shows ### rather than
     overflowing like text does, so the range-selector's own values need
     an explicit width, not just the day sheets'. */
  const colsXml = `<cols>` +
    `<col min="1" max="1" width="30" customWidth="1"/>` +
    // Widened from 12: the whole-range stat VALUES this column also
    // holds ("2026-08-23 18:20 UTC", "-90.31 to 90.13 deg") are longer
    // than that, and were visibly overflowing (found live, not assumed
    // fixed - the per-day table's "Samples" column shares this width
    // too, which just leaves it wider than it strictly needs).
    `<col min="2" max="2" width="26" customWidth="1"/>` +
    `<col min="3" max="3" width="20" customWidth="1"/>` +
    `<col min="4" max="4" width="20" customWidth="1"/>` +
    `<col min="5" max="8" width="16" customWidth="1"/>` +
    `<col min="9" max="10" width="14" customWidth="1"/>` +
    `</cols>`;
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n` +
    `<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">\n` +
    `${colsXml}\n<sheetData>${body}</sheetData>\n<drawing r:id="rId1"/>\n</worksheet>`;
}

async function generateExcelXlsxZip(samples, fromTs, toTs, onProgress) {
  const stats = computeStatsAndIntervals(samples);
  const days = groupSamplesByDay(samples);
  const chartData = makeChartDataSheetXml(days);
  const chartCount = TIME_SERIES.length + 1 /* Measured vs Target overlay */ + ANGLE_SERIES.length;
  const overviewXml = makeOverviewSheetXml(days, samples, stats, fromTs, toTs, chartCount);
  /* Day-sheet XML is NOT built here - each is built lazily, one at a
     time, inside the filesMap entries below, so createZipArchive can
     compress and discard one day's text before building the next
     rather than holding every day's raw XML in memory simultaneously. */

  const lastRow = chartData.maxRows + 1;
  const rangeXml = (colPairIdx) => {
    const [xCol, yCol] = chartData.colPairs[colPairIdx];
    return { xFormula: `ChartData!$${xCol}$2:$${xCol}$${lastRow}`,
             yFormula: `ChartData!$${yCol}$2:$${yCol}$${lastRow}` };
  };

  /* One chart per TIME_SERIES entry - every field gets the same
     treatment (R5's own 10 August principle: no field singled out). */
  const timeChartXmls = TIME_SERIES.map((f, i) => {
    const { xFormula, yFormula } = rangeXml(i);
    const refs = chartData.perField[i];
    return makeChartXml(f.title, f.axis, [{
      seriesName: f.title, colorHex: f.color, catFormula: xFormula, valFormula: yFormula,
      catCache: refs.map((r) => excelSerialDate(r.ts)), valCache: refs.map((r) => r.value),
    }], chartData.maxRows);
  });

  /* Measured vs Target overlay - the one chart that exists specifically
     to show the gap between where the mechanism is and where it was
     told to go, the same purpose the live UI's target marker serves
     (renderState(), style.css .subline). Two series, one time axis, tangerine/bluebell
     matching the app's own colour semantics throughout this file. */
  const outputIdx = TIME_SERIES.findIndex((f) => f.key === "output_deg");
  const targetIdx = TIME_SERIES.findIndex((f) => f.key === "target_deg");
  const outputRange = rangeXml(outputIdx);
  const targetRange = rangeXml(targetIdx);
  const overlayXml = makeChartXml("Measured vs Target Angle", "Degrees (deg)", [
    { seriesName: "Measured", colorHex: "FF9900",
      catFormula: outputRange.xFormula, valFormula: outputRange.yFormula,
      catCache: chartData.perField[outputIdx].map((r) => excelSerialDate(r.ts)),
      valCache: chartData.perField[outputIdx].map((r) => r.value) },
    { seriesName: "Target", colorHex: "8888BB",
      catFormula: targetRange.xFormula, valFormula: targetRange.yFormula,
      catCache: chartData.perField[targetIdx].map((r) => excelSerialDate(r.ts)),
      valCache: chartData.perField[targetIdx].map((r) => r.value) },
  ], chartData.maxRows);

  /* Angle-correlated charts - mechanical team's request: each field
     against the mechanism's own travel, not against time. */
  const angleChartXmls = ANGLE_SERIES.map((f, i) => {
    const seriesIdx = TIME_SERIES.length + i;
    const { xFormula, yFormula } = rangeXml(seriesIdx);
    const refs = chartData.perField[seriesIdx];
    return makeScatterChartXml(f.title, "Output Angle (deg)", f.axis, f.title, f.color,
                               xFormula, yFormula,
                               refs.map((r) => r.angle), refs.map((r) => r.value));
  });

  const chartXmls = [...timeChartXmls, overlayXml, ...angleChartXmls];
  /* Anchored starting at column D (index 3), clear of the text columns
     (A: labels, C: the range-selector values) so the drawing layer
     never sits on top of readable cell content. CHART_GRID_COLS/
     CHART_ROW_HEIGHT are the same constants chartGridBottomRow() uses to
     tell the per-day table where the drawing ends - one grid geometry,
     not two copies of it drifting apart. */
  const drawing1Xml = makeDrawingXml(
    chartXmls.map((_, i) => ({
      rId: `rId${i + 1}`,
      fromCol: 3 + (i % CHART_GRID_COLS) * 8,
      fromRow: 1 + Math.floor(i / CHART_GRID_COLS) * CHART_ROW_HEIGHT,
      toCol: 3 + (i % CHART_GRID_COLS) * 8 + 7,
      toRow: 1 + Math.floor(i / CHART_GRID_COLS) * CHART_ROW_HEIGHT + (CHART_ROW_HEIGHT - 1),
    })));

  /* LCARS palette, ported from style.css's actual hex values (not
     re-guessed) - --tangerine #FF9900 (headers/title band),
     --panel2 #F6EEDA (row banding), --alarm-bg #F9E2DE (fault rows),
     --action-ink #2A1A00 (text on a colour fill), --ink #2A2310 (body
     text). Fonts: "Bahnschrift SemiCondensed" is the app's own
     documented zero-download LCARS face (style.css:3-5, stock on Win
     10/11); Consolas mirrors --mono for numeric columns. Real fill/font
     XML shape (8-hex ARGB, not the chart namespace's 6-hex) confirmed
     against an XlsxWriter-generated reference before writing this by
     hand - the fill namespace is not the chart namespace, and guessing
     that class of detail is exactly what cost the corrupted-zip defect
     last session (BACKLOG.md R5). Row banding is a ROW-level style
     (s= + customFormat="1", no per-cell stamps) - confirmed to render in
     LibreOffice via a hand-built minimal file before relying on it here,
     since the alternative (restyling every cell) is the kind of per-row
     cost that matters at the 5.18M-row scale this export is built for. */
  const stylesXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="1">
  <numFmt numFmtId="164" formatCode="yyyy-mm-dd hh:mm:ss"/>
</numFmts>
<fonts count="4">
  <font><sz val="10"/><color rgb="FF2A2310"/><name val="Consolas"/></font>
  <font><b/><sz val="10"/><color rgb="FF2A1A00"/><name val="Bahnschrift SemiCondensed"/></font>
  <font><b/><sz val="16"/><color rgb="FF2A1A00"/><name val="Bahnschrift SemiCondensed"/></font>
  <font><b/><sz val="10"/><color rgb="FF2A2310"/><name val="Bahnschrift SemiCondensed"/></font>
</fonts>
<fills count="5">
  <fill><patternFill patternType="none"/></fill>
  <fill><patternFill patternType="gray125"/></fill>
  <fill><patternFill patternType="solid"><fgColor rgb="FFFF9900"/><bgColor indexed="64"/></patternFill></fill>
  <fill><patternFill patternType="solid"><fgColor rgb="FFF6EEDA"/><bgColor indexed="64"/></patternFill></fill>
  <fill><patternFill patternType="solid"><fgColor rgb="FFF9E2DE"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="1"><border/></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="7">
  <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>                                          <!-- 0: default data -->
  <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>               <!-- 1: header row (day sheets + Overview) -->
  <xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>                   <!-- 2: date - unchanged index, referenced pervasively as s="2" -->
  <xf numFmtId="0" fontId="0" fillId="3" borderId="0" xfId="0" applyFill="1"/>                             <!-- 3: banded row -->
  <xf numFmtId="0" fontId="0" fillId="4" borderId="0" xfId="0" applyFill="1"/>                             <!-- 4: fault row -->
  <xf numFmtId="0" fontId="2" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>               <!-- 5: title band -->
  <xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyFont="1"/>                             <!-- 6: bold label on white -->
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

  return await createZipArchive(fileEntries, onProgress);
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

      /* Header/sample sizes here must track SAMPLE_BYTES/HEADER_BYTES
         above - this is an estimate for a progress bar, not the parse
         itself, but it is still a third place stating the wire format
         and it drifted out of sync with the real one once already
         (BACKLOG.md). */
      if (chunks.length === 1 && value.length >= HEADER_BYTES) {
        const view = new DataView(value.buffer, value.byteOffset, value.byteLength);
        const sampleCount = view.getUint32(8, true);
        if (sampleCount > 0) {
          totalUncompressedBytes = (sampleCount * SAMPLE_BYTES) + HEADER_BYTES;
        }
      }

      const recKb = Math.round(receivedBytes / 1024);
      const totKb = Math.round(totalUncompressedBytes / 1024);
      /* Stage 1 of 3: downloading the compact stream, 0-50%. */
      const pct = Math.min(50, Math.round((receivedBytes / totalUncompressedBytes) * 50));

      labelEl.textContent = "Downloading data… " + recKb + " / " + totKb + " KB (" + pct + "%)";
      fillEl.style.width = pct + "%";
    }

    /* Stage 2 of 3: parsing the binary payload into samples. */
    labelEl.textContent = "Parsing telemetry…";
    fillEl.style.width = "52%";

    const totalLen = chunks.reduce((acc, c) => acc + c.length, 0);
    const fullBuffer = new Uint8Array(totalLen);
    let offset = 0;
    for (const chunk of chunks) {
      fullBuffer.set(chunk, offset);
      offset += chunk.length;
    }

    /* servo_deg is already computed per-sample inside parseBinaryTelemetry
       from the header's ratio - servoRatio itself isn't needed past this
       point, so it isn't threaded any further (one derived value, not a
       second copy of the constant it came from). */
    const { samples } = parseBinaryTelemetry(fullBuffer.buffer);

    /* Stage 3 of 3: building the workbook - real progress per file (each
       day sheet, plus charts/overview/etc), not a frozen percentage. A
       30-day export takes well over a minute here, so this is the stage
       that actually needed honest feedback. */
    labelEl.textContent = "Building workbook…";
    fillEl.style.width = "55%";
    const xlsxBlob = await generateExcelXlsxZip(samples, fromTs, toTs,
      (done, total, filename) => {
        const pct = 55 + Math.round((done / total) * 40);
        fillEl.style.width = pct + "%";
        labelEl.textContent = `Building workbook… ${filename.split("/").pop()} (${done}/${total})`;
      });

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
  /* Angle snaps to the servo's own step grid (D32) - speed has no such
     grid, so it just takes the delta as asked. */
  const input = $(inputId);
  const value = parseFloat(input.value) || 0;
  const next = inputId === "inAngle"
    ? Math.round((value + delta) / ANGLE_STEP) * ANGLE_STEP
    : value + delta;
  input.value = next.toFixed(2);
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
  bind("isoCube", toggleIsolate);
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
