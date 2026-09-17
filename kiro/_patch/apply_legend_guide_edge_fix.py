#!/usr/bin/env python3
"""Move Legend/Guide CSS out of min-width 900px; fix phone FS, icons, kind leftover."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG-portable.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
]

CSS_END = ".catalog-help-body code{font-size:.85em;background:var(--bg);border:1px solid var(--border);border-radius:4px;padding:.05em .3em}\n"

CSS_NEW = r'''/* fix-LEGEND-GUIDE-EDGE: left-border Legend/Guide widgets on the content pane */
#catalogEdgeStack{display:none;position:fixed;z-index:41;flex-direction:column;align-items:flex-start;gap:.4rem;pointer-events:none;width:0;overflow:visible}
body.display-sides #catalogEdgeStack,body.display-middle #catalogEdgeStack{display:flex}
#catalogEdgeStack .catalog-edge-btn,.catalog-edge-btn{pointer-events:auto;box-sizing:border-box;flex:0 0 auto;width:2.55rem!important;height:2.55rem!important;min-width:2.55rem!important;min-height:2.55rem!important;padding:0!important;margin:0;display:inline-flex!important;align-items:center;justify-content:center;border:1px solid var(--border)!important;border-left-width:0!important;border-radius:0 8px 8px 0!important;background:var(--bg-card)!important;color:var(--text)!important;cursor:pointer;touch-action:manipulation;transform:translateX(.42rem);transition:transform .16s ease,color .16s ease,border-color .16s ease,background .16s ease;box-shadow:4px 0 10px rgba(0,0,0,.18)}
.catalog-edge-btn svg{width:1.4rem!important;height:1.4rem!important;display:block;pointer-events:none;color:inherit;stroke:currentColor;fill:none}
.catalog-edge-btn:hover,.catalog-edge-btn:focus-visible{color:var(--accent-instrument)!important;border-color:var(--accent-instrument)!important;background:var(--accent-instrument-bg)!important;outline:none}
.catalog-edge-btn[aria-pressed="true"]{transform:translateX(1.05rem);color:var(--accent-instrument)!important;border-color:var(--accent-instrument)!important;background:var(--accent-instrument-bg)!important}
body:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open):not(.catalog-help-open):not(.catalog-help-fs) #catalogEdgeStack{visibility:hidden!important;pointer-events:none!important}
body.catalog-help-open #catalogEdgeStack,body.catalog-help-fs #catalogEdgeStack{z-index:10060;display:flex!important}
.catalog-help-card{display:none;position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:840;box-sizing:border-box;width:min(86vw,70rem);height:auto;min-height:min(52vh,26.25rem);max-width:min(86vw,70rem);max-height:min(88vh,53.75rem);margin:0;padding:0;overflow:hidden;flex-direction:column;background:var(--bg-card);color:var(--text);border:1px solid var(--border);border-radius:8px;box-shadow:0 18px 56px rgba(0,0,0,.5);isolation:isolate}
body.catalog-help-open .catalog-help-card,body.catalog-help-fs .catalog-help-card{display:flex!important}
body.catalog-help-open:not(.catalog-help-fs)::before{content:"";position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:830;pointer-events:none}
body.catalog-help-fs{overflow:hidden}
body.catalog-help-fs .catalog-help-card{inset:0!important;left:0!important;top:0!important;right:0!important;bottom:0!important;transform:none!important;width:100%!important;height:100%!important;max-width:none!important;max-height:none!important;min-height:100%!important;border-radius:0;z-index:10050!important;padding-top:var(--safe-top);padding-bottom:var(--safe-bottom);background:var(--bg)!important}
body.catalog-help-fs .catalog-header,body.catalog-help-fs .hdr-bar-toggle{visibility:hidden!important;pointer-events:none!important}
.catalog-help-chrome{display:flex;align-items:center;gap:.4rem;flex:0 0 auto;min-height:calc(var(--card-chrome-btn) + 1rem);padding:.5rem .6rem .35rem;border-bottom:1px solid var(--border);background:var(--bg-surface);box-sizing:border-box}
.catalog-help-back,.catalog-help-fs-btn{box-sizing:border-box;width:var(--card-chrome-btn);height:var(--card-chrome-btn);min-width:var(--card-chrome-btn);min-height:var(--card-chrome-btn);display:inline-flex;align-items:center;justify-content:center;padding:0;border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:1.375rem;line-height:1;flex:0 0 auto}
.catalog-help-back{background:var(--bg-card);color:var(--text);border:1px solid var(--border)}
.catalog-help-back:hover{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
.catalog-help-fs-btn{margin-left:auto;background:var(--bg-surface);color:var(--accent-instrument);border:1px solid var(--accent-instrument);font-size:1.25rem}
.catalog-help-fs-btn:hover{color:var(--accent-instrument-active);border-color:var(--accent-instrument-active);background:var(--accent-instrument-bg)}
body.catalog-portable .catalog-help-fs-btn,body.catalog-help-fs .catalog-help-fs-btn{display:none!important}
@media(max-width:899px){.catalog-help-fs-btn{display:none!important}}
.catalog-help-title{flex:1 1 auto;min-width:0;margin:0;font-size:1.05rem;font-weight:650;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.catalog-help-tabs{display:none;flex:1 1 auto;min-width:0;align-items:flex-end;gap:0;height:100%;padding-top:.15rem}
body.catalog-help-kind-guide .catalog-help-tabs{display:flex}
body.catalog-help-kind-guide .catalog-help-title{display:none}
.catalog-help-tab{flex:1 1 0;min-width:0;min-height:2.35rem;margin:0;padding:.35rem .7rem 0;border:1px solid var(--border);border-bottom:0;border-radius:8px 8px 0 0;background:var(--bg);color:var(--text-muted);font:inherit;font-size:.9rem;cursor:pointer;touch-action:manipulation}
.catalog-help-tab[aria-selected="true"]{background:var(--bg-card);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:650;z-index:1}
.catalog-help-body{flex:1 1 auto;min-height:0;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:.7rem .9rem 1.1rem;color:var(--text);font-size:.95rem}
.catalog-help-panel[hidden]{display:none!important}
.catalog-help-body h2{margin:.2rem 0 .55rem;font-size:1.15rem;border:0;padding:0;color:var(--text)}
.catalog-help-body h3{margin:.85rem 0 .3rem;font-size:1rem;color:var(--text)}
.catalog-help-body p,.catalog-help-body li{color:var(--text);font-size:.95rem}
.catalog-help-body .catalog-help-muted{color:var(--text-muted)}
.catalog-help-body details{margin:.45rem 0;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);padding:.15rem .7rem .45rem}
.catalog-help-body summary{cursor:pointer;font-weight:650;min-height:2.15rem;display:flex;align-items:center;color:var(--text);touch-action:manipulation}
.catalog-help-body code{font-size:.85em;background:var(--bg);border:1px solid var(--border);border-radius:4px;padding:.05em .3em}
'''

SVG_GUIDE_OLD = """    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.55" stroke-linecap="round" stroke-linejoin="round">
      <path d="M5.2 4.8h10.1c.9 0 1.7.8 1.7 1.7v11.4H6.7c-.8 0-1.5.5-1.5 1.4V6.5c0-.9.8-1.7 1.7-1.7z"/>
      <path d="M5.2 4.8v14.6"/>
      <path d="M8 8.2h6.6M8 10.7h5.1"/>
      <circle cx="17.35" cy="6.7" r="3.2" fill="var(--bg-card)"/>
      <circle cx="17.35" cy="6.7" r="3.2"/>
      <circle cx="17.35" cy="5.5" r=".45" fill="currentColor" stroke="none"/>
      <path d="M17.35 7.15v2.05" stroke-width="1.7"/>
    </svg>"""

SVG_GUIDE_NEW = """    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4.6 5.1h10.4a1.7 1.7 0 0 1 1.7 1.7v11.6H6.2A1.6 1.6 0 0 0 4.6 20V5.1z"/>
      <path d="M4.6 5.1v14.9"/>
      <rect x="7.15" y="7.35" width="7.6" height="7.1" rx=".7"/>
      <path d="M8.6 9.7h4.6M8.6 11.7h3.5"/>
      <circle cx="17.6" cy="6.55" r="3.35" fill="var(--bg-card)" stroke="currentColor"/>
      <circle cx="17.6" cy="5.35" r=".42" fill="currentColor" stroke="none"/>
      <path d="M17.6 7.05v2.15" stroke-width="1.7"/>
    </svg>"""

SVG_KEY_OLD = """    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.55" stroke-linecap="round" stroke-linejoin="round">
      <g transform="rotate(-42 12 12)">
        <circle cx="12" cy="5.15" r="2.55"/>
        <circle cx="9.65" cy="8.55" r="2.55"/>
        <circle cx="14.35" cy="8.55" r="2.55"/>
        <circle cx="12" cy="5.15" r=".95"/>
        <circle cx="9.65" cy="8.55" r=".95"/>
        <circle cx="14.35" cy="8.55" r=".95"/>
        <path d="M12 11.1v8.55"/>
        <path d="M12 16.9h2.25"/>
        <path d="M12 19.65h3.05"/>
        <path d="M14.25 16.9v-1.05"/>
        <path d="M15.05 19.65v-1.1"/>
      </g>
    </svg>"""

SVG_KEY_NEW = """    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <g transform="rotate(-38 12.2 12)">
        <circle cx="12.2" cy="5.4" r="2.7"/>
        <circle cx="9.55" cy="9.05" r="2.7"/>
        <circle cx="14.85" cy="9.05" r="2.7"/>
        <circle cx="12.2" cy="5.4" r="1.05"/>
        <circle cx="9.55" cy="9.05" r="1.05"/>
        <circle cx="14.85" cy="9.05" r="1.05"/>
        <path d="M12.2 11.75v8.2"/>
        <path d="M12.2 16.7h2.55v-1.15"/>
        <path d="M12.2 19.95h3.35v-1.2"/>
      </g>
    </svg>"""

SYNC_OLD = """  var kind=window._catalogHelpKind||'legend';
  document.body.classList.toggle('catalog-help-kind-guide',kind==='guide');
  document.body.classList.toggle('catalog-help-kind-legend',kind==='legend');
  var title=document.getElementById('catalogHelpTitle');
  if(title)title.textContent=kind==='guide'?'Guide':'Legend';
"""
SYNC_NEW = """  var open=document.body.classList.contains('catalog-help-open')||document.body.classList.contains('catalog-help-fs');
  var kind=window._catalogHelpKind||'legend';
  document.body.classList.toggle('catalog-help-kind-guide',open&&kind==='guide');
  document.body.classList.toggle('catalog-help-kind-legend',open&&kind==='legend');
  var title=document.getElementById('catalogHelpTitle');
  if(title)title.textContent=kind==='guide'?'Guide':'Legend';
  var tabs=document.getElementById('catalogHelpTabs');
  if(tabs)tabs.hidden=!(open&&kind==='guide');
"""

TABS_OLD = '<div class="catalog-help-tabs" id="catalogHelpTabs" role="tablist" aria-label="Guide">'
TABS_NEW = '<div class="catalog-help-tabs" id="catalogHelpTabs" role="tablist" aria-label="Guide" hidden>'

HIDE_ANCHOR = (
    "body:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open,.catalog-help-open,.catalog-help-fs) .bottom"
    "{visibility:hidden!important;pointer-events:none!important}\n"
)


def once(text, old, new, label, name):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{name}: {label} count={n}")
    return text.replace(old, new, 1)


def patch(path: Path) -> None:
    raw = path.read_bytes()
    orig = len(raw)
    if not raw.rstrip().endswith(b"</html>"):
        raise SystemExit(f"{path.name}: missing html")
    t = raw.decode("utf-8")
    name = path.name
    a = t.find("/* fix-LEGEND-GUIDE-EDGE")
    if a < 0:
        raise SystemExit(f"{name}: marker missing")
    b = t.find(CSS_END, a)
    if b < 0:
        raise SystemExit(f"{name}: css end missing")
    b += len(CSS_END)
    t = t[:a] + t[b:]
    if HIDE_ANCHOR not in t:
        raise SystemExit(f"{name}: hide anchor missing after cut")
    # avoid duplicating if already moved
    if t.count("/* fix-LEGEND-GUIDE-EDGE") != 0:
        raise SystemExit(f"{name}: marker still present after cut")
    t = t.replace(HIDE_ANCHOR, HIDE_ANCHOR + CSS_NEW, 1)
    t = once(t, SVG_GUIDE_OLD, SVG_GUIDE_NEW, "svg-guide", name)
    t = once(t, SVG_KEY_OLD, SVG_KEY_NEW, "svg-key", name)
    t = once(t, SYNC_OLD, SYNC_NEW, "sync-kind", name)
    t = once(t, TABS_OLD, TABS_NEW, "tabs-hidden", name)

    if t.count("/* fix-LEGEND-GUIDE-EDGE") != 1:
        raise SystemExit(f"{name}: marker count {t.count('/* fix-LEGEND-GUIDE-EDGE')}")
    if not t.strip().endswith("</html>"):
        raise SystemExit(f"{name}: truncated")
    out = t.encode("utf-8")
    if orig > 4_000_000 and len(out) < orig * 0.9:
        raise SystemExit(f"{name}: collapsed")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(out)
    wrote = tmp.read_bytes()
    if len(wrote) != len(out) or not wrote.rstrip().endswith(b"</html>"):
        tmp.unlink()
        raise SystemExit(f"{name}: tmp bad")
    tmp.replace(path)
    print("OK", name, "delta", len(out) - orig)


def main():
    for p in FILES:
        patch(p)


if __name__ == "__main__":
    main()
