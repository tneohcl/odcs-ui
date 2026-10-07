"""Qt-free: the desktop accent, read where each desktop keeps it.

PySide6's bundled Qt can't load the system's platform-theme plugins (e.g.
LXQt's libqtlxqt.so), so QPalette only ever holds Qt's default blue there."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from odcs_ui import desktop


class Portal(unittest.TestCase):
    def test_reads_the_rgb_triple(self):
        out = "(<(0.20784313725490197, 0.51764705882352946, 0.89411764705882357)>,)\n"
        self.assertEqual(desktop.parse_portal_accent(out), "#3584e4")

    def test_out_of_range_means_unset(self):
        self.assertIsNone(desktop.parse_portal_accent("(<(-1.0, -1.0, -1.0)>,)"))

    def test_garbage_or_error_means_unset(self):
        self.assertIsNone(desktop.parse_portal_accent(""))
        self.assertIsNone(desktop.parse_portal_accent("Error: GDBus.Error:...NotFound"))


class Config(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        (self.home / ".config/lxqt").mkdir(parents=True)

    def env(self, desktop_name):
        return {"XDG_CURRENT_DESKTOP": desktop_name, "HOME": str(self.home)}

    def test_lxqt_palette_highlight(self):
        (self.home / ".config/lxqt/lxqt.conf").write_text(
            "[General]\ntheme=Material-3-Dark\n\n[Palette]\nhighlight_color=#cba6f7\nhighlighted_text_color=#11111b\n")
        self.assertEqual(desktop.config_accent(self.env("LXQt"), self.home), "#cba6f7")

    def test_kde_accent_color(self):
        (self.home / ".config/kdeglobals").write_text(
            "[Colors:Selection]\nBackgroundNormal=61,174,233\n\n[General]\nAccentColor=233,84,32\n")
        self.assertEqual(desktop.config_accent(self.env("KDE"), self.home), "#e95420")

    def test_kde_without_accent_uses_the_selection_colour(self):
        (self.home / ".config/kdeglobals").write_text("[Colors:Selection]\nBackgroundNormal=61,174,233\n")
        self.assertEqual(desktop.config_accent(self.env("KDE"), self.home), "#3daee9")

    def test_xdg_config_home_is_used_first(self):
        other = self.home / "elsewhere"
        (other / "lxqt").mkdir(parents=True)
        (other / "lxqt/lxqt.conf").write_text("[Palette]\nhighlight_color=#a6e3a1\n")
        env = dict(self.env("LXQt"), XDG_CONFIG_HOME=str(other))
        self.assertEqual(desktop.config_accent(env, self.home), "#a6e3a1")

    def test_other_desktops_and_missing_files_give_nothing(self):
        self.assertIsNone(desktop.config_accent(self.env("LXQt"), self.home))
        self.assertIsNone(desktop.config_accent(self.env("GNOME"), self.home))
        self.assertIsNone(desktop.config_accent({}, self.home))

    def test_bad_values_give_nothing(self):
        (self.home / ".config/lxqt/lxqt.conf").write_text("[Palette]\nhighlight_color=mauve\n")
        self.assertIsNone(desktop.config_accent(self.env("LXQt"), self.home))


class Order(unittest.TestCase):
    def test_portal_wins_over_config(self):
        with patch.object(desktop, "portal_accent", return_value="#3584e4"), \
             patch.object(desktop, "config_accent", return_value="#cba6f7"):
            self.assertEqual(desktop.accent(), "#3584e4")

    def test_config_when_the_portal_has_none(self):
        with patch.object(desktop, "portal_accent", return_value=None), \
             patch.object(desktop, "config_accent", return_value="#cba6f7"):
            self.assertEqual(desktop.accent(), "#cba6f7")


if __name__ == "__main__":
    unittest.main()
