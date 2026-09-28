# QR → A1

A local URL-to-QR and 3D model generator for macOS and Bambu Studio.

## Setup

Install Python 3.9+ and Bambu Studio, then run in this folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Double-click `Launch QR Maker.command`, or run `.venv/bin/python app.py`, then use http://127.0.0.1:8765.

1. Paste a website link. Choose diameter and model style.
2. Generate. The QR image is decoded to check its contents; the base is checked for a closed connected mesh.
3. Download the model, or open it in Bambu Studio.
4. Select A1, your actual nozzle/filament/plate, and assign colors if needed. Slice and inspect the model before selecting Print plate and your connected printer.

**Printer connection:** Studio was signed out during setup. Sign in and connect the A1, or configure LAN mode in Studio. This utility opens Studio; it does not implement a direct printer upload or automatically start printing. No printer credentials are collected.

**Model choices:** Hollow mode retains the circular rim, rear grid and optional garage grip; it is decorative, not scan-verified. Solid mode provides a base and separate raised QR for contrasting colors. Black-only relief is not a reliable scannable QR. A passed PNG decode is not a physical scan test.

3MF holds two mesh parts as one assembly with suggested light/dark colors. Colors must be checked in Studio. Separate STL parts retain matching coordinates. STL has no filament colors. Geometry files are not pre-sliced and no print-time estimate is claimed.

The garage grip has 20 mm between upright legs and a top bar 10 mm above the base plane. Small diameters may be rejected to keep QR modules printable. Grip fit, bridge quality and strength need a physical test.

Generated files stay in `generated/`. The server listens only on this Mac, with a per-launch request token. Stop using Ctrl-C in the launcher terminal. Python dependencies are in `.venv`; reinstall if relocating to a different machine.

## Reinforced 35 mm example

Use `QR_35mm_reinforced_A1.3mf` for the latest A1 0.4 mm nozzle slice. `QR_single_color.stl` is now a boolean-fused, single watertight body, verified after export. The supporting grid is 0.48 mm wide and 0.84 mm thick; raised QR detail is 0.56 mm tall with 0.08 mm internal overlap to fuse it to the grid. Disc diameter stays 35 mm and the garage opening stays 20 mm wide.

Estimated model printing is 9m 2s, or 15m 23s including preparation, with 1.48 g of filament. The profile assumes Generic PLA and Textured PEI Plate. The upright garage bar still needs bridge/strength testing. Physical scanning remains unverified. The older `QR_35mm_fast_A1.3mf` is retained as a thinner alternative, not the reinforced version. A three-minute design has not been implemented.
