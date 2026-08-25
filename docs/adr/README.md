# Architecture decision records

Why the system is built the way it is. Each record exists because the decision is
**hard to reverse**, **surprising without context**, and **the result of a real
trade-off**. If a decision fails any of those three, it does not get an ADR.

Do not re-litigate these. If you believe one is wrong, reopen it explicitly —
amend the ADR or supersede it with a new one — rather than quietly building
against it.

| # | Decision | Read before touching |
|---|---|---|
| [0001](0001-network-path-through-the-mcu.md) | The network path runs through the MCU, not the Linux side | the relay, connection limits, anything network |
| [0002](0002-no-frontend-framework.md) | Plain HTML/CSS/JS — no framework, no build step | `python/static/` |
| [0003](0003-travel-window-plus-minus-90-output-degrees.md) | Travel window is ±90 output degrees; multi-turn off | angles, ranges, calibration |
| [0004](0004-repository-abstraction-and-simulated-backend.md) | Servo access sits behind a repository abstraction | `deps.py`, repositories, tests |
| [0005](0005-air-gapped-by-default-development.md) | Develop as if already air-gapped | dependencies, deployment, libraries |
| [0006](0006-csv-bridge-payloads.md) | Bridge payloads are CSV strings | either side of the MCU boundary |
| [0007](0007-moves-are-permitted-while-position-is-unverified.md) | Moves are permitted while position is unverified | motion, calibration, safety behaviour |
| [0008](0008-a-failed-read-is-reported-as-unknown.md) | A failed read is reported as unknown, never as a number | the servo read path, the API contract, the UI |
| [0009](0009-connection-ceiling.md) | Connection ceiling stays at 6; `timeout_keep_alive` is the real lever | the relay, connection limits |
| [0010](0010-motor-isolation-state-survives-a-reboot.md) | Motor isolation state survives a reboot | R2, motor isolation, reboot/startup behaviour |

## Numbering

Scan this directory for the highest number and increment. `0011` is next.

## Candidates not yet written

- **How motor isolation, the Lock and emergency stop compose.** Decided in
  principle — they stay separate controls (backlog R2, R8) — but the flow between
  them is not designed. Write the ADR when it is.
