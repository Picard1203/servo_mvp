# Develop as if already air-gapped

Production runs on a secure isolated network with no internet access. Rather than
build connected and port later, the project is developed as though the air gap
were already in place, so shipping is "zip the folder".

This constraint is invisible in the code and explains several things that
otherwise look like over-engineering: the vendored `wheelhouse/`, the patched
`Ethernet`/`SCServo` libraries checked into `libraries/`, the pinned
`arduino:zephyr` core version, and the absence of any build tooling (ADR-0002).

## Consequences

- Python wheels are built ahead of time for ARM64
  (`--platform manylinux2014_aarch64`).
- The Arduino core version must already be present on the target — Board Manager
  does not exist on an isolated machine. This is the most likely cause of "it
  worked on my laptop".
- No CDN, no package fetch, no dependency resolution at deploy time.

## Currently unverified

Development happens on a **WiFi-mounted board**, because there is only one servo
bus adapter and it sits on a "coloured" internet-facing network that cannot be
introduced to the secure one. The air-gapped path has therefore never actually
been exercised end to end. See backlog T2 and R7.
