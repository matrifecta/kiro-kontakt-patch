#!/usr/bin/env python3
"""Replace blank PNG path glyphs with themed inline SVGs. Do not touch cover CSS."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

OLD_FN = """function ensurePathIconGlyph(btn,kind){
  if(!btn)return;
  var src=catalogPathIconSrc(kind);
  if(!src)return;
  var img=btn.querySelector('.path-icon-glyph');
  if(!img){
    img=document.createElement('img');
    img.className='path-icon-glyph';
    img.alt='';
    img.draggable=false;
    btn.appendChild(img);
  }
  if(img.getAttribute('src')!==src)img.setAttribute('src',src);
}"""

NEW_FN = r"""function ensurePathIconGlyph(btn,kind){
  if(!btn)return;
  var svg=btn.querySelector('svg.path-icon-glyph');
  var img=btn.querySelector('img.path-icon-glyph');
  if(img)img.remove();
  var d=kind==='folder'
    ?'<path d="M3 8.2A2.2 2.2 0 0 1 5.2 6h4.1l1.7 1.8h7.8A2.2 2.2 0 0 1 21 10v7.8A2.2 2.2 0 0 1 18.8 20H5.2A2.2 2.2 0 0 1 3 17.8V8.2z"/>'
    :(kind==='copy'
    ?'<rect x="8" y="8" width="12" height="12" rx="2.4"/><rect x="4" y="4" width="12" height="12" rx="2.4"/>'
    :'<rect x="3.6" y="3.6" width="16.8" height="16.8" rx="4.2"/><path d="M12 7.2v9.6"/><path d="M8.8 9.4 12 6.8 15.2 9.4"/><path d="M8.8 14.6 12 17.2 15.2 14.6"/>');
  var html='<svg class="path-icon-glyph" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'+d+'</svg>';
  if(!svg){btn.insertAdjacentHTML('beforeend',html);}
  else if(svg.getAttribute('data-kind')!==kind){svg.outerHTML=html;svg=btn.querySelector('svg.path-icon-glyph');}
  svg=btn.querySelector('svg.path-icon-glyph');
  if(svg)svg.setAttribute('data-kind',kind);
}"""

OLD_CSS = """.path-icon-btn .path-icon-glyph{
  display:block!important;width:64%!important;height:64%!important;object-fit:contain!important;
  pointer-events:none!important;opacity:.82!important;
  filter:brightness(0) saturate(100%) invert(58%) sepia(8%) saturate(420%) hue-rotate(169deg) brightness(95%) contrast(88%)!important
}
.path-icon-btn:hover .path-icon-glyph,.path-icon-btn:focus-visible .path-icon-glyph{
  opacity:1!important;
  filter:brightness(0) saturate(100%) invert(72%) sepia(68%) saturate(1200%) hue-rotate(359deg) brightness(101%) contrast(101%)!important
}"""

NEW_CSS = """/* fix-PATH-SVG-ICONS: stroke glyphs, no white-bg PNG filter */
.path-icon-btn .path-icon-glyph, .path-icon-btn svg.path-icon-glyph{
  display:block!important;width:62%!important;height:62%!important;
  pointer-events:none!important;opacity:.92!important;filter:none!important;
  color:inherit!important;stroke:currentColor!important;fill:none!important
}
.path-icon-btn:hover .path-icon-glyph,.path-icon-btn:focus-visible .path-icon-glyph{
  opacity:1!important;filter:none!important
}"""


def patch(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    n = path.name
    if t.count(OLD_FN) != 1:
        raise SystemExit(f"{n}: ensurePathIconGlyph count {t.count(OLD_FN)}")
    t = t.replace(OLD_FN, NEW_FN, 1)
    if OLD_CSS in t:
        t = t.replace(OLD_CSS, NEW_CSS, 1)
    elif "fix-PATH-SVG-ICONS" not in t:
        raise SystemExit(f"{n}: glyph CSS missing")
    raw = t.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    if not tmp.read_bytes().decode("utf-8").strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated")
    tmp.replace(path)
    print("OK", n, len(raw))


def main() -> None:
    for p in FILES:
        patch(p)


if __name__ == "__main__":
    main()
