# Taste

## Communication

- Writes requests in casual Indonesian and expects replies/code comments in Indonesian; instructions are short and outcome-focused (e.g. "re make menjadi fullscreen aja") rather than step-by-step specs. Confidence: 0.65

## Workflow & Tooling

- Expects Python projects to have a `.gitignore` that keeps virtualenvs (`.venv/`, venv/) and other generated artifacts out of commits — repo hygiene should be declared explicitly, not left implicit. Confidence: 0.5

## UI / Design

- Prefers fullscreen/edge-to-edge views over floating centered cards for immersive surfaces (e.g. the reader dialog fills the viewport on desktop too, content constrained by a text measure like 66ch rather than by a 880px card). Confidence: 0.6
- Prefers real routes/pages over in-page dialogs, modals, or pop-ups for primary content views — "Baca" should navigate to its own URL (e.g. a `/read/<slug>/<index>` page) rather than open a `<dialog>` overlay, so it is linkable and browser back/forward works. Confidence: 0.75
