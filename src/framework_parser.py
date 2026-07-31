"""Parser for the therapeutic framework each formulation declares.

The instruction template requires every formulation to open with
``"Leo este caso desde un marco [X]."`` and offers a closed menu of ten
frameworks. This module recovers ``[X]`` and maps it to one of the ten.

The framework labels stay in Spanish. They are data, not identifiers: the models
were shown a Spanish menu and their replies quote it, so translating them would
misrepresent what the models wrote.

Two layers, matching the analysis as run:

* the base parser, which requires the exact template phrasing;
* an extension that recovers two documented surface variants (a Markdown heading
  and a bold label) and several orthographic wrappings of menu labels.

The extension's patterns were defined from the instruction template and the
observed surface forms alone. Neither the dissent contribution nor the identity
of the model was used in deciding which patterns to admit.
"""
import re
import unicodedata

FRAMEWORK_NOT_EXTRACTED = "FRAMEWORK_NOT_EXTRACTED"

#: The ten menu labels, copied verbatim from the instruction template.
CANONICAL_FRAMEWORKS = [
    "cognitivo-conductual",
    "humanista-existencial",
    "psicodinámico-psicoanalítico",
    "integrativo",
    "basado en mindfulness o tercera generación",
    "apego",
    "trauma somático/sensoriomotor",
    "sistémico estructural-estratégico",
    "sistémico transgeneracional Bowen",
    "terapia narrativa",
]

_DECLARATION = re.compile(
    r"leo\s+este\s+caso\s+desde\s+un\s+[*_]*\s*marco\s+(.+?)\s*\.",
    re.IGNORECASE | re.DOTALL,
)
# Variant surface forms: a heading ("# Lectura desde un marco X") and a bold
# label ("**Marco:** X"). Searched over the first 600 characters only.
_HEADING = re.compile(r"desde\s+(?:un\s+)?[*_]*\s*marco\s+(.+?)\s*(?:\.|\n|$)", re.IGNORECASE)
_LABEL = re.compile(r"(?:^|\n)\s*[#>*_\s]*marco\s*[:：]\s*[*_]*\s*(.+?)\s*(?:\.|,|;|\n|$)",
                    re.IGNORECASE)

# Prepositions some models put before a noun-like framework ("un marco DE apego").
# No canonical label begins with one, so stripping one can never break a label
# that already matched; the direct attempt is always tried first.
_PREPOSITIONS = ["desde los", "desde las", "desde el", "desde la", "desde",
                 "de los", "de las", "de la", "del", "de"]
# Generic nouns some models interpose ("del ENFOQUE sistémico").
_GENERIC_NOUNS = ["enfoque", "perspectiva", "modelo", "abordaje", "paradigma", "lente"]
# Descriptive lead-ins stripped by the extension; none is a framework label.
_LEAD_INS = ["basado en el", "basado en la", "basada en el", "basada en la",
             "basado en", "basada en", "centrado en el", "centrado en la",
             "centrada en el", "centrada en la", "centrado en", "centrada en"]
#: Unambiguous abbreviations. An abbreviation qualifies only if it shares a stem
#: with exactly one canonical label; "sistémico" is ambiguous and is rejected.
_ALIASES = {"narrativo": "terapia narrativa", "narrativa": "terapia narrativa"}
_BOUNDARIES = {" ", "", ",", ".", ";", ":"}


def _normalise(text: str) -> str:
    """Lower-case, strip markdown and quotes, collapse whitespace, keep accents."""
    text = text.lower()
    for character in ("*", "_", "`", '"', "'", "«", "»", "“", "”", "‘", "’"):
        text = text.replace(character, "")
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


_CANONICAL_NORMALISED = {_normalise(label): label for label in CANONICAL_FRAMEWORKS}


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a or not b:
        return len(a) or len(b)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1,
                               previous[j - 1] + (0 if ca == cb else 1)))
        previous = current
    return previous[-1]


def _match_menu(text: str, relaxed_boundary: bool = False):
    """Map normalised text to a menu label by exact, prefix or edit distance."""
    if text in _CANONICAL_NORMALISED:
        return _CANONICAL_NORMALISED[text], "exact"

    boundaries = _BOUNDARIES if relaxed_boundary else {" ", ""}
    candidates = [(len(normalised), label)
                  for normalised, label in _CANONICAL_NORMALISED.items()
                  if text.startswith(normalised)
                  and text[len(normalised):len(normalised) + 1] in boundaries]
    if candidates:
        return max(candidates)[1], "prefix"
    if relaxed_boundary:
        return None

    head = text.split(" con ")[0].strip()
    best = None
    for normalised, label in _CANONICAL_NORMALISED.items():
        distance = _levenshtein(head, normalised)
        if distance <= 2 and (best is None or distance < best[0]):
            best = (distance, label)
    return (best[1], f"levenshtein(d={best[0]})") if best else None


def _strip_preposition(text: str):
    for preposition in _PREPOSITIONS:
        if text.startswith(preposition + " "):
            rest = text[len(preposition) + 1:].strip()
            for noun in _GENERIC_NOUNS:
                if rest.startswith(noun + " "):
                    return rest[len(noun) + 1:].strip()
            return rest
    return None


def _map_label(raw: str):
    """Base matcher: direct, then preposition-stripped, then alias."""
    text = _normalise(raw)
    match = _match_menu(text)
    if match is not None:
        return match

    stripped = _strip_preposition(text)
    if stripped is not None:
        match = _match_menu(stripped)
        if match is not None:
            return match[0], f"{match[1]}+prep"

    for candidate, method in ((text, "alias"), (stripped, "alias+prep")):
        if candidate is not None and candidate in _ALIASES:
            return _ALIASES[candidate], method
    return None, "off_menu"


def _map_label_extended(raw: str):
    """Extended matcher: adds relaxed boundaries, lead-ins and alias on the head."""
    framework, method = _map_label(raw)
    if framework is not None:
        return framework, method

    text = _normalise(raw)
    variants = [(text, "")]
    stripped = _strip_preposition(text)
    if stripped is not None:
        variants.append((stripped, "+prep"))
    for lead_in in _LEAD_INS:
        if text.startswith(lead_in + " "):
            variants.append((text[len(lead_in) + 1:].strip(), "+leadin"))
            break

    for variant, suffix in variants:
        match = _match_menu(variant, relaxed_boundary=True)
        if match is not None:
            return match[0], f"{match[1]}{suffix}"
    for variant, suffix in variants:
        head = variant.split(" con ")[0].strip()
        if head in _ALIASES:
            return _ALIASES[head], f"alias_head{suffix}"
    return None, "off_menu"


def parse_base(text: str) -> dict:
    """Base parser: requires the exact declaration phrasing of the template."""
    match = _DECLARATION.search(text or "")
    if not match:
        return {"framework": FRAMEWORK_NOT_EXTRACTED, "method": "no_regex_match",
                "raw_declaration": None, "structural_match": False}
    raw = match.group(1).strip()
    framework, method = _map_label(raw)
    return {"framework": framework or FRAMEWORK_NOT_EXTRACTED, "method": method,
            "raw_declaration": raw, "structural_match": True}


def parse(text: str) -> dict:
    """Extended parser. This is the one the published analysis uses.

    Returns the same keys as :func:`parse_base` plus ``via``, which records
    whether the base parser resolved the case or which extension recovered it.
    """
    base = parse_base(text)
    if base["structural_match"] and base["framework"] != FRAMEWORK_NOT_EXTRACTED:
        return {**base, "via": "base"}

    if base["structural_match"]:  # declaration found but label off the menu
        framework, method = _map_label_extended(base["raw_declaration"])
        if framework is not None:
            return {"framework": framework, "method": method,
                    "raw_declaration": base["raw_declaration"],
                    "structural_match": True, "via": "matcher_extension"}
        return {**base, "via": "unmapped"}

    head = (text or "")[:600]
    for pattern, tag in ((_HEADING, "heading"), (_LABEL, "label")):
        match = pattern.search(head)
        if match:
            raw = match.group(1).strip()
            framework, method = _map_label_extended(raw)
            return {"framework": framework or FRAMEWORK_NOT_EXTRACTED,
                    "method": f"{tag}:{method}", "raw_declaration": raw,
                    "structural_match": True, "via": "regex_extension"}
    return {**base, "via": "structural_failure"}
