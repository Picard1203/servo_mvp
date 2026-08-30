/* Drives static/app.js against a stubbed DOM, to check the behaviours
   the Python suite cannot reach.
 *
 *   REPO=. node tools/check_client_behaviour.js
 *
 * Requires node on the development machine only. It is NOT part of the
 * deployment, and NOT one of the three verification commands - see
 * backlog T12, which is the decision about whether it should be.
 *
 * What it does NOT prove: it is a stub, not a browser. Layout, CSS and
 * real event dispatch are untested here. It calls the click listener
 * directly, so "disabled blocks the press" is asserted by design
 * rather than exercised - that half still wants an operator's eye on
 * the board.
 *
 * Written 8 August 2026 alongside Batch 1 (D14, D15, D16, D20, D21),
 * whose client halves had no other way to be checked. */

const fs = require("fs");
const vm = require("vm");
const path = require("path");

const REPO = process.env.REPO || path.join(__dirname, "..");
const APP = path.join(REPO, "python/static/app.js");

/* Mirrors the one DOM behaviour escapeHtml() in app.js actually relies
   on: assigning textContent HTML-escapes into innerHTML. */
function escapeForInnerHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function makeEl(id) {
  let _textContent = "";
  const el = {
    id,
    get textContent() { return _textContent; },
    set textContent(v) { _textContent = v; el.innerHTML = escapeForInnerHtml(v); },
    innerHTML: "",
    value: "",
    disabled: false,
    hidden: false,
    className: "",
    style: {},
    dataset: {},
    offsetWidth: 0,
    children: [],
    _classes: new Set(),
    _listeners: {},
    classList: {
      add: (...c) => c.forEach((x) => el._classes.add(x)),
      remove: (...c) => c.forEach((x) => el._classes.delete(x)),
      contains: (c) => el._classes.has(c),
      toggle: (c, on) => {
        const want = on === undefined ? !el._classes.has(c) : !!on;
        if (want) el._classes.add(c); else el._classes.delete(c);
        return want;
      },
    },
    addEventListener: (name, fn) => { el._listeners[name] = fn; },
    removeEventListener: () => {},
    querySelector: () => {
      if (!el._sub) el._sub = makeEl(id + "/.s");
      return el._sub;
    },
    querySelectorAll: () => [],
    appendChild: (c) => { el.children.push(c); return c; },
    remove: () => {},
    setAttribute: () => {},
    click: () => { if (!el.disabled && el._listeners.click) el._listeners.click(); },
    focus: () => {},
    showModal: () => {},
    close: () => {},
    open: false,
  };
  return el;
}

const els = {};
const $ = (id) => (els[id] || (els[id] = makeEl(id)));

const toasts = [];

const ctx = {
  console,
  setTimeout,
  clearTimeout,
  setInterval: () => 0,
  Date,
  Math,
  isNaN,
  isFinite,
  parseFloat,
  parseInt,
  String,
  Array,
  Object,
  Number,
  Promise,
  JSON,
  fetch: async () => { throw new TypeError("Failed to fetch"); },
  window: { location: { host: "board", href: "" } },
  document: {
    getElementById: $,
    createElement: (tag) => makeEl("<" + tag + ">"),
    querySelectorAll: () => [],
    addEventListener: () => {},
  },
};
ctx.globalThis = ctx;

vm.createContext(ctx);
vm.runInContext(fs.readFileSync(APP, "utf8"), ctx);

/* capture what the operator is told */
ctx.toast = (message, level) => toasts.push({ message, level });

let failures = 0;
function check(name, condition, detail) {
  if (condition) {
    console.log("  ok   " + name);
  } else {
    failures += 1;
    console.log("  FAIL " + name + (detail ? "  <" + detail + ">" : ""));
  }
}

function lastToast() { return toasts.length ? toasts[toasts.length - 1] : null; }

/* ---------- D14: a network-level failure ---------- */
console.log("\nD14 - a refused connection reads as something to act on");
(async () => {
  let thrown = null;
  try { await ctx.apiGet("/servo/state"); } catch (e) { thrown = e; }
  check("fetch rejection is turned into a reason code",
        thrown && thrown.reason === "unreachable", thrown && thrown.reason);
  check("it carries no HTTP status", thrown && thrown.status === 0);

  toasts.length = 0;
  ctx.sayError(thrown);
  const t = lastToast();
  check("the operator is not shown the browser's words",
        t && !/Failed to fetch/i.test(t.message), t && t.message);
  check("the message says what to do",
        t && /wait a moment and try again/.test(t.message), t && t.message);
  check("it is shown as a warning", t && t.level === "warn");

  /* ---------- D21: the step comes from the backend ---------- */
  console.log("\nD21 - the enforced step, in the backend's words");
  toasts.length = 0;
  const stepErr = new Error("angle must be in steps of 0.06 deg");
  stepErr.status = 422;
  stepErr.reason = "step";
  ctx.sayError(stepErr);
  const s = lastToast();
  check("the backend's figure reaches the operator",
        s && /0\.06/.test(s.message), s && s.message);
  check("the hardcoded 0.1 is gone", s && !/0\.1\u00b0/.test(s.message),
        s && s.message);

  /* an unmapped backend refusal must still not leak browser text */
  toasts.length = 0;
  const odd = new Error("something the backend said");
  odd.status = 409;
  odd.reason = "";
  ctx.sayError(odd);
  check("an unmapped refusal uses the backend's words, prefixed",
        lastToast().message === "refused — something the backend said",
        lastToast().message);

  toasts.length = 0;
  const fault = new Error("internal");
  fault.status = 500;
  fault.reason = "";
  ctx.sayError(fault);
  check("a 5xx reads as a fault, distinct from a refusal",
        /reported a fault/.test(lastToast().message), lastToast().message);

  /* ---------- D16: nothing is rendered as measured ---------- */
  console.log("\nD16 - a failed read renders no measurements");
  const good = {
    output_deg: 12.5, reading_valid: true, moving: false, locked: false,
    settling: false, position_verified: true,
    temperature_c: 34.2, voltage_v: 12.1, current_a: 0.22,
    torque_kgcm: 1.4, overload: false, overcurrent: false, overheat: false,
    voltage_fault: false, sensor_fault: false, angle_fault: false,
    servo_deg: 18.3, target_deg: 20.0, target_stale: false,
    output_min_deg: -90.0, output_max_deg: 90.0,
    isolated: false, isolation_idle_timeout_s: 900,
  };
  const dead = {
    // D23: a failed read nulls moving and the six fault flags too, not
    // just the five readings - this fixture used to say `false` for all
    // six, which stopped being what the real API sends the moment D23
    // shipped.
    output_deg: null, reading_valid: false, moving: null, locked: false,
    settling: false, position_verified: true,
    temperature_c: null, voltage_v: null, current_a: null,
    torque_kgcm: null, overload: null, overcurrent: null, overheat: null,
    voltage_fault: null, sensor_fault: null, angle_fault: null,
    servo_deg: null, target_deg: 20.0, target_stale: false,
    output_min_deg: -90.0, output_max_deg: 90.0,
    isolated: false, isolation_idle_timeout_s: 900,
  };

  ctx.renderState(good);
  check("a good read shows the readings",
        $("vVolt").textContent === "12.10", $("vVolt").textContent);
  check("a good read shows HOLDING", $("movechip").textContent === "HOLDING");
  check("servo angle follows the measured reading",
        $("servoVal").textContent === "18.3°", $("servoVal").textContent);
  check("target renders with sign-free formatting",
        $("targetVal").textContent === "20.00°", $("targetVal").textContent);
  check("delta is signed and reads target minus measured",
        $("deltaVal").textContent === "+7.50°", $("deltaVal").textContent);
  check("the target marker is shown once a target exists",
        $("targetMarker").classList.contains("show"));
  check("the marker sits at the target's position on the REAL range"
        + " (-90..+90), not a hardcoded /360",
        $("targetMarker").style.left === "61.111111111111114%",
        $("targetMarker").style.left);
  check("the bar itself is scaled the same way",
        $("posBar").style.width === "56.94444444444444%",
        $("posBar").style.width);

  ctx.renderState(dead);
  check("one blip holds the last MEASURED voltage, not 0.00",
        $("vVolt").textContent === "12.10", $("vVolt").textContent);
  check("one blip does not blank the chip",
        $("movechip").textContent === "HOLDING", $("movechip").textContent);

  ctx.renderState(dead);
  ctx.renderState(dead);
  check("a sustained loss blanks the voltage",
        $("vVolt").textContent === "—", $("vVolt").textContent);
  check("...and never renders it as 0.00 V",
        $("vVolt").textContent !== "0.00", $("vVolt").textContent);
  check("...the temperature", $("vTemp").textContent === "—");
  check("...the current", $("vCur").textContent === "—");
  check("...the torque", $("vTorq").textContent === "—");
  check("...and the position", $("posN").textContent === "—");
  check("...and the servo angle (follows the measured reading)",
        $("servoVal").textContent === "—", $("servoVal").textContent);
  check("but the target is INDEPENDENT of reading validity - still known"
        + " when the servo goes silent",
        $("targetVal").textContent === "20.00°", $("targetVal").textContent);
  check("...while delta blanks anyway, since the measured side is gone",
        $("deltaVal").textContent === "—", $("deltaVal").textContent);
  check("the chip stops claiming HOLDING",
        $("movechip").textContent === "—", $("movechip").textContent);
  check("the fault lamps stop claiming OK",
        $("fOverload")._sub.textContent === "—",
        $("fOverload")._sub.textContent);
  check("the fault lamps are marked unknown",
        $("fOverload").classList.contains("unknown"));
  check("the position track shows it is not reporting",
        $("posTrack").classList.contains("unknown"));
  check("the banner says the position is unknown",
        /Position unknown/.test($("alarmslot").textContent),
        $("alarmslot").textContent);
  check("clear-fault stays hidden on an unknown read",
        $("recoverwrap").hidden === true);

  ctx.renderState(good);
  check("recovery restores the readings",
        $("vVolt").textContent === "12.10", $("vVolt").textContent);
  check("recovery clears the unknown lamps",
        !$("fOverload").classList.contains("unknown"));

  /* ---------- D25: a reported alarm survives the reading going unknown --- */
  console.log("\nD25 - an overload alarm stays visible through an unknown read");
  const tripped = Object.assign({}, good, { overload: true });

  ctx.renderState(tripped);
  check("a fresh trip shows the alarm",
        /ALARM/.test($("alarmslot").textContent), $("alarmslot").textContent);
  check("...naming the fault",
        /Overload/.test($("alarmslot").textContent));
  check("recover is visible while overload is active",
        $("recoverwrap").hidden === false);
  check("recover is enabled while the position is known",
        $("recoverBtn").disabled === false);

  ctx.renderState(dead);
  ctx.renderState(dead);
  ctx.renderState(dead);   // three failures: position is now genuinely unknown
  check("the alarm survives the reading going unknown, not blanked to"
        + " 'Position unknown' the way D16's rule alone would have",
        /ALARM/.test($("alarmslot").textContent), $("alarmslot").textContent);
  check("...marked as last-known, not presented as a live reading",
        /last known/.test($("alarmslot").textContent),
        $("alarmslot").textContent);
  check("recover stays visible - hidden would teach the operator the"
        + " alarm is over, which it is not",
        $("recoverwrap").hidden === false);
  check("recover is disabled once the position is unknown - it cannot"
        + " re-command a position it does not have",
        $("recoverBtn").disabled === true);
  check("...with the reason stated on the control itself",
        $("recoverBtn").title.length > 0, $("recoverBtn").title);
  check("D16's own rule is untouched: a fault lamp still stops claiming"
        + " OK once unknown (this is about not ERASING a true report,"
        + " not about trusting stale data)",
        $("fOverload")._sub.textContent === "TRIP",
        $("fOverload")._sub.textContent);

  ctx.renderState(Object.assign({}, good, { overload: false }));
  check("a fresh clean read clears the alarm",
        // The clean branch sets innerHTML (it needs the ok-dot span), not
        // textContent - a real DOM's textContent reflects either; this
        // stub's does not, so both are checked here.
        /No active alarms/.test($("alarmslot").innerHTML),
        $("alarmslot").innerHTML);
  check("...and hides recover again",
        $("recoverwrap").hidden === true);

  /* ---------- R2: motor isolation - cube, movechip rank, recover guard */
  console.log("\nR2 - motor isolation: cube, movechip rank, recover guard");
  ctx.renderState(Object.assign({}, good, { isolated: true }));
  check("the cube shows Isolated",
        $("isoCube").textContent === "Isolated", $("isoCube").textContent);
  check("the cube carries the isolated class",
        $("isoCube").classList.contains("isolated"));
  check("the movechip shows ISOLATED, not HOLDING - torque is cut, so"
        + " HOLDING would claim the servo is actively holding position"
        + " when friction is (D9's species: the screen asserting"
        + " something untrue about the mechanism)",
        $("movechip").textContent === "ISOLATED", $("movechip").textContent);
  check("recover is disabled while isolated - it needs torque to"
        + " re-command a position",
        $("recoverBtn").disabled === true);
  check("...with the reason stated on the control itself (D25's pattern)",
        /isolated/i.test($("recoverBtn").title), $("recoverBtn").title);
  check("the hint is hidden once isolated - the countdown it describes is"
        + " no longer live",
        $("isoHint").textContent === "", $("isoHint").textContent);

  ctx.renderState(Object.assign({}, good, { isolated: false }));
  check("the cube reverts to Isolate",
        $("isoCube").textContent === "Isolate", $("isoCube").textContent);
  check("...and drops the isolated class",
        !$("isoCube").classList.contains("isolated"));

  ctx.renderState(Object.assign({}, good, { isolated: true, overload: true }));
  check("FAULT still outranks ISOLATED on the movechip - D25's rule that"
        + " an alarm must never be displaced applies here too",
        $("movechip").textContent === "FAULT", $("movechip").textContent);
  ctx.renderState(good);   // clear the fault for the checks that follow

  /* ---------- LOCKED movechip state, and the hint's scoping ---------- */
  console.log("\nLOCKED movechip state, and the isoHint's scoping to it");
  ctx.renderState(Object.assign({}, good, { locked: true }));
  check("a locked, idle servo shows LOCKED on the movechip, not plain"
        + " HOLDING - locked is a distinct operator-set state",
        $("movechip").textContent === "LOCKED", $("movechip").textContent);
  check("the hint is shown while locked and not yet isolated - the only"
        + " state where the auto-isolate countdown is actually live",
        /^Isolate: auto-engages after 15 min locked$/.test(
          $("isoHint").textContent),
        $("isoHint").textContent);

  ctx.renderState(Object.assign({}, good, { locked: false }));
  check("the hint is hidden again once unlocked",
        $("isoHint").textContent === "", $("isoHint").textContent);

  ctx.renderState(
    Object.assign({}, good, { locked: true, isolated: true }));
  check("ISOLATED still outranks LOCKED on the movechip when both are"
        + " true - isolation is the more consequential state",
        $("movechip").textContent === "ISOLATED", $("movechip").textContent);
  ctx.renderState(good);   // reset for the checks that follow

  /* ---------- R2: the refusal names the remedy, not just the state --- */
  console.log("\nR2 - a move refused while isolated says how to fix it");
  toasts.length = 0;
  const isolatedErr = new Error("motor is isolated");
  isolatedErr.status = 409;
  isolatedErr.reason = "isolated";
  ctx.sayError(isolatedErr);
  check("the refusal names the state AND the remedy - D12's lesson:"
        + " naming a state with no way out leaves the operator stuck",
        lastToast() && /isolated/.test(lastToast().message) &&
        /un-isolate/.test(lastToast().message), lastToast());

  /* ---------- both gates at once name both reasons -------------------- */
  console.log("\nlocked AND isolated together - the refusal names both, not"
             + " just whichever gate the backend happened to check first");
  toasts.length = 0;
  const bothErr = new Error("servo is locked and motor is isolated");
  bothErr.status = 409;
  bothErr.reason = "locked_isolated";
  ctx.sayError(bothErr);
  check("the refusal names locked AND isolated, not just one of them",
        lastToast() && /locked/.test(lastToast().message) &&
        /isolated/.test(lastToast().message), lastToast());

  /* ---------- R2: isolating reminds about the physical lock ---------- */
  console.log("\nR2 - isolating reminds the operator the physical lock is manual");
  toasts.length = 0;
  let isolatePost = null;
  const realApiPost = ctx.apiPost;
  ctx.apiPost = async (url, body) => { isolatePost = { url, body }; return {}; };
  await ctx.toggleIsolate();
  check("it posts to /servo/isolate",
        isolatePost && isolatePost.url === "/servo/isolate", isolatePost);
  check("...isolated:true, since this harness never observes a prior"
        + " server-confirmed state (state.lastState stays unset - the"
        + " same reason toggleLock() has no equivalent test)",
        isolatePost && isolatePost.body.isolated === true, isolatePost);
  check("the reminder names the physical lock, since the software"
        + " cannot sense whether it is actually engaged either way",
        lastToast() && /physical lock is manual/.test(lastToast().message),
        lastToast());
  ctx.apiPost = realApiPost;

  /* ---------- R2: releasing Lock while isolated nudges once, not on ---
     ---------- every subsequent poll ------------------------------- */
  console.log("\nR2 - unlocking while isolated nudges once, not every poll");
  toasts.length = 0;
  ctx.renderState(Object.assign({}, good, { locked: true, isolated: true }));
  check("locking alone does not nudge",
        toasts.length === 0, toasts.length);
  ctx.renderState(Object.assign({}, good, { locked: false, isolated: true }));
  check("releasing lock while still isolated nudges once",
        toasts.length === 1, toasts.length);
  ctx.renderState(Object.assign({}, good, { locked: false, isolated: true }));
  check("...and does not repeat on the next poll while nothing changed",
        toasts.length === 1, toasts.length);
  ctx.renderState(good);   // restore baseline (unlocked, un-isolated)

  /* ---------- target: no target yet, and a stale (post-Stop) target -- */
  console.log("\nTarget angle - never fabricated, stale after Stop");
  ctx.renderState(Object.assign({}, good, { target_deg: null }));
  check("no target yet renders as unknown, not 0.0",
        $("targetVal").textContent === "—", $("targetVal").textContent);
  check("delta blanks with no target to compare against",
        $("deltaVal").textContent === "—", $("deltaVal").textContent);
  check("the marker hides when there is no target",
        !$("targetMarker").classList.contains("show"));

  ctx.renderState(Object.assign({}, good, { target_stale: true }));
  check("a stale target is kept, not cleared, and says so",
        $("targetVal").textContent === "20.00° · STOPPED",
        $("targetVal").textContent);
  check("delta keeps reading while stale - that is the point of keeping it",
        $("deltaVal").textContent === "+7.50°", $("deltaVal").textContent);
  check("the marker is dimmed while stale",
        $("targetMarker").classList.contains("stale"));

  /* ---------- D15: the second press never leaves ---------- */
  console.log("\nD15 - a command in flight refuses a second press");
  let calls = 0;
  let release;
  const slow = () => { calls += 1; return new Promise((r) => { release = r; }); };
  const btn = $("probeBtn");
  ctx.bind("probeBtn", slow);

  btn._listeners.click();
  await Promise.resolve();
  check("the first press runs the handler", calls === 1, "calls=" + calls);
  check("the control is disabled while in flight", btn.disabled === true);
  check("the control shows it is working",
        btn.classList.contains("busy"));

  btn._listeners.click();
  await Promise.resolve();
  check("the second press is dropped", calls === 1, "calls=" + calls);

  release();
  await new Promise((r) => setTimeout(r, 5));
  check("the control is released when it answers", btn.disabled === false);
  check("the working state is cleared", !btn.classList.contains("busy"));

  btn._listeners.click();
  await Promise.resolve();
  check("a later press works again", calls === 2, "calls=" + calls);
  release();
  await new Promise((r) => setTimeout(r, 5));

  /* a handler that throws must still release the control */
  const bad = $("badBtn");
  ctx.bind("badBtn", async () => { throw new Error("boom"); });
  try { await bad._listeners.click(); } catch (_) { /* expected */ }
  await new Promise((r) => setTimeout(r, 5));
  check("a failing handler still releases the control",
        bad.disabled === false && !bad.classList.contains("busy"));

  /* ---------- the Enter key, the tenth entry point ---------- */
  console.log("\nD15 - Enter in the angle field obeys the same guard");
  ctx.initUi();
  $("inAngle").value = "12";
  let moves = 0;
  const realPost = ctx.apiPost;
  ctx.apiPost = async () => { moves += 1; return {}; };
  const keydown = $("inAngle")._listeners.keydown;
  keydown({ key: "Enter", preventDefault: () => {} });
  await new Promise((r) => setTimeout(r, 5));
  check("Enter routes through the guarded control", moves === 1,
        "moves=" + moves);
  $("moveBtn").disabled = true;
  keydown({ key: "Enter", preventDefault: () => {} });
  await new Promise((r) => setTimeout(r, 5));
  check("Enter is refused while that control is busy", moves === 1,
        "moves=" + moves);
  $("moveBtn").disabled = false;
  ctx.apiPost = realPost;

  /* ---------- the slow-command notice ---------- */
  console.log("\nD15 - the slow notice belongs to the request, not the press");
  toasts.length = 0;
  let dismissed = 0;
  ctx.toast = (m, l) => { toasts.push({ message: m, level: l });
                          return () => { dismissed += 1; }; };
  const held = [];
  ctx.fetch = () => new Promise((r) => { held.push(r); });
  const pending = ctx.apiPost("/servo/move", {}).catch(() => {});
  const polling = ctx.apiGet("/servo/state").catch(() => {});
  await new Promise((r) => setTimeout(r, 2600));
  check("a slow command says so", toasts.length === 1,
        "toasts=" + toasts.length);
  check("a slow POLL stays silent", toasts.length === 1,
        "toasts=" + toasts.length);
  check("it is not shown as an error",
        toasts.length === 1 && toasts[0].level === null);
  held.forEach((r) => r({ ok: true, json: async () => ({}) }));
  await pending;
  await new Promise((r) => setTimeout(r, 5));
  check("the notice is taken down when the command answers", dismissed === 1,
        "dismissed=" + dismissed);
  void polling;

  /* ---------- D20: eventTime ---------- */
  console.log("\nD20 - eventTime, with the dead branch gone");
  check("an ISO timestamp still formats",
        /^\d\d:\d\d:\d\d$/.test(ctx.eventTime({ timestamp: "2026-08-08T14:22:07" })),
        ctx.eventTime({ timestamp: "2026-08-08T14:22:07" }));
  check("an unparsable timestamp falls back to the time part",
        ctx.eventTime({ timestamp: "notadate T09:10:11" }) === "09:10:11",
        ctx.eventTime({ timestamp: "notadate T09:10:11" }));
  check("a missing timestamp does not throw",
        ctx.eventTime({}) === "");

  /* ---------- D32: nudge() steps the angle field by its own unit ---------- */
  console.log("\nD32 - the angle field snaps to the servo's step grid");
  $("inAngle").value = "90";
  ctx.nudge("inAngle", -0.06);
  check("angle still snaps to the servo's step grid",
        $("inAngle").value === "89.94", $("inAngle").value);

  /* ---------- D32: doMove sends exactly what was typed ---------- */
  console.log("\nD32 - a typed angle reaches the backend unmodified");
  let sentBody = null;
  ctx.fetch = async (url, init) => {
    sentBody = JSON.parse(init.body);
    return {
      ok: false, status: 422, statusText: "Unprocessable Entity",
      json: async () => ({ detail: "angle must be in steps of 0.06 deg",
                           reason: "step" }),
    };
  };
  toasts.length = 0;
  $("inAngle").value = "0.08";
  await ctx.doMove();
  check("the client no longer pre-snaps the typed value",
        sentBody && sentBody.target_deg === 0.08, sentBody);
  check("the backend's own refusal reaches the operator",
        lastToast() && /0\.06/.test(lastToast().message), lastToast());

  /* ---------- R10: saved positions ---------- */
  console.log("\nR10 - the position angle field snaps to the servo's step grid");
  $("posAngle").value = "12";
  ctx.nudge("posAngle", 0.06);
  check("posAngle snaps like inAngle does",
        $("posAngle").value === "12.06", $("posAngle").value);

  console.log("\nR10 - renderPositions renders the empty state");
  ctx.fetch = async () => ({ ok: true, json: async () => [] });
  await ctx.fetchPositions();
  let listEl = $("positionList");
  let lastChild = listEl.children[listEl.children.length - 1];
  check("an empty list shows guidance, not a blank box",
        lastChild && /Press New/.test(lastChild.textContent),
        lastChild && lastChild.textContent);

  console.log("\nR10 - a position row escapes its name and flags an earlier reference");
  ctx.fetch = async () => ({
    ok: true,
    json: async () => [{ id: 1, name: "<b>gate</b>", description: "note",
                         raw_counts: 100, output_deg: 12.34,
                         stale_reference: true, created_at: "t",
                         updated_at: "t" }],
  });
  await ctx.fetchPositions();
  listEl = $("positionList");
  let row = listEl.children[listEl.children.length - 1];
  const mainHtml = row.children[0].innerHTML;
  const subHtml = row.children[1].innerHTML;
  check("the name is escaped, not rendered as markup",
        mainHtml.indexOf("<b>gate</b>") === -1
        && /&lt;b&gt;gate&lt;\/b&gt;/.test(mainHtml), mainHtml);
  check("the live angle the server computed is shown, not derived here",
        /12\.34/.test(mainHtml), mainHtml);
  check("a position saved before the current datum carries the advisory tag",
        /earlier\s*reference/i.test(subHtml), subHtml);

  console.log("\nR10 - askPosition refuses an empty name");
  let resolved = null;
  ctx.askPosition("New position", "Save",
    { name: "", description: "", targetDeg: 0, staleReference: false })
    .then((v) => { resolved = { value: v }; });
  $("posName").value = "";
  $("positionDlgYes")._listeners.click();
  await Promise.resolve();
  check("an empty name does not close the dialog", resolved === null, resolved);
  $("posName").value = "work point";
  $("positionDlgYes")._listeners.click();
  await Promise.resolve();
  check("a real name resolves with the typed fields",
        resolved && resolved.value && resolved.value.name === "work point",
        resolved);

  console.log("\nR10 - goToPosition names the position and its angle before moving");
  ctx.fetch = async () => ({
    ok: true,
    json: async () => [{ id: 7, name: "stow", description: "",
                         raw_counts: 0, output_deg: -45.5,
                         stale_reference: false, created_at: "t",
                         updated_at: "t" }],
  });
  await ctx.fetchPositions();
  listEl = $("positionList");
  listEl.children[listEl.children.length - 1].onclick();
  let goCalled = false;
  ctx.fetch = async (url) => {
    if (String(url).indexOf("/positions/7/go") !== -1) goCalled = true;
    return { ok: true, json: async () => ({ accepted: true }) };
  };
  const goPromise = ctx.goToPosition();
  check("the confirmation names the position",
        /stow/.test($("confirmBody").textContent), $("confirmBody").textContent);
  check("the confirmation states the angle it will move to",
        /-45\.5/.test($("confirmBody").textContent), $("confirmBody").textContent);
  $("confirmYes")._listeners.click();
  await goPromise;
  check("confirming sends the go command", goCalled === true);

  console.log("\n" + (failures ? failures + " FAILURE(S)" : "all checks passed"));
  process.exit(failures ? 1 : 0);
})();
