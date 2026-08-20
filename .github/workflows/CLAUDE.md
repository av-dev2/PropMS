# CLAUDE.md — PropMS

Guidance for Claude Code when working in this repository. Adjust the
placeholders below (marked `TODO`) to match reality — this was scaffolded
without direct access to the repo.

## What this app is

PropMS is a custom Frappe app for property management, built by Aakvatech.
Notable features: OpenImmo XML export (XSD schema, `openimmo_anid` field,
`kontaktperson` sequence validation), property inspection workflows.

- Frappe version: version-15 (frappe 15.100.1)
- ERPNext: required implicitly — not declared in `hooks.py`
  `required_apps`, but `doc_events` hooks directly into ERPNext
  doctypes (Sales Invoice, Journal Entry Account, Material Request,
  Sales Order). PropMS will not install/migrate without erpnext
  present. Worth flagging upstream that this should be declared
  formally.
- A separate app, `openimmo_propms`, handles OpenImmo export — this is
  NOT part of the PropMS app itself. If a bug touches OpenImmo XML
  export, check whether it belongs in this repo or in openimmo_propms.
- Python version: TODO (run `python --version` in the bench)
- No `before_tests` hook is defined — tests run against standard
  Frappe/ERPNext fixtures with no PropMS-specific test setup.

## Conventions

### Branch naming
- `fix/<short-description>` — bug fixes
- `feat/<short-description>` — new features
- `chore/<short-description>` — tooling, deps, non-functional changes

### Commit messages
Use Conventional Commits:
```
<type>(<scope>): <short summary>

<optional body — why, not just what>
```
Types: `fix`, `feat`, `chore`, `refactor`, `test`, `docs`.
Example: `fix(openimmo-export): handle missing kontaktperson sequence`

### Pull requests
- Target branch: `develop` (TODO — confirm; adjust if it's `main`)
- Title mirrors the commit type/summary
- Description includes: root cause, what changed, how it was tested
- Never merge automatically — PRs are the human review checkpoint

## Testing

Frappe apps use `bench run-tests`. Tests live under
`propms/**/doctype/<doctype_name>/test_<doctype_name>.py` using
`FrappeTestCase`. If a bug fix touches a doctype or controller method
without an existing test file, add one alongside the fix.

Run locally:
```bash
bench --site <test-site> run-tests --app propms
```

## Working style

- Before implementing, explore the relevant doctype/controller code and
  any existing OpenImmo/inspection logic it touches.
- Always verify a fix against the test suite (or a new test if none
  exists) before committing — don't declare something fixed without
  running it.
- Keep changes scoped to the reported issue; don't refactor unrelated
  code in the same PR.
- Flag anything that looks like it needs an XSD schema update (OpenImmo
  export) rather than silently changing validation logic.
