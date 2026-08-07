# Moves are permitted while the position reference is unverified

`_position_verified` is `False` after every boot, and the UI says so. The backend
nevertheless **accepts move commands in that state**, deliberately.

The safety-shaped intuition is to refuse them — an unverified datum is how the
system reaches its worst failure mode (see ADR-0003 and backlog D1). That
intuition is wrong here, and the reason is operational rather than technical.

## Why

The installation is remote and access is expensive — on the order of a three-hour
drive, to a site that cannot be casually visited. Two consequences follow:

- If the signal being measured is lost, the operator must be able to move the
  mechanism to recover it **without dispatching anyone**.
- The operator may hold an external reference for what is being measured and need
  to drive the mechanism to that position programmatically.

Refusing movement until someone has physically stood at the machine and pressed
Calibrate converts a recoverable situation into a site visit. A system that locks
itself out of the only remedy available to a remote operator is less safe, not
more.

## Consequences

- The unverified state must stay **visible**, since it is no longer enforced.
  `app.js:276` and `:287` already surface it; that warning is now load-bearing
  and must not be quietly removed.
- Travel-window enforcement (ADR-0003) remains the real guard: targets outside
  the reachable range are refused as `out_of_travel` rather than clamped,
  verified or not.
- D1 must therefore be fixed by making the *datum* trustworthy (backlog D2), not
  by gating movement behind calibration.
