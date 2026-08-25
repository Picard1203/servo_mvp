# Motor isolation state survives a reboot

Motor isolation (backlog R2) — removing drive power from the servo while its
sensors stay energised — **latches**. Once engaged, it survives a restart
(watchdog, power blip, App Lab redeploy) and is re-applied at startup, before
the servo can be commanded to do anything.

## Why

Isolation is a protective act, so its safe state is the one that persists. A
reboot silently re-energising a mechanism somebody chose to make safe is the
failure that hurts people; a reboot leaving the drive dead until someone
clears a latch by hand hurts a schedule — the lesser cost.

ADR-0007's argument for *not* gating movement on calibration does not
transfer here, and that is the crux. ADR-0007 refuses to gate movement on
calibration because clearing that state needs somebody **physically
present**, three hours away. Clearing isolation does not — it is one click
in the same UI the remote operator already has open. A latched state that
costs a click to clear is a different tradeoff than one that costs a site
visit.

The register is not the record: the servo's own `kTorqueSwitch` (0x28)
re-enables on power-up regardless of what it held before. The latch
therefore lives in the database as operator intent, not in servo state, and
is re-applied to the register at startup.

## Consequences

- Isolation state must be visible **as a consequence of the reboot**, not
  merely as a current state — an operator who does not know the drive was
  isolated before a restart will power-cycle the board, which changes
  nothing under this decision and wastes a trip.
- Re-application must happen **before** any move can be accepted at boot, or
  a queued command racing startup wins and momentarily re-energises the
  servo.
- `isolated` on `ServoStateResponse` follows `locked`'s existing shape, not
  the fault flags': a plain, never-null `bool`. It is state the system
  already knows regardless of whether the servo answers a read — the same
  situation `locked` is already in.
- Reopen this if R8 (emergency stop) or R4 (unified Lock, mechanical
  restraint) changes the model — an e-stop almost certainly latches too, and
  the two decisions must agree.

## Status

Accepted, 8 August 2026 (as `OPEN_QUESTIONS.md` Q4), at the operator's
instruction to make the engineering call on the reboot tradeoff. Promoted to
this ADR 25 August 2026, ahead of R2's build, following the operator's
doc-grounded `/grilling` pass on R2's design.
