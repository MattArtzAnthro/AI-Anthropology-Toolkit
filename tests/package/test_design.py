"""The design system as code: tokens, theme CSS, the stylesheet, and the A2UI mapping."""

import json
import re
import unittest
from importlib import resources
from pathlib import Path

from ai_anthro_toolkit import design

TOKENS = json.loads(resources.files("ai_anthro_toolkit.design").joinpath("tokens.json").read_text(encoding="utf-8"))
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
BUNDLE_JS = Path(__file__).resolve().parents[2] / "src/ai_anthro_toolkit/desk/app/dist/desk-app.js"

# What a themed value may contain: token variables, color-mix over them,
# transparent, numbers and lengths. Any colour of its own (a hex, rgb(),
# or a named colour such as black) is outside this grammar.
VALUE_WORD = re.compile(
    r"var\(--[a-z0-9-]+\)|color-mix\(|in|srgb|transparent|[\d.]+(px|rem|em|%)?|[(),]"
)

# One line of generated CSS: a :root rule or the dark media query opening a block,
# a declaration, or a close.
CSS_LINE = re.compile(
    r"\s*(?::root\S* \{|@media \(prefers-color-scheme: dark\) \{|(?:--[a-z0-9-]+|color-scheme)\s*:\s*[^{};]+;|\})"
)


def _colour_tokens() -> dict[str, dict[str, str]]:
    """Colour tokens as name -> {light, dark}. An alias is one string for both themes."""
    out = {}
    for t in TOKENS["color"]["tokens"]:
        v = t["value"]
        out[t["name"]] = {"light": v, "dark": v} if isinstance(v, str) else v
    return out


def _declarations(block: str) -> dict[str, str]:
    """Custom-property declarations in a CSS block, name -> value."""
    return dict(re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", block))


def _resolve(name: str, declarations: dict[str, str], depth: int = 0) -> str:
    """Follow var() references to a final value, as a browser would."""
    value = declarations[name]
    m = re.fullmatch(r"var\((--[a-z0-9-]+)\)", value)
    if m is None:
        return value
    if depth > 10:
        raise AssertionError(f"{name} refers in a loop")
    return _resolve(m.group(1), declarations, depth + 1)


def _css_problems(css: str) -> list[str]:
    """Lines that are not a selector, a declaration or a close, and unbalanced braces."""
    problems, depth = [], 0
    for line in css.splitlines():
        if not line.strip():
            continue
        if not CSS_LINE.fullmatch(line):
            problems.append(f"malformed: {line!r}")
        depth += line.count("{") - line.count("}")
        if depth < 0:
            problems.append(f"closes a block that is not open: {line!r}")
    if depth:
        problems.append(f"{depth} block(s) left open")
    return problems


def _block(css: str, selector: str) -> str:
    """The body of the first rule whose selector is exactly ``selector``."""
    m = re.search(re.escape(selector) + r"\s*{([^{}]*)}", css)
    if m is None:
        raise AssertionError(f"no rule for {selector!r} in:\n{css}")
    return m.group(1)


class TestTokens(unittest.TestCase):
    def test_tokens_returns_the_shipped_file(self):
        self.assertEqual(design.tokens(), TOKENS)

    def test_tokens_returns_a_fresh_copy(self):
        design.tokens()["color"]["tokens"].clear()
        self.assertTrue(design.tokens()["color"]["tokens"])


class TestTokensCss(unittest.TestCase):
    def setUp(self):
        self.css = design.tokens_css()

    def test_light_values_sit_on_root(self):
        light = _declarations(_block(self.css, ":root"))
        for name, value in _colour_tokens().items():
            target = value["light"]
            if target.startswith("{"):  # an alias resolves to its target's value
                target = _colour_tokens()[target.strip("{}")]["light"]
            self.assertEqual(_resolve(f"--{name}", light), target, name)

    def test_every_var_in_the_theme_names_a_defined_variable(self):
        defined = set(_declarations(_block(self.css, ":root")))
        used = set(re.findall(r"var\((--[a-z0-9-]+)", self.css))
        self.assertEqual(used - defined, set())

    def test_malformed_css_is_reported(self):
        self.assertEqual(_css_problems(":root {\n  --a: 1px;\n}\n"), [])
        self.assertTrue(_css_problems("XX:root {\n  XX--a: 1px;XX\n}\n"))
        self.assertTrue(_css_problems(":root {\n  --a: 1px;\n"))

    def test_the_theme_css_is_well_formed(self):
        self.assertEqual(_css_problems(self.css), [])

    def test_only_a_braced_name_is_an_alias(self):
        self.assertEqual(design._value("{action}"), "var(--action)")
        for literal in ("#1f4f8f", "{action", "action}", "16px"):
            self.assertEqual(design._value(literal), literal, literal)

    def test_dark_values_under_the_guarded_query_and_the_attribute(self):
        media = re.search(r"@media \(prefers-color-scheme: dark\)\s*{(.*?)}\s*}", self.css, re.S)
        self.assertIsNotNone(media, "no dark media query")
        assert media is not None
        guarded = _declarations(_block(media.group(1) + "}", ':root:not([data-theme="light"])'))
        forced = _declarations(_block(self.css, ':root[data-theme="dark"]'))
        for name, value in _colour_tokens().items():
            if value["dark"].startswith("{"):
                # An alias follows its target, so the dark blocks never restate it.
                self.assertNotIn(f"--{name}", guarded, name)
                continue
            self.assertEqual(guarded.get(f"--{name}"), value["dark"], name)
            self.assertEqual(forced.get(f"--{name}"), value["dark"], name)

    def test_color_scheme_follows_the_theme(self):
        self.assertIn("  color-scheme: light;\n", _block(self.css, ":root"))
        self.assertIn("  color-scheme: dark;\n", _block(self.css, ':root[data-theme="dark"]'))

    def test_fonts_spacing_radius_and_sizes_are_variables(self):
        root = _declarations(_block(self.css, ":root"))
        for family, stack in TOKENS["type"]["families"].items():
            self.assertEqual(root[f"--font-{family}"], stack)
        for group in ("spacing", "radius", "size"):
            for tok in TOKENS[group]["tokens"]:
                self.assertEqual(root[f"--{tok['name']}"], tok["value"], tok["name"])

    def test_every_variable_the_stylesheet_reads_is_defined(self):
        defined = set(_declarations(_block(self.css, ":root")))
        used = set(re.findall(r"var\((--[a-z0-9-]+)", design.stylesheet(fonts=True)))
        self.assertEqual(used - defined, set())


class TestStylesheet(unittest.TestCase):
    def test_with_fonts_keeps_the_import(self):
        css = design.stylesheet(fonts=True)
        self.assertTrue(css.startswith(f'@import url("{design.FONTS_URL}");'))

    def test_without_fonts_drops_only_the_import(self):
        with_fonts = design.stylesheet(fonts=True)
        without = design.stylesheet(fonts=False)
        self.assertNotIn("@import", without)
        self.assertNotIn("fonts.googleapis.com", without)
        self.assertEqual(without.strip(), with_fonts.split("\n", 1)[1].strip())

    def test_r8_6_every_literal_colour_in_the_stylesheet_is_a_token(self):
        """R8.6: a colour written into bundle.css (a shadow's rgb with alpha)
        is a token colour, so it changes when the token does."""
        palette = {
            v.lower() for pair in _colour_tokens().values() for v in pair.values() if v.startswith("#")
        }
        css = design.stylesheet(fonts=False)
        for h in HEX.findall(css):
            self.assertIn(h.lower(), palette, h)
        for r, g, b in re.findall(r"rgba?\(\s*(\d+)[ ,]+(\d+)[ ,]+(\d+)", css):
            self.assertIn(f"#{int(r):02x}{int(g):02x}{int(b):02x}", palette, f"rgb({r} {g} {b})")

    def test_a_stylesheet_without_the_fonts_line_is_refused(self):
        with self.assertRaisesRegex(ValueError, "fonts @import"):
            design._import_line("body { color: red; }\n")

    def test_fonts_url_and_domains(self):
        self.assertTrue(design.FONTS_URL.startswith("https://fonts.googleapis.com/css2?"))
        self.assertEqual(design.FONT_DOMAINS, ("https://fonts.googleapis.com", "https://fonts.gstatic.com"))


class TestA2uiCss(unittest.TestCase):
    def setUp(self):
        self.css = design.a2ui_css()
        self.values = _declarations(_block(self.css, ":root"))

    def test_r8_6_a2ui_tokens_come_from_toolkit_tokens(self):
        """R8.6: every --a2ui-* value is built from toolkit token variables, so
        the renderer's basic components draw in the design system's colours."""
        defined = set(_declarations(_block(design.tokens_css(), ":root")))
        for name, value in self.values.items():
            self.assertTrue(name.startswith("--a2ui-"), name)
            refs = re.findall(r"var\((--[a-z0-9-]+)\)", value)
            self.assertTrue(refs, f"{name}: {value} names no token")
            self.assertEqual(set(refs) - defined, set(), name)
            leftover = VALUE_WORD.sub(" ", value).split()
            self.assertEqual(leftover, [], f"{name}: {value} carries its own colour or syntax")

    def test_the_a2ui_css_is_well_formed(self):
        self.assertEqual(_css_problems(self.css), [])

    @unittest.skipUnless(BUNDLE_JS.is_file(), "no desk bundle built")
    def test_r8_6_every_renderer_colour_role_is_mapped(self):
        """R8.6: read from the bundled renderer itself, every --a2ui-color-* role
        is mapped (or is a shade the renderer derives from a mapped role), and
        every variable whose fallback is a literal colour is mapped."""
        js = BUNDLE_JS.read_text(encoding="utf-8")
        derived = re.compile(r"--a2ui-color-(primary|secondary)-(light|dark|hover)")
        for role in sorted(set(re.findall(r"--a2ui-color-[a-z0-9-]+", js))):
            if derived.fullmatch(role):
                base = role.rsplit("-", 1)[0]
                self.assertIn(base, self.values, f"{role} derives from {base}")
                continue
            self.assertIn(role, self.values, role)
        literal = re.compile(r"\s*(#[0-9a-fA-F]{3,8}|rgba?\(|hsla?\(|red|black|white)")
        for name, fallback in re.findall(r"var\((--a2ui-[a-z0-9-]+)\s*,([^;]*)", js):
            if literal.match(fallback) and not derived.fullmatch(name):
                self.assertIn(name, self.values, f"{name} falls back to a literal colour")

    def test_r8_6_primary_is_the_action_colour(self):
        self.assertEqual(self.values["--a2ui-color-primary"], "var(--action)")
        self.assertEqual(self.values["--a2ui-color-on-primary"], "var(--on-action)")


if __name__ == "__main__":
    unittest.main()
