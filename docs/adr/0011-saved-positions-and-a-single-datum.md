# Saved positions replace zeros; the datum is the only reference

The client didn't want a saved position to redefine what 0° means (R10,
decided with the team lead 30 August 2026). The old model let any saved
zero be *activated*, silently relocating the baseline every angle was
measured from — D9's exact shape, invited by the feature itself. There is
now exactly one reference, the datum, set only by Calibrate. Saved
positions store an absolute encoder count and carry no baseline concept.

**Considered and rejected: the servo's own re-centre (register `0x28 = 128`)
instead of a software datum.** It is a live, irreversible mutation of the
servo's own encoder reference — no undo, no history, wrong if the shaft
isn't exactly at the physical reference when sent — and it would entangle
calibration with one servo's register quirk, breaking the repository
abstraction (ADR-0004) that lets calibration logic run against the
simulated backend. `ServoController.cpp` already had scar tissue on this
same register family (R2's board verification found the wrong ack
sentinel checked on writes to it).

## Consequences

- Calibration collapsed into `app_state` as two keys
  (`datum_raw_counts`, `datum_captured_at`) — no dedicated table for one
  row. `ServoStateStore` reads the datum per access, never cached, since
  `CalibrationService.calibrate()` can change it mid-process.
- Saved positions are a real table (`saved_positions`), storing
  `raw_counts`, never a degree value — a point stored as degrees would
  silently point to a different physical position after any future
  recalibration.
- A database created before this change is migrated on first open: the
  old `is_datum = 1` row moves into `app_state`, every other row moves
  into `saved_positions`, and `zeros` is dropped.
- `active_zero` is gone from `ServoStateResponse` and the SSE `state`
  event — with only a datum, "which zero is active" carries no
  information `position_verified` didn't already carry.
