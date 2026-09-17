#!/usr/bin/env python3
"""Remove debug ingest instrumentation; keep product fixes."""
import re
from pathlib import Path

FILES = [
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh"),
]

ARTIFACT_HTML = [
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/DS-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/KONTAKT-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/DS-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/KONTAKT-CATALOG-portable.html"),
]

DEBUG_FUNCS = [
    "logPickLock",
    "logSidesRestore",
    "logModeIndep",
    "logLayoutModes",
    "logSidesEdit",
    "logDisplayOrient",
    "logMiddleLayout",
    "logSidesGeom",
    "logNestFix",
    "logPortraitSides",
    "dbgCoverStats",
    "dbgCoverCensus",
    "dbgCoverStripe",
    "dbgKwPane",
    "dbgIndexGate",
    "dbgIndexAc",
    "dbgIndexWin",
    "handleSnap",
    "hitLog",
]

BAN = [
    "7529/ingest",
    "#region agent log",
    "X-Debug-Session-Id",
    "c00e3e",
    "f491c2",
    "logPickLock",
    "dbgCoverStats",
    "dbgCoverCensus",
    "dbgCoverStripe",
    "dbgKwPane",
    "dbgIndexGate",
    "dbgIndexAc",
    "_dbgC00e3eClick",
    "logNestFix",
]

KEEP = [
    "_pinSessAcBind",
    "_acItemPointer",
    "fillAcGroupQuery",
    "matchingAcGroupLabel",
    "acGroupQuery",
]

START_RE = re.compile(r"[ \t]*// #region agent log[^\n]*\n")
END_RE = re.compile(r"[ \t]*// #endregion[^\n]*\n?")


def skip_string(text, i):
    q = text[i]
    i += 1
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == q:
            return i + 1
        if q != "`" and c == "\n":
            return i
        i += 1
    return n


def find_matching(text, open_idx):
    open_ch = text[open_idx]
    close_ch = {"(": ")", "{": "}", "[": "]"}[open_ch]
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        if c == "/" and i + 1 < n:
            nxt = text[i + 1]
            if nxt == "/":
                nl = text.find("\n", i)
                i = n if nl < 0 else nl
                continue
            if nxt == "*":
                end = text.find("*/", i + 2)
                i = n if end < 0 else end + 2
                continue
        if c in "'\"`":
            i = skip_string(text, i)
            continue
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def skip_ws(text, i, direction=-1):
    n = len(text)
    if direction < 0:
        while i > 0 and text[i - 1] in " \t":
            i -= 1
    else:
        while i < n and text[i] in " \t":
            i += 1
    return i


def strip_regions(text):
    guard = 0
    while guard < 20000:
        guard += 1
        starts = list(START_RE.finditer(text))
        if not starts:
            text2, n = END_RE.subn("", text)
            if n:
                text = text2
                continue
            break
        removed = False
        for m in reversed(starts):
            em = END_RE.search(text, m.end())
            if not em:
                text = text[: m.start()] + text[m.end() :]
                removed = True
                break
            inner = START_RE.search(text, m.end())
            if inner and inner.start() < em.start():
                continue
            text = text[: m.start()] + text[em.end() :]
            removed = True
            break
        if not removed:
            m = starts[0]
            text = text[: m.start()] + text[m.end() :]
    return text


def expand_try_catch_wrap(text, start, end):
    """If fetch is wrapped in try{...}catch(err){}, include the wrapper."""
    s = skip_ws(text, start)
    # allow newline before try
    t = s
    while t > 0 and text[t - 1] in " \t\n":
        t -= 1
        if text[t] == "\n":
            break
    prefix = text[max(0, start - 8) : start]
    try_idx = text.rfind("try{", 0, start)
    if try_idx < 0 or try_idx < start - 24:
        # try{\n  fetch
        try_idx = text.rfind("try{", 0, start)
    if try_idx >= 0 and try_idx >= start - 80:
        between = text[try_idx + 4 : start]
        if between.strip() == "":
            start = skip_ws(text, try_idx)
            rest = text[end:]
            m = re.match(r"\s*\}catch\(err\)\{\}", rest)
            if m:
                end = end + m.end()
    else:
        # inline try{fetch...}catch(err){}
        if prefix.endswith("try{"):
            start = start - 4
            start = skip_ws(text, start)
            rest = text[end:]
            m = re.match(r"\s*\}catch\(err\)\{\}", rest)
            if m:
                end = end + m.end()
    return start, end


def remove_ingest_fetches(text):
    needles = (
        "fetch('http://127.0.0.1:7529/ingest/",
        'fetch("http://127.0.0.1:7529/ingest/',
    )
    guard = 0
    while guard < 20000:
        guard += 1
        pos = -1
        for n in needles:
            p = text.find(n)
            if p >= 0 and (pos < 0 or p < pos):
                pos = p
        if pos < 0:
            break
        paren = text.find("(", pos)
        if paren < 0:
            text = text[:pos] + text[pos + 6 :]
            continue
        end = find_matching(text, paren)
        if end < 0:
            raise SystemExit(f"unbalanced fetch( at {pos}")
        rest = text[end:]
        if rest.startswith(".catch"):
            cp = rest.find("(")
            if cp >= 0:
                cend = find_matching(rest, cp)
                if cend > 0:
                    end = end + cend
                    if end < len(text) and text[end] == ";":
                        end += 1
        elif end < len(text) and text[end] == ";":
            end += 1
        start, end = expand_try_catch_wrap(text, pos, end)
        if start > 0 and text[start - 1] == "\n":
            line_start = text.rfind("\n", 0, start) + 1
            if text[line_start:start].strip() == "":
                start = line_start
        text = text[:start] + text[end:]
    return text


def remove_function(text, name):
    needle = f"function {name}("
    guard = 0
    while guard < 50:
        guard += 1
        j = text.find(needle)
        if j < 0:
            break
        paren = j + len(f"function {name}")
        args_end = find_matching(text, paren)
        if args_end < 0:
            break
        k = args_end
        while k < len(text) and text[k] in " \t\n":
            k += 1
        if k >= len(text) or text[k] != "{":
            text = text[:j] + text[j + len(needle) :]
            continue
        body_end = find_matching(text, k)
        if body_end < 0:
            break
        if body_end < len(text) and text[body_end] == "\n":
            body_end += 1
        start = j
        if start > 0 and text[start - 1] == "\n":
            line_start = text.rfind("\n", 0, start) + 1
            if text[line_start:start].strip() == "":
                start = line_start
        text = text[:start] + text[body_end:]
    text = re.sub(rf"window\.{name}={name};\n?", "", text)
    return text


def include_typeof_if(text, call_start, name):
    needle = f"if(typeof {name}==='function'"
    idx = text.rfind(needle, max(0, call_start - 500), call_start)
    if idx < 0:
        return call_start
    if_paren = idx + 2
    if text[if_paren] != "(":
        return call_start
    cond_end = find_matching(text, if_paren)
    if cond_end < 0:
        return call_start
    if text[cond_end:call_start].strip() != "":
        return call_start
    start = skip_ws(text, idx)
    return start


def remove_calls(text, name):
    token = name + "("
    out = []
    i = 0
    n = len(text)
    guard = 0
    while i < n and guard < 50000:
        guard += 1
        j = text.find(token, i)
        if j < 0:
            out.append(text[i:])
            break
        if j > 0 and (text[j - 1].isalnum() or text[j - 1] in "_$"):
            out.append(text[i : j + len(name)])
            i = j + len(name)
            continue
        before = text[max(0, j - 9) : j]
        if before.endswith("function "):
            out.append(text[i : j + len(name)])
            i = j + len(name)
            continue
        paren = j + len(name)
        end = find_matching(text, paren)
        if end < 0:
            out.append(text[i:])
            break
        if end < n and text[end] == ";":
            end += 1
        start = include_typeof_if(text, j, name)
        if start > 0 and text[start - 1] == "\n":
            line_start = text.rfind("\n", 0, start) + 1
            if text[line_start:start].strip() == "":
                start = line_start
        out.append(text[i:start])
        i = end
    return "".join(out)


DBG_IIFE = re.compile(
    r"\(function\(\)\{\n  if\(window\._dbgC00e3eClick\)return;\n  window\._dbgC00e3eClick=1;.*?\n\}\)\(\);\n",
    re.S,
)

SETTLE_150 = re.compile(
    r"  setTimeout\(function\(\)\{\n    // #region agent log\n    var dock=document.getElementById\('cardMinDock'\);.*?\n  \},150\);\n",
    re.S,
)


def _drop_marker_lines(text, marker):
    if marker not in text:
        return text
    out = []
    for line in text.splitlines(True):
        if marker in line:
            continue
        out.append(line)
    return "".join(out)


def cleanup_leftovers(text):
    # FETCH2 / PICK_CALL tails from an earlier incomplete strip
    text = _drop_marker_lines(text, "timestamp:Date.now()})}).catch(function(){});")
    text = _drop_marker_lines(text, "try{}),frontId:rec.frontId")
    frag = "if(!el)return null;var b=el.getBoundingClientRect();var fp=el.querySelector('.filter-panel');"
    if frag in text:
        i = text.find(frag)
        j = text.find("}()});", i)
        if j >= 0:
            end = j + len("}()});")
            if end < len(text) and text[end] == "\n":
                end += 1
            text = text[:i] + text[end:]
    text = text.replace(
        "  scrollAcGroupToTop(label);\n  try{\n  }catch(err){}\n",
        "  scrollAcGroupToTop(label);\n",
    )
    payload_start = "  scrollAcGroupToTop(label);\n  try{\n    var sc=acScrollRoot();\n"
    while payload_start in text:
        i = text.find(payload_start)
        j = text.find("  }catch(err){}\n", i)
        if j < 0:
            break
        text = text[:i] + "  scrollAcGroupToTop(label);\n" + text[j + len("  }catch(err){}\n") :]
    text = text.replace(
        "if(mode==='sides'||mode==='upper')setTimeout(function(){if(typeof logSidesGeom==='function')logSidesGeom('after-'+mode);},120);",
        "",
    )
    text = text.replace(
        "  if(had&&(had.indexOf('grid-template')>=0||had.indexOf('height')>=0)&&typeof logNestFix==='function')\n",
        "",
    )
    text = text.replace(
        "  requestAnimationFrame(function(){requestAnimationFrame(function(){}\n",
        "",
    )
    text = re.sub(
        r"[ \t]*if\(mode==='sides'\|\|mode==='upper'\)setTimeout\(function\(\)\{\s*\},\s*120\);",
        "",
        text,
    )
    text = re.sub(
        r"if\(typeof reviveEntryCovers==='function'\)reviveEntryCovers\(\);if\(typeof dbgCoverStats==='function'\)dbgCoverStats\('(?:boot|scroll)'\);",
        "if(typeof reviveEntryCovers==='function')reviveEntryCovers();",
        text,
    )
    text = re.sub(
        r"[ \t]*if\(typeof dbgCover(?:Census|Stripe)==='function'\)dbgCover(?:Census|Stripe)\([^;]*\);\n?",
        "",
        text,
    )
    text = re.sub(
        r"[ \t]*if\(typeof dbgKwPane==='function'\)dbgKwPane\([^;]*\);\n?",
        "",
        text,
    )
    text = re.sub(
        r"[ \t]*if\(typeof dbgIndexGate==='function'\)dbgIndexGate\([^;]*\);\n?",
        "",
        text,
    )
    text = text.replace("window.pickAc=function(text){\n// #endregion\n", "window.pickAc=function(text){\n")
    text = re.sub(r"[ \t]*try\{\s*\}catch\(err\)\{\}\n?", "", text)
    text = re.sub(r"[ \t]*setTimeout\(function\(\)\{\s*\},\s*\d+\);\n?", "", text)
    text = re.sub(r"\n[ \t]*;\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def cleanup(text, verbose=False):
    import time
    t0 = time.time()

    def step(label, fn, *args):
        nonlocal text
        s = time.time()
        text = fn(text, *args) if args else fn(text)
        if verbose:
            print(f"  {label}: {time.time()-s:.2f}s len={len(text)}", flush=True)

    step("iife", lambda t: DBG_IIFE.sub("", t))
    step("settle", lambda t: SETTLE_150.sub("", t))
    step("regions1", strip_regions)
    step("fetches1", remove_ingest_fetches)
    for name in DEBUG_FUNCS:
        step("fn " + name, remove_function, name)
        step("call " + name, remove_calls, name)
        step("win " + name, lambda t, n=name: re.sub(rf"window\.{n}={n};\n?", "", t))
    step("leftover1", cleanup_leftovers)
    step("regions2", strip_regions)
    step("fetches2", remove_ingest_fetches)
    step("leftover2", cleanup_leftovers)
    if verbose:
        print(f"  total {time.time()-t0:.2f}s", flush=True)
    return text


def leftover_counts(text):
    return {k: text.count(k) for k in BAN}


def main():
    failed = []
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        print(f"cleaning {path.name} ({len(raw)} bytes)...", flush=True)
        out = cleanup(raw, verbose=False)
        counts = leftover_counts(out)
        missing = [k for k in KEEP if k not in out]
        path.write_text(out, encoding="utf-8")
        bad = {k: n for k, n in counts.items() if n}
        print(f"{path.name}: bytes {len(raw)}->{len(out)} leftover={bad or 0} missing_keep={missing or 0}")
        if bad or missing:
            failed.append(path.name)

    for path in ARTIFACT_HTML:
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        if "7529/ingest" not in raw and "#region agent log" not in raw:
            print(f"{path.name}: skip (no ingest)")
            continue
        out = cleanup(raw)
        counts = leftover_counts(out)
        path.write_text(out, encoding="utf-8")
        bad = {k: n for k, n in counts.items() if n}
        print(f"{path.name}: bytes {len(raw)}->{len(out)} leftover={bad or 0}")
        if bad:
            failed.append(path.name)

    if failed:
        raise SystemExit("leftover debug or missing keep in: " + ", ".join(failed))


if __name__ == "__main__":
    main()
