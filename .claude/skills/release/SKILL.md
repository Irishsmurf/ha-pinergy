---
name: release
description: Cut a new release of the ha-pinergy integration — verify tests pass, choose the next semver tag, and publish a GitHub release (CI attaches the integration zip).
disable-model-invocation: true
---

Cut a new release of ha-pinergy. Requested version: $ARGUMENTS (optional, e.g. `v0.2.0`).

1. Ensure the working tree is clean and `main` is fully pushed (`git status --short`, `git log origin/main..main --oneline`). Stop and report if not.
2. Run `python -m pytest tests/` — abort if anything fails.
3. Determine the tag: use $ARGUMENTS if given; otherwise take the latest tag from `gh release list` and increment the patch version. Confirm the tag with the user before publishing.
4. Publish: `gh release create <tag> --title "<tag>" --generate-notes`.
5. The Release workflow stamps `manifest.json` with the tag version and uploads `pinergy.zip`. Watch it (`gh run watch`) and confirm the asset with `gh release view <tag> --json assets`.

Never hand-edit the `version` field in `manifest.json` for a release — the workflow handles it.
