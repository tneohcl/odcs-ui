"""Icon theme follows the app theme (breeze <-> breeze-dark), and icons
already on screen pick up the change (offscreen, with two fake themes)."""
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from odcs_ui import theming, widgets  # noqa: E402

APP = QApplication.instance() or QApplication([])
SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">'
       '<rect width="16" height="16" fill="{}"/></svg>')


def make_theme(root, name, color):
    theme = root / name
    (theme / "16x16" / "actions").mkdir(parents=True)
    (theme / "index.theme").write_text(
        f"[Icon Theme]\nName={name}\nDirectories=16x16/actions\n\n"
        "[16x16/actions]\nSize=16\nType=Fixed\n")
    (theme / "16x16" / "actions" / "odcs-probe.svg").write_text(SVG.format(color))


class IconThemeTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        make_theme(self.root, "odcstest", "#202020")        # dark glyphs, for light backgrounds
        make_theme(self.root, "odcstest-dark", "#f0f0f0")   # light glyphs, for dark backgrounds
        self.saved = (QIcon.themeSearchPaths(), QIcon.themeName(), theming._SYSTEM_ICON_THEME)
        QIcon.setThemeSearchPaths([str(self.root)] + self.saved[0])

    def tearDown(self):
        QIcon.setThemeSearchPaths(self.saved[0])
        QIcon.setThemeName(self.saved[1])
        theming._SYSTEM_ICON_THEME = self.saved[2]

    def desktop(self, name):
        QIcon.setThemeName(name)
        theming._SYSTEM_ICON_THEME = None     # as at app start: remember the desktop's

    @staticmethod
    def centre(icon):
        return icon.pixmap(16, 16).toImage().pixelColor(8, 8).name()

    def test_light_app_on_a_dark_desktop_uses_the_light_variant(self):
        self.desktop("odcstest-dark")
        self.assertEqual(theming.match_icon_theme("light"), "odcstest")
        self.assertEqual(theming.match_icon_theme("dark"), "odcstest-dark")

    def test_dark_app_on_a_light_desktop_uses_the_dark_variant(self):
        self.desktop("odcstest")
        self.assertEqual(theming.match_icon_theme("dark"), "odcstest-dark")
        self.assertEqual(theming.match_icon_theme("light"), "odcstest")

    def test_theme_without_a_variant_is_left_alone(self):
        make_theme(self.root, "solo", "#808080")
        self.desktop("solo")
        self.assertEqual(theming.match_icon_theme("dark"), "solo")

    def test_icons_already_created_follow_the_switch(self):
        self.desktop("odcstest-dark")
        icon = QIcon.fromTheme("odcs-probe")
        self.assertEqual(self.centre(icon), QColor("#f0f0f0").name())
        theming.match_icon_theme("light")
        self.assertEqual(self.centre(icon), QColor("#202020").name())

    def test_setting_row_redraws_its_icon_when_the_theme_changes(self):
        self.desktop("odcstest-dark")
        controller = theming.ThemeController(APP, [theming.BASE_QSS], choice="dark")
        controller.apply()
        rows = widgets.SettingsList("Plan")
        row = rows.addRow("Folders", "5 folders", icon=QIcon.fromTheme("odcs-probe"))
        rows.show()
        APP.processEvents()

        def shown():
            return row._icon.pixmap().toImage().pixelColor(10, 10).name()
        self.assertEqual(shown(), QColor("#f0f0f0").name())
        controller.set_choice("light")
        APP.processEvents()
        self.assertEqual(shown(), QColor("#202020").name())
        rows.close()


if __name__ == "__main__":
    unittest.main()
