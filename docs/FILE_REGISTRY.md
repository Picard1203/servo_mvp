# File registry

A catalogue of artifacts produced for this project **that do not live in this
repository** — earlier deliverables, reference documents and superseded
implementations. It exists so that when you need an old file you know which one
and why, instead of guessing from filenames.

> **Nothing here is required for day-to-day work.** The live project is this
> repository, under git. Start at `CLAUDE.md`.
>
> This file describes a pre-git workflow where the project moved between chats as
> a `servo_mvp.zip`. That is history. It is kept because the **Reference** section
> below still points at genuinely useful documents.

## The ones worth knowing about

- **`servo_truth.md`** — the ST3215 register map with every value tagged VERIFIED
  or BENCH. The servo reference, and the source of most hardware numbers now
  summarised in `PROJECT_STATE.md`.
- **`UNO_Q_Network_Options_Tradeoff.md`** — why the Ethernet-shield relay was
  chosen. Read it before anyone proposes changing the network architecture; the
  decision itself is recorded as ADR-0001.
- **`4_relay_sketch_ino.txt`** and **`5_relay_main_py.txt`** — the *working*
  relay implementation. Comparing against these is how the worst bug in the
  project was found. If a relay rewrite goes wrong, read these before
  re-deriving.

---

## Reference — still useful, not superseded

| File | Why you'd open it |
|---|---|
| `servo_truth.md` | ST3215 register map, units, every value tagged VERIFIED or BENCH. The servo reference. |
| `Arduino_UNO_Q_Complete_Field_Guide.md` | UNO Q platform notes: Bridge, pinout, boot, gotchas. |
| `UNO_Q_Network_Options_Tradeoff.md` | Why the Ethernet-shield relay was chosen. Read before anyone proposes changing the network architecture. |
| `mvp_design_plan.md` | Original architecture and rationale. (`mvp_design_plan_md.txt` is an identical copy.) |
| `servo_diag_app.txt` | The servo diagnostic app. Re-run it whenever hardware behaviour is in doubt — it produced most of the verified numbers. |

---

## Historical — superseded, keep only for provenance

**Reference implementations that proved a pattern.** Consulted when a rewrite
went wrong; that is exactly how the `accept()` bug was found.

`4_relay_sketch_ino.txt`, `5_relay_main_py.txt` — the working relay.
`2_demo_sketch_ino.txt`, `3_demo_python_main_py.txt` — first full demo.
`2_shield_test_sketch_ino.txt`, `3_shield_test_main_py.txt` — shield bring-up.
`1_README_md.txt`, `4_requirements_txt.txt`, `6_relay_requirements_txt.txt`.

**Source packages, now living inside the zip.** Superseded — the zip is newer.

`backend_project.txt`, `backend_changes_pack1.txt`, `tests_project.txt`,
`gui_project.txt`, `gui_patch1.txt`, `gui_rev2/3/4.txt`,
`gui_rev5_diffs.txt`, `python_project.txt`, `sketch_project.txt`,
`sketch.ino`, `app.js`, `ui_index_html.txt`.

**GUI design iterations.** Only if revisiting visual design.

`servo_themes.html`, `servo_themes_light.html`, `servo_gui_options.html`,
`servo_gui_rev2.html`, `servo_gui_rev3.html`, `servo_hmi_v2.html`,
`servo_lcars_chrome.html`, `servo_lcars_final.html`,
`servo_desktop_preview.html`, `servo_webui_preview.html`.

**Patch scripts — all already applied.** Do not re-run against the current
zip; they target older states. Listed so you can identify one if it turns up.

| Script | What it did |
|---|---|
| `patch_accept.py` | `available()` → `accept()` in the relay |
| `patch_stability.py` | Disconnect-before-accept, `loop()` yield, quieter logs |
| `patch_bridge_lock.py` | Serialised Bridge calls |
| `patch_backend_visible.py` | Reported hardware vs simulated backend |
| `fix_imports.py` | Undid Pylance import rewrites |
| `patch_envfile.py`, `fix_gui_css.py`, `revert_extras.py`, `servo_diag_spi_fix.txt`, `servo_diag_fixpack2.txt` | Superseded one-offs |

**Empty or stray:** `relay`, `shield_test`, `unoq_shield_first_connection.zip`.

---

## Safe to delete

Everything under "Historical" except the reference implementations
(`4_relay_sketch_ino.txt`, `5_relay_main_py.txt`) — those earned their keep
once and might again.
