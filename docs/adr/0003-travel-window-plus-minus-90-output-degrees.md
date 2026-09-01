# Travel window is ±90 output degrees, and multi-turn stays off

The reachable window is ±90° measured **at the mechanism**, after the 44:30 belt
reduction. Multi-turn is implemented and bench-proven, but disabled.

The belt ratio is the whole point of this record. 180° at the output is 264° at
the servo, which is 3004 counts — comfortably inside one 4096-count servo turn.
The original assumption was that the mechanism needed a full 360° of output
travel, which *would* have required multi-turn; the ratio made that unnecessary.
A reader who forgets the ratio will look at ±90° and conclude the servo is barely
being used.

## Consequences

- Widening the window later is two numbers in `.env`, not a code change.
  `configure_range()` is on the repository contract and runs at startup either
  way, so the multi-turn path does not bit-rot.
- The datum must sit **mid-travel** (~2048). A datum at count 0 strands the
  entire negative half — the servo clamps at 0 silently while still reporting
  success. This is the root of backlog D1 and the subject of `docs/history/AUDIT.md`.
- Targets outside the window are **refused** as `out_of_travel`, never clamped.
- No modulus-360 wrapping anywhere: in a multi-turn system −25° and 335° are
  different absolute targets a full output revolution apart, and wrapping would
  hide turn-count errors.
