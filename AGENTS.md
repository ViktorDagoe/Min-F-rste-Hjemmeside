# AGENTS.md

## Cursor Cloud specific instructions

This repository is a **static, no-build content project** ("AI Skill Workstation"): Danish
learning material in Markdown (`manual/`, `prompts/`, `projects/`, `sales/`, `workstation/`,
`tutor/`) plus two hand-written static HTML pages:

- `index.html` — the site landing page.
- `projects/projekt-01-lokal-landingsside/index.html` — a demo local-business landing page.

There is **no `package.json`, no lockfile, no build step, no test suite, and no backend**. Do
not look for or add one unless the task explicitly asks. There are no dependencies to install, so
the startup update script is intentionally a no-op.

### Run it (dev "server")

Serve the repo root with any static file server, e.g.:

```
python3 -m http.server 8000
```

Then open `http://localhost:8000/` (landing page) or
`http://localhost:8000/projects/projekt-01-lokal-landingsside/index.html` (demo page).
The HTML is fully self-contained (inline CSS, no JS beyond native `<details>` accordions), so
edits are visible on a simple browser refresh — there is no hot-reload process.

### Lint / test / build

None are configured. "Correctness" for content changes is editorial (Markdown/HTML). If you
want a quick sanity check on the HTML, open it in a browser or `curl` the served URL and confirm
HTTP 200; there is no automated linter or test runner to run.
