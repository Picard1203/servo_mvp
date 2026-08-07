# Relay: what the working implementation does, and why

This file exists because the relay was once rewritten from scratch instead of
ported, and the rewrite reintroduced problems the original had already solved.
The reference is the Stage-2 relay sketch (`4_relay_sketch_ino.txt`) and its
Python counterpart (`5_relay_main_py.txt`).

If you change `NetworkRelay`, check these five points first.

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
