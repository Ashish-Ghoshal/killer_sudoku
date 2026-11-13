# Project rules (also mirrored in CLAUDE.md)
- Modular layout: engine/, models/, ui/, telemetry/, tools/, tests/. No monolithic files.
- engine/ and models/ must NEVER import streamlit or any UI library. UI calls the engine, never the reverse.
- Every function has type hints and a docstring explaining its logical/mathematical purpose.
- Data contracts (Cage, BoardState, DeductionEvent) live in models/. Do not pass raw dicts between layers.
- Never use an LLM for arithmetic or constraint checking. Python decides; LLMs only phrase hints (Phase 3).
- Adding a technique = new Technique subclass in engine/techniques.py + entry in DEFAULT_TECHNIQUES + a test.
- Run `python -m unittest discover -s tests -v` before finishing any change.
