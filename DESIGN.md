# ODCS App Studio — Design Foundation

*Draft 3 · 2026-09-25 (Apple HIG philosophy; Keep review: recovery honesty, states, relaxed rules) · applies to Keep, VeloCoder, movieapp and every future ODCS app*

## Brand statement

**ODCS apps are quiet, trustworthy tools that do one job completely.**
They look at home on whatever desktop they run on, explain themselves in plain
language, never surprise you with a destructive action, and work fully from the
keyboard. You should be able to recognize an ODCS app by how it *behaves*
(calm, clear, safe) as much as by how it looks.

## Principles

1. **Native first.** Follow the desktop: system font, system accent color, system
   light/dark by default. The brand lives in structure, spacing and behavior, not
   in a logo color painted over everything.
2. **Plain language.** Say what will happen ("Convert 4 Videos", "Back up now"),
   not how. No jargon in the default view; details live behind *Expert* or *Details…*.
3. **Safe by default.** Preview before changing things, confirm before anything
   irreversible, keep backups of what you overwrite, and never hide a failure.
4. **One obvious next step.** The strongest accent marks the *current task's* action — usually
   the toolbar's trailing end, the default button in a dialog. When the view changes, so does
   the primary (Keep: Back up now on Status, Review restore… on Restore, Try again on an error).
   Task flow and platform convention win over position rules.
5. **Complete for everyone.** Every action works from the keyboard, every text meets
   WCAG 2.2 AA contrast (4.5:1), and state is never shown by color alone.
6. **Honest status.** Show what is really true (from the source of truth, not a
   cache that can drift), with a timestamp in the user's own time format. Separate facts get
   separate results and dates (Keep: backup completed · integrity checked · recovery tested),
   and something that never happened is shown as "Not yet recorded", never implied.
   Promises depend on verified state: say what Keep checked, and ask the user to confirm
   what only they can know (e.g. off-machine copies of a passphrase).

## Apple HIG philosophy, adopted

ODCS follows Apple's Human Interface Guidelines wherever they don't conflict with the
host desktop. On macOS they apply literally; on KDE and Windows the same ideas are expressed
with native controls.

- **Content first (deference).** Chrome recedes: fewer borders and cards, more whitespace,
  grouped lists with hairline separators, sidebars on the window color.
- **Forgiving.** Undo (⌘Z / Ctrl+Z) for every action that can be undone; confirm only the
  irreversible; move to a cleanup folder or trash rather than delete.
- **Quiet.** No modal pop-up for a successful operation: show it inline. System
  notifications only for background events (e.g. a scheduled backup failed).
- **Direct, where it fits.** Drag and drop for content, context menus on items that have
  actions, Shift/Ctrl-click multi-select in lists. The Delete key removes only where the
  removal is undoable or harmless; Space previews where it makes sense.
- **Settings** live in one Settings window on ⌘, / Ctrl+, not scattered through the main window.
- **Platform-correct details:** ⌘ on macOS, Ctrl elsewhere (Qt standard key sequences), and
  each OS's own dialog button order (QDialogButtonBox), never hard-coded.
- **Remember state:** window size and position, collapsed sections, last view.
- **Accessibility settings:** honor reduce motion, increase contrast and bold text where the
  platform exposes them.

## Tokens (single source → Qt QSS and web CSS)

Color roles, not hex codes, are the contract. `tokens.json` in this package is
the one place values live; it generates `$TOKEN` substitutions for Qt stylesheets
and `--odcs-*` CSS custom properties for the web.

| Role | Purpose | Rule |
|---|---|---|
| `BG_WINDOW` / `BG_PANEL` / `BG_FIELD` | Window, cards, inputs | Three distinct levels in both themes |
| `BG_CONTROL` (+ `_HOVER`, `_PRESSED`) | Buttons and controls | Reads more clickable than a container |
| `BORDER` / `BORDER_OUTER` / `BORDER_STRONG` | Quiet → structural → interactive edges | |
| `TEXT_PRIMARY` | Body text | ≥ 7:1 |
| `TEXT_SECONDARY` / `TEXT_READONLY` | Labels, metadata, inactive tabs | ≥ 4.5:1 on window, panel, field and control |
| `TEXT_CAPTION` | Captions under controls | ≥ 4.5:1, and quieter than secondary |
| `TEXT_DISABLED` | Disabled controls only | Exempt, but pair with a visible reason |
| `ACCENT` (+ `_HOVER`, `_PRESSED`) | **The system accent** | Only on the primary action, selection, focus and progress. Never decoration. |
| `TEXT_ON_ACCENT` | Text on accent fills | Black or white, whichever contrasts more with the live accent |
| `SUCCESS` / `WARNING` / `ERROR` | Status | Always with an icon or word, never color alone |

Themes: **Dark**, **Light**, **Match System** (default). The WCAG floor is enforced
by a test in every app that consumes the tokens.

**Web:** the accent is CSS `AccentColor` (the OS accent) with the token value as
fallback: `--odcs-accent: AccentColor;` inside `@supports (color: AccentColor)`.

## Scales

- **Spacing:** 4 px grid. Use only **4 · 8 · 12 · 16 · 24 · 32**. Inside a control: 4–8;
  between related controls: 8; between groups: 16; page margins: 16–24.
- **Corner radius:** **4** for controls (buttons, fields, segments), **8** for cards and
  panels, **full** for pills and badges. Nothing else.
- **Control height:** compact desktop controls, **28 px** at 100% scaling (the Mac HIG's
  22–28 pt; touch-sized buttons are an anti-pattern on desktop). Qt scales with the desktop;
  segmented controls and buttons share the height.
- **Type:** the system font at the system size is **body**. The scale (ratio 1.2) is
  *caption* = body − 1 pt (never smaller), *body*, *section title* = body + 1 pt semibold (600),
  *page title* = body × 1.44, weight 700. Maximum four sizes per screen. Use pt, never px,
  so the desktop's font scaling and DPI apply.

## Components

| Component | Behavior |
|---|---|
| **Primary button** | Accent fill. One per screen. Disabled (with a tooltip saying why) when there's nothing to act on. |
| **Secondary button** | Control fill + strong border. Text ends in "…" only when it opens a dialog. |
| **Segmented control** | 2–5 mutually exclusive choices; the selected segment uses the accent fill. Keyboard: arrow keys. |
| **Setting row** | Label on top (or left with a colon in forms), current value as text, and a **Change…** button. Values never pose as buttons. |
| **Collapsible section** | Leading ▸/▾, collapses to a header bar with no empty body. Remembers its state. |
| **Card** | `BG_PANEL`, radius 8, `BORDER`. Groups one topic. |
| **Status headline** | Icon + sentence ("✓ Last backup completed successfully"), then details with times. |
| **Empty state** | Icon + one instruction in `TEXT_SECONDARY`, and it must name the action ("Drop videos here or click Add Videos…"). |
| **Caption** | `TEXT_CAPTION` at caption size, directly under the control it explains. |
| **Destructive confirm** | Names the thing and the consequence; the safe choice is the default button. |

## Component states

Every interactive component defines **normal, hover, pressed, checked/selected, disabled and
keyboard focus**. Geometry is constant across states: same height, padding, radius, and a
border that is always present (transparent when unseen) at a fixed width (1 px; checkbox
1.5 px). Only colors change. Focus is a 2 px accent **outline** outside the control (inset on
list rows), shown for keyboard focus only and never removed. In Qt that means `[focusVisible="true"]` (set by
`FocusVisibleFilter` when focus arrives by Tab or Shift+Tab), never plain `:focus`, which
also fires on a click or when the window is re-activated. Disabled uses TEXT_DISABLED on
BG_CONTROL, ignores hover and press, and states its reason nearby or in a tooltip. See the
"Component states" board.

## Resilience

Design every screen against real content: long names, many selections, unavailable
destinations, 115–130% system text size, and a 960 × 640 window. Values wrap to a second line
rather than truncate essential information; the toolbar drops secondary labels (icon + tooltip)
before the primary action loses its label.

## Layout

- **Menu bar, then toolbar.** The toolbar carries labelled icons for frequent actions, a
  segmented control when the window switches views, and the **primary action at its trailing
  end** (Keep: Back up now; VeloCoder: Convert N Videos).
- **Two panes:** a sidebar on the window color on the left (fixed width), content on the right.
- **Dialogs** put their default button bottom-right (the OS decides the exact order).
- Headline status at the top of the content; details as grouped lists, not cards.
- Minimum window width 960 px at 100%; the settings pane scrolls, never clips.

## App chrome (every desktop app)

- **Menu bar**, in this order: *App-specific menu* (e.g. Backup, Queue) · **Edit** (when there's
  editable content) · **View** (Refresh, panels, **Theme ▸ Dark / Light / Match System**) ·
  **Help** (App Help **F1**, Keyboard Shortcuts, About).
- Every menu item has a mnemonic (`&`), and common actions have a shortcut shown in the menu.
- **About** dialog from `odcs-ui`: app icon, name, version, "© 2026 ODCS App Studio", links
  to System Information and Licenses.
- Each app has its own **icon**, drawn in one shared ODCS style (see Open questions).
- Window title: `App Name` (or `Document — App Name`).

## Writing

- Sentence case everywhere ("Back up now", not "Back Up Now").
- Buttons are verbs; settings labels are nouns.
- Times: the desktop's locale format via one shared helper ("Today at 4:00 AM").
- Errors: what happened, why, what to do next. No stack traces in the main UI (they go
  to the log view).

## Open questions

1. **App icons:** Keep currently uses the generic *drive-harddisk* theme icon (your choice),
   while VeloCoder has a custom icon. A shared ODCS icon style would mean a custom Keep icon.
2. **movieapp's warm amber look:** it moves to the shared tokens and system accent under this
   foundation. Is losing the amber OK for the media tools?
