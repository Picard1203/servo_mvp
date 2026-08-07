# Plain HTML, CSS and JavaScript — no framework, no build step

The UI is hand-written HTML/CSS/JS served straight from `python/static/`. There
is no framework and no build pipeline.

The binding reason is the air gap (ADR-0005): a build pipeline means a toolchain
and a dependency tree that would have to be vendored and reproduced on an
isolated network, for a UI of this size. A secondary consideration was payload
size over the MCU relay (ADR-0001).

## Considered and rejected

A framework was rejected on the air-gap ground alone. **The relay-capacity
argument is unverified** — it is plausible that the Bridge could carry a
framework's payloads perfectly well, and that assumption should not be treated as
established. See backlog R3.

The decision stands on the air gap regardless of how R3 resolves.

## Consequences

- No transpilation, no bundler, no `node_modules` to vendor.
- The UI is readable and debuggable directly in the browser on the board.
- Anything a framework would give for free — state management, reactivity — is
  hand-rolled in `app.js` and must be maintained there.
