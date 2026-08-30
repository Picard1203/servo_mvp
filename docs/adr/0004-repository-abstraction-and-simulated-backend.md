# Servo access sits behind a repository abstraction, with a simulated backend

`ServoRepository` is an abstract contract with two implementations:
`SimulatedServoRepository` and `BridgeServoRepository`. `deps.py` is the only
module that names either, and picks between them on the `use_hardware_servo`
setting.

The immediate reason was sequencing: the backend, the API and the whole UI were
built and tested before the C++ side existed. Without a simulated backend that
work would have been blocked on hardware that was not ready.

## Consequences

- The dev machine and the entire test suite need no board. 186 tests run on a
  laptop.
- Switching to hardware is a configuration flag, not a code change — everything
  above `deps.py` is untouched. **Note:** `README.md` §7 still describes this as
  future work ("when the sketch is ready, switch `deps.py`"); that is stale, the
  swap is already wired.
- The same pattern applies to storage: SQLite sits behind `SavedPositionRepository` and
  `TelemetryRepository`.
- The cost is a real one and worth stating: a green test suite proves the
  *simulated* path works. Every defect this project has actually suffered lived
  in the hardware and relay paths that the simulator does not exercise.
