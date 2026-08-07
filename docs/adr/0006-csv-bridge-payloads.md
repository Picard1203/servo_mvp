# Bridge payloads are CSV strings with typed arguments

Every call across the MCU/Linux boundary carries a plain comma-separated payload,
declared at the top of `sketch/src/BridgeApi.h` and mirrored in
`python/app/repositories/concrete/bridge_servo_repository.py`.

Chosen for debuggability: a CSV payload is readable verbatim in a log, which
matters on a boundary where a wrong argument count compiles and imports cleanly
on both sides and then fails at runtime as **silence** rather than an error.

## Consequences

- Field order is a contract. `tools/check_bridge_contract.py` compares the two
  declarations and exits non-zero on disagreement — the only mechanism that
  catches drift, since neither compiler nor interpreter can.
- Snapshot field 0 is `valid`. It exists so a failed read is distinguishable from
  a reading of zero; discarding it is how the worst defect in this project
  happened, and `read_raw_counts()` still discards it today (backlog D2).
- Run the contract checker after touching either side. It is suitable for a
  pre-commit hook.
