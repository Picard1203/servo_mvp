# D48 Session 26 — runbook for the executing agent

**Self-contained by design.** Everything needed to run this is in this file
and in the tool it invokes. You do not need the conversation that produced
it, the project knowledge graph, or any other document. You do not need to
read the source. Any capable coding agent — any model, any harness — should
be able to start cold from here.

Repository: `/home/egrisaru/Coding Projects/uno_q_workspace/servo_mvp`
Design and rationale (read once for context, optional): `D48_S26_REGIMEN.md`
in this directory.

You are running a **pre-registered experiment on real hardware**, with the
operator physically at the rig. The design is fixed. **Your job is to run the
tool, apply §5 and §6 literally, and then write up the findings per §8** —
you follow the rules exactly; you do not improvise, and you do not overclaim
in the write-up. Every gate is computed by the tool and written to the
findings file as an explicit verdict. You read verdicts; you never derive
your own.

**This is a continuation, not a fresh start.** B0–B6 already ran and
completed (findings already in `archive/d48_s26_findings.json`). The live
mechanism finding from that run: the oscillation is driven by the
minimum-drive floor register (`min_start_force`, held at 150 the whole time
those blocks ran) — every gain register tried (velocity-I, position-P,
velocity-P, acceleration) was `FUTILE`. **B7 and B8 below test that finding
properly.** Do not re-run B0–B6.

**A real incident happened testing this by hand: read it before touching the
servo.** A manual probe at `min_start_force=500` drove the servo into a
divergent (not bounded) oscillation violent enough that the operator cut
power immediately, and violent enough that it saturated the serial bus and
defeated every read-based safety guard, including the register restore on
exit — the value was still in EEPROM after the power cut. **This is why the
sweep below is capped at 150 and enforced in code** (`MAX_WRITABLE_MIN_START_FORCE`
in `tools/d48_s26_campaign.py` refuses any write above it). Do not raise that
ceiling, do not edit `MIN_START_FORCE_LEVELS`, and never write
`min_start_force` outside this runbook's own commands.

**If the servo ever stops answering, or starts moving in a way that alarms
the operator:** tell the operator to cut power immediately if they have not
already. Do not send it any more commands. Once the operator confirms it is
safe and ready to re-power, run the recovery tool **before** power is
restored:

```bash
python3 tools/d48_recover_registers.py --value 40
```

It waits for the servo to answer, then immediately disables torque and
rewrites `min_start_force` to a known-safe value, before anything can drive
the motor again. It leaves torque **off** on exit — re-enable it only when
the operator is ready, using the command the tool itself prints.

---

## 1. Hard rules

**Never:**
- change a threshold, sample size, arm, angle, seed or stopping rule;
- re-run a block because a result looks wrong, implausible or disappointing —
  that is the exact mistake this design exists to correct;
- override a gate verdict, including `INCONCLUSIVE` or `NO_REPRODUCTION`;
- add an arm, drop an arm, or "just quickly check" something off-plan;
- write `min_start_force` above 150, or edit `MIN_START_FORCE_LEVELS` /
  `MAX_WRITABLE_MIN_START_FORCE` in the tool — see the incident above;
- edit any source file, including the sketch, the campaign tool or the probe;
- hand-edit `archive/d48_s26_findings.json` or any CSV;
- in the §8 write-up: state a value "fixes" the problem unless it met the
  pre-registered acceptance bar (§5) at the full confirmatory N — a
  promising screening result is not a result.

**Always:**
- let the tool sequence the blocks and compute the gates;
- treat a surprising result as **data** — record it and continue;
- stop and report if the tool aborts on temperature or exhausts its retries;
- report anything the operator observes physically at the rig.

**A block that does not run is a normal outcome.** The gates exist to stop
work whose premise has been invalidated. Skipping a block because a gate
failed is the design working.

---

## 2. Prerequisites

- The operator confirms the rig is attached and they are present. Hardware
  runs are attended-only after an earlier shield fault caused a minor burn.
- `python3` and `adb` on PATH. The tool needs no third-party Python packages.
- The board reachable at `192.168.10.60`.

The sketch changed since the last session (velocity-loop registers are newly
exposed), so the **first run of the day must restart the app** so the sketch
recompiles. If the board is still running the old firmware, preflight fails
with an explicit message — restart the app and re-run rather than working
around it.

---

## 3. Setup

```bash
adb kill-server && adb start-server        # needed most sessions
ping -c2 192.168.10.60                     # reseat the cable if this fails
```

The tool builds the fast USB bridge itself (finds the container IP, rebuilds
the `socat` listener and the `adb forward`) and retries once if the measured
rate is below its floor. Do this by hand only if the tool reports it could
not.

---

## 4. Run it

```bash
cd "/home/egrisaru/Coding Projects/uno_q_workspace/servo_mvp"
python3 tools/d48_s26_campaign.py --only b7,b8 --skip-preflight
```

`--skip-preflight` is deliberate: the firmware and fast-path checks already
passed this session. If you have any doubt the app was restarted since, drop
that flag and let preflight check the sketch again — it fails loudly and
safely if the firmware is stale.

That runs B7 then B8, checkpointing each trial. Expect roughly 30–45 minutes
(B7 is a 12-value dose-response of `min_start_force`, all downward from the
established baseline of 150; B8 crosses the dead zone against it).

If it stops for any reason — **other than the servo not answering, which is
the incident above** — re-run the same command. It resumes at the first
trial with no recorded result and never repeats a completed trial.

| Block | Tests |
|---|---|
| **B7** | `min_start_force` dose-response: 0, 10, 20, 30, 40, 55, 70, 85, 100, 115, 130, 150. Reports swing, drive duty, on-target current *and* final positioning error at every value — the point is finding the highest value that still settles cleanly, because that is the one with the least steady-state droop under gravity, not just any value that stops the oscillation |
| **B8** | Dead zone (0, 1, 2 counts) crossed with the best value B7 finds, plus the 150 baseline, to see if the two levers interact |

B0–B6 already ran this session (do not re-run): B0 selected −60° as the test
angle and found the servo genuinely load-bearing there (H3: `ASYMMETRIC`,
holding current ~0.036A at −60° vs ~0.000A elsewhere); G1 `PASS` (not the
instrument); G2 `PERSISTS` (a true limit cycle, not decaying residual
energy); every gain register (B3–B6) was `FUTILE` at the fixed baseline of
`min_start_force=150`.

**B7 and B8 also already ran, and their own "best" pick was wrong.** Both
used a median-swing threshold to call a value "settled" — at N=6 that median
hid an outright coin flip (`min_start_force=85` was 3 clean / 3 oscillating
and still passed). `_record_dose_response` has since been fixed to pick by
the same pass/fail-proportion status `_record_arm_comparison` already
computes (Fisher exact against the in-block baseline), the way every other
block in this tool decides an arm. **B9 below is the confirmatory re-test
this correction calls for — run it next, do not re-run B7/B8.**

### B9 — confirmatory block (new; run this session, after B7/B8)

```bash
python3 tools/d48_s26_campaign.py --only b9 --skip-preflight
```

Tests `min_start_force` 40 and 45 (the fine-bracket sweep's own favourites)
against the 150 baseline, at real confirmatory N (screens at 6, promotes a
passing or ambiguous arm up to 16, drops a clearly futile one early — the
same sequential rule B3–B6 use), at **two** angles: −60° (the angle nothing
electronic has moved all session) and +45° (an angle the 7-angle validation
sweep also found the baseline fails). Expect roughly 15–35 minutes depending
on how quickly arms resolve. Read `comparisons.b9_m60` and `comparisons.b8_p45`
— sorry, `comparisons.b9_p45` — for each arm's status
(`MEETS_ACCEPTANCE_BAR`/`BETTER_THAN_BASELINE`/`FUTILE`/`UNDECIDED`), and
`dose_response.b9_m60`/`b9_p45` for the same table B7 printed, now with a
`status` and `osc/n` column instead of a median-swing yes/no. There is no
single `b9_best_min_start_force` — the two angles are reported and judged
separately, since B9 exists precisely because a single-angle pick already
proved unsafe to generalise.

---

## 5. What each verdict means for you

The tool prints these at the end and stores them under `gates` in the
findings file.

| Gate | Verdict | What you do |
|---|---|---|
| `target_angle` | `SELECTED` | nothing — the tool uses that angle for later blocks |
| `target_angle` | `NO_REPRODUCTION` | **Run only B1 and B2, then stop.** The fault did not reproduce today, so register results would be uninterpretable. This is the session's main finding — report it as such |
| `g1` | `PASS` | nothing — continue |
| `g1` | `PARTIAL` | continue; note that poll rate shifts severity and every later result is at the fast rate |
| `g1` | `FAIL` | the register blocks skip themselves automatically. Let B1 and B2 finish, then stop and report. Do not force them |
| `g2` | `PERSISTS` | nothing — continue |
| `g2` | `DECAYS` | continue, but flag it prominently: it changes which remedy class matters |
| `g2` | `INCONCLUSIVE` | note it and continue |
| `h3` | `SYMMETRIC` | note it — an entire mechanical branch is ruled out |
| `h3` | `ASYMMETRIC` | note it — the mechanical branch stays open |

Per-arm outcomes appear under `comparisons` as `MEETS_ACCEPTANCE_BAR`,
`BETTER_THAN_BASELINE`, `FUTILE`, `UNDECIDED` or `BASELINE`.

For B7 specifically, also read `dose_response.b7` and the printed table: each
row's `settled` column (`yes`/`NO`) and `median_abs_final_error_deg` matter
more than the oscillation label alone — a value can stop the oscillation and
still be a worse fix than a higher value that also stops it but droops less.
`b7_best_min_start_force` is the tool's own pick (highest settled value); use
it, do not recompute your own.

---

## 6. Contingencies — apply by row, do not improvise

| Situation | Response |
|---|---|
| Preflight says the board reports no `speed_p`/`speed_i` | The sketch is stale. Re-run with `--restart-app`. If it persists, stop and report |
| Preflight cannot reach the rate floor | The tool already retried the bridge rebuild. Do §3 by hand once, re-run. If it still fails, **stop and report** — do not run at the slow rate |
| "fast path degraded" mid-run | Re-run (it resumes). If it recurs twice, stop and report |
| Temperature abort (exit code 2) | Stop. Tell the operator. Do not restart until they say the servo has cooled |
| Current abort (exit code 3, `CURRENT ABORT` in the log) | The tool detected an over-driven trial and stopped itself before it could get worse. Tell the operator, do not re-run that arm, do not raise the current guard |
| Servo stops answering / repeated timeouts you cannot clear by reconnecting | **This is the incident scenario. Stop immediately.** Tell the operator to cut power if not already done. Do not send further commands. Follow the recovery procedure above before power is restored |
| Board or bridge drops | Re-run; it resumes. If three consecutive re-runs fail, stop and report |
| Register readback mismatch | The tool retries then aborts. Re-run once; if it repeats, stop and report — the write path is untrustworthy and so is any result after it |
| "WARNING: could not read ..." at preflight | Continue, but say which registers fell back to documented defaults |
| "COULD NOT RESTORE REGISTERS" on exit | Say so explicitly. The servo is **not** at baseline; the operator needs to know |
| EEPROM write budget exhausted | Stop and report. Do not raise the budget |
| Anything not in this table | Stop — the checkpoint is already safe — and report. Do not invent a response |

---

## 7. Data to keep

1. `archive/d48_s26_findings.json` — all trials, gate verdicts, thresholds,
   dose-response table, EEPROM count, temperature covariate.
2. `archive/jitter_trial_d48_s26b.csv` and `archive/jitter_trace_d48_s26b.csv`
   (note the `b` — this run uses a fresh CSV label so it never appends onto
   the pre-incident data under the old header).
3. Whether registers were restored on exit, and if not, what state they were
   left in.
4. Anything the operator saw or heard at the rig — especially whether the
   jitter was visible or audible by eye and hand, and at which angles.

---

## 8. Write-up — you do this yourself this session

Normally this would go back to a separate analysis session. This time it
does not, so **hold yourself to the same standard that session would**: cite
the numbers, do not round a screening result up to a confirmed one, and say
plainly when something is inconclusive rather than picking the more
satisfying reading.

**Write a new dated entry inside D48 in `docs/backlog/D.md`** (find the
existing `### D48` heading; add a `**Session 26 continued (finer sweep) —
[today's date]**` subsection after the existing Session 26 material — do not
delete or rewrite what is already there). Follow this project's own
convention: **facts and numbers, not narrative** — a closed item is 3–6
lines; this one is open, so give it what it needs and no more. Use the
project's glossary terms, not shorthand.

**Required content, in this shape:**

- **The dose-response table itself** — value, settled yes/no, swing,
  drive duty, on-target current, final error — for every row. This is the
  evidence; do not summarise it away.
- **The tool's pick** (`b7_best_min_start_force`) and whether it, or any
  other value, actually **met the pre-registered acceptance bar** in §5 at
  the full confirmatory N — not just looked good in screening. State the
  exact n and failure count.
- **B8's result**: did the dead zone add anything beyond B7's best value
  alone, or was it redundant / did it cost accuracy for no jitter benefit
  (the same pattern dead zone showed in Session 25)?
- **What this does and does not establish.** This session's data is one
  angle (−60°) on a bench proxy. It does not confirm the fix holds at other
  angles, under the real arm's load, or over a longer duration than the
  15–60s scoring windows used. Say this explicitly — do not let a good
  number at −60° read as "solved."
- **A concrete next step**, matching the acceptance criterion already in
  D48's entry (`docs/backlog/D.md`, "Acceptance:" paragraph): a no-regression
  check at the other angles Session 25 already characterised (0°, ±45°,
  ±60°, ±90°), and D47's real-arm verification, which stays open regardless
  of this result.
- **Any deviation from this runbook or the pre-registration**
  (`D48_S26_REGIMEN.md`), stated as a deviation, not folded into the results.

**Do not** also update `docs/PROJECT_STATE.md`, `docs/BACKLOG.md`'s own
index, or close D48 — closing it is a call for the operator to make, not
something to declare from one angle's dose-response curve. If the acceptance
bar was genuinely met at full N with no regressions checked yet, say that
plainly and leave the item open pending the regression check and D47.
