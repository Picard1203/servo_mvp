# Servo MVP — context

Arduino UNO Q + Waveshare ST3215 serial-bus servo, with a FastAPI backend and a
web UI served from the board.

**This file is a glossary and nothing else.** Project status lives in
`docs/PROJECT_STATE.md`, open work in `docs/BACKLOG.md`, decisions in
`docs/adr/`, code style in `CONVENTIONS.md`.

Use these words in commits, test names, issues and proposals. Prefer them over
the synonyms listed under each `_Avoid_`.

## Language

### Position and geometry

**Count**:
The servo encoder's unit of absolute position; 4096 per servo turn.
_Avoid_: tick, step, encoder unit

**Output degree**:
An angle measured at the mechanism, after the 44:30 belt reduction. One count
is 0.06 output degrees. Unqualified "degrees" always means output degrees.
_Avoid_: servo degree (that is the pre-belt angle, a different quantity)

**Zero reference**:
A saved, named position an operator captures and can later re-select. This is
the genus; the datum is one distinguished member of it.
_Avoid_: preset, bookmark, waypoint, favourite

**Datum**:
The one absolute zero reference, captured by Calibrate from a validated
reading while the mechanism sits at its documented physical reference
position. There is exactly one, it cannot be deleted, and it must sit
mid-travel — a datum at count 0 strands the negative half of the window.
_Avoid_: zero point, home, origin, offset

**Baseline**:
The position of the currently active zero reference — the point output
degrees are actually measured from. Exactly one zero reference is active at a
time; activating another moves the baseline without disturbing the datum.
_Avoid_: active zero, current origin

**Travel window**:
The reachable output-angle range, ±90° by default. A target outside it is
refused as `out_of_travel`, never clamped.
_Avoid_: range, limits, bounds

### Telemetry

**Snapshot**:
One instantaneous sensory readout from the servo, carrying its own `valid`
flag. An invalid snapshot is a failed read, not a reading of zero.
_Avoid_: reading, poll, sample

**Sample**:
One persisted telemetry row, written by the sampler at the configured
interval and subject to retention.
_Avoid_: snapshot, record, datapoint

**Fault**:
One of six conditions decoded from status register 0x41 (overload,
overcurrent, overheat, voltage, sensor, angle).
_Avoid_: error, alarm (alarm is the UI's word for a surfaced fault)

**timestamp**:
The time field on every entity, schema, DB column, CSV column and query
param. Spelled out everywhere.
_Avoid_: ts, time, when

### MCU boundary

**Bridge**:
The RPC channel between the Linux side and the MCU. Calls are serialised;
payloads are CSV strings with typed arguments.
_Avoid_: link, IPC, channel

**Relay**:
The MCU-side byte pump that mirrors Ethernet-shield connections to the Linux
side. Owns no HTTP knowledge — it moves bytes.
_Avoid_: proxy, tunnel, forwarder

**Slot**:
One mirrored TCP connection inside the relay, identified by index. Adopted
exactly once via `accept()`.
_Avoid_: socket, connection id, channel

### Control and safety

**Lock**:
The digital interlock that refuses movement while engaged. A separate control
from motor isolation — the two may be composed into a flow, but neither is the
other.
_Avoid_: e-stop (a distinct thing, below), freeze, hold, safety. Note the
servo's `kLock` register (0x37) is the EEPROM write lock and is unrelated —
never call that the Lock.

**Motor isolation**:
Removing drive power from the servo while its sensors stay energised, so
telemetry keeps reading and the cards are not burnt. Independently
controllable; engaging the Lock may trigger it, but it is not the Lock.
_Avoid_: power cut, kill switch, disable

**Emergency stop**:
A single action that engages the Lock and removes motor power at once, without
the operator composing the two. Not yet built.
_Avoid_: e-stop as a name for the Lock, panic, abort

**Mechanical restraint**:
The post-MVP servos that physically hold the mechanism in place.
_Avoid_: mechanical lock, clamp, brake

**Backend**:
Which `ServoRepository` implementation is live — simulated or hardware —
selected by `use_hardware_servo`.
_Avoid_: mode, driver, mock, fake

---

If a concept you need is not here, that is a signal: either you are inventing
language the project does not use, or there is a real gap worth adding.
