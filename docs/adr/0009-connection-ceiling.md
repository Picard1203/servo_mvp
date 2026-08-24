# The connection ceiling stays at 6 this batch

`kMaxRelaySockets` (`Config.h:45`) stays at **6**. No code change lands with
this ADR — `main.py`'s `timeout_keep_alive` and `Config.h`'s
`kMaxRelaySockets` are both left as measured, not tuned, per BACKLOG.md D13:
this is a decision, not a fix.

## Why

**The wall is fixed, not tunable.** The W5500 has 8 hardware sockets; the
relay's listener permanently consumes one, so **7** is the hard ceiling no
setting can move. `kMaxRelaySockets = 6` already leaves exactly one spare.
Raising it to 7 would spend the entire remaining budget and leave none.

**The real lever has never been measured.** `main.py:172` sets
`timeout_keep_alive=5` — chosen deliberately so an idle keep-alive connection
does not park a slot, per the reasoning already on record in
`OPEN_QUESTIONS.md` Q2. Nothing has tried a lower value and measured what it
buys. Tuning it now, before that measurement, repeats the exact mistake this
project has already paid for twice: D9 was two unverified baselines sitting
twelve lines apart, both green; D4 was a race that "stopped reproducing" and
was treated as fixed until a supervised soak proved otherwise. Session 2
exists to take that measurement — landing a change ahead of it means the soak
tests a system nobody actually decided the shape of.

**The target load, and a correction to it.** Q2 answered the target as the
remote screens, one on-site session, and one spare — roughly 3 browsers. That
undercounts the real demand. `app.js` runs `pollState` on an independent 1 s
`setInterval` and `pollZeros`/`pollEvents` on independent 15 s `setInterval`s
(`app.js:9,13,742-744`) — three separate timers, not sequential awaits. Every
~15 s a single browser can have two fetches in flight at once, and a browser
opens a second TCP connection rather than queue behind one in flight. So "one
browser = one socket" is not quite right; the real margin under the 7-socket
wall is smaller than Q2's answer implies.

**The refusal behavior at the ceiling is already right.** `rejected_total()`
exists and D14 already gives the operator a readable message when the relay
refuses a connection. This ADR records that behavior; it does not change it.

## Consequences

- Session 2 (the soak) should measure capacity at the current
  `timeout_keep_alive=5` first, as the baseline, then try a lower value (e.g.
  2s) as the first tuning experiment — not land either blind. `rejected_total`
  and `write_lock_timeouts` (backlog D3) are the two counters to watch.
- **`tools/synthetic_operator.py` does not currently reproduce the
  concurrent-fetch pattern above** — its poller hits only `/servo/state`, with
  no thread mirroring `pollZeros`/`pollEvents`'s independent timer. Measuring
  R1 against it as-is would undercount real socket demand. Tracked as a new
  backlog item, to be picked up as Session 2 prep, not fixed here.
- If Session 2's measurement shows `timeout_keep_alive` should move, that
  becomes its own backlog item with a number attached, not a retroactive edit
  to this ADR.
- Reopen this if R8 (emergency stop) or R4 (unified Lock) changes how many
  connections a session needs.
