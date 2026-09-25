# odcs-ui

The shared design foundation for **ODCS App Studio** apps (Keep, VeloCoder, movieapp).
One set of tokens, one theme engine, one component-state spec, so every app looks and
behaves like part of the same family.

Design principles, the Apple HIG layer, component states and layout rules are in
[DESIGN.md](DESIGN.md).

## What's in 0.1

| Module | Needs Qt | What it does |
|---|---|---|
| `odcs_ui/tokens.json` | — | **Single source** of color roles (light + dark) and scales (spacing, radius, control height, focus width) |
| `odcs_ui.tokens` | no | Loads the tokens; `DARK`, `LIGHT`, `THEMES` match the per-app `themes.py` it replaces |
| `odcs_ui.color` | no | WCAG luminance and contrast, compositing, `on_accent()` (black or white on any accent), `readable()` fallback |
| `odcs_ui.web` | no | Generates `web/odcs.css`: CSS custom properties, OS dark mode, and the OS accent via `AccentColor` |
| `odcs_ui.theming` | yes | `ThemeController`: Dark / Light / Match System, desktop accent, live switching, `$TOKEN` QSS rendering that fails loudly on typos |
| `odcs_ui/base.qss` | yes | Base stylesheet implementing the component states (normal, hover, pressed, checked, disabled, focus) with constant geometry |
| `odcs_ui.timefmt` | yes | `friendly_clock()` / `friendly_datetime()` in the desktop locale's own format |

## Use it in a Qt app

```bash
/path/to/app/.venv/bin/pip install "odcs-ui @ git+https://github.com/tneohcl/odcs-ui@v0.1.0"
```

```python
from pathlib import Path
from odcs_ui.theming import ThemeController, BASE_QSS, THEME_CHOICES, set_role

theme = ThemeController(app, [BASE_QSS, Path(__file__).with_name("style.qss")],
                        extra_tokens=lambda name, values: {"CHECK_PATH": str(check_icon)},
                        choice=settings.get("theme", "system"))
theme.apply()
set_role(backup_button, "primary")   # the current task's action gets the accent
```

App stylesheets keep using `$TOKEN` placeholders (`$BG_PANEL`, `$TEXT_SECONDARY`, …).

## Use it on the web

Link `web/odcs.css` and use the variables: `var(--odcs-bg-panel)`, `var(--odcs-accent)`.
Set `<html data-theme="dark">` to force a theme; otherwise it follows the OS.

## Rules the tests enforce

- Every readable text role reaches **WCAG AA 4.5:1** on window, panel and field in both themes.
- Captions stay quieter than secondary text.
- The fallback accent pairs with readable on-accent text.
- `web/odcs.css` matches the tokens (regenerate with `python -m odcs_ui.web > web/odcs.css`).

```bash
python3 -m unittest tests.test_tokens_color_web                       # no Qt needed
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_qt           # PySide6 >= 6.8
```

## Roadmap

- **0.2:** shared widgets: segmented view switch, settings list rows, status facts
  (completed / checked / tested), collapsible section, empty state, ODCS About dialog.
- **0.3:** Keep and VeloCoder migrate onto odcs-ui (toolbar model, menus); movieapp adopts `odcs.css`.

## License

MIT, see [LICENSE](LICENSE).
