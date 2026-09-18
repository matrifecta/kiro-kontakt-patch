"""Deterministic name-cleaning helpers for catalog entry names.

Strategy: strip known junk (asset IDs, version tags, timestamps,
DecentSampler/DS/Kontakt boilerplate), then drop a trailing author-name
segment ONLY if that exact segment recurs as a trailing segment across
2+ other entries in the same corpus (so genuinely unique title words are
never mistaken for an author blob). Finally split camelCase/acronym runs
into readable words.
"""
import re

VERSION_RE = re.compile(r'^v?\d+(?:[._]\d+){0,3}[a-z]?$', re.I)
IDNUM_RE = re.compile(r'^\d{2,8}$')
TIMESTAMP_RE = re.compile(r'^\d{8}-\d{6}$')
BOILERPLATE = {
    'decentsampler', 'ds', 'dspreset', 'kontakt', 'nki', 'decent',
    'sampler', 'exs', 'free', 'edition', 'lite', 'demo', 'preset', 'v1',
}
# Tokens that are boilerplate ONLY when the whole paren-group reduces to them
PAREN_BOILERPLATE = {'ds', 'decentsampler', 'decent', 'sampler', 'exs', 'kontakt'}


def _strip_boilerplate_parens(name: str) -> str:
    def repl(m):
        inner = m.group(1)
        toks = re.split(r'[\s_/,+]+', inner.strip())
        toks = [t for t in toks if t]
        if toks and all(
            VERSION_RE.match(t) or t.lower().strip('.') in PAREN_BOILERPLATE
            for t in toks
        ):
            return ''
        return m.group(0)
    return re.sub(r'\(([^()]*)\)', repl, name).strip()


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


def clean_name(raw: str, corpus_trailing_freq: dict) -> tuple[str, bool]:
    """Returns (cleaned, needs_review). needs_review True if the result
    still contains digits/special chars or looks too short/uncertain."""
    name = raw.strip()
    name = _strip_boilerplate_parens(name)
    # Only treat '_'/'-' as separators when there are no real spaces already,
    # OR when they sit around underscores specifically (underscores are
    # never meaningful in these datasets).
    has_space = ' ' in name
    if has_space:
        segs = re.split(r'_+', name)
    else:
        segs = re.split(r'[_\-]+', name)
    segs = [s for s in segs if s != '']

    # strip leading numeric ID
    while segs and IDNUM_RE.match(segs[0]):
        segs.pop(0)
    # strip version / timestamp / boilerplate tokens anywhere (but keep at
    # least one segment)
    kept = []
    for s in segs:
        low = s.lower().strip('.')
        if VERSION_RE.match(s) or TIMESTAMP_RE.match(s) or low in BOILERPLATE:
            continue
        kept.append(s)
    segs = kept if kept else segs

    # drop a trailing author-like segment only if it recurs heavily across
    # the corpus (a real "prolific author" signature) -- a low threshold
    # produces false positives on generic one-off title words like
    # "Piano"/"Organ" that just happen to end two unrelated names.
    AUTHOR_FREQ_THRESHOLD = 5
    if len(segs) >= 2:
        last_norm = segs[-1].lower()
        if corpus_trailing_freq.get(last_norm, 0) >= AUTHOR_FREQ_THRESHOLD:
            segs = segs[:-1]

    words = []
    for s in segs:
        for w in s.split(' '):
            if w:
                words.append(_camel_split(w))
    cleaned = ' '.join(' '.join(words).split())
    # re-glue single-letter version markers split apart above: "V 2" -> "V2"
    cleaned = re.sub(r'\b([A-Za-z]) (\d+)\b', r'\1\2', cleaned)
    # Title-case only ALL-lowercase or ALL-caps single tokens (leave mixed
    # case / existing capitalization alone since it's often already fine)
    parts = cleaned.split(' ')
    fixed = []
    for p in parts:
        if p.isupper() and len(p) > 3:
            fixed.append(p.capitalize())
        elif p.islower():
            fixed.append(p.capitalize())
        else:
            fixed.append(p)
    cleaned = ' '.join(fixed).strip()
    if not cleaned:
        cleaned = raw.strip()

    needs_review = bool(re.search(r'[^A-Za-z0-9 \'&]', cleaned)) or len(cleaned) < 3
    return cleaned, needs_review


def trailing_freq(names: list[str]) -> dict:
    """Pre-pass: after ID/version/timestamp/boilerplate stripping, count how
    often each candidate trailing segment recurs -- used to detect author
    blobs vs one-off title words."""
    freq: dict[str, int] = {}
    for raw in names:
        name = _strip_boilerplate_parens(raw.strip())
        has_space = ' ' in name
        segs = re.split(r'_+', name) if has_space else re.split(r'[_\-]+', name)
        segs = [s for s in segs if s]
        while segs and IDNUM_RE.match(segs[0]):
            segs.pop(0)
        kept = []
        for s in segs:
            low = s.lower().strip('.')
            if VERSION_RE.match(s) or TIMESTAMP_RE.match(s) or low in BOILERPLATE:
                continue
            kept.append(s)
        segs = kept if kept else segs
        if len(segs) >= 2:
            freq[segs[-1].lower()] = freq.get(segs[-1].lower(), 0) + 1
    return freq
