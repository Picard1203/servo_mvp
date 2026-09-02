# Load-Dependent Settling Oscillation in a Geared STS3215 Serial-Bus Servo: Diagnosis and Remedies

**Source:** deep-research response from Claude, 2 September 2026, run against the
prompt in this session's own record (see D48 in `docs/backlog/D.md` for
context and how this feeds the next experiment). Kept verbatim as the
reasoning is the record — do not edit in place; correct or supersede in
D48/D40's own entries instead.

## TL;DR
- The symptom is most consistent with a **load-coupled resonant/compliance-driven limit cycle** interacting with the servo's discrete position loop and near-target friction — not pure Coulomb stick-slip. The single most load-tested remedy in this exact ecosystem is **lowering the position-loop P gain**: Xingdong Zuo's HuggingFace LeKiwi/PincOpen build report (June 7, 2026) calls it "the MOST CRITICAL fix," the LeRobot codebase ships P=16 (down from factory 32), and that build lowers it to 10 on the four biggest joints.
- The STS3215 exposes tuning beyond position P/I/D, MinStartForce and dead zone: a **velocity-loop P (register 37, default 10) and velocity-loop I (register 39, default 200)**, plus an **acceleration/ramp register (41, unit = 100 steps/s², 0 = max acceleration)** that provides trapezoidal profile shaping — the closest thing the servo has to resonance-avoidance trajectory shaping. There is no notch filter or low-pass constant in this servo's firmware, and the **position D gain (register 22, default 32) has never been changed** and is your most direct untried damping lever.
- You probably **cannot reliably predict whether the problem reproduces on the real arm** from the bench proxy, because resonant frequency is set by the real assembly's inertia and mounting stiffness, both of which change with joint angle — but you CAN bound it with a couple of cheap, decisive bench experiments (a fast current/load-spectrum log and a D-gain/acceleration sweep) that distinguish resonance from friction before the real arm exists.

## Key Findings

**1. The literature strongly supports two distinct failure modes, and your evidence points at the resonance/compliance one.**
Friction-induced limit cycles (stick-slip) and compliance/load-induced resonant limit cycles are both well documented, and both produce sustained low-amplitude oscillation near a commanded target. Ramírez & Guesalaga (*A Friction Model Describing Limit Cycles in Positioning Servos*, Journal of Defense Modeling & Simulation, 2009) integrate friction, backlash, controller and process dynamics in one closed loop and state that the model "reproduces the dependence of the resonant frequencies to the rotating velocity that is generally observed in this type of feedback system" — i.e., resonant behavior is load/state-dependent, a signature you observed. Distinguishing signatures from the literature:
- *Stick-slip*: amplitude and behavior largely deterministic at fixed settings; monotonic threshold response to friction-floor and gain changes; worsens as stiction/Coulomb ratio rises; classic ~1 Hz, ~0.1 mm limit cycle; exacerbated by compliant coupling.
- *Resonance/two-mass compliance*: frequency set by reflected load inertia and coupling stiffness; strongly position/orientation-dependent; intermittent and phase/timing-sensitive; suppressed by damping.
Your four observations — non-monotonic response to MinStartForce and P, overshoot magnitude not mattering, position-specific severity unrelated to travel limits, and ~40–60% intermittency — line up better with the resonance/compliance column.

**2. ~10 Hz position-vs-time logging is insufficient to confirm the mechanism.** Belt-transmission mechanical resonances typically fall in the tens-to-hundreds of Hz (industry sources cite 30–300 Hz for toothed-belt and harmonic drives). Your 80–150 ms polling (≈7–12 Hz) is far below the Nyquist limit for those frequencies and will alias. It CAN reveal a slow (~1 Hz) stick-slip limit cycle, but it cannot confirm or exclude a mechanical resonance. Distinguishing them properly needs either the servo's Present-Current/Present-Load telemetry logged fast, or an accelerometer/FFT.

**3. The dominant, load-validated community remedy is lowering position-loop P — precisely, not "just lower P" as a platitude.** Zuo's LeKiwi/PincOpen build report, after exhaustively sweeping acceleration, max torque limit, overload torque and protective torque, concluded those were "all unnecessary" and that "the ultimate solution is simply to lower the P-gain from its default… This is the MOST CRITICAL fix." That build sets arm P=14 ("14: smooth, 16: jittery") and lowers it to 10 on the four big joints (shoulder_pan, shoulder_lift, elbow_flex, wrist_flex — "10: smooth, 12: jittery"). LeRobot's default `configure()` writes P_Coefficient=16, I=0, D=32 with the source comment "Set P_Coefficient to lower value to avoid shakiness (Default is 32)." The sprung-gripper uses P=8 with Torque_Limit=75. This corroborates your own finding that P=24 helped and P=16 removed trembling.

**4. The STS3215 has velocity-loop gains and an acceleration ramp you have not yet touched.** A live register dump (iotdesignshop/Feetech-tuna) confirms register 37 "Speed closed loop P proportional coefficient" (default 10) and register 39 "Velocity closed loop I integral coefficient" (default 200) — a full inner velocity PI loop separate from the position P/I/D you have been tuning. Register 41 "Acceleration" (unit = 100 steps/s², 0 = max acceleration) shapes the trapezoidal start/stop ramp.

**5. Deliberate-overshoot anti-backlash positioning has a documented failure interaction, and there is a cleaner alternative.** The final approach leg is itself a small point-to-point move whose deceleration can excite the resonance; input-shaping and S-curve literature show that abrupt stops inject energy at the natural frequency. The better-established backlash technique remains *unidirectional (single-direction) approach* — which you already use — but it does not require a fixed large overshoot: the correct form is to always finish the LAST segment moving in one consistent direction, sized just above backlash, with a smoothed (jerk-limited/acceleration-limited) final deceleration.

**6. Real-hardware testing is effectively required to confirm the resonance will appear at specific angles, but the mechanism can be bounded on the bench.** Because reflected inertia scales with the square of any effective lever and changes with joint angle, and belt stiffness sets the two-mass natural frequency, the exact resonant angles are a property of the real arm. A robot-diagnostics patent (Canon, "Examination method for examining robot apparatus") states the resonance frequency "changes according to the load or the orientation of a hand portion attached to the end of the hand of the robot." However, whether the *mechanism* is resonance or friction is bench-determinable now.

## Details

### Q1 — Literature on load-induced resonant limit cycles vs Coulomb stick-slip; diagnostic signatures; is 10 Hz logging enough?

There is established literature in exactly this space. Peer-reviewed control-theory sources model both friction-induced hunting and compliance/two-mass resonance in a single servo positioning loop (Ramírez & Guesalaga 2009; the IEEE conference paper *Friction and backlash induced limit cycles in mechanical control systems*; and *Limit cycle oscillations in high performance robot drives*, which notes that zero-speed limit cycles from Coulomb friction depend on regulator stability, load inertia, spring constant and closed-loop natural frequency). Industry motion-control sources (Control Engineering, PMD Corp, Parker) describe belt/harmonic-drive resonances as a two-mass system whose resonant frequency ≈ (1/2π)√(K/J) of coupled motor and reflected-load inertias, commonly 30–300 Hz for toothed-belt/harmonic transmissions.

**Distinguishing signatures:**

| Signature | Coulomb stick-slip | Load/compliance resonance |
|---|---|---|
| Determinism at fixed settings | High (deterministic threshold) | Low — sensitive to starting phase/timing |
| Response to friction floor / P gain | Monotonic threshold | Non-monotonic |
| Dependence on where in travel | Weak, or tied to gear-mesh geometry | Strong — shifts with inertia/lever angle |
| Sensitivity to overshoot distance | Can matter (breakaway) | Little — excited by final decel dynamics |
| Frequency | Low, ~1 Hz, ~0.1 mm | Tens–hundreds of Hz (belt) |
| Hand damping | Helps | Helps (textbook fix) |

Your data matches the right column on determinism, gain response, position dependence and overshoot-independence. Hand damping helps in both, so it is corroborating, not decisive. The literature agrees stick-slip is *exacerbated by compliant coupling*, so the two are not mutually exclusive — a compliant belt makes any residual stiction more likely to produce a limit cycle. (Note: the ScienceDirect *Coulomb Friction* overview gives the classic stick-slip limit cycle as "~1 Hz and small amplitudes ~0.1 mm," and states "when stiction is less than 70% of Coulomb friction, stick-slip is eliminated" — a useful quantitative anchor for the friction hypothesis.)

**Is ~10 Hz position logging enough?** No. It can capture a slow (~1 Hz) stick-slip cycle but will alias any true belt resonance (tens of Hz+). To confirm the mechanism you need one of: (a) the servo's own **Present Current (register 69, ×6.5 mA)** and/or **Present Load (register 60)** logged as fast as the bus allows during the oscillation — a resonance shows a coherent near-sinusoidal current oscillation at the mechanical frequency, whereas stick-slip shows asymmetric sawtooth current spikes at stick-release events; or (b) an accelerometer on the output plus an FFT. A tell you can extract even from your existing slow logs: measure the reversal *period* — if reversals are separated by ~0.5–1 s it is a slow friction/integral-windup cycle; if the position band jitters faster than you can sample cleanly, it is aliased high-frequency resonance.

### Q2 — Standard remedies for load-induced resonance (as distinct from friction remedies)

The documented, resonance-specific remedies, ranked by applicability to this hardware:

1. **Reduce loop gain (position P).** The universal first-line fix for resonance instability: high P gain drives oscillation at the mechanical resonant frequency; lowering gain trades bandwidth for stability. This is both the textbook motion-control answer and the LeRobot community's hard-won answer (see Q3).
2. **Trajectory/profile shaping — S-curve / jerk limiting.** S-curve profiles "inject dramatically less vibrational energy into the connecting mechanisms" (PMD Corp), and input shaping (ZV/ZVD shapers) cancels residual vibration by convolving the command with an impulse sequence tuned to the natural frequency. On this servo you cannot do true input shaping in firmware, but the Acceleration register (41) gives you trapezoidal ramp control, and you can approximate jerk limiting host-side by breaking the final leg into a short micro-ramp.
3. **Mechanical: increase mounting stiffness / add damping / reduce compliance.** Raising K raises the resonant frequency out of the loop bandwidth; adding damping removes limit-cycle energy (this is why your hand works). Zuo's LeKiwi report independently found that a loose arm mount — "The arm is pretty heavy. If the mount is even a bit loose, the arm very likely becomes jittery" — and that tightening the mount plus a 3D-printed support block (shell_085_of_LeKiwi.stl) was necessary.
4. **Notch / low-pass filter in the loop.** The standard industrial cure — but the STS3215 firmware exposes no notch or low-pass constant, so this is unavailable here except by moving to host-side command filtering.
5. **Inertia matching.** Resonance severity scales with load/motor inertia mismatch; the belt reduction already helps (reflected inertia ∝ 1/N²), but a heavy real arm at a long lever can still mismatch badly.

Friction remedies you have already exhausted (dead zone, MinStartForce/punch, and to some extent P) address the *other* mode; the fact that they were non-monotonic and incomplete is itself evidence you are fighting the resonance mode.

### Q3 — STS3215 registers/features beyond position P/I/D, MinStartForce and dead zone

Confirmed registers relevant to buzzing/hunting under load:
- **Register 37 (0x25), "Speed closed loop P proportional coefficient," default 10** — the proportional gain of the servo's *inner velocity loop*, entirely separate from the position P you have been tuning. In a cascaded loop, an over-aggressive velocity loop is a common cause of hunting that no amount of position-P tuning fixes.
- **Register 39 (0x27), "Velocity closed loop I integral coefficient," default 200** — velocity-loop integral gain. Integral action in the presence of friction/backlash is a documented limit-cycle driver; a large velocity-I can sustain hunting.
- **Register 41 (0x29), "Acceleration," unit = 100 steps/s², range 0–254, 0 = max acceleration** — trapezoidal start/stop ramp. LeRobot's `configure_motors()` sets acceleration high (200–254) for speed; for resonance you want the opposite — a *lower* acceleration produces a gentler ramp with less vibrational energy injected. (Caveat from robonine's bench testing: lower acceleration also increased heating in a continuous-oscillation test, so do not set it extremely low for sustained motion.)
- **D coefficient (register 22, default 32)** — you have never changed it. Derivative gain is the direct damping term in the position loop and is the textbook control-side knob for settling oscillation; raising D adds electronic damping (mimicking your hand). This is a genuine untried lever.

The LeRobot/HuggingFace community's practical guidance is unusually direct. Zuo's LeKiwi/PincOpen build is the best-documented load-bearing case: after sweeping acceleration, max torque limit, overload torque and protective torque, he concluded those were "all unnecessary" and that lowering position P was "the MOST CRITICAL fix," settling on P=14 for the arm and P=10 for the four large joints, with explicit "smooth vs jittery" boundaries one integer apart. LeRobot's shipped default is P=16, I=0, D=32 (comment: "Set P_Coefficient to lower value to avoid shakiness (Default is 32)"). The community answer is not merely "lower P" — it is "lower P quite far (to ~10–16), accept a small steady-state offset, and don't bother with the torque/acceleration registers for this symptom." The offset you saw at P=16 (~0.17° droop) is expected (lower P = higher steady-state error under gravity) and is the reason your fine-approach exists; a modest position-I (register 17) or velocity-loop I can trim residual droop, but I-terms must be added cautiously because they are themselves limit-cycle drivers.

### Q4 — Does overshoot-and-return anti-backlash interact badly with resonance, and is there a better technique?

The interaction is real in principle and supported by the literature indirectly: the return leg is a short point-to-point move, and abrupt deceleration at the end of ANY move injects energy at the mechanism's natural frequency (the entire rationale for S-curve profiles and input shaping). If your final leg decelerates hard onto the target, it is a resonance excitation event — which explains why *reducing overshoot distance from 1.5° to 0.4° did not help*: the excitation is in the stop dynamics, not the swing distance.

The better-established alternatives:
- **Keep unidirectional approach, but soften and shrink the final leg.** Single-direction positioning is the standard CNC anti-backlash method (Fanuc-style "always approach from the same direction") and does not inherently require a large overshoot — only that the final segment always arrives from the same side, sized just above measured backlash (your ≤0.18° tolerance), with a jerk-limited/low-acceleration final ramp so the stop does not ring. This keeps your backlash immunity while removing the excitation.
- **Preload / dual-motor counter-drive** eliminates backlash mechanically (demonstrated on this exact servo by robonine's two-STS3215 pre-tension rig, and in the AhaRobot dual-motor counter-drive design with a feed-forward backlash bias plus a high-frequency dither term for stiction) — overkill for a single joint but the definitive fix where play must vanish.
- **Dual-loop feedback (output encoder)** measures load position directly and removes the need to compensate at all — the CNC "linear scale" analog — but adds hardware.
Given your constraints, the recommended change is not to abandon unidirectional approach but to **make the final leg a slow, acceleration-limited micro-move**.

### Q5 — Can bench-proxy data predict the real arm, or is real-hardware testing the only way?

Bounding, yes; precise prediction, no. The resonant frequency f ≈ (1/2π)√(K_eff/J_eff) depends on belt/mount stiffness K and reflected load inertia J, and J changes with joint angle (a robot arm's effective inertia and gravitational lever vary through the workspace). This is exactly why your worst point was −60°, not a travel extreme, and why the Canon robot-diagnosis patent computes resonant frequency as a function of load and orientation. The real arm has different mass distribution AND different mounting stiffness than a hand-held bench proxy, so the specific bad angles will move.

What the bench proxy CAN establish decisively *before* the real arm exists:
- **Whether the mechanism is resonance or friction** (via the current-spectrum / reversal-period tests in Q1). This is the single most valuable thing to nail down, and it does not need the real arm.
- **A conservative gain envelope.** If a given P (~14–16) is stable across your bench inertia range including a deliberately *exaggerated* hand-held inertia (bench proxy with added mass at a long lever to bracket the real arm's worst reflected inertia), that gives a defensible starting P for the real arm.
- **The qualitative efficacy of D-gain, velocity-loop gains, and acceleration-ramp softening** — these interventions either work on the mechanism or they don't, largely independent of the exact frequency.

So the team's assumption ("only real-hardware testing will tell") is right about the *specific bad angles and final tuning numbers*, but too pessimistic about the *mechanism and the intervention strategy*, which are bench-decidable now.

## Recommendations

**Stage 1 — Identify the mechanism (do this on the bench, now; decisive and cheap):**
1. During a known-bad oscillation at −60° under proxy load, log **Present Current (reg 69, ×6.5 mA)** and **Present Load (reg 60)** as fast as the 1 Mbps bus allows (aim for ≥50 Hz), simultaneously with position. Coherent near-sinusoidal current = resonance; asymmetric sawtooth spikes at reversals = stick-slip. This single test resolves the central uncertainty.
2. From existing slow logs, compute the reversal period. >0.4 s period → slow friction/integral cycle; unresolvably fast band → aliased resonance.

**Stage 2 — Apply the mechanism-appropriate fix:**
- If resonance (expected): (a) set position **P to ~14–16** to match LeRobot's validated range; (b) **raise D (register 22)** from 32 in steps (e.g., 48, 64) — your untried electronic-damping lever and the most direct analog to the hand; (c) **lower the Acceleration register (41)** to soften the final-leg ramp (try ~20–50, i.e., 2,000–5,000 steps/s²), accepting slightly slower moves and watching temperature; (d) make the **fine-approach final leg a slow acceleration-limited micro-move** rather than a hard stop.
- If stick-slip: your dead-zone-2 result is the pragmatic fix; combine with MinStartForce ~85–95 (which you found clean-ish) and accept the ~0.13° offset, or add a small position-I to null it.

**Stage 3 — Probe the inner velocity loop (only if Stage 2 is insufficient):** carefully reduce **velocity-loop P (register 37)** below its default 10 and/or **velocity-loop I (register 39)** below 200, one at a time, re-running the −60° repeat test. These are firmware-real but not documented in an official English register-table PDF; change them one at a time and record originals.

**Stage 4 — Bracket the real arm:** repeat the best Stage-2 configuration with a deliberately exaggerated inertia (added mass at a long lever on the bench) to bracket the real arm's worst reflected inertia; if the config is stable across that range, adopt it as the real-arm starting point.

**Benchmarks that would change the recommendation:** if the fast current log shows sawtooth-at-reversal (friction), abandon the D-gain/acceleration path and commit to dead-zone-2 + MinStartForce. If lowering P below ~14 still oscillates at −60° under exaggerated inertia, compliance is too high for a control-only fix and you must stiffen the mount / add mechanical damping before the real arm. If raising D reduces reversals markedly, the mechanism is confirmed resonance and D becomes your primary knob.

## Caveats
- The resonance-vs-friction conclusion is inferential, not confirmed — no current spectrum or FFT has been taken. Stage 1 exists precisely to settle it; treat everything downstream as conditional on that result.
- Registers 37 and 39 (velocity-loop P/I) are confirmed by a live community register dump (iotdesignshop/Feetech-tuna) and Feetech's host-software field labels, **not** by a cleanly published official English register-table PDF. Their exact control-law role is inferred from their names; change them cautiously and reversibly.
- The Acceleration register unit (100 steps/s², 0 = max) is from Waveshare/Feetech ecosystem documentation; the "0 = max acceleration" semantic means do not confuse 0 with "no motion."
- The Canon robot-diagnostics patent quotation was surfaced from USPTO full-text ("Examination method for examining robot apparatus"); the exact patent number should be re-verified before any formal citation, though the substantive claim (resonant frequency varies with load and orientation) is independently supported by two-mass/reflected-inertia theory.
- The robonine bench data notes a firmware dead zone of ~10 encoder counts on some units and measured backlash (~0.87°) higher than the 0.5° datasheet spec — unit-to-unit variation is real, so a tune validated on one servo may need re-checking on another.
- Lower P reintroduces steady-state droop under gravity (you measured ~0.17° at P=16). That is expected and is the trade-off; the fine-approach and/or a small I-term is how you recover final accuracy.
- Community sources (LeKiwi blog, robonine, forum posts) are practitioner reports, not controlled studies; they are strong corroboration but not peer-reviewed. The control-theory claims (limit cycles, two-mass resonance, S-curve/input shaping) are from peer-reviewed and established industry sources.
