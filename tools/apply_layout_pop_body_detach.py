import os

FILES = [
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

TAG = "LAYOUTS-POP-BODY-DETACH-v1"

OLD_JS = """  ['uiScale','layoutPresets'].forEach(function(id){
    var el=document.getElementById(id);
    if(el&&el.parentElement!==host)host.appendChild(el);
  });"""
NEW_JS = """  ['uiScale','layoutPresets'].forEach(function(id){
    var el=document.getElementById(id);
    if(el&&el.parentElement!==host)host.appendChild(el);
  });
  /* fix-LAYOUTS-POP-BODY-DETACH-v1: #hdrLayoutBtns is deliberately display:none on
     portable (it's just a relocation host for header/more controls), so a popup left
     nested inside it can never be shown no matter what display value the popup
     itself is given -- an ancestor's display:none removes the whole subtree from
     rendering. Detach the popup itself to <body> so its own position:fixed +
     display:flex actually takes effect regardless of where its trigger button lives. */
  var lpPopDetach=document.getElementById('layoutPresetsPop');
  if(lpPopDetach&&lpPopDetach.parentElement!==document.body)document.body.appendChild(lpPopDetach);"""

OLD_CSS = """  body.catalog-portable #hdrLayoutBtns .layout-presets-pop:not([hidden]){
    display:flex!important;position:fixed!important;z-index:430!important
  }
  body.catalog-portable #hdrLayoutBtns .layout-presets-tab[hidden]{display:none!important}"""
NEW_CSS = """  body.catalog-portable #hdrLayoutBtns .layout-presets-pop:not([hidden]){
    display:flex!important;position:fixed!important;z-index:430!important
  }
  /* fix-LAYOUTS-POP-BODY-DETACH-v1: same rule, unscoped -- the popup is now moved to
     be a direct child of <body> (see ensureLayoutChromeBtns), so it is no longer a
     descendant of the always-hidden #hdrLayoutBtns and needs its own selector. */
  body.catalog-portable #layoutPresetsPop:not([hidden]){
    display:flex!important;position:fixed!important;z-index:430!important
  }
  body.catalog-portable #hdrLayoutBtns .layout-presets-tab[hidden]{display:none!important}"""


def apply_file(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    if TAG in html:
        print(f"SKIP (already applied): {path}")
        return
    if html.count(OLD_JS) != 1:
        raise AssertionError(f"OLD_JS not found exactly once in {path}: {html.count(OLD_JS)}")
    if html.count(OLD_CSS) != 1:
        raise AssertionError(f"OLD_CSS not found exactly once in {path}: {html.count(OLD_CSS)}")
    html = html.replace(OLD_JS, NEW_JS, 1)
    html = html.replace(OLD_CSS, NEW_CSS, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"APPLIED: {path}")


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in FILES:
        apply_file(os.path.join(base, rel))
