# Relay: what the working implementation does, and why

This file exists because the relay was once rewritten from scratch instead of
ported, and the rewrite reintroduced problems the original had already solved.
The reference is the Stage-2 relay sketch (`4_relay_sketch_ino.txt`) and its
Python counterpart (`5_relay_main_py.txt`).

If you change `NetworkRelay`, check these seven points first.

## 1. Adopt connections with `accept()`, never `available()`

    accept()     hands over a connection EXACTLY ONCE, transferring
                 ownership. This is what an accept loop needs.
    available()  returns whichever client currently has UNREAD DATA, and
                 returns THAT SAME CLIENT AGAIN on every call. The server
                 keeps ownership.

Building an accept loop on `available()` adopts one connection into several
slots, and each slot then forwards fragments of the same TCP stream under a
different slot number - so one HTTP request arrives split across several
sockets on the Linux side. Symptom: the first exchange or two work, then
everything is corrupt.

## 2. Detect disconnects BEFORE accepting, and on the edge

Order inside Poll() matters: disconnect detection first, then accept, then
pump. If accept runs first, a slot whose client has just dropped can be
handed to a new connection in the same pass while `net_close` for the old one
has not been sent - and the Linux side then feeds the new connection's bytes
into the old socket. Symptom: uvicorn logging "Invalid HTTP request
received" during rapid connection churn.

Track `was_up[slot]` and act on the was-connected -> not-connected
transition. Testing `!connected()` every pass emits `net_close` continuously
for slots that are merely idle.

## 3. `loop()` must yield

`Poll()` returns immediately when there is nothing to do, so `loop()` spins
at full speed. The Bridge RPC runs on its own thread; a loop that never gives
up the CPU starves it, and a `servo_read` then misses its 10 s deadline. The
late reply arrives as "Response for unknown msgid". A `delay(1)` at the end
of `Tick()` costs nothing against the relay's latency budget and prevents it.

## 4. One bulk read per slot per pass

`client.read(buffer, sizeof(buffer))`, not a byte-at-a-time loop. Never
block, never `delay()` inside the pump - the same `loop()` also drives the
servo bus.

## 5. Chunk size must match the Python side

`kRelayChunkBytes` here and `relay_chunk_bytes` in the backend settings are
one number in two places. It is bytes per Bridge message: halving it doubles
the number of Bridge round trips for identical payload. 256 is the value the
working relay used.

**Contested, 7 August 2026.** The operator recalls 256 *failing* at the very
first demo. Both statements cannot be the whole truth, and nobody has the
measurement. Treat 256 as an experiment with a recorded result, not as a
known-good value to restore. Note also that any chunk-size measurement taken
before rule 7 was applied is worthless: a larger chunk means a longer SPI
transaction, so it changed the width of the race window rather than the
throughput. See backlog D6.

## 7. Serialise access to the W5500 across threads

The five rules above are all about ordering *within* `Poll()`. This one is
about two threads, and it is the bug they did not cover.

    Poll()            runs on the LOOP thread
    WriteToClient()   run on the BRIDGE thread, via net_tx / net_shutdown
    CloseClient()

Six sockets, but **one chip and one SPI bus.** Every socket operation -
`connected()`, `accept()`, `read()`, `write()`, `stop()` - is a conversation
over that one wire. Two threads talking at once splice their messages
together: the chip answers nonsense, or waits for the rest of a message that
never arrives while the Bridge thread blocks behind it and `servo_read` dies
at its 10 s deadline.

Symptom, measured on the board before the fix: sampler gaps of **10.99 s,
11.00 s, 11.00 s** - the servo_read timeout plus one sampler interval - each
storing a fabricated position of count 0, and one of count -1, which no
0..4095 servo can report. Connections dropping, and a first button press
doing nothing.

The relay shipped with **no mutex anywhere in `sketch/src/`** for a year.
`provide_safe` is largely to blame: it means "you are now responsible for
thread safety", but it reads as "registered safely", and the comment beside
it describing the hazard was easy to walk past.

Three things the fix must get right:

1. **Never hold the lock across a sink callback.** The sinks notify Linux over
   the Bridge, and the Bridge thread may be waiting for this same lock inside
   `net_tx`. Holding it there deadlocks both threads permanently - worse than
   the stall it fixes. Collect under the lock, release, then dispatch.
2. **Bound the wait on the Bridge side** (`K_MSEC`, not `K_FOREVER`). A
   blocked Bridge thread is the failure being fixed; a write that fails
   honestly is recoverable, a wedged RPC thread is not. `write_lock_timeouts()`
   counts these - a non-zero value means `loop()` is holding the chip too long.
3. **Cover whole operations**, not individual calls, or the race window is
   merely narrowed and it will look fixed while still failing occasionally.

A mutex, not a semaphore: this protects one resource, it is not a count of
several. `k_mutex` also gives priority inheritance, which matters when the
Bridge thread outranks the loop thread.

## 6. Console: `Serial` works; `Monitor` is an option, not a requirement

The sketch prints through `Serial`, and that is proven - the servo
diagnostic used it and both output and typed commands worked over USB.

`Monitor` (the Bridge's console facade) is the alternative the Stage-2 relay
demo used. Its only advantage is that it also reaches App Lab when App Lab is
attached over WiFi rather than USB. Switch only if you actually need that;
there is no correctness reason to.

## Bridge contract (both directions)

    MCU -> Linux   net_open(slot, client_ip)   net_rx(slot, data)
                   net_close(slot)
    Linux -> MCU   net_tx(slot, data)          net_shutdown(slot)

`net_tx` and `net_shutdown` are registered with `provide_safe`: they are
called from the Bridge thread while `loop()` may be inside the relay.
Payloads are `MsgPack::bin_t<uint8_t>` - the byte stream is binary and must
not be packed into a String.

`tools/check_bridge_contract.py` verifies both sides agree on every name and
argument count.
