"""Build the design system's brand spec and brand guide from its tokens.

src/ai_anthro_toolkit/design/tokens.json is the source. This script writes:

- design/brand-spec.json, in the brand-guide-builder plugin's schema. It always
  writes this file and checks every colour pairing against WCAG 2.2 AA first;
  any miss stops the build.
- design/brand-guide.html, only when --template names the plugin's
  brand-guide-template.html. The script fills every placeholder in it.

    python scripts/build_design_docs.py [--template PATH] [--check]

--check writes nothing and exits 1 if the committed brand-spec.json differs
from what the tokens produce.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOKENS = REPO / "src" / "ai_anthro_toolkit" / "design" / "tokens.json"
BUNDLE = REPO / "src" / "ai_anthro_toolkit" / "design" / "bundle.css"
SPEC = REPO / "design" / "brand-spec.json"
GUIDE = REPO / "design" / "brand-guide.html"
COMPONENTS = REPO / "design" / "system" / "components"

SPEC_VERSION = "1.0.0"
SPEC_DATE = "2026-11-15"
REPO_URL = "https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit"
TEXT, NON_TEXT = 4.5, 3.0

# (foreground, background, minimum ratio, use). Each is checked in both themes.
PAIRINGS = [
    ("ink", "paper", TEXT, "Primary text on the page"),
    ("ink", "surface", TEXT, "Primary text on cards, inputs and tables"),
    ("ink", "action-soft", TEXT, "Text on a quiet button's hover"),
    ("ink-muted", "paper", TEXT, "Hints and counts on the page"),
    ("ink-muted", "surface", TEXT, "Hints, captions and IDs on cards"),
    ("on-action", "action", TEXT, "Primary button text and selected choices"),
    ("on-action", "action-hover", TEXT, "Primary button text on hover"),
    ("action", "surface", TEXT, "Links and quiet buttons on cards"),
    ("action", "paper", TEXT, "Links on the page"),
    ("action", "action-soft", TEXT, "Step numbers and quiet buttons on hover"),
    ("on-attention", "attention", TEXT, "The Needs-you status"),
    ("done", "surface", TEXT, "Done status on cards"),
    ("done", "done-soft", TEXT, "Done status on its own fill"),
    ("refusal", "surface", TEXT, "Errors and refusals on cards"),
    ("refusal", "refusal-soft", TEXT, "Refusal notices"),
    ("model", "surface", TEXT, "Model drafts on cards"),
    ("model", "model-soft", TEXT, "Model drafts in their dashed box"),
    ("line-strong", "paper", NON_TEXT, "Control borders on the page"),
    ("line-strong", "surface", NON_TEXT, "Control borders on cards"),
    ("model-line", "model-soft", NON_TEXT, "The dashed border of a model draft"),
    ("action", "paper", NON_TEXT, "The focus ring on the page"),
] + [(f"code-{n}", "surface", NON_TEXT, f"Code colour {n} as a mark") for n in range(1, 7)]

COLOR_RULES = [
    ("action means you can do this", "Primary buttons, selected choices, links and the current stage. Text on it is on-action."),
    ("attention is only the Needs-you status", "and the current segment of Progress. It is the loudest colour in the system and is never decoration."),
    ("done, refusal and model keep one meaning each", "done is recorded results, refusal is errors and server refusals with a sentence, model is what the model wrote that nobody has decided."),
    ("Code colours are marks, never text", "code-1 to code-6 colour dots, lines and nodes. A code keeps the same tone everywhere; past six, repeat with the name shown."),
    ("line is decorative only", "Control borders use line-strong, which meets 3:1. focus is an alias of action."),
]

TYPE_RULES = [
    ("Who is speaking decides the typeface", "Figtree for the interface, Source Serif 4 for participants' words, Source Code Pro for raw machine text."),
    ("The passage is the largest text in a decision", "A participant's words are what is being decided about."),
    ("Never set labels in all caps", "Labels and status words are sentence case."),
    ("Keep running text within measure", "Running text and passages stop at 68ch."),
]

VOICE_ATTRIBUTES = [
    "Plain: plain words, sentence case, no exclamation marks.",
    "Exact: numbers are counted from the record, such as 208 of 212 chunks, never most.",
    "Accountable: the interface says who decided. The model is the model; the researcher is you.",
    "Faithful: participants are quoted exactly, never tidied, trimmed or paraphrased.",
]

WRITING_RULES = [
    "Labels are verbs plus objects: Record ruling, Ratify codebook, Review the record.",
    "Questions end in a question mark: Which codes apply to this passage?",
    "Refusals say what was refused and exactly what is missing: Can't ratify yet. 2 codes have no decision. No apologies, no something went wrong.",
    "Call machine output the model. Don't call it AI, assistant or Claude in the interface.",
    "A disabled button always says why, beside it.",
]

TONE_CONTEXTS = {
    "A decision inside a chat": ("Direct and brief; one question at a time.", "Which codes apply to this passage?"),
    "A refusal from the server": ("Factual; names what is missing.", "Can't ratify yet. 2 codes have no decision: Being watched, Permits and city rules."),
    "An exported decision record": ("Formal and complete; fit for a methods appendix.", "Ratified by the researcher on 12 March: 6 codes, 2 revised, 1 merged."),
}

DO_LIST = [
    "Show one open decision at a time, with Progress above it.",
    "Put what the model wrote in a dashed model box until someone decides.",
    "Number the clicks inside a decision with Step: 1 choose, 2 record.",
    "End every view with the Byline.",
    "Pair every status colour with a word and a mark.",
]

DONT_LIST = [
    "Restyle a model draft as solid because it was accepted.",
    "Use attention, done or refusal for decoration.",
    "Set code colours as text.",
    "Add a logo or mark beside the Byline, or reword it.",
    "Put more than one primary button in a view.",
]


# ── Colour maths ──────────────────────────────────────────────────────────────

def hex_to_rgb(value: str) -> list[int]:
    value = value.lstrip("#")
    return [int(value[i:i + 2], 16) for i in (0, 2, 4)]


def _luminance(value: str) -> float:
    def channel(c: int) -> float:
        s = c / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in hex_to_rgb(value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg: str, bg: str) -> float:
    a, b = sorted((_luminance(fg), _luminance(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def palettes(tokens: dict) -> dict[str, dict[str, str]]:
    """Return {theme: {token: hex}}, with aliases such as {action} resolved."""
    out: dict[str, dict[str, str]] = {"light": {}, "dark": {}}
    aliases = {}
    for tok in tokens["color"]["tokens"]:
        if isinstance(tok["value"], str):
            aliases[tok["name"]] = tok["value"].strip("{}")
        else:
            for theme in out:
                out[theme][tok["name"]] = tok["value"][theme]
    for name, target in aliases.items():
        for theme in out:
            out[theme][name] = out[theme][target]
    return out


def check_contrast(tokens: dict, pairings=PAIRINGS) -> list[dict]:
    """Every pairing in both themes, with its ratio. Raises ValueError on any miss."""
    rows, misses = [], []
    for theme, colours in palettes(tokens).items():
        for fg, bg, minimum, use in pairings:
            ratio = contrast(colours[fg], colours[bg])
            row = {"foreground": fg, "background": bg, "theme": theme,
                   "ratio": f"{ratio:.2f}:1", "minimum": f"{minimum}:1", "use": use}
            rows.append(row)
            if ratio < minimum:
                misses.append(f"{fg} on {bg} ({theme}) is {ratio:.2f}:1, needs {minimum}:1")
    if misses:
        raise ValueError("Contrast check failed: " + "; ".join(misses))
    return rows


# ── Spec ──────────────────────────────────────────────────────────────────────

def _px(value: str) -> float:
    return float(value.removesuffix("px"))


def build_spec(tokens: dict) -> dict:
    pal = palettes(tokens)
    colour_tokens = {}
    for tok in tokens["color"]["tokens"]:
        name = tok["name"]
        colour_tokens[name] = {
            "hex": pal["light"][name], "rgb": hex_to_rgb(pal["light"][name]),
            "dark": {"hex": pal["dark"][name], "rgb": hex_to_rgb(pal["dark"][name])},
            "role": tok["usage"],
        }
    families = tokens["type"]["families"]
    fonts = {
        "sans": {"family": "Figtree", "source": "google", "weights": [400, 500, 600, 700], "fallback": families["sans"]},
        "serif": {"family": "Source Serif 4", "source": "google", "weights": [400], "fallback": families["serif"]},
        "mono": {"family": "Source Code Pro", "source": "google", "weights": [400], "fallback": families["mono"]},
    }
    text_colour = {"small": "ink-muted", "id": "ink-muted", "model-label": "model"}
    scale = {}
    for group in tokens["type"]["groups"]:
        for style in group["styles"]:
            scale[style["name"]] = {
                "font": group["family"], "weight": style["fontWeight"], "size": style["fontSize"],
                "color": text_colour.get(style["name"], "ink"),
                "line_height": round(_px(style["lineHeight"]) / _px(style["fontSize"]), 3),
                "transform": "none",
            }
    sizes = {t["name"]: t["value"] for t in tokens["size"]["tokens"]}
    radii = {t["name"]: t["value"] for t in tokens["radius"]["tokens"]}
    space = {t["name"]: t["value"] for t in tokens["spacing"]["tokens"]}
    pill = radii["radius-full"]
    return {
        "meta": {
            "name": tokens["name"], "version": SPEC_VERSION, "created": SPEC_DATE, "updated": SPEC_DATE,
            "description": "The interface system for every screen the AI Anthropology Toolkit shows.",
            "url": REPO_URL,
        },
        "colors": {
            "tokens": colour_tokens,
            "rules": [{"rule": r, "reason": why} for r, why in COLOR_RULES],
            "approved_pairings": check_contrast(tokens),
        },
        "typography": {
            "fonts": fonts, "scale": scale,
            "rules": [f"{r}. {why}" for r, why in TYPE_RULES],
        },
        "spacing": {
            "content_max_width": sizes["page"],
            "section_padding_v": space["space-12"], "section_padding_h": space["space-4"],
            "card_padding": "clamp(20px, 4vw, 36px)", "card_border_radius": radii["radius-lg"],
            "breakpoints": {"any": "Components wrap with flex and clamp; there are no fixed breakpoints."},
        },
        "buttons": {
            "primary": {"bg": "action", "text": "on-action", "border": "1.5px solid action", "radius": pill,
                        "padding": f"0 {space['space-6']}", "font": "sans", "weight": 600},
            "secondary": {"bg": "surface", "text": "ink", "border": "1.5px solid line-strong", "radius": pill,
                          "padding": f"0 {space['space-6']}", "font": "sans", "weight": 600},
            "tertiary": {"bg": "transparent", "text": "action", "border": "none", "radius": pill,
                         "padding": f"0 {space['space-2']}", "font": "sans", "weight": 500, "decoration": "underline"},
        },
        "voice": {
            "attributes": VOICE_ATTRIBUTES, "writing_rules": WRITING_RULES,
            "tone_contexts": {k: v[0] for k, v in TONE_CONTEXTS.items()},
        },
        "imagery": {"style": "None. The toolkit uses no photography or illustration."},
    }


# ── Guide ─────────────────────────────────────────────────────────────────────

def _e(text: str) -> str:
    return html.escape(str(text), quote=True)


def _rows(rows) -> str:
    return "\n".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)


def _rules(rules) -> str:
    return "\n".join(f'<div class="rule"><strong>{_e(r)}</strong> &mdash; {_e(why)}</div>' for r, why in rules)


def _li(items) -> str:
    return "\n".join(f"<li>{_e(i)}</li>" for i in items)


def _code(pairs) -> str:
    return "<br>\n".join(f'<span class="prop">{_e(k)}</span>: <span class="val">{_e(v)}</span>;' for k, v in pairs)


def _dot(hex_value: str) -> str:
    return f'<span class="color-dot" style="background:{hex_value}"></span>'


def _fonts_href(bundle_css: str) -> str:
    first = bundle_css.splitlines()[0]
    match = re.match(r'@import url\("([^"]+)"\);', first)
    if not match:
        raise ValueError("bundle.css must start with its Google Fonts @import")
    return match.group(1)


def _component_purposes() -> list[tuple[str, str]]:
    out = []
    for readme in sorted(COMPONENTS.glob("*/README.md")):
        lines = [ln for ln in readme.read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.startswith(("#", "<!--"))]
        out.append((readme.parent.name, lines[0] if lines else ""))
    return out


def guide_values(spec: dict, tokens: dict, bundle_css: str) -> dict[str, str]:
    pal = palettes(tokens)
    light = pal["light"]
    sans = tokens["type"]["families"]["sans"]
    serif = tokens["type"]["families"]["serif"]
    radii = {t["name"]: t["value"] for t in tokens["radius"]["tokens"]}
    name = spec["meta"]["name"]

    swatches = "\n".join(
        f'<div class="palette-swatch"><div class="swatch-color" style="background:{light[t["name"]]}"></div>'
        f'<div class="swatch-info"><div class="swatch-token">{_e(t["name"])}</div>'
        f'<div class="swatch-hex">{light[t["name"]]} &middot; dark {pal["dark"][t["name"]]}</div>'
        f'<div class="swatch-usage">{_e(t["usage"])}</div></div></div>'
        for t in tokens["color"]["tokens"])
    contrast_rows = _rows(
        (f'{_dot(light[p["foreground"]])}{_e(p["foreground"])} on {_e(p["background"])} ({p["theme"]})',
         p["ratio"], f'<span class="pass">Pass</span> (needs {p["minimum"]})')
        for p in spec["colors"]["approved_pairings"])
    application = _rows(
        (_e(use), f'{_dot(light[fg])}{_e(fg)}', _e(bg))
        for fg, bg, minimum, use in PAIRINGS if minimum == TEXT)
    family_of = {"sans": "Figtree", "serif": "Source Serif 4", "mono": "Source Code Pro"}
    font_rows = _rows(
        (_e(role), _e(f["family"]), ", ".join(map(str, f["weights"])), "Google Fonts")
        for role, f in (("Interface (sans)", spec["typography"]["fonts"]["sans"]),
                        ("People's words (serif)", spec["typography"]["fonts"]["serif"]),
                        ("Raw machine text (mono)", spec["typography"]["fonts"]["mono"])))
    specimens = []
    for group in tokens["type"]["groups"]:
        fam = tokens["type"]["families"][group["family"]]
        for s in group["styles"]:
            colour = light[spec["typography"]["scale"][s["name"]]["color"]]
            specimens.append(
                f'<div class="type-specimen"><div class="type-meta"><span>{_e(s["name"])}</span>'
                f'<span>{family_of[group["family"]]} {s["fontWeight"]}</span>'
                f'<span>{s["fontSize"]} / {s["lineHeight"]}</span></div>'
                f'<div style="font:{s["fontWeight"]} {s["fontSize"]}/{s["lineHeight"]} {_e(fam)};color:{colour}">{_e(s["sample"])}</div>'
                f'<p style="margin-top:8px;font-size:14px;opacity:.7">{_e(s["usage"])}</p></div>')
    spacing_rows = _rows((_e(t["name"]), t["value"], t["value"], _e(t["usage"])) for t in tokens["spacing"]["tokens"])
    radius_rows = _rows((_e(t["usage"]), f'{_e(t["name"])} ({t["value"]})') for t in tokens["radius"]["tokens"])
    button_rows = _rows([
        ("Primary", "action", "1.5px action", "on-action", "0 24px", "action-hover fill"),
        ("Secondary", "surface", "1.5px line-strong", "ink", "0 24px", "ink-muted border"),
        ("Quiet", "transparent", "none", "action, underlined", "0 8px", "action-soft fill"),
        ("Disabled", "transparent", "1.5px dashed line-strong", "ink-muted", "0 24px", "none; the reason sits beside it"),
    ])
    shared = _rows([
        ("Height", "at least 46px; every clickable thing is at least 44px"),
        ("Shape", f"pill ({radii['radius-full']})"),
        ("Type", "Figtree 600, 16px"),
        ("Focus", "2px solid focus ring, 2px gap"),
        ("Hover", "colour only, 150ms"),
        ("Per view", "one primary button"),
    ])
    components = ('<div class="table-scroll"><table class="usage-table"><thead><tr><th>Component</th><th>What it is for</th></tr></thead><tbody>'
                  + _rows((_e(n), _e(p)) for n, p in _component_purposes()) + "</tbody></table></div>")

    colour_css = ";\n    ".join(f"--{k}: {v}" for k, v in light.items()) + ";"
    mapped = {"--color-primary": light["action"], "--color-accent": light["line-strong"], "--color-bg": light["surface"],
              "--color-bg-alt": light["paper"], "--color-text": light["ink"], "--color-border": light["line"]}
    token_block = lambda group: _code((f"--{t['name']}", t["value"]) for t in tokens[group]["tokens"])  # noqa: E731

    not_set = "Not set. The toolkit has no logo; the name is set in type."
    return {
        "brand_name": _e(name),
        "spec_version": spec["meta"]["version"],
        "spec_date": spec["meta"]["updated"],
        "google_fonts_link": f'<link rel="stylesheet" href="{_e(_fonts_href(bundle_css))}">',
        "css_color_tokens": colour_css + "\n    " + ";\n    ".join(f"{k}: {v}" for k, v in mapped.items()) + ";",
        "css_color_variants": "/* none */",
        "css_font_tokens": f"--font-heading: {sans};\n    --font-body: {sans};\n    --font-serif: {serif};",
        "css_spacing_tokens": f"--content-width: {spec['spacing']['content_max_width']};\n    --space-section-v: 64px;\n    --space-section-h: 48px;",
        "css_component_tokens": (f"--radius: {radii['radius-md']};\n    --radius-lg: {radii['radius-lg']};\n"
                                 "    --accent-width: 48px;\n    --accent-height: 4px;\n    --accent-radius: 999px;"),
        "cover_logo_svg": "",
        "footer_logo": "",
        "footer_affiliation": f'<p>{_e(name)} by Matt Artz &middot; {_e(REPO_URL.removeprefix("https://"))}</p>',
        # 01 Overview
        "brand_overview_intro": "One small set of tokens and components for every screen the toolkit shows, from a ratification desk inside a chat to an exported decision record.",
        "brand_positioning": "The toolkit asks researchers to decide things the model has drafted: codes, rulings, themes. The interface exists to make those decisions clear, quick and on the record, and to never let a model draft pass for a decision.",
        "brand_principles_list": _li([
            "Show who decided. Model drafts sit in a dashed model box; the researcher's decisions are solid.",
            "What needs you is the loudest thing on screen. One open decision at a time, raised, with the yellow Needs-you status.",
            "One next step, numbered. One primary button per view; a disabled button says why.",
        ]),
        "brand_descriptors": "Plain &middot; Exact &middot; Accountable &middot; Calm",
        # 02 Archetype
        "archetype_intro": "No archetype is set for the toolkit. Its visual and verbal decisions follow from the three principles in the overview.",
        "archetype_primary_name": "&mdash;",
        "archetype_primary_description": "Not set.",
        "archetype_secondary_name": "&mdash;",
        "archetype_secondary_description": "Not set.",
        "archetype_influence_rows": _rows([("All dimensions", "Governed by the three principles, not an archetype.")]),
        "archetype_conflict_rule": "Where two rules pull apart, the one that keeps the researcher's decision visible wins.",
        # 03 Logo
        "logo_intro": "The toolkit has no logo. The Byline is its only branding.",
        "logo_lockup_description": "The name is set in Figtree 600, in ink on surface or paper, inside the Byline: AI Anthropology Toolkit by Matt Artz, the version, Cite (DOI), GitHub and mattartz.me.",
        "logo_variant_cards": (f'<div class="logo-card" style="background:{light["surface"]};border:1px solid {light["line"]}"><span class="logo-text" style="color:{light["ink"]}">{_e(name)}</span></div>'
                               f'<div class="logo-card" style="background:{pal["dark"]["paper"]}"><span class="logo-text" style="color:{pal["dark"]["ink"]}">{_e(name)}</span></div>'),
        "logo_mark_only_description": "There is no mark. Hosts show their own icon.",
        "logo_mark_only_demos": "",
        "logo_clear_space": "The Byline sits below a 1px line with space-3 (12px) above it.",
        "logo_min_mark_size": not_set,
        "logo_min_lockup_width": not_set,
        "logo_text_alignment": "Left, as running text.",
        "logo_mark_construction": not_set,
        # 04 Colour
        "color_intro": "Harbor: navy for what you can do, on a cool grey page, with yellow kept for what needs you. Every token has a light and a dark value; the swatches show light.",
        "color_swatches": swatches,
        "color_application_rows": application,
        "color_accessibility_intro": "Every text pairing meets 4.5:1 and every control border, focus ring and code mark meets 3:1, in both themes. The build checks these pairings and stops on any miss.",
        "color_contrast_rows": contrast_rows,
        "color_rules": _rules(COLOR_RULES),
        # 05 Type
        "typography_intro": "Who is speaking decides the typeface.",
        "font_stack_rows": font_rows,
        "type_specimens": "\n".join(specimens),
        "typography_rules": _rules(TYPE_RULES),
        # 06 Spacing
        "spacing_intro": "Spacing comes from one scale. Shapes say what a thing is: pills are controls, the round card is the open decision.",
        "spacing_content_widths": f"<p>Pages are at most {spec['spacing']['content_max_width']} wide. Running text and passages stop at 68ch.</p>",
        "spacing_scale_rows": spacing_rows,
        "border_radius_rows": radius_rows,
        "accent_line_description": "The toolkit uses no accent line. The bars in this guide are its own section marks, drawn in line-strong.",
        "accent_line_dimensions": "48 &times; 4px, this guide only",
        "accent_line_placement": "This guide only; never in the toolkit's screens.",
        "breakpoint_rows": _rows([("Any width", "&mdash;", "Rows wrap with flex; the decision card's padding scales with clamp(20px, 4vw, 36px)."),
                                  ("Phone", "about 400px", "Choices stack; the sticky Tally stays one row.")]),
        # 07 Buttons
        "buttons_intro": "Three kinds: primary for the one thing the view is for, secondary for everything else, quiet for small moves.",
        "button_primary_label": "Ratify codebook",
        "button_secondary_label": "Skip for now",
        "button_tertiary_label": "Review the record",
        "button_primary_padding": "13px 24px",
        "button_primary_border": f"1.5px solid {light['action']}; border-radius: 999px",
        "button_secondary_padding": "13px 24px",
        "button_secondary_border": f"1.5px solid {light['line-strong']}; border-radius: 999px",
        "button_additional_backgrounds": "",
        "button_spec_rows": button_rows,
        "button_shared_properties": shared,
        # 08 Components
        "components_intro": "Fifteen components cover every screen. Their markup, React versions and previews live in design/system/components/.",
        "component_demos": components,
        # 09 Imagery
        "imagery_intro": "The toolkit uses no photography or illustration.",
        "imagery_style": "None.",
        "imagery_off_brand_list": _li(["Stock photography", "Illustrations or mascots", "Icons without a word beside them"]),
        "imagery_aspect_ratio_rows": _rows([("Not used", "&mdash;", "&mdash;")]),
        "imagery_overlay_description": "Not used.",
        "imagery_overlay_rows": _rows([("Not used", "&mdash;", "&mdash;", "&mdash;")]),
        "imagery_overlay_rule": "Not used.",
        "imagery_alt_text_guidance": "Charts and network maps carry alt text that states what they show and the numbers behind it.",
        # 10 Print
        "print_intro": "Exported records print from the browser in the light theme. No print colours are set.",
        "print_cmyk_description": "Not set.",
        "print_cmyk_rows": _rows([("Not set", "&mdash;", "&mdash;", "&mdash;", "&mdash;", "&mdash;")]),
        "print_pantone_description": "Not set.",
        "print_pantone_rows": _rows([("Not set", "&mdash;")]),
        "print_paper_description": "Not set.",
        "print_paper_rows": _rows([("Not set", "&mdash;", "&mdash;")]),
        "print_proof_rule": "check an exported record's print preview in the light theme.",
        # 11 Co-branding
        "cobranding_intro": "The toolkit runs inside other products, such as a chat host, without co-branding.",
        "cobranding_principles": "The host's own chrome stays the host's. The toolkit's views carry only the Byline.",
        "cobranding_size_rule": "Not used.",
        "cobranding_affiliation_description": "The Byline is the affiliation line.",
        "cobranding_affiliation_demo": f'<span style="font:400 14px/22px {_e(sans)};color:{light["ink-muted"]}">{_e(name)} by Matt Artz</span>',
        "cobranding_lockup_description": "Not used.",
        "cobranding_lockup_demo": "&mdash;",
        "cobranding_rules": _rules([("Never alter the palette for a host", "Follow the host's light or dark theme with the dark tokens.")]),
        # 12 Email
        "email_sig_intro": "Not used. The toolkit sends no email.",
        "email_sig_structure_description": "Not used.",
        "email_sig_structure_rows": _rows([("Not used", "&mdash;", "&mdash;", "&mdash;")]),
        "email_sig_example_description": "Not used.",
        "email_sig_rendered_example": "&mdash;",
        "email_sig_rules": "<p>Not used.</p>",
        # 13 Voice
        "voice_intro": "Plain words for a researcher who is deciding something that matters.",
        "voice_attributes_list": _li(VOICE_ATTRIBUTES),
        "voice_writing_rules_list": _li(WRITING_RULES),
        "voice_tone_context_rows": _rows((_e(k), _e(t), _e(ex)) for k, (t, ex) in TONE_CONTEXTS.items()),
        # 14 Usage
        "usage_intro": "The rules most often broken.",
        "usage_do_list": _li(DO_LIST),
        "usage_dont_list": _li(DONT_LIST),
        # 15 Tokens
        "tokens_intro": "tokens.json in the package is the source. These are the light values; the dark ones are in the same file.",
        "tokens_color_block": _code((f"--{k}", v) for k, v in light.items()),
        "tokens_typography_block": _code([(f"--font-{k}", v) for k, v in tokens["type"]["families"].items()]),
        "tokens_spacing_block": token_block("spacing"),
        "tokens_component_block": token_block("radius") + "<br>\n" + token_block("size"),
    }


def render_guide(template: str, values: dict[str, str]) -> str:
    """Fill every {{placeholder}}. Raises ValueError if one has no value."""
    # The template titles the archetype subsections "Primary: The {{name}}"; with
    # no archetype set, drop the article so the heading reads cleanly.
    template = template.replace("Primary: The {{archetype_primary_name}}", "Primary archetype: {{archetype_primary_name}}")
    template = template.replace("Secondary: The {{archetype_secondary_name}}", "Secondary archetype: {{archetype_secondary_name}}")
    missing = sorted(set(re.findall(r"{{(\w+)}}", template)) - set(values))
    if missing:
        raise ValueError("No value for placeholders: " + ", ".join(missing))
    return re.sub(r"{{(\w+)}}", lambda m: values[m.group(1)], template)


def spec_text(tokens: dict) -> str:
    return json.dumps(build_spec(tokens), indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the design brand spec and guide from tokens.json.")
    parser.add_argument("--template", type=Path, help="brand-guide-builder's brand-guide-template.html")
    parser.add_argument("--check", action="store_true", help="exit 1 if brand-spec.json is out of date")
    args = parser.parse_args(argv)
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    text = spec_text(tokens)
    if args.check:
        current = SPEC.read_text(encoding="utf-8") if SPEC.exists() else ""
        if current != text:
            print("design/brand-spec.json is out of date; run scripts/build_design_docs.py", file=sys.stderr)
            return 1
        return 0
    SPEC.write_text(text, encoding="utf-8")
    print(f"wrote {SPEC.relative_to(REPO)}")
    if args.template:
        values = guide_values(json.loads(text), tokens, BUNDLE.read_text(encoding="utf-8"))
        GUIDE.write_text(render_guide(args.template.read_text(encoding="utf-8"), values), encoding="utf-8")
        print(f"wrote {GUIDE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
