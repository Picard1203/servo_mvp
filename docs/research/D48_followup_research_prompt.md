# D48 follow-up deep-research prompt (prepared, not yet run)

Prepared 6 September 2026, Session 25, for a second deep-research pass (Claude
and/or Gemini, matching the first round in `D40_resonance_research_claude.md`/
`_gemini.md`). Not run yet — hand this to a deep-research-capable model
verbatim. Kept as its own file per that same convention: the prompt is the
record, edit by superseding, not in place.

## Why a second pass

The first research pass (2 September) worked from inference and predicted
mechanical resonance. Session 25 (6 September) ran the actual experiments and
found the confirmed mechanism disagrees with several of that pass's specific
predictions. This prompt gives a fresh pass the real data instead of asking it
to guess again from the same starting point.

---

## The prompt itself

```
I'm debugging a settling-jitter problem on a Waveshare ST3215 / Feetech
STS3215 serial-bus servo (geared, magnetic encoder, 0.06deg/count position
resolution, driving a belt-coupled load through a small bench rig). A prior
deep-research pass (yours or a peer's) predicted mechanical resonance from a
compliant belt-load coupling and recommended lowering position P gain,
trying the servo's velocity-loop P/I registers (37/39) and acceleration
ramp register (41), and softening the anti-backlash final approach leg. I
ran the actual experiments. Here is what was found, please reconcile it
with the literature and tell me what to try next.

CONFIRMED MECHANISM (not resonance): a fast (~100Hz) simultaneous
position+current trace at a reliably-bad point recorded a reversal period
identical to three significant figures across three separate trials
(0.2668s, 0.2670s, 0.2668s) with modest oscillating current (0.026-0.058A).
This is a deterministic digital-control limit cycle from position-sensor
quantisation (the servo toggles between two adjacent 0.06deg counts), not
a mechanical mode - the tight period repeatability across independent
trials is inconsistent with mechanical resonance (which would be set by
load mass/belt stiffness, not repeat to 4 significant figures) and with
stick-slip (irregular, friction-release driven). This matches the
"quantizer-induced limit cycle" literature (e.g. Peterchev & Sanders on
quantization resolution and limit cycling in digitally-controlled PWM) more
than either resonance or Coulomb stick-slip.

WHAT WAS TRIED AND FAILED, ALL AT ONE TEST ANGLE (+60deg output, approached
via a ~60deg move from a 0deg anchor - the harshest condition found in an
11-angle survey):

1. Position P/D gain sweep (7 configs, N=10 trials each): P24/D32(factory-
   adjacent baseline)=7/10 trials failed, P20=7/10, P16=5/10, P12=5/10,
   D24=5/10, D16=2/10 (best), D8=9/10 (WORSE than baseline - D response is
   non-monotonic, lower is not simply better). A follow-up bracket around
   D16 (D14, D18, D20, N=8 each) came back 7/8, 8/8, 6/8 - D16 turned out
   to be an isolated spike surrounded by near-total failure on both
   sides (Fisher's exact test: D16-vs-baseline p=0.070, not significant;
   D16-vs-D24 neighbour p=0.35, indistinguishable) - almost certainly a
   lucky N=10 draw, not a real optimum. A D16+P16 combination also failed
   (5/8).

2. Fine-approach final-leg dynamics (the anti-backlash technique: overshoot
   past target by a fixed amount, wait for the servo's own `moving` flag
   to clear, then command a final corrective move back to true target from
   one consistent direction). Read the firmware/host-side implementation
   directly: the final leg is a fresh, independent position command that
   only starts once the servo reports it has stopped from the overshoot -
   there is no raw momentum carryover between the two legs. Tested at N=8/
   arm, baseline P/D registers: unsoftened (default final-leg speed/accel,
   same as the overshoot leg) = 4/8 failures (the BEST of all four arms);
   final leg slowed to 10deg/s + acceleration 20 = 8/8 failures (worse);
   final leg slowed further to 5deg/s + acceleration 10 = 6/8 (still worse
   than baseline); overshoot distance reduced from 1.5deg to 0.5deg
   (default final-leg speed) = 8/8 failures (worse). Every deliberate
   softening of the final leg or reduction in overshoot distance made
   things WORSE than the untouched default, the opposite of the
   "softened landing" prediction.

3. Move-size independent of the final-leg mechanism: a full-travel
   preceding move (~150deg) reliably produced worse settling than a short
   (~5deg) final approach to the same target, even though (per point 2)
   the final corrective leg's own distance and dynamics are identical
   either way and only starts once the firmware already considers the
   preceding leg fully stopped. At the harder of two test angles this
   short-approach improvement was real but partial (7/10 to 4/10 failures);
   at a second, worse-behaving angle on the opposite side of centre, a
   short approach gave ZERO improvement (stayed 10/10 failing) regardless
   of preceding move length, approach direction, or any register value
   tried.

4. A left/right asymmetry with no register or approach-based explanation:
   testing the mirror-image angle on the opposite side of centre (-60deg
   vs +60deg) found it failing under EVERY condition tried all session -
   every approach direction, every move size, every P/D register value,
   and dead-zone at two settings - while the +60deg point responded
   partially to several of these. Both angles are equally far from centre
   and from the mechanical travel limits.

5. Dead-zone (last resort - deliberately avoided earlier for its accuracy
   cost): tested at 1 and 2 encoder counts (0.06deg/0.12deg), N=10 per
   angle, baseline P/D. At the more responsive angle: dead-zone=1 gave
   4/10 failures at a small accuracy cost (mean/max absolute final error
   0.042deg/0.070deg); dead-zone=2 gave 2/10 failures at a larger cost
   (0.114deg/0.190deg). At the unresponsive angle from point 4: BOTH
   values still failed 10/10, and dead-zone=2 there also produced a much
   larger positioning error (mean/max 0.277deg/1.480deg) for zero jitter
   benefit. Neither value cleared a pre-registered pass bar (<=1 failure
   of 10) at either angle.

NEVER TRIED (from your own prior research, not yet followed up): the
servo's velocity-loop P (register 37, default 10) and velocity-loop I
(register 39, default 200), and the acceleration/ramp register (41,
0=max acceleration, unit ~100 steps/s^2). All testing this round was
position-loop P/D (registers 21/22) and host-side fine-approach timing
only.

QUESTIONS:
1. Given the confirmed mechanism is quantizer-induced limit cycling
   (not resonance), does the quantizer-induced-limit-cycle literature
   (describing-function analysis, dithering, deadband/hysteresis design)
   predict the specific non-monotonic D-gain response we measured (D16
   better than both D8 and D32), or does it suggest D-gain is the wrong
   axis entirely for this mechanism and something else (e.g. the velocity
   loop, or the position loop's sample rate) is more load-bearing?
2. Why would softening the final corrective leg's speed/acceleration make
   things reliably WORSE rather than better, given the final leg starts
   from what the firmware considers a dead stop either way? Is there a
   known phenomenon (stiction/breakaway torque at very low commanded
   speeds, cogging torque, integrator windup at low velocity) in small
   geared serial-bus servos that would explain a slower corrective move
   being LESS able to reliably close a sub-count error than a faster one?
3. The overshoot-leg's own `moving` flag clearing does not guarantee the
   physical belt/load has stopped vibrating (this is a documented blind
   spot of this project's own settle-detection). Is "residual mechanical
   energy in a compliant belt-drive that a coarse velocity estimate
   already calls stopped" a recognized, named phenomenon in belt-driven
   or geared-servo positioning literature, and if so what is the
   established diagnostic (e.g. a specific settle-time-vs-load-inertia
   relationship) or remedy (e.g. a mandatory dwell time before the final
   leg, scaled to the preceding move's size) for it?
4. What would cause consistent left/right (positive vs negative direction
   from centre) asymmetry in jitter susceptibility on a belt-and-pulley or
   geared serial-bus servo setup, when the position control law and every
   tested register value are direction-symmetric? Rank plausible physical
   causes (belt pretension asymmetry, idler/pulley eccentricity,
   gravity-assisted vs gravity-opposed motion if the rig is not perfectly
   balanced, one-sided backlash from an off-center mounting) by how
   diagnosable each is from the servo's own telemetry (position, current,
   voltage) versus requiring physical/mechanical inspection.
5. Given register 37 (velocity P) and 39 (velocity I) and the acceleration
   ramp (register 41) have never been touched in this investigation, what
   would you predict for each given the confirmed quantizer-limit-cycle
   mechanism - and in what order should they be tried, at what candidate
   values, given position P/D tuning and fine-approach tuning have both
   been exhausted without a reliable fix?
6. Is a non-uniform or hysteretic dead-zone (larger during correction,
   effectively zero once truly settled; or a dead-zone that only engages
   after N consecutive counts of the same error sign) a documented
   technique for getting dead-zone's jitter benefit without its flat
   accuracy penalty, and is it achievable on this servo's exposed register
   set or does it require firmware not present in the vendored SDK
   (`libraries/SCServo/`)?
```

## What to do with the answer

Feed the response back into `docs/backlog/D.md` D48 the same way the first
pass's answer became the "Two independent deep-research passes" section —
verbatim, dated, cited as input to the next session's plan rather than
authoritative fact. Cross-check anything about registers 37/39/41 against
`libraries/SCServo/SMS_STS.h` before trusting it (D48's own note: those
registers are community-sourced, absent from any official English table and
from the vendored SDK).
