#!/usr/bin/env python3
"""Follow-up: cancel jump smooth-scroll; park History button; keep menu open."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh",
]


def once(text, old, new, label, path):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{path.name}: {label} count={n} expected 1")
    return text.replace(old, new, 1)


PARK_OLD = """function parkHistoryCloud(){
  var cloud=historyCloudEl();
  if(cloud&&cloud.parentNode!==document.body)document.body.appendChild(cloud);
  return cloud;
}
"""
PARK_NEW = """function parkHistoryCloud(){
  var wrap=document.getElementById('searchHistoryWrap');
  var strip=document.getElementById('searchStrip');
  var clr=strip&&strip.querySelector('.search-strip-clear');
  if(wrap&&strip&&wrap.parentElement!==strip){
    if(clr&&clr.nextSibling)strip.insertBefore(wrap,clr.nextSibling);
    else strip.appendChild(wrap);
  }
  var cloud=historyCloudEl();
  if(cloud&&cloud.parentNode!==document.body)document.body.appendChild(cloud);
  return cloud;
}
"""

SHOW_OLD = """function showHistoryCloud(){
  var cloud=historyCloudEl(),btn=historyBtnEl();
  if(!cloud||!btn)return;
  cloud=parkHistoryCloud()||cloud;
  if(typeof renderHistoryPicks==='function')renderHistoryPicks();
  cloud.hidden=false;
  window.__histIgnoreUntil=Date.now()+400;
  btn.setAttribute('aria-expanded','true');
  placeHistoryCloud();
"""
SHOW_NEW = """function showHistoryCloud(){
  var cloud=historyCloudEl(),btn=historyBtnEl();
  cloud=parkHistoryCloud()||cloud;
  if(!cloud)return;
  if(typeof renderHistoryPicks==='function')renderHistoryPicks();
  cloud.hidden=false;
  window.__histIgnoreUntil=Date.now()+800;
  if(btn)btn.setAttribute('aria-expanded','true');
  placeHistoryCloud();
"""

PLACE_OLD = """  if(!cloud||!btn||cloud.hidden)return;
"""
PLACE_NEW = """  if(!cloud||cloud.hidden)return;
  if(!btn){cloud.style.left='12px';cloud.style.top='72px';return;}
"""

GOTOP_OLD = """    if(cm){try{cm.scrollTo({top:0,behavior:'smooth'});}catch(err){cm.scrollTop=0;}}
"""
GOTOP_NEW = """    if(cm){try{cm.scrollTo({top:cm.scrollTop,behavior:'instant'});}catch(err){cm.scrollTop=cm.scrollTop;}try{cm.scrollTo({top:0,behavior:'smooth'});}catch(err){cm.scrollTop=0;}}
"""

GOBOT_OLD = """    if(cm){try{cm.scrollTo({top:cm.scrollHeight,behavior:'smooth'});}catch(err){cm.scrollTop=cm.scrollHeight;}}
"""
GOBOT_NEW = """    if(cm){try{cm.scrollTo({top:cm.scrollTop,behavior:'instant'});}catch(err){cm.scrollTop=cm.scrollTop;}try{cm.scrollTo({top:cm.scrollHeight,behavior:'smooth'});}catch(err){cm.scrollTop=cm.scrollHeight;}}
"""


def patch(path: Path):
    text = path.read_text(encoding="utf-8")
    if "behavior:'instant'" in text and "if(!btn){cloud.style.left='12px'" in text:
        print(f"SKIP already patched {path}")
        return
    text = once(text, PARK_OLD, PARK_NEW, "park-hist-btn", path)
    text = once(text, SHOW_OLD, SHOW_NEW, "show-hist", path)
    text = once(text, PLACE_OLD, PLACE_NEW, "place-hist", path)
    text = once(text, GOTOP_OLD, GOTOP_NEW, "go-top", path)
    text = once(text, GOBOT_OLD, GOBOT_NEW, "go-bot", path)
    path.write_text(text, encoding="utf-8")
    print(f"OK {path}")


def main():
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)
    print("all ok")


if __name__ == "__main__":
    main()
