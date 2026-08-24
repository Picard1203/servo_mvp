# A failed read is reported as unknown, never as a number

When the servo does not answer a position read, the API reports
`output_deg: null` with `reading_valid: false`, no telemetry row is written, and
the UI shows an unknown position rather than a value. **No substitute number is
invented — not zero, not the last known position, not the centre of travel.**

## Why

A failed read arrives as **count 0**, and count 0 is a perfectly plausible
genuine reading: it is the bottom of the servo's travel. There is nothing in the
number itself to distinguish "the servo is at the bottom" from "the servo did not
answer". Only the snapshot's `valid` flag carries that distinction, and once it
is discarded the information is gone for good.

This is not hypothetical. On 7 August 2026, on hardware, three Bridge stalls of
10.99 seconds each produced empty snapshots whose `raw_counts` were used anyway.
The UI displayed −212.74°, the database stored seven fabricated samples, and one
row recorded count −1, which no 0..4095 servo can report.

**The bus failure itself was logged, and clearly** — three `servo.bridge.error`
records reading `function=servo_read error="Request 'servo_read' timed out after
10s"`, one per stall. What was not recorded anywhere was the consequence: that a
position had been **invented** from the failure and handed to the operator and
the database. Reading the log, an engineer sees a bus that timed out and
recovered; nothing says the screen lied in the meantime.

That gap is the point. A logged cause with an unlogged consequence is how a
defect survives a log review.

The stakes are set by ADR-0007. Moves are permitted while the position reference
is unverified, so **the travel window is the only guard** against driving into a
silent clamp — and that window is computed from the reported position. A
fabricated position displaces the guard by exactly the error it exists to catch.
The operator is also commanding moves from what the readout says: D9 is the case
where a wrong displayed position turned a 90° command into 212.7° of real
movement.

## The alternative that was considered

Holding the last good value and marking it stale. Rejected for the API: it still
puts a number on screen that is no longer measured, and the failure mode being
guarded against is precisely a plausible-looking number that nobody questions.

**This does not decide how the UI paces the transition.** Reporting truthfully
every 1 second and *displaying* a change the instant one sample is invalid are
different things — the end users are not programmers, and a readout that blinks
to unknown on a single blip reads as "broken". Debouncing the display is
permitted and wanted (backlog D11) as long as a sustained loss is unmistakable.
The API contract stays honest underneath it.

## Consequences

- `ServoRepository` has **no** `read_raw_counts()`. It returned a bare int, so
  the `valid` flag had to be thrown away to produce one. Removing it forces every
  caller — present and future — to hold a snapshot and decide what an invalid one
  means. Guarding a call site fixes today; deleting the method fixes every call
  site that will ever exist.
- Callers that genuinely need a number and cannot proceed without one raise
  `InvalidReadingError`: `ZeroService.capture()`, `ZeroService.calibrate()`,
  `MotionService.recover()`.
- Telemetry leaves a **gap** rather than a fabricated row. A gap is honest and
  visible in a time series; a zero is neither.
- Every failed read logs `servo.read.failed`, at the point where the position
  would have been fabricated. `servo.bridge.error` already reported the *cause*;
  this reports the *consequence*, which is the half that was missing.
- Clients must render `null` as unknown. Anything that formats it as a number is
  reintroducing the defect at the last hop.

## Extended, 8 August 2026 — `valid` governs the whole snapshot

The decision above was written about the **position** and implemented for the
position alone. Too narrow: a failed read does not return a bad position inside
a good snapshot, it returns a **zeroed struct**. `temperature_c`, `voltage_v`,
`current_a` and `torque_kgcm` all arrived as `0.0` beside a position that
correctly said unknown — and **0.00 V reads as a servo that has lost power**, a
worse false statement than any position. That was backlog D16.

`ServoStateResponse` and `ServoStateView` now report `null` for all four when
the read failed, as they already did for `output_deg` and `raw_counts`.

Two deliberate limits:

- **The boolean flags are not covered.** `moving` and the six fault flags are
  still `false` on a failed read, stating "not moving, no faults" about a servo
  that said nothing. `bool | None` ripples into the CSV and every consumer, so
  it is a separate decision — **backlog D23**, which amends this ADR again.
- **Display pacing is still not the API's business.** The client holds the last
  measured readings through a blip and blanks them once the read is genuinely
  unknown, on the position's debounce. The contract stays honest every second.

## Status

Accepted, 7 August 2026. Decided by the operator when the alternatives were put
side by side. Implemented in commit `c903182`; six tests cover it.

**Extended 8 August 2026** (backlog D16) to the four telemetry readings; four
further tests. **Still open: the boolean flags — backlog D23.**
