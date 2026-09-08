# D48 Session 26 — experiment regimen (pre-registration)

Written 7 September 2026, before any trial. Pre-registered: the hypotheses,
predictions, decision gates and stopping rules below are fixed **before**
data. Deviations get recorded in D48's entry as deviations, not edited in
here.

Supersedes the Session 25 resume points. Read §1 first — it invalidates part
of the basis those resume points rested on.

---

## 1. What today's re-analysis of Session 25's own data changed

Two findings, both from archive data, no hardware time.

**(a) The famous 0.2668s period exists in only two trial blocks, and those
two are the only blocks that ran at ~98Hz — and also the two earliest
blocks of the day.** Poll rate and time-of-day are perfectly confounded in
every existing trial. `resonance_campaign.py:320` calls `jp.probe()` without
passing `poll_seconds`, so all 500+ campaign trials silently used
`DEFAULT_POLL_SECONDS = 0.08` (~10.4Hz achieved) and never touched the fast
USB path the tool works hard to build.

**(b) Sampling rate is NOT the explanation, so the difference is real.**
Decimating the 98Hz traces to 8–12Hz — including with ±60% timing jitter to
mimic real HTTP polling — preserves the score exactly: 33 / 32.5 reversals,
period ~0.267s. The detector is rate-robust. Therefore the later low counts
are genuine behaviour, not missed events.

| Angle | Anchor | 13:12–13:16 (98Hz) | 16:42–17:00 (10.4Hz) |
|---|---|---|---|
| +30° | 0.0 | **33 reversals** | **0 reversals** |
| +45° | 0.0 | **32.5 reversals** | **12.5 reversals** |

Identical anchor, target, registers and day. **Either fast polling induces
the oscillation, or the system's behaviour drifts substantially over
hours.** Both are alive; existing data cannot separate them.

**Consequences.** Session 25's between-configuration comparisons (register
sweep, D-bracket, final-leg, dead-zone, move-size) each ran as a contiguous
block at a different time of day. If drift is real, every one of them is
confounded with time, which economically explains the whole non-replicating
picture — the D16 spike, ±30 flipping status, +45 clean at N=3 then 8/10
bad. Those results are **not wrong, they are uninterpretable as they
stand.** Nothing in them needs re-deriving; they need re-running under a
design that defends against drift.

Also found: temperature is not recorded per trial (no CSV column), despite
a 55°C trip that session.

---

## 2. Design principles (each answers a specific defect above)

| Principle | Defends against |
|---|---|
| **Randomised assignment of configuration order within every block** — never all N of one arm then all N of the next | drift / time-of-day confounding, the central §1 defect |
| **Control-chart baseline**: the baseline config is re-run inside every block, randomised among the arms | measures drift instead of assuming it away; gives the covariate |
| **Per-trial temperature** recorded alongside position/current | drift's leading candidate cause, currently unmeasured |
| **Sham register write in every arm, including baseline** — write the value even when unchanged | holds the torque-off/unlock/EEPROM ritual constant, so an arm differs only in the register *value* (exclusion restriction) |
| **Anchor reset + cooldown pacing between trials** | carryover between trials (SUTVA/noninterference) |
| **Sequential stopping**: screen at N=6, promote or drop on a pre-declared rule | spends trials on live candidates, not on proving duds |
| **Fine approach ON and fixed all day** | Session 25 established OFF is worse; it is a fixed condition, not a factor |

---

## 3. Outcome measures and estimands

Two different questions need two different measures, and they have very
different costs. This is the core efficiency of the regimen.

**Primary — "does it fix it": P(oscillate).** A trial is *oscillating* if
`current_mean_a` in the 5–15s window > `C_max` **or** `reversals` > `R_max`.
`C_max`/`R_max` are re-calibrated **today**, at the fast poll rate, from
clean-angle trials — yesterday's values were locked at one rate and applied
at another. Within-config spread is bimodal (CV clusters at ~0.10 or
~1.0–2.0), i.e. a trial either oscillates or does not, so a proportion is
the right model. Test: Fisher's exact, one-sided (we predict reduction).
Cost: **N≈10–16 per arm.**

**Primary — "what is the mechanism": median reversal period.** At the fast
poll rate the period is measured with sd 0.0005–0.0011s on a ~0.267s value
— **a coefficient of variation under 0.5%.** A 5% change in period is
therefore detectable with N=3–5. Test: regression of period on register
value; a change beyond ±2% is real. Cost: **N≈3–5 per arm.**

This is why the regimen front-loads mechanism discrimination: it is roughly
**four times cheaper per bit** than fix-testing, and it tells us which fix
is worth the expensive N.

**Secondary:** `current_mean_a` conditional on oscillating (amplitude),
`final_error_deg` (the accuracy cost of any candidate fix), temperature.

**SESOI.** Acceptance bar stays the pre-registered operator-facing one:
**≤1 oscillating trial in 10.** For mechanistic interest, a 50% relative
reduction in P(oscillate), or a >5% shift in period.

**Null predictions get equivalence tests, not "we failed to reject".**
Where a hypothesis predicts no effect (H6), the test is TOST against bounds
of ±5% on period and ±0.15 on P(oscillate).

---

## 4. Hypotheses

Tiered: **P**rimary (error rates controlled, central claims), **S**econdary
(motivated, may be underpowered), **E**xploratory.

### H1 (P) — Instrument. The oscillation is a property of the servo, not of the measurement.
- **Counter-hypothesis it must beat:** fast polling (≈98 bus transactions/s
  through `/servo/state`, each a real read — `.snapshot()` does no caching)
  induces or worsens the oscillation.
- **Predicts:** P(oscillate) and period are independent of poll rate once
  order is randomised.
- **Disconfirmed by:** a poll-rate main effect surviving randomisation.
- **Gate G1, three-valued** — deliberately narrow, so only the genuinely
  disqualifying outcome halts the session. Oscillation is already known to
  occur at *both* rates (10.4Hz blocks showed ~13 reversals and elevated
  current), so a bare "there is an effect" must not block register work:

  | Verdict | Condition | Consequence |
  |---|---|---|
  | **PASS** | no significant poll-rate difference in P(oscillate) | proceed; run everything at the fast rate |
  | **PARTIAL** | rate shifts severity, but oscillation present at both (P(osc)<sub>slow</sub> > 0.15) | proceed at the fast rate; poll rate becomes a **fixed condition** for all later blocks and is reported with every result |
  | **FAIL** | oscillation essentially absent when not polling fast: P(osc)<sub>slow</sub> ≤ 0.15 **and** P(osc)<sub>fast</sub> ≥ 0.6 | our instrument is implicated in the defect; register programme deferred, session pivots to characterising that |

### H2 (P) — Persistence. It is a true self-sustaining limit cycle, not decaying residual energy.
- **Counter-hypothesis:** residual elastic energy in the belt that the
  firmware's `moving` flag already calls stopped (Gemini's and Claude's
  shared Q3 mechanism) — which would decay given time.
- **Predicts:** amplitude and current roughly constant across a 60s window.
- **Disconfirmed by:** monotone decay; log-decrement fits a damped mode.
- **Gate G2:** decay → dwell-before-final-leg becomes the primary remedy
  class and register tuning drops to secondary. Persistence → the reverse.

### H3 (S) — Load asymmetry. The ±60° asymmetry is gravitational/load-borne.
- **Predicts:** steady holding current at rest differs measurably between
  +60° and −60°.
- **Prior from existing data — this is a real directional prediction that
  the data already leans against:** clean angles sit at ~0.000A holding
  current, consistent with a ~345:1 train that is essentially
  non-backdrivable and needs no current to hold. If confirmed null, **the
  entire mechanical-asymmetry branch is pruned** — no re-datum, no rig
  inversion, no belt re-tension. That is an entire research question's worth
  of planned work removed for ~6 minutes of trials.
- Note the asymmetry may not exist at all: the N=10 bad set {−60,−45,+45,+60}
  is *symmetric* in |angle|. The asymmetry lives only in intervention
  response, all of it graded under the §1-confounded design.

### H4 (P) — Velocity-loop integrator. The cycle is driven by velocity-I (0x27, default 200).
Both research passes' #1 lever; Claude's argues the 3.75Hz period is far too
slow for a position-quantiser cycle and fits integrator-vs-stiction hunting.
Position-I is 0, so velocity-I is the only integrator in stock config.
- **Predicts, directionally:** as I falls 200→0, the period *lengthens*
  monotonically and P(oscillate) falls.
- **Disconfirmed by:** period invariant to I (beyond ±2%). That result kills
  H4 outright and is exactly the "revert to the quantisation track" branch
  Claude's own report names.

### H5 (P) — Position-loop quantiser. The period is set by position-loop bandwidth.
Gemini's reading. Adjudicates directly against H4 — the two make opposite
predictions about which register moves the period, so **one block tests
both.**
- **Predicts:** period scales with position P; invariant to velocity-I.
- **Disconfirmed by:** period invariant to P.
- If *both* H4 and H5 are disconfirmed (period invariant to every register),
  the period is set by something outside the servo's control law — escalate
  to H7.

### H6 (S) — Acceleration ramp (0x29) is not load-bearing.
A null-by-design prediction from Claude's report (register shapes the
transient only). **Free to test: acceleration is already a per-move API
parameter, no code change.** Serves as a manipulation control — an arm we
expect to do nothing, which validates the rest of the design if it indeed
does nothing.
- Tested by equivalence (TOST), not NHST.

### H7 (E) — Thermal/temporal state. Severity is a function of servo temperature or run-time state.
The §1 drift finding, promoted to a hypothesis rather than treated as noise.
- **Predicts:** control-chart baseline P(oscillate) correlates with
  temperature across the session.
- Measured **for free** by the control chart running all day; no dedicated
  block. If it holds, it explains the cross-session non-replication that has
  dogged this item since Session 22, and every future D48 result needs
  temperature reported alongside it.

---

## 5. Blocks, in order. Each checkpoints per trial and resumes.

Trial ≈ 45s (anchor reset + 15s window + overhead).

| # | Block | Design | Trials | ~Time | Code? |
|---|---|---|---|---|---|
| **B0** | Target + instrument | 4 candidate angles {−60,−45,+45,+60} × 2 poll rates {0.010, 0.096} × N=4, **fully randomised** | 32 | 24m | poll fix only |
| **B1** | Persistence (H2) | 60s window, N=5, at selected angle | 5 | 8m | window param |
| **B2** | Hold current (H3) | park & hold 20s, no move, {0,±45,±60}, N=3 | 15 | 6m | hold mode |
| **B3** | Accel ramp (H6) | accel {0,10,30,100} + baseline, N=6, randomised | 30 | 23m | none |
| **B4** | Position P (H5) | P {32,24,16,12} + baseline, N=6 screen → promote | 30–60 | 23–45m | none |
| **B5** | Velocity loop (H4) | I {200,100,50,25,0}, N=6 screen → promote | 30–60 | 23–45m | **twin-path** |
| **B6** | Velocity P | 0x25 {10,20,40}, N=6 | 18 | 14m | (same) |

B0 does triple duty: picks today's worst angle, delivers the H1 poll-rate
main effect, and re-calibrates `C_max`/`R_max` at the fast rate.

**Sequential stopping (pre-declared).** After N=6 in any arm:
- ≤1/6 oscillating → **promote** to N=16 total for a confirmatory test.
- ≥4/6 → **drop** the arm, record as futile, do not spend more.
- 2–3/6 → one more block of 6 (N=12), then decide on the same rule.

**Gates.** G1 after B0 (H1 must pass before B3+). G2 after B1 (sets remedy
class). H3's null after B2 prunes the mechanical branch. **B5 requires the
twin-path change and is only written after G1 passes** — per the sequencing
below.

---

## 6. Code changes required

Ordered by when they gate a block. Everything but the last is small.

1. **`resonance_campaign.py:320` — pass `poll_seconds` through
   `probe_resilient` to `jp.probe`.** The one-line §1 defect. Blocks
   everything.
2. **`jitter_probe.py` — record temperature per trial** (new CSV column;
   `/servo/state` already returns `temperature_c`) and **parameterise
   `WINDOW_SECONDS`** (currently a module constant; B1 needs 60s).
3. **Campaign: randomised-block runner** — a helper that takes arms, N, and
   a baseline, emits a randomised trial order, applies the sham write, and
   checkpoints per trial. Replaces the per-phase sequential loops.
4. **Hold-without-move probe** for B2.
5. **(Gated, only after G1) Expose 0x25/0x27 on the twin path**:
   `TuningSnapshot` + `ReadTuningRegisters`/`WriteTuningRegisters`
   (`ServoController.cpp/.h`), Bridge RPC, `TuningRegisters` entity, API
   request/response, simulated repository, tests, `check_bridge_contract.py`.
   ~1–1.5h. **Not started before G1 passes** — if polling induces the
   oscillation, this work is wasted.

Registers 0x25/0x27 sit in EEPROM: writes need torque-off + unlock. Position
P/D already go through that path, so the pattern exists. EEPROM write count
is capped and logged (see §7).

---

## 7. Contingencies — pre-declared, so the run does not need me to improvise

The point of this section is that a surprise resolves by rule, not by
stopping to re-plan.

| Situation | Pre-declared response |
|---|---|
| **No candidate angle reproduces** (all <4/6 in B0) | Run 11-angle N=4 sweep. Still none → the fault is state-dependent; session pivots to H7 (thermal/temporal) and does **not** go register-hunting on a non-reproducing fault |
| Board/bridge drop | Existing resilient retry; >3 consecutive failures → checkpoint, abort block, alert operator |
| Temperature >50°C | Existing hard abort; cooldown; resume from checkpoint |
| Temperature elevated but <50°C | Existing cooldown pacer; temperature recorded as covariate either way |
| Register readback mismatch | Retry once; then abort that arm, record it, continue with the rest |
| An arm makes the servo unstable or hot | Revert immediately, mark arm unsafe, continue the block |
| Control chart shows drift mid-block | Comparisons stay valid (randomisation protects them); flag for covariate adjustment. **Do not re-run** — that is the trap Session 25 fell into |
| Bimodal arm straddles the stopping rule | The N=12 re-screen rule decides it; no judgement call |
| Out of time | Blocks are ordered by information value and each checkpoints per trial; stop anywhere, resume next session |
| EEPROM writes | Capped at 200 for the session and counted in the findings file |

**Registers are restored to baseline on normal exit, on abort, and on
temperature trip.** Baseline is recorded in the findings file at session
start, read from the servo, not assumed.

---

## 8. What this regimen will and will not settle

**Will settle:** whether our own instrument is part of the defect (H1);
whether it is a limit cycle or residual ringing (H2); whether the mechanical
asymmetry branch is worth any further work (H3); which of the two competing
research diagnoses is right, or whether both are wrong (H4 vs H5, adjudicated
on period).

**Will not settle:** the real arm. Every number here is bench-proxy. A
configuration that passes still needs D47. Both research passes agree the
specific bad angles are a property of the real assembly's inertia and
mounting, and today cannot change that.

**Honest note on what a pass means.** With the §1 drift finding unresolved,
even a clean N=16 result is a claim about today's machine state. The control
chart is what lets us say how much of that to trust, and it should be
reported with every result rather than dropped.

---

## 9. Orchestration contract — the running agent is Sonnet, not a human

This regimen is executed by a Claude Sonnet session, with the operator
physically present at the rig (hardware runs are attended-only since the
Session 25 shield incident). Conclusions come back to Opus. The design is
therefore built so that **judgement lives in the tool, not in the running
agent.**

**Every gate is computed and written, never inferred.** The campaign tool
evaluates each gate itself and writes an explicit verdict to
`archive/d48_s26_findings.json` — `"gate_g1": {"verdict": "PASS"|"FAIL"|
"INCONCLUSIVE", "evidence": {...}}` — and prints it. The running agent reads
the verdict. It does not compute Fisher tests, compare proportions, or
decide what a result means. Angle selection, sequential
promote/drop/re-screen, and the equivalence tests are all likewise computed
by the tool and written as directives.

**The running agent MUST NOT:**
- change any threshold, N, arm, angle, or stopping rule;
- re-run a block because the result looks wrong, implausible, or
  disappointing — that is precisely the Session 25 trap;
- reinterpret or override a gate verdict, including `INCONCLUSIVE`;
- add or drop an arm, or "quickly check" something off-plan;
- draw mechanism conclusions, or write them into D48;
- start the twin-path code change (§6.5) or edit any sketch/Python source.

**The running agent MUST:**
- run the named command, and let the tool sequence the blocks;
- apply the §7 contingency table literally, by row;
- treat a surprising result as **data**: record it, let the tool continue.
  Investigation is Opus's job, after the run;
- stop and report if the tool aborts on temperature or exhausts retries;
- keep the findings file and run log intact — never hand-edit either.

**The one area of allowed discretion is infrastructure**, where a known
recipe exists (D48's own environment notes): `adb kill-server && adb
start-server`; re-seating the wired NIC if `ping 192.168.10.60` fails;
rebuilding the `socat` bridge and `adb forward` if the container IP changed.
The tool already automates these; the agent may re-run them. Nothing else.

**Fast poll path is mandatory.** B0's poll-rate arms need both ~98Hz and
~10.4Hz. If the fast path cannot be established, the tool aborts rather than
silently falling back to the slow default — that silent fallback is the §1
defect and must not be able to recur.

## 10. Handback to Opus

At the end of the run, the agent returns, without interpretation:

1. `archive/d48_s26_findings.json` — all trials, gate verdicts, control-chart
   points, temperature covariate, EEPROM write count.
2. The per-trial CSVs (`jitter_trial_*` / `jitter_trace_*`).
3. A factual run log: blocks completed, blocks skipped and the gate that
   skipped them, every contingency-table row that fired and when, and
   anything the operator observed physically at the rig.
4. Any deviation from this document, stated as a deviation.

Opus then does the analysis, decides what it means for H1–H7, and writes
D48. **A block that did not run is a normal outcome**, not a failure — the
gates exist to stop work whose premise has been invalidated.
