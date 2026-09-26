"""Widget behaviour and the constant-geometry rule (offscreen)."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QFont  # noqa: E402
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


    def test_fill_takes_the_width_and_splits_it_evenly(self):
        # A sidebar switch lines up with the cards under it: the frame spans
        # the width, and the segments are equal whatever their labels.
        from PySide6.QtWidgets import QVBoxLayout, QWidget
        panel = QWidget()
        panel.setFixedWidth(300)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        switch = widgets.ViewSwitch(["Status", "Restore"], fill=True)
        layout.addWidget(switch)
        panel.show()
        APP.processEvents()
        first, second = (b.geometry() for b in switch.buttons())
        self.assertEqual(switch.geometry().width(), 300 - 32)          # the full width
        self.assertLessEqual(abs(first.width() - second.width()), 1)   # equal, not sized by label
        # It asks for room for its widest label, so a layout won't squeeze it.
        widest = max(b.sizeHint().width() for b in switch.buttons())
        self.assertGreaterEqual(switch.minimumSizeHint().width(), 2 * widest)
        gaps = {"left": first.left(), "right": switch.rect().right() - second.right(),
                "top": first.top(), "bottom": switch.rect().bottom() - first.bottom()}
        self.assertEqual(len(set(gaps.values())), 1, gaps)   # still an even inset
        panel.close()

    def test_inset_is_even_in_a_taller_row(self):
        # The frame must hug its segments: stretched to a taller row (a toolbar
        # with 36 px buttons), the gap above and below grew while the sides
        # stayed at 2 px.
        from PySide6.QtWidgets import QHBoxLayout, QWidget
        row = QWidget()
        layout = QHBoxLayout(row)
        switch = widgets.ViewSwitch(["Status", "Restore"])
        tall = QPushButton("Back up now")
        tall.setMinimumHeight(40)
        layout.addWidget(switch)
        layout.addWidget(tall)
        row.resize(420, 60)
        row.show()
        APP.processEvents()
        frame, first, last = switch.rect(), switch.buttons()[0].geometry(), switch.buttons()[-1].geometry()
        gaps = {"left": first.left(), "right": frame.right() - last.right(),
                "top": first.top(), "bottom": frame.bottom() - first.bottom()}
        self.assertEqual(len(set(gaps.values())), 1, gaps)
        row.close()


def _lines_fit(label, width):
    """Lay the label's text out as QLabel's word wrap does; True if no line is
    wider than `width` (a long unbreakable word would overflow and clip)."""
    from PySide6.QtGui import QTextLayout, QTextOption
    layout = QTextLayout(label.text(), label.font())
    option = QTextOption()
    option.setWrapMode(QTextOption.WordWrap)
    layout.setTextOption(option)
    layout.beginLayout()
    widest = 0.0
    while (line := layout.createLine()).isValid():
        line.setLineWidth(width)
        widest = max(widest, line.naturalTextWidth())
    layout.endLayout()
    return widest <= width


class LargeTextRowTests(unittest.TestCase):
    """Whatever the font size, a row fits the width it is given: long values
    and labels wrap, even with no spaces, instead of widening the row.
    Regression: at 14 pt (Windows) one hyphenated host name made a sidebar
    card 71 px wider than its column."""

    LONG = ("NAS share · Synology-DS920plus-Living-Room · /volume1/backups/"
            "TITAN-i_home_terence_keep_repository_2026")

    def run_at(self, points):
        from PySide6.QtWidgets import QVBoxLayout, QWidget
        font = APP.font()
        self.addCleanup(APP.setFont, QFont(font))
        if points:
            font.setPointSize(points)
            APP.setFont(font)
        page = QWidget()
        self.addCleanup(page.close)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)  # Keep's 300 px sidebar
        box = self.box = widgets.SettingsList("What's backed up")
        short = box.addRow("Folders", "5 folders")
        long = box.addRow("Recovery access for this computer", self.LONG)
        empty = box.addRow("Schedule", "")
        layout.addWidget(box)
        page.resize(300, 900)
        page.show()
        APP.processEvents()
        return short, long, empty

    def test_rows_fit_a_narrow_column_at_any_size(self):
        for points in (0, 14, 22):
            with self.subTest(points=points):
                short, long, empty = self.run_at(points)
                self.assertLessEqual(long.minimumSizeHint().width(), short.minimumSizeHint().width())
                self.assertLessEqual(long.width(), 300 - 2 * 16)
                for label in (long._label, long._value):
                    self.assertTrue(_lines_fit(label, label.width()), label.text())
                self.assertGreaterEqual(long.height(), long.heightForWidth(long.width()))
                # and asks no more height than its rows need at that width
                # (QLabel's squarish wrap guess made it hundreds of px taller)
                self.assertLessEqual(self.box.minimumSizeHint().height(), self.box.heightForWidth(self.box.width()))

    def test_ordinary_words_never_break(self):
        for text in ("All application data", "Tested · not yet verified", "Internationalization"):
            with self.subTest(text=text):
                shown = widgets._wrappable(text)
                self.assertEqual([word.strip("\u200b") for word in shown.split()], text.split())
                self.assertNotIn("\u200b", "".join(shown.split("·\u200b")))
        # An ID with no breaks splits every 20 characters, never at its end.
        self.assertEqual(widgets._wrappable("a" * 40), "a" * 20 + "\u200b" + "a" * 20)
        self.assertEqual(widgets._wrappable("a" * 41).count("\u200b"), 2)

    def test_text_reads_back_unchanged(self):
        short, long, empty = self.run_at(0)
        self.assertEqual(long.value(), self.LONG)
        self.assertEqual(long.accessibleName(), f"Recovery access for this computer: {self.LONG}. Change")
        self.assertNotIn("​", long.accessibleName())
        self.assertEqual(empty.value(), "")

    def test_an_empty_value_keeps_the_row_height(self):
        # Constant geometry: a row whose value has not loaded yet is as tall
        # as it will be once it has, instead of collapsing to the label.
        for points in (0, 14):
            with self.subTest(points=points):
                short, long, empty = self.run_at(points)
                self.assertEqual(empty.height(), short.height())


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

    def test_a_wrapped_value_gets_its_full_height_in_a_list(self):
        # Regression: a Fixed row in a Maximum box was capped at its one-line
        # size hint, so the second line of a wrapped value was clipped.
        from PySide6.QtWidgets import QVBoxLayout, QWidget
        page = QWidget()
        layout = QVBoxLayout(page)
        box = widgets.SettingsList("Recovery")
        row = box.addRow("Recovery access", "Tested")
        layout.addWidget(box)
        layout.addStretch(1)
        page.resize(260, 600)
        page.show()
        APP.processEvents()
        row.setValue("Tested · not yet verified · Synology-DS920plus-Living-Room")  # wraps after it is shown
        APP.processEvents()
        self.assertGreater(row.heightForWidth(row.width()), row.sizeHint().height())  # really wraps
        self.assertGreaterEqual(row.height(), row.heightForWidth(row.width()))
        self.assertGreaterEqual(row._value.height(), row._value.heightForWidth(row._value.width()))
        page.close()

    def test_rows_are_never_squeezed_below_their_size(self):
        # Regression: the row's QSS `min-height: 0` made its minimum 2 px, so a
        # short window squashed every row instead of honouring the list's size.
        box = widgets.SettingsList("What's backed up")
        rows = [box.addRow(label, "value") for label in ("Folders", "Applications", "Destination")]
        box.show()
        APP.processEvents()
        needed = sum(row.sizeHint().height() for row in rows)
        self.assertGreaterEqual(box.minimumSizeHint().height(), needed)
        box.close()

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

    def test_two_lines_label_above_value(self):
        box = widgets.SettingsList()
        row = box.addRow("Destination", "TITAN-i")
        box.resize(280, 200)
        box.show()
        APP.processEvents()
        self.assertGreater(row._value.geometry().top(), row._label.geometry().top())
        self.assertEqual(row._value.geometry().left(), row._label.geometry().left())
        box.close()

    def test_indicator_dot_is_optional_and_never_alone(self):
        row = widgets.SettingRow("Destination", "TITAN-i")
        self.assertIsNone(row.indicator())
        row.setValue("TITAN-i · Connected", indicator="ok")
        self.assertEqual(row.indicator(), "ok")
        self.assertIn("Connected", row.accessibleName())  # the words carry it
        row.setValue("TITAN-i · Not connected", "error", indicator="error")
        self.assertEqual(row.indicator(), "error")
        row.setValue("TITAN-i")
        self.assertIsNone(row.indicator())

    def test_leading_icon_column_keeps_rows_aligned(self):
        from PySide6.QtGui import QIcon
        box = widgets.SettingsList()
        with_icon = box.addRow("Folders", "5 folders", icon=QIcon())  # null: column kept, empty
        without = widgets.SettingRow("Plain", "row")
        self.assertFalse(with_icon._icon.isHidden())
        self.assertTrue(without._icon.isHidden())

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

    def test_action_sits_under_its_description_aligned_with_it(self):
        facts = widgets.StatusFacts()
        facts.addFact("backup", "Backup completed", "Your selected files were saved")
        facts.addFact("recovery", "Recovery tested", "Restore one file using only your passphrase",
                      action=("Test recovery…", lambda: None))
        facts.resize(700, 200)
        facts.show()
        APP.processEvents()
        fact = facts.facts["recovery"]
        description, button, when = fact["description"], fact["action"], fact["when"]

        def box(widget):
            top_left = widget.mapTo(facts, widget.rect().topLeft())
            return top_left.x(), top_left.y(), widget.height()
        dx, dy, dh = box(description)
        bx, by, _ = box(button)
        self.assertEqual(bx, dx)                   # same left edge as the description
        self.assertGreaterEqual(by, dy + dh)       # on its own line below it
        self.assertEqual(box(when)[1], dy)         # the date stays level with the first line
        self.assertEqual(box(facts.facts["backup"]["when"])[0], box(when)[0])   # one date column
        for key in ("backup", "recovery"):         # descriptions use the column, never clipped
            label = facts.facts[key]["description"]
            self.assertGreater(label.width(), button.width() * 2, key)
            self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()), key)
        facts.close()

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
