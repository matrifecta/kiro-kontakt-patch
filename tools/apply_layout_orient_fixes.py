import re, sys

FILES = [
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

TAG1 = "LAYOUTS-CONTENT-MODE-CHROME-v1"
TAG2 = "PORTRAIT-ORIENT-COMBO-RESTORE-v1"

OLD1 = """    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
    if(typeof bindPortablePathHits==='function')bindPortablePathHits();
    return;
  }"""
NEW1 = """    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
    if(typeof bindPortablePathHits==='function')bindPortablePathHits();
    /* fix-LAYOUTS-CONTENT-MODE-CHROME-v1: content-only mode returns early above and
       used to skip ensureLayoutChromeBtns(), so #layoutPresets (Layouts popup) stayed
       parked inside the now-hidden Keywords panel (#filterWrap display:none) instead
       of being relocated into the always-visible header host (#hdrLayoutBtns). */
    try{if(typeof ensureLayoutChromeBtns==='function')ensureLayoutChromeBtns();}catch(errLayC){}
    return;
  }"""

OLD2 = """    document.body.classList.remove('display-middle');
    if(typeof applySidesCols==='function')applySidesCols();
    if(typeof placeMenusForDisplay==='function')placeMenusForDisplay('sides');
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
  }
  if(hold&&typeof portableRestoreHeldFs==='function')portableRestoreHeldFs();"""
NEW2 = """    document.body.classList.remove('display-middle');
    if(typeof applySidesCols==='function')applySidesCols();
    if(typeof placeMenusForDisplay==='function')placeMenusForDisplay('sides');
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
  }
  /* fix-PORTRAIT-ORIENT-COMBO-RESTORE-v1: the landscape branch above restores which
     menus were open and reapplies sizing/placement after rotating; the portrait
     direction (rotating back) had no equivalent, so the Middle-mode menu lost its
     open/closed combo and its persisted size ("contracted") on landscape->portrait. */
  if(window.CATALOG_PORTABLE&&o==='portrait'&&next==='middle'){
    try{currentDisplay='middle';}catch(ePortCur){}
    if(!hold){
    if(combo&&typeof portableRestoreMenuCombo==='function')portableRestoreMenuCombo(combo);
    if(combo&&combo.searchOn&&typeof expandSearchMenu==='function')expandSearchMenu();
    if(combo&&combo.kwOn&&typeof expandKwMenu==='function')expandKwMenu();
    if(combo&&!combo.searchOn&&typeof collapseSearchMenu==='function')collapseSearchMenu();
    if(combo&&!combo.kwOn&&typeof collapseKwMenu==='function')collapseKwMenu();
    }
    if(typeof applyMiddleLayout==='function')applyMiddleLayout();
    if(typeof placeMenusForDisplay==='function')placeMenusForDisplay('middle');
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
  }
  if(hold&&typeof portableRestoreHeldFs==='function')portableRestoreHeldFs();"""

def apply_file(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    if TAG1 in html and TAG2 in html:
        print(f"SKIP (already applied): {path}")
        return
    if html.count(OLD1) != 1:
        raise AssertionError(f"OLD1 not found exactly once in {path}: {html.count(OLD1)}")
    if html.count(OLD2) != 1:
        raise AssertionError(f"OLD2 not found exactly once in {path}: {html.count(OLD2)}")
    html = html.replace(OLD1, NEW1, 1)
    html = html.replace(OLD2, NEW2, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"APPLIED: {path}")

if __name__ == "__main__":
    import os
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in FILES:
        apply_file(os.path.join(base, rel))
