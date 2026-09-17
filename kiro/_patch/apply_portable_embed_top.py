#!/usr/bin/env python3
"""Portable portrait embed: park back/fs/min on the title border."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

CSS_MARK = "</style></head><body class=\"search-mode\">"
CSS_ADD = r"""
/* fix-PORTABLE-EMBED-TOP: back/fs/min on portrait title border; card below header */
@media(orientation:portrait){
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight){
    top:var(--cat-header-h,5.5rem)!important;transform:none!important;left:0!important;right:0!important;
    width:100%!important;max-width:none!important;
    height:calc(100dvh - var(--cat-header-h,5.5rem))!important;max-height:none!important;
    padding-top:.4rem!important
  }
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-start .fav-btn{
    display:none!important
  }
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .preview-back{
    position:fixed!important;top:max(.2rem,env(safe-area-inset-top,0px))!important;
    left:max(.2rem,env(safe-area-inset-left,0px))!important;right:auto!important;bottom:auto!important;
    z-index:10060!important;display:flex!important;
    width:2.1rem!important;height:2.1rem!important;min-width:2.1rem!important;min-height:2.1rem!important
  }
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .hl-min{
    position:fixed!important;top:max(.2rem,env(safe-area-inset-top,0px))!important;
    right:max(.2rem,env(safe-area-inset-right,0px))!important;left:auto!important;bottom:auto!important;
    z-index:10060!important;display:flex!important;
    width:2.1rem!important;height:2.1rem!important;min-width:2.1rem!important;min-height:2.1rem!important
  }
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .fs-btn{
    position:fixed!important;top:max(.2rem,env(safe-area-inset-top,0px))!important;
    right:calc(max(.2rem,env(safe-area-inset-right,0px)) + 2.1rem + .28rem)!important;
    left:auto!important;bottom:auto!important;z-index:10060!important;display:flex!important;
    width:2.1rem!important;height:2.1rem!important;min-width:2.1rem!important;min-height:2.1rem!important
  }
}
""" + CSS_MARK

LOG_OLD = """  cardSearchShowEmbedHint();
  return true;
}"""

LOG_NEW = """  cardSearchShowEmbedHint();
  // #region agent log
  try{
    var _b=function(n){if(!n)return null;var r=n.getBoundingClientRect();var cs=getComputedStyle(n);return {t:Math.round(r.top),l:Math.round(r.left),b:Math.round(r.bottom),r:Math.round(r.right),d:cs.display,p:cs.position};};
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'O',location:'catalog:openCardSearchEmbed',message:'embed chrome vs header',data:{portable:!!window.CATALOG_PORTABLE,orient:window.matchMedia&&window.matchMedia('(orientation:portrait)').matches?'port':'land',vw:innerWidth,vh:innerHeight,preview:document.body.classList.contains('chosen-preview-open'),embed:document.body.classList.contains('card-embed-open'),back:_b(document.querySelector('.entry.selected .preview-back,.preview-back')),fs:_b(document.querySelector('.entry.selected .fs-btn,.fs-btn')),min:_b(document.querySelector('.entry.selected .hl-min,.hl-min')),h1:_b(document.querySelector('h1#top')),s:_b(document.getElementById('hdrSearchBtn')),k:_b(document.getElementById('hdrKwBtn')),embedBack:_b(document.querySelector('.card-search-back')),embedFs:_b(document.querySelector('.card-search-fs'))},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgO){}
  // #endregion
  return true;
}"""


def patch(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    n = path.name
    if "fix-PORTABLE-EMBED-TOP" not in t:
        if t.count(CSS_MARK) != 1:
            raise SystemExit(f"{n}: css mark {t.count(CSS_MARK)}")
        t = t.replace(CSS_MARK, CSS_ADD, 1)
    if "hypothesisId:'O'" not in t:
        if t.count(LOG_OLD) != 1:
            raise SystemExit(f"{n}: log mark {t.count(LOG_OLD)}")
        t = t.replace(LOG_OLD, LOG_NEW, 1)
    out = t.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(out)
    if not tmp.read_bytes().decode("utf-8").strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated")
    tmp.replace(path)
    print("OK", n, "bytes", len(out))


def main() -> None:
    for p in FILES:
        patch(p)


if __name__ == "__main__":
    main()
