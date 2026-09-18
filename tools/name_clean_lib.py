"""Deterministic name-cleaning helpers for catalog entry names.

Two very different kinds of raw name show up in this catalog:

1. A raw folder-name "blob" with NO spaces of its own, e.g.
   "1065349_NativeFluteOriginal_ChristianHenson_DecentSampler" or
   "ampco-v1-dspreset". These come straight from a Pianobook-style zip
   name / on-disk folder name: leading numeric asset IDs, version tags,
   timestamps and an appended author name are all fair game to strip, and
   underscore/hyphen are pure word separators to camelCase-split apart.

2. A name that ALREADY uses spaces, e.g. "GetGood Drums - Modern and
   Massive Pack" or "1930s Wurlitzer Upright". This is a deliberately-
   authored display name. Bare numbers in it are almost always meaningful
   (a year, a count, a model number like "X-99B"/"808"), and an internal
   CamelCase or hyphenated word (like "GetGood", a real brand, or
   "Jupiter-6") is intentional styling, not an ID blob to tear apart. Only
   an explicit version marker (v1.0, V2, 1.0.0) or known boilerplate word
   is removed; everything else is left exactly as authored.
"""
import re

# Kind 1 (raw blob) version token: v-prefixed, OR a bare digit run --
# with or without internal dots (an asset ID/timestamp/version fragment
# in a raw blob is always just digits, e.g. "20220303", "060600", "0.0.0").
BLOB_VERSION_RE = re.compile(r'^(?:v\.?\d+(?:[._]\d+){0,3}[a-z]?\.?|\d+(?:[._]\d+)*[a-z]?)$', re.I)
# Kind 2 (already-spaced name) version token: must look explicitly like a
# version (v-prefixed, or a bare number with an internal dot/underscore
# separator) -- a bare integer alone ("1930s", "808", "1984") is NEVER
# treated as a version here, since those are meaningful in a real title.
SPACED_VERSION_RE = re.compile(r'^(?:v\.?\d+(?:[._]\d+){0,3}[a-z]?\.?|\d+(?:[._]\d+)+[a-z]?)$', re.I)
IDNUM_RE = re.compile(r'^\d{2,8}$')
TIMESTAMP_RE = re.compile(r'^\d{8}-\d{6}$')
# Pure product/plugin-format boilerplate -- never meaningful title content.
# Deliberately does NOT include words like "free"/"edition"/"lite"/"demo"/
# "preset": those describe the release itself (a free/lite/demo tier, a
# named "Free Edition") and are useful, real information to keep.
BOILERPLATE = {
    'decentsampler', 'ds', 'dspreset', 'kontakt', 'nki', 'decent',
    'sampler', 'exs',
}
# Tokens that are boilerplate ONLY when the whole bracket-group reduces to them
BRACKET_BOILERPLATE = {'ds', 'decentsampler', 'decent', 'sampler', 'exs', 'kontakt'}


def _bracket_repl(m):
    inner = m.group(2)
    toks = re.split(r'[\s_/,+]+', inner.strip())
    toks = [t for t in toks if t]
    if toks and all(
        re.match(r'^\d+$', t) or BLOB_VERSION_RE.match(t)
        or t.lower().strip('.') in BRACKET_BOILERPLATE
        for t in toks
    ):
        # Boilerplate, a version marker, or a bare "(1)"/"(2)" variant
        # number -- drop the whole group.
        return ''
    # Not boilerplate -- keep the content but drop the brackets themselves
    # (e.g. "[ESSENTIAL EDITION]" -> "ESSENTIAL EDITION") rather than leave
    # stray "[" "]" characters in the display name.
    return inner


def _strip_boilerplate_brackets(name: str) -> str:
    name = re.sub(r'(\()([^()]*)(\))', _bracket_repl, name)
    name = re.sub(r'(\[)([^\[\]]*)(\])', _bracket_repl, name)
    return re.sub(r'\s+', ' ', name).strip()


def _camel_split(word: str) -> str:
    if word.isupper() or word.islower() or word.isdigit():
        return word
    # digit-run -> letter boundary: "12Oscillator" -> "12 Oscillator", but
    # keep digit+lowercase glued ("3dPrinted" -> "3d Printed", "9000ft" ->
    # "9000ft") since that's normally an abbreviation, not a word break.
    word = re.sub(r'(\d)([A-Z])', r'\1 \2', word)
    word = re.sub(r'([A-Za-z])(\d)', r'\1 \2', word)
    # acronym run followed by a Titlecase word: "NFOAlternative" -> "NFO Alternative"
    word = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', word)
    # lowercase -> Uppercase boundary: "pitchedElectric" -> "pitched Electric"
    word = re.sub(r'([a-z])([A-Z])', r'\1 \2', word)
    return word


def _words_for(name: str):
    """Split into (words, had_space). Underscores are always a separator.
    A hyphen is only a separator when the raw name has no spaces of its
    own -- otherwise it's presumed to be inside a deliberately-formatted
    token (e.g. "Jupiter-6", "X-99B", "NTS-2") and kept intact."""
    had_space = ' ' in name
    pattern = r'[_\s]+' if had_space else r'[_\-\s]+'
    words = [w for w in re.split(pattern, name) if w]
    return words, had_space


def _core_words(raw: str):
    """Shared first pass: bracket-boilerplate stripped, leading ID dropped
    (raw blobs only), version/timestamp/boilerplate words filtered out
    (rules depend on whether this is a raw blob or an already-spaced
    name). Returns (words, had_space)."""
    name = _strip_boilerplate_brackets(raw.strip())
    words, had_space = _words_for(name)

    if had_space:
        # Version/timestamp tokens are safe to drop wherever they appear.
        # A plain boilerplate word ("DS", "Kontakt"...) is only dropped
        # from the very end -- a "Title ... DS" suffix is almost always
        # a redundant format tag, but the same word earlier in the name
        # (e.g. "DS + VT - Altstrings Free Edition", a joint pack name)
        # is part of the actual title and must not be torn out.
        kept = [w for w in words if not (SPACED_VERSION_RE.match(w) or TIMESTAMP_RE.match(w))]
        while kept and kept[-1].lower().strip('.') in BOILERPLATE:
            kept.pop()
    else:
        # leading numeric asset ID -- only meaningful for raw blobs, where
        # the "NNNNN_Title_..." shape is a Pianobook/export convention
        while words and IDNUM_RE.match(words[0]):
            words.pop(0)
        kept = [
            w for w in words
            if not (BLOB_VERSION_RE.match(w) or TIMESTAMP_RE.match(w)
                    or w.lower().strip('.') in BOILERPLATE)
        ]
    words = kept if kept else words
    return words, had_space


def clean_name(raw: str, corpus_trailing_freq: dict) -> tuple[str, bool]:
    """Returns (cleaned, needs_review). needs_review True only for
    genuinely uncertain results (a leftover underscore, a long bare digit
    run, or an empty/too-short result) -- NOT for ordinary punctuation
    (apostrophes, hyphens-as-subtitle-separators, accented letters,
    parenthetical descriptors) which are perfectly valid in a name."""
    words, had_space = _core_words(raw)

    # Drop a trailing author-like word only if it recurs heavily across the
    # corpus (a real "prolific author" signature) AND the raw name was a
    # raw blob in the first place -- that "ID_Title_Author_Boilerplate"
    # shape is exclusively a feature of raw folder-name dumps. A name that
    # already uses spaces is a deliberately-formatted display name; its
    # last word is almost always part of the real title (Piano, Drums,
    # Bowl, Pack...), not an appended author, and dropping it would be
    # destructive.
    AUTHOR_FREQ_THRESHOLD = 5
    if not had_space and len(words) >= 2:
        last_norm = words[-1].lower()
        if corpus_trailing_freq.get(last_norm, 0) >= AUTHOR_FREQ_THRESHOLD:
            words = words[:-1]

    if had_space:
        # Already a deliberately-formatted display name -- keep tokens as
        # authored (no camelCase/digit splitting), just drop junk words,
        # and drop a now-dangling trailing separator ("Title -" after its
        # "- Decent Sampler" suffix was removed).
        while words and words[-1] in ('-', '&', '+'):
            words.pop()

        # Whole-name case normalization -- but ONLY when the name reads as
        # a genuinely shouted/all-lowercase-typed phrase (has a real,
        # length > 3 word in it), not a couple of short acronyms/codes
        # ("YE C55" must stay as-is). Checked on the words BEFORE any
        # partial fix below, so e.g. "curly - electric piano" (entirely
        # lowercase) is recognized and Title-Cased as a whole.
        alpha_words = [w for w in words if w.isalpha()]
        has_real_word = any(len(w) > 3 for w in alpha_words)
        all_upper = bool(alpha_words) and has_real_word and all(w.isupper() for w in alpha_words)
        all_lower = bool(alpha_words) and has_real_word and all(w.islower() for w in alpha_words)

        if all_upper or all_lower:
            cleaned = ' '.join(words).title()
        else:
            # A name that's already a normal mix of cases (e.g. "Beyond
            # the Strings") is left untouched -- real connector words
            # ("the", "and", "of") already correctly lowercase are never
            # force-capitalized. The one targeted exception: a lowercase
            # tail after a "Title - attribution" separator (e.g. "Milk
            # Factory - jd cheetham") is a lowercase-typed author/credit,
            # not a connector word -- proper-case it.
            if '-' in words:
                i = len(words) - 1 - words[::-1].index('-')
                tail = words[i + 1:]
                if tail and all(w.isalpha() and w.islower() for w in tail):
                    words[i + 1:] = [w.capitalize() for w in tail]
            # Still fix an individual ALL-CAPS word sitting among
            # otherwise normal-case words (e.g. "Synth FREE" -> "Synth
            # Free") -- length > 3 only, so short acronyms (NFO, CH, MG)
            # and codes with digits (C55) are left alone.
            words = [
                w.capitalize() if (w.isalpha() and w.isupper() and len(w) > 3) else w
                for w in words
            ]
            cleaned = ' '.join(words)
    else:
        cleaned = ' '.join(_camel_split(w) for w in words)
        cleaned = ' '.join(cleaned.split())
        # re-glue single-letter version markers split apart above: "V 2" -> "V2"
        cleaned = re.sub(r'\b([A-Za-z]) (\d+)\b', r'\1\2', cleaned)
        # Raw blobs have no real-language connector words to protect, so
        # simply Title-Case any still-all-caps (len > 3) or all-lowercase
        # leftover word (a stylistic quirk of the original filename).
        cleaned = ' '.join(
            w.capitalize() if (w.isalpha() and (w.islower() or (w.isupper() and len(w) > 3))) else w
            for w in cleaned.split(' ')
        )

    cleaned = cleaned.strip()
    if not cleaned:
        cleaned = raw.strip()

    # needs_review: only for signs the cleanup didn't fully resolve -- a
    # leftover underscore, or a long (3+) bare digit run with a real word
    # boundary on both sides (an unclear ID, not a year/model number like
    # "1930s" or "X-99B"). Ordinary punctuation is fine and NOT flagged.
    needs_review = bool(re.search(r'_|\b\d{3,}\b', cleaned)) or len(cleaned) < 3
    return cleaned, needs_review


def trailing_freq(names: list[str]) -> dict:
    """Pre-pass: after ID/version/timestamp/boilerplate stripping, count how
    often each candidate trailing word recurs (raw-blob names only) --
    used to detect author blobs vs one-off title words."""
    freq: dict[str, int] = {}
    for raw in names:
        words, had_space = _core_words(raw)
        if not had_space and len(words) >= 2:
            freq[words[-1].lower()] = freq.get(words[-1].lower(), 0) + 1
    return freq
