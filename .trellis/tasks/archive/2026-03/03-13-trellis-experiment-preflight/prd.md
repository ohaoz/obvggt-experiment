# Add Experiment Preflight To Trellis

## Goal
Make Trellis surface experiment-run safety checks automatically so new sessions and experiment tasks consistently see the right server targets, path expectations, and forbidden operations before running anything on production machines.

## Requirements
- Add Trellis-owned configuration for experiment operations context, including default server info, remote roots, and production red lines.
- Surface that context in Trellis startup output so `get_context.py` shows an experiment preflight section by default.
- Add a Trellis-owned backend spec for experiment operations / safety, and link it from the backend index and workflow guidance.
- Add an automatic lifecycle reminder so starting a Trellis task prints a short experiment preflight banner.

## Acceptance Criteria
- [ ] `.trellis/config.yaml` contains structured experiment operations settings that can be read by scripts.
- [ ] `python .trellis/scripts/get_context.py` includes an experiment preflight section with server info and forbidden operations.
- [ ] `.trellis/spec/` includes a dedicated experiment operations / safety guide and the relevant indexes reference it.
- [ ] Starting a Trellis task triggers a readable preflight reminder without breaking task start.
- [ ] Validation confirms the updated Trellis scripts still run locally.

## Technical Notes
- Keep all Trellis docs in English, even if the source operational rules were originally written in Chinese.
- Do not store secrets in Trellis config; only store stable, non-secret operational facts.
- Prefer minimal parser-compatible YAML structures because Trellis uses a lightweight custom YAML reader.
