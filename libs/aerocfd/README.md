# aerocfd

Aircraft CFD post-processing library for the AerisVault ecosystem.

Turns raw steady-state Fluent force/moment reports (body frame) into aerodynamic
polars: CL, CD, L/D, drag polar, and Cm — via body→wind rotation and the
pitching-moment sign convention. Pure Python + numpy + plotly; no database, no
Streamlit. The UI lives as a module inside the `apps/aerisvault/` portal shell.

See `docs/superpowers/specs/2026-05-10-aerocfd-design.md` for the full design.
