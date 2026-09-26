# odcs-ui

The shared design foundation for **ODCS App Studio** apps (Keep, VeloCoder, movieapp).
One set of tokens, one theme engine, one component-state spec, so every app looks and
behaves like part of the same family.

Design principles, the Apple HIG layer, component states and layout rules are in
[DESIGN.md](DESIGN.md).

## What's in it

| Module | Needs Qt | What it does |
|---|---|---|
| `odcs_ui/tokens.json` | — | **Single source** of color roles (light + dark) and scales (spacing, radius, control height, focus width) |
| `odcs_ui.tokens` | no | Loads the tokens; `DARK`, `LIGHT`, `THEMES` match the per-app `themes.py` it replaces |
| `odcs_ui.color` | no | WCAG luminance and contrast, compositing, `on_accent()` (black or white on any accent), `readable()` fallback |
| `odcs_ui.web` | no | Generates `web/odcs.css`: CSS custom properties, OS dark mode, and the OS accent via `AccentColor` |
| `odcs_ui.theming` | yes | `ThemeController`: Dark / Light / Match System, desktop accent, live switching, `$TOKEN` QSS rendering that fails loudly on typos, keyboard-only focus ring |
| `odcs_ui/base.qss` | yes | Base stylesheet implementing the component states (normal, hover, pressed, checked, disabled, focus) with constant geometry |
| `odcs_ui.timefmt` | yes | `friendly_clock()` / `friendly_datetime()` in the desktop locale's own format |
| `odcs_ui.widgets` | yes | **0.2:** `ViewSwitch`, `SettingsList`/`SettingRow`, `StatusFacts`, `CollapsibleSection`, `EmptyState`, `AboutDialog` |
| `odcs_ui.demo` | yes | **0.2:** a gallery of every widget: `python -m odcs_ui.demo --theme dark` |

## The widgets (0.2)

| Widget | Behaviour |
|---|---|
| `ViewSwitch` | Segmented view switch (Status / Restore). Quiet raised selection, never the accent; arrow keys move; selection changes colour only, so nothing shifts |
| `SettingsList` + `SettingRow` | Grouped settings, two lines per row: label, then the value (wraps, never truncates) with an optional status dot; optional leading icon; chevron. Each row is a real button (focus, Space/Enter, accessible name "Label: value. Change"). `setValue(text, "error", indicator="error")` colours the value and shows a dot while the words carry the meaning |
| `StatusFacts` | Separate facts with their own result and date (backup completed / integrity checked / recovery tested). Never-happened facts read "Not yet recorded"; optional action button per fact |
| `StatusIcon` | Painted ok / warning / error / never / info glyphs in the live theme's colours |
| `CollapsibleSection` | Leading ▸/▾, collapses to the header only |
| `EmptyState` | Icon and an instruction that names the action |
| `AboutDialog` | App icon, name, version, description, "© 2026 ODCS App Studio", extra buttons (System Information, Licenses), Close as default in the platform's button order |

Plain `QWidget` windows get the theme background with `theming.set_surface(widget, "window")`
(`QMainWindow` and `QDialog` get it automatically).

## Use it in a Qt app

```bash
/path/to/app/.venv/bin/pip install "odcs-ui @ git+https://github.com/tneohcl/odcs-ui@v0.4.3"
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
QT_QPA_PLATFORM=offscreen python3 -m unittest tests.test_qt tests.test_widgets   # PySide6 >= 6.8
```

## Roadmap

- **0.2 (done):** the shared widgets above.
- **0.3 (done):** keyboard-only focus ring (`FocusVisibleFilter`, installed by `ThemeController`;
  base.qss styles `[focusVisible="true"]`, never plain `:focus`); no separator under the last
  status fact. Keep and VeloCoder run on it (toolbar model, menu bar everywhere).
- **0.4 (done):** two-line `SettingRow` (label over value), optional leading icon, `StatusDot` indicator.

## License

MIT, see [LICENSE](LICENSE).
