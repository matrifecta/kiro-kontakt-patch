"""Deterministic cleanup rules for catalog `<p class="desc">` text.

Strips markdown/header/boilerplate cruft from README-derived descriptions.
Does NOT handle translation or semantic removal of engine-mention sentences
embedded in otherwise-meaningful prose -- that's handled by a manual
rewrite pass (see tools/_generated/desc-overrides.json) for entries this
deterministic pass can't safely resolve on its own.
"""
import re

PLACEHOLDER = "No additional description provided."

URL_RE = re.compile(r'https?://\S+')

# Leading "# Name - Version: [1.0] Name: Author" style header line(s).
HEADER_LINE_RE = re.compile(
    r'^\s*#{1,3}\s*\[?[^\n#]*?\]?\s*[-–]?\s*Version:\s*\[?[\w.]+\]?\s*'
    r'(?:Name:\s*[^\n#]+?)?\s*(?=(?:#{1,3}\s|$))',
    re.I,
)
LEADING_TITLE_VERSION_RE = re.compile(
    r'^\s*[\w \'"’.]+?\s*[-–]\s*Version:\s*\[?[\w.]+\]?\s*(?:Name:\s*[^\n#]+?)?\s*(?=(?:#{1,3}\s|$|[A-Z]))',
    re.I,
)

# "## Included formats - Decent Sampler" / "## Release notes" / etc section
# labels, including their immediate engine/format list content.
SECTION_LABEL_RE = re.compile(
    r'#{1,3}\s*(?:Included\s+Formats?|Release\s+Notes?|Presets?\s+Included|'
    r'Formats?\s+Included|Using\s+the\s+Instrument|New)\b[^#]*?'
    r'(?=#{1,3}\s|$)',
    re.I,
)

# Dash-bullet "-Decent Sampler" / "-Formats Included-" style spec lines.
SPEC_BULLET_RE = re.compile(
    r'[-*]{1,2}\s*(?:Decent\s*Sampler|Kontakt|Formats?\s+Included|Presets?\s+Included|The\s+Story)\s*[-*]{0,2}',
    re.I,
)

MARKDOWN_SYMBOLS_RE = re.compile(r'[#*_`]+')

ENGLISH_MARKER_RE = re.compile(r'\*{2,3}\s*ENGLISH VERSION FOLLOWS\s*\*{2,3}', re.I)

EMOJI_RE = re.compile(
    '[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]+'
)

WS_RE = re.compile(r'\s+')
PUNCT_RUN_RE = re.compile(r'\s*[-–—]{2,}\s*')


def strip_markdown_and_links(text: str) -> str:
    text = URL_RE.sub('', text)
    text = ENGLISH_MARKER_RE.sub('', text)
    text = EMOJI_RE.sub('', text)
    text = MARKDOWN_SYMBOLS_RE.sub('', text)
    text = PUNCT_RUN_RE.sub(' ', text)
    text = WS_RE.sub(' ', text).strip()
    return text


HEADING_SPLIT_RE = re.compile(r'#{1,3}\s*([^\n#]+?)\s*(?=#{1,3}\s|$)')

DROP_HEADINGS_RE = re.compile(
    r'^\**\s*(included\s+formats?|release\s+notes?|presets?\s+included|formats?\s+included|'
    r'new|bugfixes?|bug\s*fixes?|development\s+log|changelog|known\s+issues?|credits?|'
    r'license|licence|version\s+history)\b',
    re.I,
)

NATIVE_INSTRUMENTS_PLACEHOLDER_RE = re.compile(
    r'^Native Instruments library:\s*[^.]*\.\s*(?:Tags:.*)?$', re.I,
)


def deterministic_clean(raw: str) -> str:
    """Split on markdown headings; drop the body of any heading that is
    pure boilerplate (Included formats/Release notes/Bugfixes/etc.), keep
    everything else (preamble + all other headings' bodies) as candidate
    narrative text, then strip the remaining header/version line and any
    markdown symbols/links. Does not translate or remove engine-mention
    prose sentences embedded in otherwise-real narrative -- that needs a
    manual pass."""
    parts = HEADING_SPLIT_RE.split(raw)
    if len(parts) < 3:
        t = raw
    else:
        # parts alternates: [preamble, heading1, body1, heading2, body2, ...]
        kept = [parts[0]]
        i = 1
        while i < len(parts) - 1:
            heading, body = parts[i].strip(), parts[i + 1]
            if not DROP_HEADINGS_RE.match(heading):
                kept.append(body)
            i += 2
        t = ' '.join(kept)
    t = HEADER_LINE_RE.sub('', t)
    t = LEADING_TITLE_VERSION_RE.sub('', t)
    t = SPEC_BULLET_RE.sub(' ', t)
    t = strip_markdown_and_links(t)
    return t.strip()
