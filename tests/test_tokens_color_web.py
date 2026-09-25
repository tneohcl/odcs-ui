"""Qt-free checks: token contract, WCAG floors, color math, web CSS."""
import re
import unittest

from odcs_ui import color, tokens, web


class TokenContract(unittest.TestCase):
    def test_both_themes_define_the_same_roles(self):
        self.assertEqual(set(tokens.DARK), set(tokens.LIGHT))

    def test_readable_text_meets_wcag_aa_on_every_text_surface(self):
        for name, theme in tokens.THEMES.items():
            for fg in tokens.READABLE_TEXT:
                for bg in tokens.TEXT_SURFACES:
                    with self.subTest(theme=name, fg=fg, bg=bg):
                        self.assertGreaterEqual(color.contrast(theme[fg], theme[bg]), tokens.MIN_TEXT_CONTRAST)

    def test_secondary_text_is_readable_on_controls_too(self):
        for name, theme in tokens.THEMES.items():
            with self.subTest(theme=name):
                self.assertGreaterEqual(color.contrast(theme["TEXT_SECONDARY"], theme["BG_CONTROL"]), 4.5)

    def test_caption_stays_quieter_than_secondary(self):
        for name, theme in tokens.THEMES.items():
            with self.subTest(theme=name):
                self.assertLess(color.contrast(theme["TEXT_CAPTION"], theme["BG_WINDOW"]),
                                color.contrast(theme["TEXT_SECONDARY"], theme["BG_WINDOW"]))

    def test_fallback_accent_pairs_with_readable_on_accent_text(self):
        for name, theme in tokens.THEMES.items():
            with self.subTest(theme=name):
                self.assertGreaterEqual(color.contrast(theme["ACCENT"], color.on_accent(theme["ACCENT"])), 4.5)

    def test_scale_follows_design(self):
        self.assertEqual(tokens.SCALE["space"], [4, 8, 12, 16, 24, 32])
        self.assertEqual(tokens.SCALE["controlHeight"], 28)
        self.assertEqual(tokens.SCALE["radius"]["control"], 4)
        self.assertEqual(tokens.SCALE["radius"]["card"], 8)

    def test_theme_returns_a_copy(self):
        copy = tokens.theme("dark")
        copy["BG_PANEL"] = "#000000"
        self.assertNotEqual(tokens.DARK["BG_PANEL"], "#000000")
        self.assertEqual(tokens.theme("nonsense"), tokens.DARK)


class ColorMath(unittest.TestCase):
    def test_contrast_extremes_and_symmetry(self):
        self.assertAlmostEqual(color.contrast("#000000", "#ffffff"), 21.0, places=2)
        self.assertAlmostEqual(color.contrast("#777777", "#777777"), 1.0)
        self.assertAlmostEqual(color.contrast("#1c72c4", "#ffffff"), color.contrast("#ffffff", "#1c72c4"))

    def test_on_accent_picks_the_higher_contrast_partner(self):
        self.assertEqual(color.on_accent("#3daee9"), color.DARK_ON_ACCENT)   # KDE Breeze: light blue
        self.assertEqual(color.on_accent("#0067c0"), color.LIGHT_ON_ACCENT)  # Windows 11: deep blue
        self.assertEqual(color.on_accent("#ffd400"), color.DARK_ON_ACCENT)
        self.assertEqual(color.on_accent("#8e44ad"), color.LIGHT_ON_ACCENT)

    def test_composite_translucent_over_background(self):
        self.assertEqual(color.composite("#00000080", "#ffffff"), "#7f7f7f")
        self.assertEqual(color.composite("#123456ff", "#ffffff"), "#123456")

    def test_readable_falls_back_below_the_floor(self):
        self.assertEqual(color.readable("#8c8e91", "#ffffff", "#565d6b"), "#565d6b")  # the old 3.3:1 hint
        self.assertEqual(color.readable("#1a1d23", "#ffffff", "#565d6b"), "#1a1d23")
        self.assertEqual(color.readable("#14141480", "#171a1f", "#9098a6"), "#9098a6")  # translucent, dark bg

    def test_shade_moves_toward_white_or_black(self):
        self.assertGreater(color.luminance(color.shade("#3daee9", 0.2)), color.luminance("#3daee9"))
        self.assertLess(color.luminance(color.shade("#3daee9", -0.2)), color.luminance("#3daee9"))

    def test_parse_rejects_garbage(self):
        with self.assertRaises(ValueError):
            color.parse("blue")


class WebCss(unittest.TestCase):
    def test_every_token_becomes_a_css_variable_in_both_themes(self):
        out = web.css()
        for name in tokens.LIGHT:
            var = "--odcs-" + name.lower().replace("_", "-")
            self.assertGreaterEqual(out.count(var + ":"), 3, var)  # light, dark (media), dark (data-theme)

    def test_accent_follows_the_os_where_supported(self):
        out = web.css()
        self.assertIn("@supports (color: AccentColor)", out)
        self.assertIn("--odcs-accent: AccentColor", out)
        self.assertIn("AccentColorText", out)

    def test_committed_css_matches_the_tokens(self):
        from pathlib import Path
        committed = Path(__file__).resolve().parent.parent / "web" / "odcs.css"
        self.assertEqual(committed.read_text(encoding="utf-8"), web.css(),
                         "web/odcs.css is stale: run python -m odcs_ui.web > web/odcs.css")

    def test_braces_balance_and_no_python_leftovers(self):
        out = web.css()
        self.assertEqual(out.count("{"), out.count("}"))
        self.assertIsNone(re.search(r"\$[A-Z_]+|None|\{\s*\}", out))


if __name__ == "__main__":
    unittest.main()
