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
row recorded count −1, which no 0..4095 servo can report. Nothing was logged.

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
- Every failed read logs `servo.read.failed`. Silence was how this survived.
- Clients must render `null` as unknown. Anything that formats it as a number is
  reintroducing the defect at the last hop.

## Status

Accepted, 7 August 2026. Decided by the operator when the alternatives were put
side by side. Implemented in commit `c903182`; six tests cover it.
