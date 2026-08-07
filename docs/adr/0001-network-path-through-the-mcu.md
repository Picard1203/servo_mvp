# The network path runs through the MCU, not the Linux side

Production boards have the WiFi/Bluetooth chip **desoldered**, so the Linux side
(MPU) has no native network of its own. The Ethernet shield therefore sits on the
MCU, and a relay on the MCU pumps bytes across the Bridge to the Linux side,
where FastAPI actually serves. Operators reach the app at
`http://<board-ip>:8000` over that path.

This is the single most consequential fact about the system's shape, and it is
invisible from any one file: the sketch has no HTTP knowledge, the backend has no
Ethernet knowledge, and neither reveals why the relay exists at all.

## Consequences

- Every byte between browser and backend crosses an MCU byte pump. Payload size
  and connection count are architectural concerns, not micro-optimisations.
- `kMaxRelaySockets = 6` is the only connection ceiling in the entire system —
  there is no Linux-side cap.
- The relay owns no HTTP semantics by design; it moves bytes. Keeping it that
  way is what makes it reviewable.
- Every serious defect in this project has lived on this path. See
  `sketch/src/RELAY_NOTES.md`.
