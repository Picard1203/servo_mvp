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
the number of Bridge round trips for identical payload.

**Settled, 23 August 2026 — the 256 question is closed for good, with a cause,
not just a result.** `256` is not a race-window casualty (rule 7 was already
shipped when this was tested) and not a mystery — it is a hard structural
overflow. Every Bridge RPC message, in both directions, is encoded into a
fixed-size buffer defined by the vendored library itself:

    Arduino_RPClite/src/Arduino_RPClite.h:
      #define DECODER_BUFFER_SIZE     1024
      #define DEFAULT_RPC_BUFFER_SIZE (DECODER_BUFFER_SIZE / 4)   // = 256
    Arduino_RouterBridge/src/bridge.h:
      #define BRIDGE_RPC_BUFFER_SIZE  DEFAULT_RPC_BUFFER_SIZE      // = 256

That 256 bytes is the *entire* message — MsgPack framing (method name, msg_id,
argument headers) plus payload, not payload alone. `BRIDGE_RPC_BUFFER_SIZE`
applies to every RPC call through this library, including our own `net_tx` —
we don't use RouterBridge's built-in `TcpClient` facade, so its exact
`TCP_RESPONSE_HEADER_SIZE - 20` accounting (giving **236**) is precise for a
code path we don't take, not for ours. It is still the right order of
magnitude — our own MsgPack framing for `net_tx(slot, data)` costs a similar
handful of bytes (method name, msg_id, slot argument, binary-payload header) —
but treat 236 as an estimate we're comfortably under, not an exact figure for
this call shape. A `kRelayChunkBytes` of 256 raw payload bytes, plus any framing
on top, cannot fit in a 256-byte total buffer regardless — it was never going
to work, at any chunk timing, on any board. That is what the operator saw at
the first demo.

**Not pursued, but the next lever if 224 is ever not enough**: `bridge.h`
sends `notify(SET_BUF_METHOD, BRIDGE_RPC_BUFFER_SIZE)` — a `$/setMaxMsgSize`
negotiation with the Linux-side Router, "no effect if Router is not exposing
[it]" per the library's own comment. `DECODER_BUFFER_SIZE` (1024, of which
`BRIDGE_RPC_BUFFER_SIZE` is a fixed 1/4) is the ceiling on any negotiated
value. Untested whether this board's Router actually honors it — check that
before re-deriving chunk-size math from scratch.

**`kRelayChunkBytes = 224` is the validated value**, chosen with headroom under
the ~236-byte estimated ceiling. Board-measured, 23 August 2026, full-range
telemetry export (44,827 rows, 806,898 bytes): clean transfer, zero connection
churn, zero dropped exports, throughput ~4.5 KB/s → ~6.7 KB/s (≈49% faster
than 128, fewer round trips for the same payload). **Also validated under the
exact condition that broke 256** — the 256 failure showed as churn on *other*
connections (the SSE stream), not the export itself, so 224 was re-tested with
2 SSE streams held open concurrently with a full export running: both streams
continuous and undisturbed (23,184 / 23,180 bytes, zero drops) for the whole
transfer. 256 itself, re-tested the same
session on the same rule-7-fixed relay, reproduced instant export failures
(0 rows served) and repeating ~3-second connect/disconnect churn — confirming
the overflow theory directly, not just historically.

Do not raise this past 230 without re-deriving the MsgPack framing overhead for
whatever call shape is in use at the time — the 236-byte figure is exact, the
margin is not.

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

**`DiagLog` (backlog D3) is a second lock, deliberately separate from
`chip_lock_`.** Every hardware/network file pushes diagnostic records into it
from either thread, so it needs its own mutex - but it is never a sink
callback and never touches the Bridge itself, so holding `chip_lock_` while
calling `DiagLog::Push()` is safe (the ordering is always `chip_lock_` then
`DiagLog`'s lock, never the reverse - no inversion risk). Only
`BridgeApi::DrainDiagLog()`, called from `Tick()`, ever notifies Linux with
what it collects, and it does so outside both locks.

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
