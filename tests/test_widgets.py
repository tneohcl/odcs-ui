"""Widget behaviour and the constant-geometry rule (offscreen)."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QLabel, QPushButton  # noqa: E402

from odcs_ui import theming, widgets  # noqa: E402

APP = QApplication.instance() or QApplication([])
CONTROLLER = theming.ThemeController(APP, [theming.BASE_QSS], choice="light")
CONTROLLER.apply()


class ViewSwitchTests(unittest.TestCase):
    def test_selection_signal_and_arrow_keys(self):
        switch = widgets.ViewSwitch(["Status", "Restore", "Settings"])
        seen = []
        switch.currentChanged.connect(seen.append)
        self.assertEqual(switch.currentIndex(), 0)
        switch.setCurrentIndex(1)
        QTest.keyClick(switch, Qt.Key_Right)
        self.assertEqual(switch.currentIndex(), 2)
        QTest.keyClick(switch, Qt.Key_Right)  # wraps
        self.assertEqual(switch.currentIndex(), 0)
        self.assertEqual(seen, [1, 2, 0])

    def test_selected_segment_keeps_its_size(self):
        # DESIGN.md: states change colours only. A bold selected segment would
        # widen its text and shift its neighbours (the jitter this rule exists for).
        switch = widgets.ViewSwitch(["Status", "Restore"])
        switch.show()
        APP.processEvents()
        restore = switch.buttons()[1]
        before = (restore.sizeHint(), restore.font().weight())
        switch.setCurrentIndex(1)
        APP.processEvents()
        self.assertEqual((restore.sizeHint(), restore.font().weight()), before)
        switch.close()


class SettingsTests(unittest.TestCase):
    def test_row_is_a_real_button_with_an_accessible_name(self):
        box = widgets.SettingsList("What's backed up")
        clicked = []
        row = box.addRow("Destination", "TITAN-i", lambda: clicked.append(True))
        self.assertIsInstance(row, QPushButton)
        self.assertEqual(row.accessibleName(), "Destination: TITAN-i. Change")
        QTest.mouseClick(row, Qt.LeftButton)
        row.setFocus()
        QTest.keyClick(row, Qt.Key_Space)
        self.assertEqual(clicked, [True, True])

    def test_long_values_wrap_instead_of_truncating(self):
        row = widgets.SettingRow("Destination", "Offline — Synology-DS920plus-Living-Room-Backups/home/backups/TITAN-i")
        self.assertTrue(row.hasHeightForWidth())
        self.assertGreater(row.heightForWidth(240), row.heightForWidth(1200))

    def test_row_label_uses_primary_text_colour(self):
        # Regression: a `:disabled` pseudo-state on an ancestor in a Qt selector
        # is invalid and greyed every row label. Labels must render TEXT_PRIMARY.
        from PySide6.QtGui import QPalette
        box = widgets.SettingsList()
        row = box.addRow("Folders", "5 folders")
        box.show()
        APP.processEvents()
        self.assertEqual(row._label.palette().color(QPalette.WindowText).name(), CONTROLLER.values["TEXT_PRIMARY"])
        self.assertEqual(row._value.palette().color(QPalette.WindowText).name(), CONTROLLER.values["TEXT_SECONDARY"])
        box.close()

    def test_only_the_last_row_drops_its_separator(self):
        box = widgets.SettingsList()
        first = box.addRow("Folders", "5 folders")
        second = box.addRow("Schedule", "Daily")
        self.assertEqual((first.property("last"), second.property("last")), ("false", "true"))

    def test_value_state_colours_but_words_carry_meaning(self):
        row = widgets.SettingRow("Destination", "TITAN-i")
        row.setValue("Offline", "error")
        self.assertEqual(row.value(), "Offline")
        self.assertEqual(row._value.property("role"), "error")
        self.assertIn("Offline", row.accessibleName())


class StatusFactsTests(unittest.TestCase):
    def test_never_is_shown_as_never_and_facts_are_separate(self):
        facts = widgets.StatusFacts("Can you get your files back?")
        facts.addFact("backup", "Backup completed", state="ok", when="Today at 8:51 AM")
        facts.addFact("recovery", "Recovery tested", action=("Test recovery…", lambda: None))
        self.assertEqual(facts.whenText("recovery"), widgets.StatusFacts.NEVER)
        self.assertEqual(facts.facts["recovery"]["icon"].state(), "never")
        facts.setFact("recovery", "ok", "Today at 9:02 AM")
        self.assertEqual(facts.whenText("recovery"), "Today at 9:02 AM")
        self.assertEqual(facts.whenText("backup"), "Today at 8:51 AM")
        self.assertIsNotNone(facts.facts["recovery"]["action"])

    def test_only_the_last_fact_drops_its_separator(self):
        facts = widgets.StatusFacts()
        facts.addFact("backup", "Backup completed")
        facts.addFact("recovery", "Recovery tested", action=("Test recovery…", lambda: None))
        first, last = facts._rows
        self.assertEqual({c.property("last") for c in first}, {"false"})
        self.assertEqual({c.property("last") for c in last}, {"true"})

    def test_status_icons_paint_in_every_state(self):
        for state in ("ok", "warning", "error", "never", "info"):
            with self.subTest(state=state):
                icon = widgets.StatusIcon(state, 24)
                self.assertFalse(icon.grab().isNull())


class SectionEmptyAboutTests(unittest.TestCase):
    def test_collapsible_section_hides_content_and_uses_a_leading_triangle(self):
        section = widgets.CollapsibleSection("Expert", QLabel("content"))
        self.assertTrue(section.content.isHidden())
        self.assertTrue(section.header.text().startswith("▸"))
        seen = []
        section.expandedChanged.connect(seen.append)
        section.setExpanded(True)
        self.assertFalse(section.content.isHidden())
        self.assertTrue(section.header.text().startswith("▾"))
        self.assertEqual(seen, [True])

    def test_empty_state_names_the_action_in_secondary_text(self):
        empty = widgets.EmptyState("Drop videos here or choose Add Videos…")
        self.assertIn("Add Videos", empty.message.text())
        self.assertEqual(empty.message.property("role"), "secondary")

    def test_about_dialog_carries_the_studio_name_and_close_is_default(self):
        opened = []
        dialog = widgets.AboutDialog("Keep", "0.9.2", "Back up and recover your files.",
                                     extra_buttons=[("Licenses", lambda: opened.append(True))])
        self.assertEqual(dialog.windowTitle(), "About Keep")
        self.assertIn("ODCS App Studio", dialog.copyright.text())
        self.assertIn("2026", dialog.copyright.text())
        defaults = [b for b in dialog.findChildren(QPushButton) if b.isDefault()]
        self.assertEqual(len(defaults), 1)
        licenses = next(b for b in dialog.findChildren(QPushButton) if b.text() == "Licenses")
        licenses.click()
        self.assertEqual(opened, [True])


class GalleryTests(unittest.TestCase):
    def test_demo_gallery_builds_under_both_themes(self):
        from odcs_ui import demo
        for choice in ("dark", "light"):
            with self.subTest(theme=choice):
                CONTROLLER.set_choice(choice)
                window = demo.build()
                window.show()
                APP.processEvents()
                self.assertFalse(window.grab().isNull())
                window.close()
        CONTROLLER.set_choice("light")


if __name__ == "__main__":
    unittest.main()
