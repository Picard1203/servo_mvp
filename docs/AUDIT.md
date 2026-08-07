# Full-system audit

> **FROZEN — historical record.** This documents one past investigation and the
> fixes that came out of it. It is dated by nature and is **not maintained**.
>
> For open work see `BACKLOG.md`. For current status see `PROJECT_STATE.md`.
>
> Read this before touching the relay or the calibration path — the reasoning
> here is why those are shaped as they are.
>
> **One claim below is now out of date.** "Calibration refuses a reading the
> servo never gave" is true of `calibrate()` only; `capture()` has no such guard
> and can still store a failed read as position 0. See backlog D2.

Written after "-90 physically stops at 0". That one observation was worth
more than every log: it is a hardware-range failure, not a networking one,
and following it found a chain of four defects that share a single cause -
**failures were never distinguishable from data.**

---

## The chain, end to end

1. The Bridge was timing out (concurrent RPC, no lock).
2. `servo_read` returned nothing, so the repository produced an all-zero
   snapshot.
3. The sketch DOES send a `valid` flag as field 0 of the payload. Python
   parsed it **and threw it away**. `TelemetrySnapshot` had no validity
   field at all, so a failed read was indistinguishable from a genuine
   reading of position 0.
4. Calibrate ran at that moment. It captured `read_raw_counts()` with **no
   validation** and stored **raw_counts = 0** as the datum. This is in the
   log verbatim: `servo.calibrated ... raw_counts=0`.
5. With the baseline at 0, -90 deg maps to count **-1502**.
6. The servo is configured min angle limit 0, max 4095. It **clamps
   silently** - stops at 0 and still acknowledges the command. **Nothing
   anywhere checked the count range**, so the API reported success.

Six steps, and only the first was ever a "bug" in the sense we were hunting.
The rest were missing guards.

---

## What changed

### 1. A reading now carries its own validity
`TelemetrySnapshot.valid`, populated from field 0 of the sketch payload.
An unanswered read can no longer masquerade as position zero.

### 2. Calibration refuses a reading the servo never gave
`InvalidReadingError` -> HTTP 409 `reason=invalid_reading`. Previously it
would happily store the zero that made half the travel unreachable.

### 3. Unreachable targets are refused, not clamped
`ServoStateStore.is_reachable()` / `reachable_output_range_deg()`, enforced
in `MotionService` as `OutOfTravelError` -> HTTP 422
`reason=out_of_travel`, with a message naming the range that IS reachable.
The sketch refuses out-of-range counts too, so a bad target never reaches
`WritePosEx` even if something upstream misses it.

### 4. The default baseline is the CENTRE of travel, not zero
This was the quiet one. With no datum captured the baseline used to be
count 0 - which puts the entire negative half of the range out of reach
before the operator touches anything. It is now `counts_per_turn / 2`.

### 5. Calibration warns when the datum is off-centre
If the captured position leaves part of the configured window unreachable,
that is logged with the numbers, instead of being discovered by a servo
that stops early.

### 6. Bridge access is serialised (previous round)
An `RLock` plus a 0.25 s read cache. The sampler thread and every HTTP
request were calling `Bridge.call` concurrently; interleaved message ids
produced `Response for unknown msgid` and 10 s timeouts.

---

## Answering "did we even test the sketch?"

**Native tests: yes, and they run on every build** - now 164 checks. But be
clear about what they covered: sign-magnitude decoding, angle conversion,
status bits. **Pure maths.** They could not have caught any of the above,
because none of it is maths.

**On-target tests: never run.** `sketch/tests/OnTarget/` is a separate
sketch that has to be uploaded deliberately. It has not been.

**The relay and controller have no automated coverage at all.** Every bug in
this project lived there: `available()` vs `accept()`, accept-before-detect
ordering, the missing yield, the missing lock. That is the real gap, and it
is honest to say the test suite's green light never meant much for those.

New native tests cover the range logic specifically, including one that
reproduces the exact failure:
`range_a_datum_at_zero_strands_the_negative_half`.

---

## Still open - deliberately, with reasons

**Your stored datum is still 0.** Nothing here rewrites it. After deploying,
move the mechanism to mid-travel and press Calibrate again. The new
off-centre warning will tell you if it is still poorly placed.

**Relay behaviour remains untested by machine.** Making it testable means
extracting slot management from `EthernetClient`, which is a real
refactor and not something to start while the system is unstable.

**On-target tests should actually be run.** Upload `sketch/tests/OnTarget/`
once with the servo free-shafted. It checks ping, configuration writes,
landing accuracy and stop-holds - the things a host cannot.

---

## Verification as it stands

    186 Python tests, 100% line coverage of app/
    164 native sketch checks, -Wall -Wextra -Wpedantic -Werror
    every sketch .cpp compiles
    Bridge contract checker: both sides agree

Coverage at 100% is not the same as correctness - it did not stop any of
the six defects above. It means every line ran, not that every assumption
was questioned.
