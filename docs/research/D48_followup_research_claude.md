# Servo Settling-Jitter Reconciliation: STS3215 Belt-Drive Limit Cycle

**Source:** deep-research response from Claude, 7 September 2026, run against
the prompt in `D48_followup_research_prompt.md` (the second research pass,
following up on `D40_resonance_research_claude.md`/`_gemini.md` now that
Session 25's actual experiments contradicted several of that first pass's
predictions). Filed alongside `D48_followup_research_gemini.md` per that
file's own note — not overwriting it. Kept verbatim as the reasoning is the
record — do not edit in place; correct or supersede in D48's own entry
instead. **Diverges from Gemini's answer to the same prompt on the root
cause**: Gemini argues sensor-quantization limit cycling; this argues
integrator-driven friction/deadband hunting (velocity-loop I, register 39)
with quantization as a contributing nonlinearity, not the primary cause —
both agree the velocity loop (37/39) is the untested, highest-value lever.
Reconcile the disagreement with a real experiment (the velocity-I sweep both
propose), not by picking the more appealing story.

---

## TL;DR

- The user's core inference is half-right: the reversal period's repeatability to 4 significant figures correctly rules out mechanical resonance and random stick-slip, but it does **not** uniquely identify *sensor quantization* as the driver. A 3.75 Hz (0.267 s) cycle is far too slow for a pure position-quantizer limit cycle in a fast inner loop; it is the classic signature of an **integrator-driven friction/deadband "hunting" limit cycle** — here almost certainly the untouched velocity-loop integrator (register 39, default 200) winding up against stiction and the firmware dead zone. Quantization is a contributing nonlinearity, not the sole cause.
- This reframing explains every "paradoxical" result: D-gain is the wrong axis (its apparent optimum was statistical noise, p=0.070); softening the final leg makes things worse because low commanded velocity pushes the actuator into the Stribeck/stiction regime; larger preceding moves store more belt wind-up energy that is still ringing when the "stopped" flag (derived from the coarse motor/encoder-side velocity estimate) fires; and left/right asymmetry points to encoder-magnet eccentricity, cogging phase, gravity, or belt tight/slack-side asymmetry rather than the control law.
- Highest-value untested lever is the **velocity loop**: sweep register 39 (velocity-I) downward from 200 and register 37 (velocity-P) — with a host-side supervisory hysteretic in-position window as the escape hatch. The 1 Mbps bus supports a host loop of roughly 200–1000 Hz for one servo, more than fast enough to police a 3.75 Hz cycle.

## Key Findings

1. **The register map is confirmed with two firmware-dependent caveats.** The STS3215/SCS control table is: 21 = position-loop P (default 32), 22 = position-loop D (default 32), 23 = position-loop I (default 0), 24 = minimum startup force / "punch" (default 0), 26/27 = CW/CCW dead zone, 28 = overcurrent-protection threshold, 33 = operating mode (0 position / 1 constant-speed / 2 PWM / 3 step), 34 = protective torque, 35 = protection time, 36 = overload-torque threshold, 37 = **speed-loop P (default 10)**, 38 = overcurrent-protection time (default 200), 39 = **velocity-loop I (default 200)**, 40 = torque enable, 41 = acceleration, 42 = goal position, 46 = goal speed, 56 = present position, 58 = present speed, 60 = present load, 69 = present current. Caveats: (a) the *user-facing* dead-zone registers 26/27 default to 0 on this bench, but Robo9/Robonine's teardown documents a separate **firmware-defined dead zone of ~10 encoder counts** on the STS3215 ("there's a built-in dead zone of 10 encoder counts, meaning the motor ignores small commands within that range"; "Command input < 10 encoder steps → No motion observed") — a crucial detail, because a ~10-count internal deadband is a large nonlinearity that dominates the sub-count quantization argument. (b) The classic Feetech **SCS-series** memory table (feetechrc.com tutorial PDF) repurposes addresses 37/39 as "Address: 37 protection torque" and "Address: 39 … Overload torque: 80%"; the STS3215 speed-P / velocity-I meanings above are the correct ones for this servo — a genuine cross-series difference to guard against.
2. **The acceleration register (41) is a trapezoidal-ramp shaper with unit 100 steps/s² and an effective cap at 150.** A value of 10 = 1000 steps/s². The user's "no effect above ~50" observation is fully explained: 50 → 5000 steps/s², already large enough that the accel phase of a short move completes almost instantly, so the profile saturates and higher values change nothing. This register shapes only the transient, not the steady-state hold, so it is predicted to have little effect on settling jitter.
3. **Registers 37/39 (velocity loop) have never been touched and are the prime suspects.** The servo runs a cascade: outer position loop (21/22/23) commanding an inner velocity loop (37/39). Position-loop I is 0, so the *only* integrator in the stock configuration is velocity-loop I = 200. Integrator + stiction is the textbook recipe for slow hunting limit cycles.
4. **Internal loop rate and velocity-estimation method are undocumented.** Feetech publishes neither the internal PID sample rate nor how the velocity estimate is formed. The most plausible mechanism — a backward difference of the quantized 12-bit encoder (4096 steps/rev, 0.088°/step) — is inference, not documented fact, and it matters directly to the quantization argument.
5. **Host-side loop rate is fast enough for a supervisory fix.** At 1 Mbps, 8N1, a read+response is ~16 bytes ≈ 160 µs of wire time; the dominant real-world cost is USB-adapter latency-timer and half-duplex turnaround. With the latency timer minimized and the servo's Return_Delay_Time reduced from its 500 µs default to ~2 µs, a single-servo read+write cycle of roughly 1–5 ms (≈200–1000 Hz) is realistic — orders of magnitude above the 3.75 Hz cycle to be suppressed.

## Details

### Q1 — Does quantizer-limit-cycle theory predict the non-monotonic D response, or is D the wrong axis?

**The literature does NOT support "pure sensor quantization" as the mechanism, and it says D is largely the wrong axis.**

Peterchev & Sanders (IEEE Trans. Power Electron. 18(1):301–308, Jan 2003, doi:10.1109/TPEL.2002.807092) establish the canonical no-limit-cycle condition for a digitally controlled loop with integral action: the actuator's effective output resolution must be finer than the sensor's quantization bin, *and* they model the round-off quantizer with a describing function whose gain rises as the input amplitude falls below one bin. Crucially, their analysis requires **integral action** to force the steady-state DC offset at the quantizer to zero (so the zero-offset describing function applies). The mechanism is fundamentally an *integrator hunting across quantization bins*, not quantization alone. This is the single most important reconciliation point: the user's citation is apt, but the paper's own mechanism is integrator-plus-quantizer, which reframes the diagnosis toward the velocity-loop integrator.

The frequency is the tell. A pure position-quantizer limit cycle in a fast inner loop oscillates near the loop rate (typically hundreds of Hz to kHz). The observed **3.75 Hz is ~2–3 orders of magnitude too slow** for that. Slow limit cycles are produced by integral action: the integrator ramps until its output overcomes stiction/deadband, the joint breaks free, overshoots, re-sticks, and the cycle repeats. The period is set by the integrator ramp rate (gain) and the stiction/inertia — both fixed and deterministic, which is exactly why the period repeats to 4 significant figures. **Repeatability therefore does NOT discriminate quantization from integrator-hunting; it only excludes mechanical resonance (set by mass/stiffness) and random stick-slip (irregular).** The user's exclusion logic is sound; the positive identification of "quantization" is not. Note also that a ~10-count firmware dead zone (Key Finding 1) makes a *sub-count* quantizer cycle implausible as the sole story — the servo already ignores errors well above one count.

Derivative action on a quantized signal: if the firmware differentiates the raw quantized position by finite difference, every one-count transition looks like an impulse to the D path ("derivative kick" on measurement noise). Standard practice is to low-pass the derivative; whether the STS firmware does is undocumented, but the empirical non-monotonicity (D8 worse, D16 best, D32 worse than baseline) is *qualitatively* the predicted trade-off: too little D leaves the loop underdamped and hunting; too much D amplifies quantization noise into chatter. **However, the user's own follow-up bracket demolishes the D16 optimum**: D14 = 7/8, D18 = 8/8, D20 = 6/8 fails surrounding an isolated D16 = 2/10, with Fisher's exact D16-vs-baseline p = 0.070 (not significant). The honest read is that D16 was a lucky draw and **D-gain is a weak axis for this mechanism**. Theory agrees: derivative damping cannot cure an integrator-driven hunting cycle whose energy source is the velocity-loop integrator you have not touched. The load-bearing axes are the velocity loop (37/39) and effective sensor/actuator resolution (dither, deadband), not position-loop D.

### Q2 — Why does softening the final corrective leg make settling reliably worse?

This is the strongest single piece of evidence for a **friction/stiction mechanism**, and it is exactly backwards from what a "gentle landing" intuition predicts — but exactly what the friction literature predicts.

At very low commanded velocity the actuator operates on the falling (Stribeck) branch of the friction curve, where static friction exceeds Coulomb friction. Armstrong-Hélouvry, Dupont & Canudas de Wit's survey (Automatica 30:1083–1138, 1994) and Olsson & Åström ("Friction Generated Limit Cycles," IEEE Trans. Control Syst. Technol. 9(4):629–636, 2001) show that a PID/PI loop driving through the Stribeck region is precisely where hunting limit cycles are born: the integrator builds torque against stiction, breaks free abruptly, overshoots, and re-sticks. This servo is measured to show exactly the low-speed instability the theory predicts — Robo9/Robonine's bench characterisation records no-load speeds of 45.6 RPM (±0.48) at 100% command, 21.9 RPM at 50%, and only 2.3 RPM at 5%, noting "minor oscillations were observed at lower speeds." A slow final leg *maximizes* time spent in this regime; a fast final leg carries enough momentum and commanded torque to break through stiction and backlash in one motion and arrive with the error already inside the holding band, minimizing integrator wind-up. Additional low-speed pathologies reinforce this: minimum startup force / "punch" (register 24) and PWM minimum-duty/dead-time effects mean that below some duty the motor does not move until the integrator accumulates, then jumps (micro stick-slip); and cogging torque, amplified by the 1:345 gearset, creates preferred "snap" positions most disruptive at crawl speed.

The overshoot-reduction result (1.5° → 0.5° made it worse, 8/8) is the **anti-backlash mechanism failing**: Robo9/Robonine measured **0.87° of output backlash (0.0151 rad, from 1.3 mm displacement at an 86 mm lever) — well above the ≤0.5° datasheet spec** and equivalent to ~14–15 counts at the motor, orders of magnitude above one count. A 1.5° overshoot reliably drives the gear train hard against one flank so the final corrective leg approaches from a fully-loaded, backlash-free direction; a 0.5° overshoot may not fully take up that ~0.87° of free play, so the final leg spends part of its travel crossing backlash at low speed — right back in the stiction/lost-motion regime. **A faster corrective move closes a sub-count error more reliably because it converts the last fraction of a count into a momentum-carried, single-strike arrival rather than a creep that the stiction/deadband nonlinearity can trap.**

### Q3 — Is "residual belt energy that a coarse velocity estimate already calls stopped" a named phenomenon?

**Yes, on both halves.** The general phenomenon is residual vibration in a flexible-joint / two-inertia (motor-side vs load-side) system, and the specific failure mode — declaring "settled" before the load has actually settled — is the well-documented **in-position (INP) false positive / settle-detection-vs-actual-settling** distinction. Disk-drive servo patents (e.g. US 5,646,797) implement explicit hysteresis and dwell/settle windows on the position-error signal precisely to keep encoder-side noise and residual ring from prematurely or falsely asserting "on track." The STS3215's `Moving` flag (register 66) is derived from the servo's own motor/encoder-side velocity estimate; on a compliant belt the *load* can still be ringing after the encoder-side reads zero — the classic **encoder-side vs load-side settle discrepancy**.

This directly explains the move-size effect (Experiment 3): a ~150° preceding move stores far more elastic wind-up energy in the belt and excites the two-inertia mode more strongly than a ~5° approach, so when the final leg begins — after `Moving` clears on the motor side — the load is still oscillating, seeding the hunting cycle. Established diagnostics: (i) settle-time as a function of preceding-move size / load inertia; (ii) log-decrement of the residual oscillation to extract the mode's damping and frequency; (iii) direct encoder-side vs load-side settle comparison (requires an external sensor on the output).

Established remedies, in rough order of effort: a **mandatory dwell before the final leg, scaled to the preceding move size**; input shaping (ZV or the more robust ZVD shaper — Singer & Seering, 1990; a ZV shaper adds half a vibration period, ZVD one full period, to the command); S-curve profiles; and load-side sensing.

**Sizing the dwell — with an important caveat.** The 0.267 s period is almost certainly the *integrator-hunting* period, not the belt mode. A belt torsional/two-inertia mode on a low-inertia paddle with a stiff short belt is expected in the tens-to-hundreds of Hz, not 3.75 Hz. So **do not size the dwell from 0.267 s.** Instead, command a step, capture the ~100 Hz position/current trace on ring-down, measure the actual residual oscillation frequency f_belt and its decay, and set the dwell to 3–5 time constants (≈ 3–5/(ζ·2π·f_belt)); as a rule of thumb, 3–5 periods of f_belt. Scale the dwell linearly (with a small floor) with preceding-move size. The 0.267 s number is diagnostic of the *integrator* (Q5), not of the belt.

### Q4 — What causes consistent left/right asymmetry when the control law is direction-symmetric?

Ranked by diagnosability from the servo's own telemetry (position/current/load/voltage/temperature) vs requiring mechanical inspection:

1. **Gravity-assisted vs gravity-opposed on an unbalanced rig — MOST diagnosable.** Telemetry signature: asymmetric steady holding current/load (registers 60/69) between +60° and −60°, and asymmetric current during the two approach directions. Cheap discriminator: invert the rig (or re-mount so gravity torque flips sign) — if the bad side follows gravity, confirmed.
2. **Belt pretension tight-side vs slack-side asymmetry — diagnosable.** One travel direction loads the stiff tight span, the other the compliant slack span, giving direction-dependent effective stiffness and residual ring (classic in belt-drive dynamics, where tight-side vs slack-side spring constants differ). Signature: asymmetric load and settle time. Discriminator: re-tension the belt, or rotate the load 180° on the pulley and see whether the asymmetry moves with output angle or stays with direction.
3. **Encoder magnet eccentricity / non-linearity — highly diagnosable, and a top suspect given the mechanism.** An off-center magnet produces a once-per-revolution sinusoidal angle-error (r_e(θ) = r₀ + a₁·sin(θ−φ₁)); a tilted magnet gives a twice-per-rev error. At the encoder count where the error curve's slope is steepest, the local effective quantization and loop gain are worst, so a specific *encoder count* — not output angle — jitters. AS5600-class magnetic encoders (the same family as the STS3215's sensor) are quoted at ±0.5° typical accuracy with optimal placement, degrading with eccentricity — comparable to several counts. Signature: failure tracks encoder count, not mechanical angle. **Decisive cheap experiment (do this first): re-datum so the same output angle sits at a different encoder count.** If failure follows the count, it is encoder nonlinearity/eccentricity.
4. **Motor cogging phase relative to electrical angle — diagnosable via the same sweep.** Cogging snap-points recur at the pole-passing period; map failure vs count modulo one motor revolution — a periodic failure pattern at the cogging period implicates cogging (most disruptive at low speed, per the cogging literature).
5. **Separate CW/CCW dead-zone or punch registers — diagnosable but partly tested.** Even with 26/27 symmetric, an asymmetric interaction between punch (24) and gravity can appear directional; confirm by swapping.
6. **One-sided backlash from off-center mounting / gear-mesh position — requires mechanical inspection**, though rotating the load 180° on the pulley is a cheap partial discriminator.

The single most informative experiment is the **whole-travel failure-rate map vs encoder count** (and vs count-mod-motor-rev): it simultaneously tests eccentricity (once/rev), cogging (pole period), and mechanical-angle dependence in one sweep.

### Q5 — Predictions and test plan for the untouched velocity loop (37/39) and acceleration (41)

**Predictions under the corrected (integrator-hunting) mechanism:**

- **Velocity-I (register 39, default 200): the dominant driver.** With position-loop I = 0, this is the only integrator, and integrator gain sets the hunting ramp rate — hence the 3.75 Hz period. Prediction: reducing 39 (toward 100, 50, 25) reduces or eliminates the slow cycle at the cost of steady-state stiffness/holding accuracy — directly supported by the integrator-leakage-for-hunting-suppression literature (ASME J. Dyn. Sys. Meas. Control, "Integrator Leakage for Limit Cycle Suppression in Servo Mechanisms With Stiction"). If lowering 39 does *nothing*, that is the experiment that would resurrect the pure-quantization hypothesis.
- **Velocity-P (register 37, default 10):** adds inner-loop damping; raising it may tighten velocity tracking and reduce overshoot into stiction, but the effect is secondary and could worsen quantization-noise pickup. Ambiguous a priori.
- **Acceleration (register 41):** predicted near-null on settling jitter (it shapes transient only), consistent with the "no effect above ~50" observation.

**Velocity-loop estimate:** most plausibly a backward difference of the quantized position (undocumented — flag as inference). If so, at low speed the differenced-quantized velocity is itself a coarse staircase feeding the velocity-I integrator — a second route by which quantization enters, but *through* the integrator, reinforcing the reframing.

**Ordered test plan (pre-registered style, pass bar ≤1 failure/10 at each of the two test angles):**

1. **Velocity-I sweep** (register 39): values 200 (baseline), 150, 100, 50, 25; N=20 each (raise N because effects may be graded). Expected signature: monotone reduction of failure rate and lengthening/disappearance of the 0.267 s cycle as I falls; watch steady-state error creeping up. Highest-value experiment — run it first.
2. **Velocity-P sweep** (register 37): 10, 20, 40; N=10. Expected: modest change; possible increase in high-frequency chatter at 40 if quantization noise is amplified.
3. **Confirm acceleration null** (register 41): 0, 30, 100; N=10. Expected: no significant change — a control that validates the mechanism.
4. **Only if 1–3 fail:** dither injection (host-side small pseudo-random ±1 count on goal position, Peterchev–Sanders style) and/or the escape hatches below.

Note that 37/39 sit in the EEPROM region: changing them requires torque-off + unlock (register 55), so they are fine to set once per configuration but cannot be scheduled on the fly.

**Mode changes and host escape hatch.** The servo supports position (mode 0), constant-speed (1), PWM/open-loop (2), and step (3) modes via register 33. Running the inner loop in a different mode does not remove friction, but **closing the loop on the host is a viable escape hatch**: a host supervisory loop at ~200–1000 Hz can implement its own position control with an explicit hysteretic in-position window, integrator leakage, and dither — none of which the stock firmware exposes. Against a 3.75 Hz cycle this is comfortably fast (Nyquist needs >7.5 Hz; you have 25–100×).

### Q6 — Is a non-uniform / hysteretic dead zone a documented technique, and can this servo do it?

**Documented, yes.** Hysteretic (Schmitt-trigger) deadband, the "in-position window with hysteresis" (standard in disk-drive and precision-stage servos to stop noise-driven boundary chatter — US 5,646,797 explicitly adds hysteresis zones around the position-error window "to prevent the noise from causing undesirable switching oscillations"), gain scheduling near setpoint, integral-only "trim" near target, dither injection (Peterchev–Sanders), and PID-with-error-deadband anti-hunt logic in industrial motion/valve controllers are all established. The specific idea of a dead zone that engages only after N consecutive same-sign counts, or is wide during correction and ~zero once settled, is exactly the "in-position window with hysteresis + settle counter" pattern found in the disk-drive servo patents.

**Achievability on this servo — the binding constraint is EEPROM vs RAM:**

- **Dead-zone registers 26/27 are EEPROM.** Writing them dynamically requires torque-off + unlock/lock and incurs EEPROM wear — **not feasible at loop rate.** A hardware hysteretic deadband inside the servo firmware cannot be synthesised this way. (And recall the servo also has a fixed ~10-count internal dead zone that you cannot remove.)
- **Position P/D (21/22) are also EEPROM** → **on-the-fly gain scheduling near setpoint is not feasible over the bus** without EEPROM writes. Key negative result: the "switch P/D near target" idea is impractical on stock firmware.
- **Torque enable (register 40) is RAM** → can be toggled fast; a crude "release inside window, re-grab outside" scheme is possible but risks drift/backlash.
- **Host supervisory loop is the practical route.** At ~200–1000 Hz the host can implement a hysteretic in-position window (command corrections only when |error| exceeds an outer threshold, stop correcting until it re-exceeds it, optionally after N consecutive same-sign counts), integrator-only trim, and ±1-count dither on the goal position. All are synthesizable from RAM-level writes (goal position 42, torque enable 40) plus fast reads (position 56, current 69).
- **Requires firmware not present:** a true internal hysteretic deadband, internal integral-leakage, and internal near-setpoint gain scheduling are not exposed by the vendored SCServo SDK.

**Is the host loop fast enough?** Yes. A 3.75 Hz limit cycle has a 267 ms period; a 1–5 ms host cycle samples it 50–250×, ample to detect boundary crossings and apply hysteresis/dither. The realistic bottleneck is USB-adapter latency (minimise the FTDI/CH340 latency timer and set Return_Delay_Time to 0) rather than the 1 Mbps wire.

## Recommendations

**Stage 1 — Diagnose the mechanism (cheap, decisive, do before more tuning):**

1. **Re-datum experiment:** move the servo's zero so +60°/−60° output sits at different encoder counts. If failure follows encoder count, it is encoder eccentricity/nonlinearity (Q4). Benchmark that flips the plan: if failure tracks count not angle, prioritise dither and host-side sub-count estimation over velocity-loop tuning.
2. **Whole-travel sweep:** map failure rate vs encoder count and vs count-mod-one-motor-revolution. Periodicity at once/rev → eccentricity; at the cogging period → cogging.
3. **Gravity/belt discriminators:** invert the rig and rotate the load 180° on the pulley; watch holding current (60/69) for left/right asymmetry.
4. **Ring-down capture:** command a step, record the ~100 Hz trace, measure the true belt residual frequency f_belt and its log-decrement. This sizes any dwell time and confirms the belt mode is much faster than 3.75 Hz.

**Stage 2 — Attack the integrator (highest expected payoff):**

5. Run the **velocity-I sweep (register 39: 200→150→100→50→25, N=20)**. Threshold: if failure rate falls monotonically and the 0.267 s cycle lengthens/vanishes, the integrator-hunting diagnosis is confirmed and you tune 39 to the knee that still meets your steady-state error budget. If no change, revert to the quantization track (dither).
6. Follow with the **velocity-P sweep (37: 10→20→40, N=10)** and the **acceleration null control (41: 0/30/100)**.

**Stage 3 — If registers are exhausted, go host-side:**

7. Implement a **host supervisory hysteretic in-position window + ±1-count dither** on goal position at the maximum achievable loop rate (minimise USB latency timer; set Return_Delay_Time = 0). Add the integrator-leakage semantics the firmware lacks.
8. Retain the **fast, full-overshoot anti-backlash final leg** (the unsoftened default was best) and add a **move-size-scaled dwell** sized from the measured f_belt, not from 0.267 s.

**What would change these recommendations:** if the re-datum sweep shows failure locked to encoder count, dither/resolution enhancement moves ahead of velocity-loop tuning. If holding current is strongly asymmetric with gravity, mechanically rebalance the paddle before any further register work. If the velocity-I sweep is null, the pure-quantization hypothesis is back and the dither/host-resolution path becomes primary.

## Caveats

- The single largest evidence gap is that **the STS3215's internal control-loop rate and velocity-estimation method are undocumented by Feetech.** The "integrator-hunting at 3.75 Hz" diagnosis is a strong inference from the frequency, the low current (0.026–0.058 A), the untouched velocity-I=200, the measured low-speed oscillation, and the friction literature — but it is not proven; the velocity-I sweep (Recommendation 5) is the experiment that confirms or refutes it.
- Repeatability of the period to 4 significant figures rules out mechanical resonance and random stick-slip but does **not** by itself distinguish sensor-quantization limit cycling from integrator-driven friction hunting — both are deterministic and both repeat.
- The belt two-inertia mode frequency is *assumed* to be well above 3.75 Hz (tens–hundreds of Hz); this must be measured (Recommendation 4) before sizing any dwell.
- Register semantics and defaults vary by firmware version and across the SCS/STS/SMS families; the map above is for STS3215-class firmware and should be re-read from the servo. Note the servo carries a fixed firmware dead zone (~10 counts per Robo9/Robonine) in addition to the user-settable 26/27 registers.
- Host-side round-trip Hz (≈200–1000 Hz single-servo) is an engineering estimate from packet sizes and the known USB-latency bottleneck, not a rigorous published STS3215 benchmark; measure it on your own rig before relying on a specific supervisory rate.
- The D16 optimum is statistically a null result (p=0.070); treating it as real would be a mistake.
