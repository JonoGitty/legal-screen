"""Pseudonymise a contract locally, and put the names back afterwards.

v0 is rules only (no model, nothing leaves the machine):
  1. Parties as the contract defines them in its preamble, working back from
     each ("SHORT") definition: `Acme Inc., a Delaware corporation ("Acme")`.
     The name, the name without its suffix, and SHORT share a placeholder.
     SHORT is kept when it is a role word (Customer, Supplier, ...), which
     identifies no one.
  2. Organisation names with a company suffix (Inc., Ltd, LLC, GmbH, ...),
     anywhere, and the same name without the suffix.
  3. Things with a shape: emails, web addresses, phone numbers, money,
     dates, street addresses, postcodes, people introduced by Mr/Ms/Dr or
     on a signature line (By:, Name:, Attention:).
Placeholders look like ⟦PARTY_A⟧, ⟦ORG_2⟧, ⟦AMOUNT_3⟧. The mapping stays on this
machine, and restore() puts the canonical names back into, e.g., a cloud
model's answer. Indirect identifiers (a unique deal fact) are NOT caught by
any of this, which is why sending is always the lawyer's decision.
"""
import re
from dataclasses import dataclass, field

OPEN, CLOSE = "⟦", "⟧"
PREAMBLE_CHARS = 4000

# case-insensitive: contracts write "WESTERN COPPER CORPORATION" as often as "Acme Corp."
SUFFIX = r"(?i:Inc\.?|Incorporated|Corp\.?|Corporation|L\.?L\.?C\.?|Ltd\.?|Limited|PLC|L\.?L\.?P\.?|L\.?P\.?|GmbH|AG|S\.A\.|N\.V\.|B\.V\.|Co\.,?\s*Ltd\.?|Company|Trust|Bank|Partners|Fund|Foundation|Association|University|Authority)"
_CAP = r"[A-Z][A-Za-z0-9&'\-.]*"
_JOIN = r"(?:of|and|for|the|de|la|du|von|&)"
_NAMEWORD = rf"(?!{SUFFIX}(?![A-Za-z])){_CAP}"
ORG = re.compile(rf"\b({_NAMEWORD}(?:[ \t]+(?:{_NAMEWORD}|{_JOIN})){{0,6}}),?[ \t]+{SUFFIX}(?![A-Za-z])")
LEADING_JUNK = re.compile(r"^(?:(?:the|and|of|&|about|source|between|by|with|from|for|to|re|dear|this|that|each|both)\b[:,]?\s+)+", re.I)
DEF_TERM = re.compile(
    r"\(\s*(?:hereinafter\s+(?:referred\s+to\s+as\s+|called\s+)?)?(?:collectively\s+)?(?:the\s+)?[\"“](?:the\s+|this\s+)?([^\"”]{1,40})[\"”]",
    re.I,
)
DESCRIPTOR = re.compile(
    r",?\s+(?:an?\s+[A-Za-z .,\-]{0,80}?(?:corporation|company|partnership|association|bank|trust|entity|organi[sz]ation|society|firm|business)\b"
    r"|(?:with|having)\s+(?:its\s+|an\s+)?(?:registered\s+|principal\s+)?(?:offices?|place\s+of\s+business|address)\b).*$",
    re.I | re.S,
)
NAME_TAIL = re.compile(rf"({_CAP}(?:,?[ \t]+(?:{_CAP}|{_JOIN})){{0,8}}),?\s*$")
# a lower-case name ("i-on interactive"): the last few words after a comma or "and"
LOWER_TAIL = re.compile(r"(?:^|,|\band\b)\s*([a-z][\w&'\-.]*(?:\s+[\w&'\-.]+){0,4})\s*$")
ROLE_WORDS = {
    w.lower()
    for w in """Agreement Party Parties Customer Client Supplier Seller Buyer Purchaser Vendor Licensor Licensee
    Distributor Reseller Contractor Consultant Company Corporation Employer Employee Provider Recipient Discloser
    Lender Borrower Landlord Tenant Lessor Lessee Manufacturer Agent Principal Partner Member Owner Investor
    Guarantor Franchisor Franchisee Developer Publisher Sponsor Host Operator Producer Bank Trust Fund
    Licensors Licensees Sellers Buyers Purchasers Sub-Licensor Sublicensor Sublicensee Each Collectively Individually""".split()
}
NOT_A_PARTY = re.compile(r"agreement|contract|schedule|exhibit|annex|appendix|date|term\b|period|territory|product|service|information|material|fee|price|plan|policy|business|trademark|mark\b|patent|asset|right|licen[cs]e|software|know-how|program|project|budget|plan\b|work", re.I)
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("WEB", re.compile(r"\b(?:https?://|www\.)[\w./?=&%#-]+", re.I)),
    ("PHONE", re.compile(r"(?<![\w$£€.])(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{2,5}\)[\s.-]?|\d{2,5}[\s.-])\d{3,4}[\s.-]?\d{3,4}(?!\d|\.\d)")),
    ("AMOUNT", re.compile(r"(?:[$£€]\s?|\b(?:USD|GBP|EUR|US\$)\s?)\d[\d,]*(?:\.\d+)?(?:\s?(?:million|billion|thousand|m|bn|k)\b)?", re.I)),
    ("DATE", re.compile(r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})\b")),
    ("ADDRESS", re.compile(r"\b\d{1,6}\s+[\w .'-]{2,40},\s*[\w .'-]{2,30},\s*[A-Za-z .]{2,20},?\s*\d{5}(?:-\d{4})?\b")),
    ("ADDRESS", re.compile(r"\b\d{1,6}\s+(?:[A-Za-z][A-Za-z.]*\s+){1,4}(?:Street|St\.|Avenue|Ave\.?|Road|Rd\.|Boulevard|Blvd\.?|Lane|Ln\.|Drive|Dr\.|Way|Place|Pl\.|Court|Ct\.|Square|Parkway|Pkwy\.?)", re.I)),
    ("POSTCODE", re.compile(r"\b(?:[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2})\b")),
    ("PERSON", re.compile(r"\b(?:Mr|Mrs|Ms|Miss|Dr|Prof)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}")),
    ("PERSON", re.compile(r"(?im)^\s*(?:By|Name|Attention|Attn|Signed)\s*:\s*(?:/s/\s*)?([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,3})\s*$")),
]


@dataclass
class Pseudonymised:
    text: str
    mapping: dict[str, str] = field(default_factory=dict)  # placeholder -> canonical original

    def restore(self, text: str) -> str:
        for ph, orig in self.mapping.items():
            text = text.replace(ph, orig)
        return text


def _norm(s: str) -> str:
    return re.sub(r"[\s,.]+", " ", s).strip().lower()


def _strip_suffix(name: str) -> str:
    return re.sub(rf",?\s+{SUFFIX}\s*$", "", name).strip(" ,")


def _words(s: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z\-]*", s)


def _is_role(s: str) -> bool:
    ws = _words(s)
    return bool(ws) and all(w.lower() in ROLE_WORDS or w.lower() in {"the", "a", "an"} for w in ws)


def find_parties(text: str) -> list[tuple[str, str | None]]:
    """(name, short name or None) for each party the preamble defines."""
    out = []
    for m in DEF_TERM.finditer(text):
        short = m.group(1).strip()
        if NOT_A_PARTY.search(short):
            continue
        before = text[max(0, m.start() - 300) : m.start()]
        before = before.split(")")[-1]  # only what follows the previous definition
        before = re.split(r"\n\s*\n|;|\.\s+(?=[A-Z])|\bbetween\b|\bamong\b|\band\b(?=\s+[A-Z])|\bby\b(?=\s+[A-Z])", before)[-1]
        before = DESCRIPTOR.sub("", before.strip()).strip(" ,")
        tail = NAME_TAIL.search(before) or LOWER_TAIL.search(before)
        if not tail:
            continue
        name = LEADING_JUNK.sub("", re.sub(r"\s+", " ", tail.group(1)).strip(" ,"))
        has_suffix = re.search(rf"{SUFFIX}\s*$", name) is not None
        # parties are defined in the preamble; deeper in, only a suffixed name counts
        if m.start() > PREAMBLE_CHARS and not has_suffix:
            continue
        if len(name) < 2 or not re.search(r"[A-Za-z]{2}", name) or _is_role(name):
            continue
        if NOT_A_PARTY.search(name) and not has_suffix:
            continue
        out.append((name, None if _is_role(short) else short))
    return out


def pseudonymise(text: str) -> Pseudonymised:
    if OPEN in text or CLOSE in text:
        raise ValueError("the document already contains placeholder brackets; refusing to pseudonymise")
    entities: dict[str, tuple[str, set[str]]] = {}
    order: list[str] = []

    def add(kind: str, forms: list[str]):
        forms = [f.strip(" ,") for f in forms if f and len(f.strip(" ,")) >= 2]
        if not forms:
            return
        # one entity per normalised name without suffix; a later sighting can add forms
        key = _norm(_strip_suffix(forms[0]))
        for k in (key, *(_norm(_strip_suffix(f)) for f in forms)):
            if k in entities:
                entities[k][1].update(forms)
                return
        entities[key] = (kind, set(forms))
        order.append(key)

    for name, short in find_parties(text):
        add("PARTY", [name, _strip_suffix(name), *([short] if short else [])])
    for m in ORG.finditer(text):
        # "a Florida corporation", "an English limited company": a description, not a name
        if re.search(r"\b(?:an?)\s+$", text[max(0, m.start() - 4) : m.start()], re.I):
            continue
        core = LEADING_JUNK.sub("", m.group(1)).strip()
        if _is_role(core) or len(core) < 2:
            continue
        add("ORG", [LEADING_JUNK.sub("", m.group(0).strip()), core])

    mapping: dict[str, str] = {}
    surface: list[tuple[str, str]] = []
    letters = iter("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    n_org = 0
    for key in order:
        kind, forms = entities[key]
        if kind == "PARTY":
            ph = f"{OPEN}PARTY_{next(letters, 'Z')}{CLOSE}"
        else:
            n_org += 1
            ph = f"{OPEN}ORG_{n_org}{CLOSE}"
        mapping[ph] = max(forms, key=len)
        surface.extend((f, ph) for f in forms)

    out = text
    for form, ph in sorted(surface, key=lambda x: -len(x[0])):
        out = re.sub(rf"(?<![A-Za-z0-9]){re.escape(form)}(?![A-Za-z0-9])", ph, out, flags=re.I)

    counters: dict[str, int] = {}
    seen: dict[tuple[str, str], str] = {}
    for kind, pat in PATTERNS:

        def repl(m, kind=kind):
            s = m.group(1) if m.groups() else m.group(0)
            if OPEN in s or CLOSE in s:
                return m.group(0)
            k = (kind, _norm(s))
            if k not in seen:
                counters[kind] = counters.get(kind, 0) + 1
                seen[k] = f"{OPEN}{kind}_{counters[kind]}{CLOSE}"
                mapping[seen[k]] = s
            return m.group(0).replace(s, seen[k])

        out = pat.sub(repl, out)
    return Pseudonymised(out, mapping)
