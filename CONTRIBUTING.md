# Contributing to AI Security Lab

Thanks for your interest in improving AI Security Lab! 🎉 This project is an
educational platform for AI/ML security. Contributions of new modules, fixes,
tests, and docs are all welcome.

> ⚠️ **Ethics first.** Every vulnerability here is *intentional* and runs only
> against the lab's own simulated targets. Do not use anything you learn here
> against systems you are not authorized to test.

## Getting set up

```bash
git clone https://github.com/<your-fork>/AI-Security-Lab.git
cd AI-Security-Lab

python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Full runtime (includes the ML stack)
pip install -r requirements.txt

# Dev tooling only (fast; enough to run the tests)
pip install -r requirements-dev.txt
```

Run the app:

```bash
python app.py        # http://localhost:5000
```

Run the test suite:

```bash
pytest -q
```

The app degrades gracefully to deterministic rule-based fallbacks when
`torch`/`transformers` are not installed, so the tests run without the heavy ML
dependencies. CI uses `requirements-dev.txt` for this reason.

## Project layout

| Path | Purpose |
|------|---------|
| `app.py` / `config.py` | App factory, configuration, module & OWASP metadata |
| `models/` | Vulnerable model implementations (one file per concept) |
| `utils/` | Security levels, sanitisation, rate limiting, achievements |
| `routes/` | Flask blueprints (`main`, `modules`) |
| `content/` | Static educational content (solution walkthroughs) |
| `templates/` | Jinja2 templates (Tailwind via CDN) |
| `database/` | Schema + seed data |
| `tests/` | pytest suite |

## Adding a new vulnerability module

1. **Register it** in `MODULES` (and `OWASP_MAPPING`) in `config.py`. The dict
   key must match the route function name so `url_for('modules.<key>')` works.
2. **Implement the model** in `models/<name>.py`. Support `LOW`/`MEDIUM`/`HIGH`
   and keep all dangerous behaviour *simulated*.
3. **Add routes** in `routes/modules.py`. Decorate attack endpoints with
   `@rate_limited('<key>')`.
4. **Build the template** `templates/modules/<name>.html` (extend `base.html`).
5. **Wire the UI**: add a sidebar link and an icon branch in `index.html`.
6. **Seed hints** in `database/init_db.py` and a walkthrough in
   `content/solutions.py`.
7. **Write tests** in `tests/` covering both the model and the routes.

## Coding guidelines

- Follow PEP 8 (lines ≤ 120 chars). `flake8` runs in CI.
- Add a comment explaining **why** code is intentionally vulnerable.
- Keep the lab **offline** — no new mandatory external services or API keys.
- Add or update tests for any behaviour change; keep `pytest` green.

## Pull requests

1. Branch: `git checkout -b feature/my-change`
2. Make focused, atomic commits.
3. Ensure `pytest -q` and `flake8` pass.
4. Update `README.md` / `CHANGELOG.md` where relevant.
5. Open a PR describing the change and its educational value.

Happy (ethical) hacking! 🛡️
