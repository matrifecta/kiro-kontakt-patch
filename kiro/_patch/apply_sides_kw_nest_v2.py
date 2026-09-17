#!/usr/bin/env python3
"""Desktop Sides: header K opens KW as its own column; collapse arrow toggles nest only."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
]
MARK = "fix-SIDES-KW-NEST-v2"
KEEP = (
    "c00e3e",
    "fix-DESKTOP-SK-PAIR",
    "fix-DESKTOP-FLIP-ARRANGE",
    "fix-SIDES-KW-NEST-v1",
    "fix-SIDES-KW-NEST-v1b",
    MARK,
)

NEST_OLD = """function nestKwWithSearch(){
  if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
  if(!sidesKwCanNest()){
    collapseKwMenu();
    return;
  }
  document.body.classList.remove('kw-chrome-collapsed');
  var w=document.getElementById('filterWrap');
  if(w)w.classList.add('open');
  document.body.classList.add('kw-open','kw-nested-search');
  var a=document.querySelector('#filterToggle .toggle-arrow')||document.querySelector('.toggle-arrow');
  if(a)a.textContent='▲';
  if(typeof syncKwHideBtn==='function')syncKwHideBtn();
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
  logKwNest('nest');
}
"""

NEST_NEW = """function nestKwWithSearch(){
  if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
  if(!sidesKwCanNest()){
    logKwNest('nest-noop');
    return;
  }
  document.body.classList.remove('kw-chrome-collapsed');
  var w=document.getElementById('filterWrap');
  if(w)w.classList.add('open');
  document.body.classList.add('kw-open','kw-nested-search');
  var a=document.querySelector('#filterToggle .toggle-arrow')||document.querySelector('.toggle-arrow');
  if(a)a.textContent='▲';
  if(typeof syncKwHideBtn==='function')syncKwHideBtn();
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
  logKwNest('nest');
}
function unnestKwFromSearch(){
  if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
  document.body.classList.remove('kw-chrome-collapsed','kw-nested-search');
  var w=document.getElementById('filterWrap');
  if(w)w.classList.add('open');
  document.body.classList.add('kw-open');
  var a=document.querySelector('#filterToggle .toggle-arrow')||document.querySelector('.toggle-arrow');
  if(a)a.textContent='▲';
  if(typeof syncKwHideBtn==='function')syncKwHideBtn();
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
  logKwNest('unnest');
}
"""

EXPAND_OLD = """function expandKwMenu(){
  if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
  document.body.classList.remove('kw-chrome-collapsed');
  var w=document.getElementById('filterWrap');
  if(w)w.classList.add('open');
  document.body.classList.add('kw-open');
  if(typeof sidesKwCanNest==='function'&&sidesKwCanNest())document.body.classList.add('kw-nested-search');
  else document.body.classList.remove('kw-nested-search');
  if(typeof noteMiddleMenuOpened==='function')noteMiddleMenuOpened('keywords');
  var a=document.querySelector('#filterToggle .toggle-arrow')||document.querySelector('.toggle-arrow');
  if(a)a.textContent='▲';
  if(typeof syncKwHideBtn==='function')syncKwHideBtn();
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof window.restoreFilterUi==='function')window.restoreFilterUi();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
  logKwNest('expand');
}
function toggleKwChrome(opts){
  opts=opts||{};
  if(!document.body.classList.contains('display-sides')){
    if(typeof toggleFilter==='function')toggleFilter();
    return;
  }
  if(document.body.classList.contains('kw-chrome-collapsed')){
    expandKwMenu();
    return;
  }
  if(opts.fromArrow&&typeof sidesKwCanNest==='function'&&sidesKwCanNest()&&!document.body.classList.contains('kw-nested-search')){
    nestKwWithSearch();
    return;
  }
  collapseKwMenu();
}
"""

EXPAND_NEW = """function expandKwMenu(){
  if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
  document.body.classList.remove('kw-chrome-collapsed','kw-nested-search');
  var w=document.getElementById('filterWrap');
  if(w)w.classList.add('open');
  document.body.classList.add('kw-open');
  if(typeof noteMiddleMenuOpened==='function')noteMiddleMenuOpened('keywords');
  var a=document.querySelector('#filterToggle .toggle-arrow')||document.querySelector('.toggle-arrow');
  if(a)a.textContent='▲';
  if(typeof syncKwHideBtn==='function')syncKwHideBtn();
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof window.restoreFilterUi==='function')window.restoreFilterUi();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
  logKwNest('expand-side');
}
function sidesKwArrowPortrait(){
  if(typeof isPortraitDesktopSides==='function')return isPortraitDesktopSides();
  return !!(window.matchMedia&&window.matchMedia('(min-width:900px)').matches&&window.matchMedia('(orientation:portrait)').matches);
}
function toggleKwChrome(opts){
  opts=opts||{};
  if(!document.body.classList.contains('display-sides')){
    if(typeof toggleFilter==='function')toggleFilter();
    return;
  }
  logKwNest('toggle-enter',opts);
  if(document.body.classList.contains('kw-chrome-collapsed')){
    expandKwMenu();
    return;
  }
  if(opts.fromArrow){
    if(typeof sidesKwCanNest==='function'&&sidesKwCanNest()){
      if(document.body.classList.contains('kw-nested-search'))unnestKwFromSearch();
      else nestKwWithSearch();
      return;
    }
    if(sidesKwArrowPortrait()){
      logKwNest('portrait-hide',{fromArrow:true});
      collapseKwMenu();
      return;
    }
    logKwNest('arrow-noop',{fromArrow:true});
    return;
  }
  collapseKwMenu();
}
"""

EXPORT_OLD = (
    "window.nestKwWithSearch=nestKwWithSearch;\n"
    "window.applySidesNestedH=applySidesNestedH;\n"
)

EXPORT_NEW = (
    "window.nestKwWithSearch=nestKwWithSearch;\n"
    "window.unnestKwFromSearch=unnestKwFromSearch;\n"
    "window.sidesKwArrowPortrait=sidesKwArrowPortrait;\n"
    "window.applySidesNestedH=applySidesNestedH;\n"
)

WRAP_OLD = """    window.toggleFilter=function(){
      var w=document.getElementById('filterWrap');
      if(document.body.classList.contains('display-sides')&&document.body.classList.contains('kw-chrome-collapsed')){
        if(typeof expandKwMenu==='function'){expandKwMenu();return;}
      }
      if(document.body.classList.contains('display-sides')&&w&&w.classList.contains('open')&&!document.body.classList.contains('kw-fs-open')){
        if(typeof sidesKwCanNest==='function'&&sidesKwCanNest()&&!document.body.classList.contains('kw-nested-search')){
          if(typeof nestKwWithSearch==='function'){nestKwWithSearch();return;}
        }
        if(typeof collapseKwMenu==='function'){collapseKwMenu();return;}
      }
      _tf.apply(this,arguments);
      if(typeof applySidesCols==='function')applySidesCols();
    };
    /* fix-SIDES-KW-NEST-v1b */
"""

WRAP_NEW = """    window.toggleFilter=function(){
      var w=document.getElementById('filterWrap');
      if(document.body.classList.contains('display-sides')&&document.body.classList.contains('kw-chrome-collapsed')){
        if(typeof expandKwMenu==='function'){expandKwMenu();return;}
      }
      if(document.body.classList.contains('display-sides')&&w&&w.classList.contains('open')&&!document.body.classList.contains('kw-fs-open')){
        if(typeof sidesKwCanNest==='function'&&sidesKwCanNest()){
          if(document.body.classList.contains('kw-nested-search')){
            if(typeof unnestKwFromSearch==='function'){unnestKwFromSearch();return;}
          }else if(typeof nestKwWithSearch==='function'){nestKwWithSearch();return;}
        }
        if(typeof sidesKwArrowPortrait==='function'?sidesKwArrowPortrait():(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())){
          if(typeof collapseKwMenu==='function'){collapseKwMenu();return;}
        }
        if(typeof logKwNest==='function')logKwNest('arrow-noop',{fromArrow:true});
        return;
      }
      _tf.apply(this,arguments);
      if(typeof applySidesCols==='function')applySidesCols();
    };
    /* fix-SIDES-KW-NEST-v1b */
    /* """ + MARK + """ */
"""

CSS_CMT_OLD = "/* fix-SIDES-KW-NEST-v1: landscape Sides — Keywords nest under Search, then hide */\n"
CSS_CMT_NEW = (
    "/* fix-SIDES-KW-NEST-v1: landscape Sides — Keywords nest under Search, then hide */\n"
    "/* " + MARK + ": collapse arrow toggles nest; header K opens KW as its own side */\n"
)


def once(text: str, old: str, new: str, label: str, name: str) -> str:
    if old not in text:
        if new in text:
            print(f"  skip {label} {name}")
            return text
        raise SystemExit(f"{name}: missing {label}: {old[:160]!r}")
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{name}: {label} count {n}")
    print(f"  1x {label} {name}")
    return text.replace(old, new, 1)


def safe_write(path: Path, text: str) -> None:
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: rewrite would drop </html>")
    raw = text.encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        os.write(fd, raw)
        os.fsync(fd)
        os.close(fd)
        fd = -1
        tmp_path = Path(tmp)
        if not tmp_path.read_text(encoding="utf-8").rstrip().endswith("</html>"):
            tmp_path.unlink(missing_ok=True)
            raise SystemExit(f"{path.name}: tmp missing </html>")
        size = tmp_path.stat().st_size
        if size < 200_000:
            tmp_path.unlink(missing_ok=True)
            raise SystemExit(f"{path.name}: tmp too small {size}")
        os.replace(tmp, path)
        assert path.stat().st_size == size
        assert path.read_text(encoding="utf-8").rstrip().endswith("</html>")
        print(f"ok {path.name} bytes={size}")
    finally:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        if os.path.exists(tmp):
            os.unlink(tmp)


def patch(path: Path) -> None:
    name = path.name
    text = path.read_text(encoding="utf-8")
    c00 = text.count("sessionId:'c00e3e'")
    if MARK in text and "function unnestKwFromSearch(" in text:
        print("skip", name)
        return
    text = once(text, NEST_OLD, NEST_NEW, "nest-fns", name)
    text = once(text, EXPAND_OLD, EXPAND_NEW, "expand-toggle", name)
    text = once(text, EXPORT_OLD, EXPORT_NEW, "export", name)
    text = once(text, WRAP_OLD, WRAP_NEW, "toggle-wrap", name)
    text = once(text, CSS_CMT_OLD, CSS_CMT_NEW, "css-cmt", name)
    if MARK not in text:
        raise SystemExit(f"{name}: missing {MARK}")
    if "function unnestKwFromSearch(" not in text:
        raise SystemExit(f"{name}: missing unnestKwFromSearch")
    if "expand-side" not in text:
        raise SystemExit(f"{name}: missing expand-side")
    if "portrait-hide" not in text:
        raise SystemExit(f"{name}: missing portrait-hide")
    if "function sidesKwArrowPortrait(" not in text:
        raise SystemExit(f"{name}: missing sidesKwArrowPortrait")
    after = text.count("sessionId:'c00e3e'")
    if after < c00:
        raise SystemExit(f"{name}: lost c00e3e logs {c00}->{after}")
    for keep in KEEP:
        if keep not in text:
            raise SystemExit(f"{name}: lost {keep}")
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
