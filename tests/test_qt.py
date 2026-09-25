"""Qt checks (offscreen): theme resolution, accent tokens, QSS rendering, times."""
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QLocale, Qt  # noqa: E402
from PySide6.QtGui import QColor, QPalette  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from odcs_ui import color, theming, timefmt, tokens  # noqa: E402

APP = QApplication.instance() or QApplication([])


def palette_with_accent(accent: str) -> QPalette:
    palette = QPalette(APP.palette())
    palette.setColor(getattr(QPalette, "Accent", QPalette.Highlight), QColor(accent))
    return palette


class Resolve(unittest.TestCase):
    def test_forced_choices_pass_through(self):
        self.assertEqual(theming.resolve_theme("dark", APP), "dark")
        self.assertEqual(theming.resolve_theme("light", APP), "light")

    def test_system_resolves_to_a_real_theme(self):
        self.assertIn(theming.resolve_theme("system", APP), ("dark", "light"))


class AccentTokens(unittest.TestCase):
    def test_system_accent_drives_accent_family_and_on_accent(self):
        for accent, expected_on in (("#3daee9", color.DARK_ON_ACCENT), ("#0067c0", color.LIGHT_ON_ACCENT)):
            with self.subTest(accent=accent):
                values = theming.accent_tokens(palette_with_accent(accent), "#123456")
                self.assertEqual(values["ACCENT"], accent)
                self.assertEqual(values["TEXT_ON_ACCENT"], expected_on)
                self.assertGreater(color.luminance(values["ACCENT_HOVER"]), color.luminance(accent))
                self.assertLess(color.luminance(values["ACCENT_PRESSED"]), color.luminance(accent))

    def test_black_accent_means_unresolved_and_uses_fallback(self):
        values = theming.accent_tokens(palette_with_accent("#000000"), "#1c72c4")
        self.assertEqual(values["ACCENT"], "#1c72c4")

    def test_build_tokens_merges_theme_accent_and_extras(self):
        values = theming.build_tokens("light", palette_with_accent("#0067c0"), {"CHECK_PATH": "/x.svg"})
        self.assertEqual(values["BG_PANEL"], tokens.LIGHT["BG_PANEL"])
        self.assertEqual(values["ACCENT"], "#0067c0")
        self.assertEqual(values["ON_ACCENT_IS_DARK"], "false")
        self.assertEqual(values["CHECK_PATH"], "/x.svg")


class Render(unittest.TestCase):
    def test_base_qss_renders_completely_for_both_themes(self):
        text = theming.BASE_QSS.read_text(encoding="utf-8")
        for name in ("dark", "light"):
            with self.subTest(theme=name):
                out = theming.render(text, theming.build_tokens(name, APP.palette()))
                self.assertNotIn("$", out)

    def test_longer_tokens_are_not_clobbered_by_their_prefixes(self):
        out = theming.render("a: $BG_CONTROL; b: $BG_CONTROL_HOVER;", {"BG_CONTROL": "#111111", "BG_CONTROL_HOVER": "#222222"})
        self.assertEqual(out, "a: #111111; b: #222222;")

    def test_unknown_token_is_an_error_not_silent(self):
        with self.assertRaises(KeyError):
            theming.render("color: $BG_PANLE;", {"BG_PANEL": "#ffffff"})


class Controller(unittest.TestCase):
    def test_choice_switches_the_applied_stylesheet_and_reports_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_qss = Path(tmp, "app.qss")
            app_qss.write_text("QLabel#probe { color: $TEXT_PRIMARY; }", encoding="utf-8")
            seen = []
            controller = theming.ThemeController(APP, [theming.BASE_QSS, app_qss], choice="dark")
            controller.changed.connect(lambda name, values: seen.append(name))
            controller.apply()
            self.assertIn(tokens.DARK["TEXT_PRIMARY"], APP.styleSheet())
            controller.set_choice("light")
            self.assertIn(tokens.LIGHT["TEXT_PRIMARY"], APP.styleSheet())
            controller.set_choice("bogus")
            self.assertEqual(controller.choice, "system")
            self.assertEqual(seen[:2], ["dark", "light"])
            APP.setStyleSheet("")

    def test_theme_choices_are_the_shared_vocabulary(self):
        self.assertEqual(theming.THEME_CHOICES, [("dark", "Dark"), ("light", "Light"), ("system", "Match System")])


class FocusVisible(unittest.TestCase):
    """Keyboard-only focus ring: Tab shows it, a click or re-activation doesn't."""

    def _focus(self, widget, reason):
        from PySide6.QtGui import QFocusEvent
        QApplication.sendEvent(widget, QFocusEvent(QEvent.Type.FocusIn, reason))

    def test_tab_shows_the_ring_and_a_click_does_not(self):
        from PySide6.QtWidgets import QPushButton
        theming.install_focus_visible(APP)
        button = QPushButton("Back up now")
        self._focus(button, Qt.FocusReason.TabFocusReason)
        self.assertTrue(button.property("focusVisible"))
        QApplication.sendEvent(button, QFocusEvent_out())
        self.assertFalse(button.property("focusVisible"))
        self._focus(button, Qt.FocusReason.MouseFocusReason)
        self.assertFalse(button.property("focusVisible"))
        self._focus(button, Qt.FocusReason.ActiveWindowFocusReason)
        self.assertFalse(button.property("focusVisible"))

    def test_installed_once_by_the_controller(self):
        self.assertIs(theming.install_focus_visible(APP), theming.install_focus_visible(APP))

    def test_base_qss_never_uses_plain_focus(self):
        qss = theming.BASE_QSS.read_text(encoding="utf-8").replace("::item:focus", "")
        self.assertNotRegex(qss, r":focus\b")
        self.assertIn('[focusVisible="true"]', qss)


def QFocusEvent_out():
    from PySide6.QtGui import QFocusEvent
    return QFocusEvent(QEvent.Type.FocusOut, Qt.FocusReason.OtherFocusReason)


class Times(unittest.TestCase):
    NOW = datetime(2026, 9, 25, 12, 0)

    def test_clock_follows_locale(self):
        self.assertIn("AM", timefmt.friendly_clock(4, 0, QLocale("en_US")))
        self.assertEqual(timefmt.friendly_clock(4, 0, QLocale("de_DE")), "04:00")

    def test_relative_days(self):
        us = QLocale("en_US")
        self.assertTrue(timefmt.friendly_datetime(datetime(2026, 9, 25, 8, 51), self.NOW, us).startswith("Today at 8:51"))
        self.assertTrue(timefmt.friendly_datetime(datetime(2026, 9, 24, 4, 12), self.NOW, us).startswith("Yesterday at 4:12"))
        self.assertTrue(timefmt.friendly_datetime(datetime(2026, 9, 26, 4, 0), self.NOW, us).startswith("Tomorrow at 4:00"))
        self.assertTrue(timefmt.friendly_datetime(datetime(2026, 9, 1, 6, 25), self.NOW, us).startswith("Sep 1 at 6:25"))
        self.assertIn("2024", timefmt.friendly_datetime(datetime(2024, 3, 2, 14, 30), self.NOW, us))


if __name__ == "__main__":
    unittest.main()
