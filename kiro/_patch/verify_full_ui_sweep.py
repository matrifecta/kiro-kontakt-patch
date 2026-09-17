#!/usr/bin/env python3
"""
Comprehensive UI sweep across Upper / Sides / Full modes.
Tests: layout, button visibility, duplicate controls, sync, header toolbar, 
       search/kw toggle interoperability, Full mode isolaton, Index behaviour.
Writes results to verify_full_ui_sweep.json
"""
import json, os, socket, subprocess, sys, time, urllib.request, base64, http.server, threading
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_full_ui_sweep.json"
CDP_PORT = 9381
PROFILE = "/tmp/catalog-full-ui-sweep"
HTML_DIR = "/home/phnx/kiro-kontakt-patch/public/catalogs"
HTTP_PORT = 9181

# ── tiny static file server ───────────────────────────────────────────────────
class CatalogHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HTML_DIR, **kw)
    def log_message(self, *a): pass

srv = http.server.HTTPServer(("127.0.0.1", HTTP_PORT), CatalogHandler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.2)

URLS = [
    ("ds",      f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html"),
    ("kontakt", f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html"),
]

import shutil
if os.path.exists(PROFILE): shutil.rmtree(PROFILE)  # always fresh profile
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(["pkill", "-f", f"remote-debugging-port={CDP_PORT}"], check=False)
time.sleep(0.3)
chrome = next((p for p in ["/usr/lib/chromium/chromium","/usr/bin/chromium","/usr/bin/google-chrome","/usr/bin/chromium-browser"] if os.path.exists(p)), None)
if not chrome:
    open(OUT,"w").write(json.dumps({"err":"no chrome"})); sys.exit(1)

proc = subprocess.Popen(
    [chrome,"--headless=new","--disable-gpu","--no-first-run","--disable-extensions",
     f"--remote-debugging-port={CDP_PORT}","--remote-allow-origins=*",
     f"--user-data-dir={PROFILE}","--noerrdialogs","--ozone-platform=headless",
     "--ozone-override-screen-size=1400,900","--use-angle=swiftshader-webgl","about:blank"],
    stdout=open("/tmp/catalog-full-ui-sweep.log","w"), stderr=subprocess.STDOUT,
)

for _ in range(80):
    try: urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version",timeout=1).read(); break
    except: time.sleep(0.25)
else:
    open(OUT,"w").write(json.dumps({"err":"cdp_timeout"})); sys.exit(1)

# ── WebSocket client ──────────────────────────────────────────────────────────
class Ws:
    def __init__(self, url):
        u = urlparse(url)
        host, port = u.hostname, u.port or 80
        path = u.path + (("?" + u.query) if u.query else "")
        key = base64.b64encode(os.urandom(16)).decode()
        s = socket.create_connection((host, port), timeout=20)
        req = (f"GET {path} HTTP/1.1\r\nHost:{host}:{port}\r\nUpgrade: websocket\r\n"
               f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n")
        s.sendall(req.encode())
        hdr = b""
        while b"\r\n\r\n" not in hdr:
            c = s.recv(4096)
            if not c: raise RuntimeError("ws handshake fail")
            hdr += c
        self.s = s; self.buf = hdr.split(b"\r\n\r\n",1)[1]; self._id = 0

    def send(self, text):
        data = text.encode(); flen = len(data); mask = os.urandom(4)
        h = bytearray([0x81])
        if flen < 126: h.append(0x80|flen)
        elif flen < 65536: h.append(0x80|126); h.extend(flen.to_bytes(2,"big"))
        else: h.append(0x80|127); h.extend(flen.to_bytes(8,"big"))
        h.extend(mask)
        self.s.sendall(bytes(h)+bytes(b^mask[i%4] for i,b in enumerate(data)))

    def _fill(self):
        c = self.s.recv(65536)
        if not c: raise RuntimeError("ws closed")
        self.buf += c

    def recv(self):
        while True:
            if len(self.buf)<2: self._fill(); continue
            b1 = self.buf[1]; plen = b1&0x7f
            hlen = 2
            if plen==126: hlen+=2
            elif plen==127: hlen+=8
            while len(self.buf)<hlen: self._fill()
            if plen==126: plen=int.from_bytes(self.buf[2:4],"big")
            elif plen==127: plen=int.from_bytes(self.buf[2:10],"big")
            while len(self.buf)<hlen+plen: self._fill()
            frame = self.buf[hlen:hlen+plen]
            self.buf = self.buf[hlen+plen:]
            if (self.buf[:1]==b'\x00'): self.buf=self.buf[1:]
            return json.loads(frame.decode("utf-8","replace"))

    def call(self, method, params=None, timeout=20):
        self._id += 1; mid = self._id
        self.send(json.dumps({"id":mid,"method":method,"params":params or {}}))
        deadline = time.time()+timeout
        while time.time()<deadline:
            r = self.recv()
            if r.get("id")==mid: return r.get("result",{})
        raise TimeoutError(f"cdp timeout: {method}")

def eval_js(ws, expr, timeout=20):
    r = ws.call("Runtime.evaluate", {"expression":expr,"awaitPromise":False,"returnByValue":True}, timeout=timeout)
    if "exceptionDetails" in r:
        raise RuntimeError(f"JS: {r['exceptionDetails'].get('text','err')} | {r['exceptionDetails'].get('exception',{}).get('description','')}")
    v = r.get("result",{})
    if v.get("type")=="object" and v.get("subtype")=="error":
        raise RuntimeError(f"JS error: {v.get('description','')}")
    return v.get("value")

def navigate(ws, url, wait=2.0):
    ws.call("Page.enable")
    ws.call("Page.navigate", {"url": url})
    deadline = time.time()+wait+3
    while time.time()<deadline:
        try:
            r = ws.recv()
            if r.get("method")=="Page.loadEventFired": break
        except TimeoutError: break
    time.sleep(wait)

# ── master JS expression  ─────────────────────────────────────────────────────
# Returns a rich snapshot of current UI state
SNAPSHOT_JS = """
(function(){
  var B=document.body,S=function(id){return document.getElementById(id);},
      Q=function(sel){return document.querySelector(sel);},
      QA=function(sel){return Array.from(document.querySelectorAll(sel));},
      vis=function(el){if(!el)return{ok:false};var s=getComputedStyle(el);return{ok:true,disp:s.display,vis:s.visibility,op:s.opacity,rect:el.getBoundingClientRect().toJSON()};},
      hasClass=function(cls){return B.classList.contains(cls);},
      rect=function(el){return el?el.getBoundingClientRect().toJSON():null;};

  // --- body classes ---
  var bc=Array.from(B.classList).join(' ');

  // --- header toolbar buttons ---
  var hdrSearch=S('hdrSearchBtn'), hdrKw=S('hdrKwBtn');
  var hdrSearchV=vis(hdrSearch), hdrKwV=vis(hdrKw);
  var hdrSearchPressed=hdrSearch&&hdrSearch.getAttribute('aria-pressed');
  var hdrKwPressed=hdrKw&&hdrKw.getAttribute('aria-pressed');

  // --- search chrome ---
  var sc=S('searchChrome');
  var scV=vis(sc);
  var collapsed=hasClass('search-chrome-collapsed');

  // --- search strip buttons ---
  var hideBtn=Q('.search-strip-hide');
  var clearBtn=Q('.search-strip-clear');
  var fsBtn=S('searchStripFs');
  var moreBtn=S('searchStripMore');
  var hideBtnV=vis(hideBtn), fsBtnV=vis(fsBtn), moreBtnV=vis(moreBtn);

  // --- kw strip hide ---
  var kwHide=S('kwStripHide');
  var kwHideV=vis(kwHide);
  var kwFsBtn=Q('.kw-fs-btn');
  var kwFsBtnV=vis(kwFsBtn);

  // --- filter wrap state ---
  var fw=S('filterWrap');
  var fwV=vis(fw);
  var fwOpen=fw&&fw.classList.contains('open');
  var fwParent=fw&&fw.parentElement&&(fw.parentElement.id||fw.parentElement.tagName);

  // --- acShell position ---
  var sh=S('acShell');
  var shV=vis(sh);
  var shClasses=sh?Array.from(sh.classList).join(' '):'';

  // --- catalog index ---
  var ix=S('catalogIndex'), il=S('catalogIndexList');
  var ixV=vis(ix);
  var ixCls=ix?Array.from(ix.classList).join(' '):'';
  var ilStyle=il?il.getAttribute('style'):'';

  // --- mode nav buttons visibility (pick/search in kw panel) ---
  var modeNavBtns=QA('.fs-mode-nav .mode-btn').map(function(b){
    return{txt:b.textContent.trim(),disp:getComputedStyle(b).display,pressed:b.getAttribute('aria-pressed')};
  });

  // --- display buttons ---
  var dispBtns=QA('.display-btn').map(function(b){
    return{d:b.getAttribute('data-display'),active:b.classList.contains('is-active')};
  });

  // onScreen: true only if the element has non-zero rendered area
  // (getBoundingClientRect correctly returns 0x0 for display:none ancestors)
  var onScreen=function(el){if(!el)return false;var r=el.getBoundingClientRect();return r.width>0&&r.height>0;};

  // count visible "enable/disable Search" controls
  var searchToggleControls=[];
  if(onScreen(hdrSearch))searchToggleControls.push('hdrSearchBtn');
  if(onScreen(hideBtn))searchToggleControls.push('search-strip-hide');
  var acComp=Q('.ac-companion-btn');
  if(onScreen(acComp))searchToggleControls.push('ac-companion-btn');
  // kw mode-nav "Search" button: inside #kwFsModeNav (in filter-top of Keywords panel)
  var kwModeNavSearch=document.getElementById('kwFsModeNav');
  kwModeNavSearch=kwModeNavSearch&&kwModeNavSearch.querySelector('.mode-btn[data-mode="search"]');
  if(onScreen(kwModeNavSearch))searchToggleControls.push('kw-search-mode-btn(kwFsModeNav)');
  // ac mode-nav "Search" button: inside #acFsModeNav (in ac-fs-bar, fullscreen search panel)
  var acModeNavSearch=document.getElementById('acFsModeNav');
  acModeNavSearch=acModeNavSearch&&acModeNavSearch.querySelector('.mode-btn[data-mode="search"]');
  if(onScreen(acModeNavSearch))searchToggleControls.push('search-mode-btn(acFsModeNav)');

  // keywords toggle controls (visible = onScreen)
  var kwToggleControls=[];
  if(onScreen(hdrKw))kwToggleControls.push('hdrKwBtn');
  if(onScreen(kwHide))kwToggleControls.push('kwStripHide');
  if(onScreen(kwFsBtn))kwToggleControls.push('kw-fs-btn');
  var kwComp=Q('.kw-companion-btn');
  if(onScreen(kwComp))kwToggleControls.push('kw-companion-btn');
  var kwFsBack=S('kwFsBack');
  if(onScreen(kwFsBack))kwToggleControls.push('kwFsBack');

  // catalog main
  var cm=S('catalogMain')||Q('.catalog-body');
  var cmRect=cm?cm.getBoundingClientRect().toJSON():null;

  // upper: index position
  var ixRect=ix?ix.getBoundingClientRect().toJSON():null;

  // check if search input is interactable (not occluded)
  var inp=S('searchInput');
  var inpRect=inp?inp.getBoundingClientRect().toJSON():null;
  var inpOnTop=inp&&(function(){
    if(!inpRect||inpRect.width<1)return false;
    var cx=inpRect.x+inpRect.width/2, cy=inpRect.y+inpRect.height/2;
    var top=document.elementFromPoint(cx,cy);
    return !!(top&&(top===inp||inp.contains(top)));
  })();

  // Full-mode specific: ac-fs-open, kw-fs-open class
  var acFsOpen=hasClass('ac-fs-open');
  var kwFsOpen=hasClass('kw-fs-open');
  var dualFsOpen=hasClass('dual-fs-open');

  return{
    bodyClasses:bc,
    display:typeof currentDisplay!=='undefined'?currentDisplay:'unknown',
    dataMode:typeof currentMode!=='undefined'?currentMode:'unknown',
    collapsed:collapsed,
    acFsOpen:acFsOpen, kwFsOpen:kwFsOpen, dualFsOpen:dualFsOpen,
    hdrSearch:{vis:hdrSearchV,pressed:hdrSearchPressed},
    hdrKw:{vis:hdrKwV,pressed:hdrKwPressed},
    searchChrome:{vis:scV,rect:rect(sc)},
    searchStripHide:{vis:hideBtnV},
    searchStripFs:{vis:fsBtnV,pressed:fsBtn&&fsBtn.getAttribute('aria-pressed')},
    searchStripMore:{vis:moreBtnV},
    kwStripHide:{vis:kwHideV},
    kwFsBtn:{vis:kwFsBtnV},
    filterWrap:{vis:fwV,open:fwOpen,parent:fwParent,rect:rect(fw)},
    acShell:{vis:shV,classes:shClasses,rect:rect(sh)},
    catalogIndex:{vis:ixV,classes:ixCls,rect:ixRect},
    catalogIndexListStyle:ilStyle,
    modeNavBtns:modeNavBtns,
    displayBtns:dispBtns,
    searchToggleControls:searchToggleControls,
    kwToggleControls:kwToggleControls,
    catalogMain:{rect:cmRect},
    searchInput:{rect:inpRect,onTop:inpOnTop},
    fwParent:fwParent,
  };
})()
"""

# ── run one catalog ───────────────────────────────────────────────────────────
def sweep_catalog(label, url):
    targets = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json",timeout=5).read())
    # open new tab (requires POST)
    req = urllib.request.Request(f"http://127.0.0.1:{CDP_PORT}/json/new", data=b"", method="PUT")
    r = json.loads(urllib.request.urlopen(req, timeout=5).read())
    ws_url = r["webSocketDebuggerUrl"]
    ws = Ws(ws_url)

    results = {}
    errs = []

    def snap(tag):
        try:
            return eval_js(ws, SNAPSHOT_JS, timeout=15)
        except Exception as ex:
            errs.append(f"{tag}: {ex}")
            return {"err": str(ex)}

    def do_js(expr, tag=""):
        try:
            return eval_js(ws, expr, timeout=10)
        except Exception as ex:
            errs.append(f"js-{tag}: {ex}")
            return None

    # navigate and wait for full load
    navigate(ws, url, wait=2.5)

    # --- 1. UPPER mode (default) ---
    do_js("setDisplayMode('upper')", "upper-set")
    time.sleep(0.5)
    results["upper_default"] = snap("upper_default")

    # --- 2. UPPER + search visible + kw visible ---
    do_js("if(typeof expandSearchMenu==='function')expandSearchMenu();", "upper-expand-search")
    do_js("if(filterWrap)filterWrap.classList.add('open');document.body.classList.add('kw-open');if(typeof toggleFilter==='function'&&!document.getElementById('filterWrap').classList.contains('open'))toggleFilter();", "upper-open-kw")
    time.sleep(0.4)
    results["upper_both_open"] = snap("upper_both_open")

    # --- 3. UPPER + hide search via header btn ---
    do_js("toggleHdrSearch()", "upper-hdr-search-hide")
    time.sleep(0.3)
    results["upper_search_hidden_via_hdr"] = snap("upper_search_hidden")

    # --- 4. UPPER + re-show search via strip-hide button click ---
    do_js("if(typeof toggleSearchChrome==='function')toggleSearchChrome()", "upper-re-show-search")
    time.sleep(0.3)
    results["upper_search_reshown"] = snap("upper_search_reshown")

    # --- 5. UPPER + kw open, check kwStripHide on same bar as search ---
    do_js("setDisplayMode('upper')", "reset-upper")
    time.sleep(0.3)
    results["upper_kw_open_bar"] = snap("upper_kw_open_bar")

    # --- 6. SIDES mode ---
    do_js("setDisplayMode('sides')", "sides-set")
    time.sleep(0.6)
    results["sides_default"] = snap("sides_default")

    # --- 7. SIDES: hide search via 'Hide search' button ---
    do_js("if(typeof toggleSearchChrome==='function')toggleSearchChrome()", "sides-hide-search")
    time.sleep(0.3)
    results["sides_search_hidden"] = snap("sides_search_hidden")

    # --- 8. SIDES: show search again via header 🔍 ---
    do_js("toggleHdrSearch()", "sides-hdr-show-search")
    time.sleep(0.3)
    results["sides_search_reshown_hdr"] = snap("sides_search_reshown_hdr")

    # --- 9. SIDES: collapse kw via 'Hide Keywords' button ---
    do_js("if(typeof toggleKwChrome==='function')toggleKwChrome()", "sides-hide-kw")
    time.sleep(0.3)
    results["sides_kw_hidden"] = snap("sides_kw_hidden")

    # --- 10. SIDES: restore kw via hdrKw button ---
    do_js("toggleHdrKw()", "sides-hdr-kw-restore")
    time.sleep(0.3)
    results["sides_kw_reshown_hdr"] = snap("sides_kw_reshown_hdr")

    # --- 11. SIDES: index collapse ---
    do_js("if(typeof toggleCatalogIndex==='function')toggleCatalogIndex()", "sides-index-collapse")
    time.sleep(0.3)
    results["sides_index_collapsed"] = snap("sides_index_collapsed")

    # --- 12. SIDES: index expand ---
    do_js("if(typeof toggleCatalogIndex==='function')toggleCatalogIndex()", "sides-index-expand")
    time.sleep(0.3)
    results["sides_index_expanded"] = snap("sides_index_expanded")

    # --- 13. SIDES: index embed ---
    do_js("if(typeof toggleIndexEmbed==='function')toggleIndexEmbed()", "sides-index-embed")
    time.sleep(0.3)
    results["sides_index_embedded"] = snap("sides_index_embedded")

    # --- 14. SIDES: index un-embed ---
    do_js("if(typeof toggleIndexEmbed==='function')toggleIndexEmbed()", "sides-index-unembed")
    time.sleep(0.3)
    results["sides_index_unembedded"] = snap("sides_index_unembedded")

    # --- 15. FULL mode (click Full button → defaults to search menu) ---
    do_js("setDisplayMode('fs')", "fs-set")
    time.sleep(0.6)
    results["full_default"] = snap("full_default")

    # --- 16. FULL: check that ac-fs-open is set, kw-fs-open is NOT ---
    # (This checks Full mode isolation)
    full_snap = results["full_default"]
    results["full_isolation_check"] = {
        "acFsOpen": full_snap.get("acFsOpen"),
        "kwFsOpen": full_snap.get("kwFsOpen"),
        "dualFsOpen": full_snap.get("dualFsOpen"),
        "filterWrapParent": full_snap.get("filterWrap",{}).get("parent"),
        "filterWrapOpen": full_snap.get("filterWrap",{}).get("open"),
        "acShellClasses": full_snap.get("acShell",{}).get("classes"),
        "searchToggleControls": full_snap.get("searchToggleControls"),
        "kwToggleControls": full_snap.get("kwToggleControls"),
        "bodyClasses": full_snap.get("bodyClasses"),
    }

    # --- 17. FULL: toggle to kw fullscreen ---
    do_js("setDisplayMode('fs',{menu:'keywords'})", "fs-kw")
    time.sleep(0.5)
    results["full_kw"] = snap("full_kw")

    # --- 18. Return to Upper from Full ---
    do_js("setDisplayMode('upper')", "fs-to-upper")
    time.sleep(0.4)
    results["full_to_upper"] = snap("full_to_upper")

    # --- 19. Check duplicate controls in each state ---
    # Already captured in each snap via searchToggleControls / kwToggleControls

    # --- 20. Check hdrSearchBtn sync after toggleSearchChrome ---
    do_js("setDisplayMode('upper')", "reset-upper2")
    time.sleep(0.3)
    do_js("if(typeof toggleSearchChrome==='function')toggleSearchChrome()", "hide-search-direct")
    time.sleep(0.2)
    results["hdr_btn_sync_after_strip_hide"] = snap("hdr_sync")

    # --- 21. Same but via hdrSearch, then check strip hide text ---
    do_js("if(typeof toggleSearchChrome==='function')toggleSearchChrome()", "show-search-back")
    time.sleep(0.2)
    do_js("toggleHdrSearch()", "hide-via-hdr")
    time.sleep(0.2)
    results["strip_sync_after_hdr_hide"] = snap("strip_sync")

    # --- analysis -------------------------------------------------------
    issues = []

    def chk(tag, state, tests):
        snap_data = results.get(state, {})
        if "err" in snap_data:
            issues.append(f"SNAP_ERR {tag}: {snap_data['err']}")
            return
        for desc, val, expected in tests:
            ok = (val == expected) if not callable(expected) else expected(val)
            if not ok:
                issues.append(f"FAIL [{tag}] {desc}: got {json.dumps(val)!r}, expected {json.dumps(expected)!r}")

    # Upper default
    up = results.get("upper_default", {})
    chk("upper/default", "upper_default", [
        ("display=upper", up.get("display"), "upper"),
        ("hdrSearch visible", up.get("hdrSearch",{}).get("vis",{}).get("disp"), lambda d: d not in ("none",None)),
        ("hdrKw visible",    up.get("hdrKw",   {}).get("vis",{}).get("disp"), lambda d: d not in ("none",None)),
        ("acFsOpen=false",   up.get("acFsOpen"), False),
        ("kwFsOpen=false",   up.get("kwFsOpen"), False),
    ])

    # Sides default
    sd = results.get("sides_default", {})
    chk("sides/default", "sides_default", [
        ("display=sides", sd.get("display"), "sides"),
        ("filterWrap open", sd.get("filterWrap",{}).get("open"), True),
        ("hdrSearch visible", sd.get("hdrSearch",{}).get("vis",{}).get("disp"), lambda d: d not in ("none",None)),
        ("hdrKw visible",     sd.get("hdrKw",   {}).get("vis",{}).get("disp"), lambda d: d not in ("none",None)),
    ])

    # Full mode isolation
    fd = results.get("full_default", {})
    chk("full/isolation", "full_default", [
        ("display=fs",          fd.get("display"), "fs"),
        ("acFsOpen=true",       fd.get("acFsOpen"), True),
        ("kwFsOpen=false",      fd.get("kwFsOpen"), False),
        ("dualFsOpen=false",    fd.get("dualFsOpen"), False),
        ("filterWrap not open", fd.get("filterWrap",{}).get("open"), False),
        ("acShell has ac-fs",   fd.get("acShell",{}).get("classes",""), lambda c: "ac-fs" in c),
    ])

    # Full kw mode
    fk = results.get("full_kw", {})
    chk("full/kw", "full_kw", [
        ("display=fs",        fk.get("display"), "fs"),
        ("kwFsOpen=true",     fk.get("kwFsOpen"), True),
        ("acFsOpen=false",    fk.get("acFsOpen"), False),
        ("filterWrap open",   fk.get("filterWrap",{}).get("open"), True),
    ])

    # Search hidden → hdr btn should be NOT pressed
    sh_snap = results.get("upper_search_hidden_via_hdr", {})
    chk("upper/search_hidden", "upper_search_hidden_via_hdr", [
        ("collapsed=true", sh_snap.get("collapsed"), True),
        ("hdrSearch pressed=false", sh_snap.get("hdrSearch",{}).get("pressed"), "false"),
    ])

    # hdr btn sync after strip-hide toggle
    hs = results.get("hdr_btn_sync_after_strip_hide", {})
    chk("sync/strip-hide→hdr", "hdr_btn_sync_after_strip_hide", [
        ("collapsed=true",          hs.get("collapsed"), True),
        ("hdrSearch pressed=false", hs.get("hdrSearch",{}).get("pressed"), "false"),
    ])

    # strip sync after hdr-hide
    ss = results.get("strip_sync_after_hdr_hide", {})
    chk("sync/hdr→strip-hide", "strip_sync_after_hdr_hide", [
        ("collapsed=true",          ss.get("collapsed"), True),
        ("hdrSearch pressed=false", ss.get("hdrSearch",{}).get("pressed"), "false"),
    ])

    # duplicate search toggle controls:
    # - upper with search visible: max 2 (hdrSearchBtn + search-strip-hide)
    # - upper with search collapsed: max 1 (only hdrSearchBtn after fix-B)
    # - sides: max 2 (hdrSearchBtn + search-strip-hide when visible)
    for state_tag in ["upper_default", "upper_both_open", "sides_default"]:
        s = results.get(state_tag, {})
        ctls = s.get("searchToggleControls", [])
        if len(ctls) > 2:
            issues.append(f"DUPLICATE search controls in {state_tag}: {ctls}")

    # when search is collapsed in Upper, only hdrSearchBtn should show (fix-B)
    for state_tag in ["upper_search_hidden_via_hdr", "hdr_btn_sync_after_strip_hide", "strip_sync_after_hdr_hide"]:
        s = results.get(state_tag, {})
        ctls = s.get("searchToggleControls", [])
        if len(ctls) > 1:
            issues.append(f"DUPLICATE search controls when collapsed {state_tag}: {ctls}")

    # KW controls in Sides: after fix-C, only hdrKwBtn + kw-fs-btn visible (kwStripHide hidden)
    for state_tag in ["sides_default", "sides_search_hidden"]:
        s = results.get(state_tag, {})
        ctls = s.get("kwToggleControls", [])
        dup = [c for c in ctls if c in ("hdrKwBtn", "kwStripHide")]
        if len(dup) > 1:
            issues.append(f"DUPLICATE kw hide controls in {state_tag}: {ctls}")

    # Full mode: hdrKwBtn should be pressed=false (kw not open) — fix-A test
    chk("full/hdrKw-sync", "full_default", [
        ("hdrKw pressed=false", fd.get("hdrKw",{}).get("pressed"), "false"),
    ])

    # Sides search hidden – no search buttons in chrome, but hdrSearchBtn should be visible and not-pressed
    sshid = results.get("sides_search_hidden", {})
    chk("sides/search_hidden", "sides_search_hidden", [
        ("collapsed=true",          sshid.get("collapsed"), True),
        ("hdrSearch visible",       sshid.get("hdrSearch",{}).get("vis",{}).get("disp"), lambda d: d not in ("none",None)),
        ("hdrSearch pressed=false", sshid.get("hdrSearch",{}).get("pressed"), "false"),
    ])

    # Sides kw hidden – filterWrap not open, hdrKwBtn shows not-pressed
    skhid = results.get("sides_kw_hidden", {})
    chk("sides/kw_hidden", "sides_kw_hidden", [
        ("kw-chrome-collapsed",  skhid.get("collapsed"), lambda _: "kw-chrome-collapsed" in (skhid.get("bodyClasses",""))),
        ("hdrKw pressed=false",  skhid.get("hdrKw",{}).get("pressed"), "false"),
    ])

    # Index collapse/expand
    ix_col = results.get("sides_index_collapsed",{})
    if ix_col.get("catalogIndex",{}).get("classes"):
        if "is-collapsed" not in ix_col["catalogIndex"]["classes"]:
            issues.append(f"FAIL [sides/index] collapse did not add is-collapsed class: {ix_col['catalogIndex']['classes']}")

    return {"label": label, "results": results, "issues": issues, "errors": errs}

# ── run all catalogs ──────────────────────────────────────────────────────────
all_results = {}
for label, url in URLS:
    print(f"  sweeping {label}...", flush=True)
    try:
        r = sweep_catalog(label, url)
    except Exception as ex:
        r = {"label": label, "err": str(ex)}
    all_results[label] = r
    print(f"    {len(r.get('issues',[]))} issues, {len(r.get('errors',[]))} errors", flush=True)

proc.terminate()
open(OUT,"w").write(json.dumps(all_results, indent=2))
print(f"\nResults → {OUT}")

# summary
total_issues = sum(len(v.get("issues",[])) for v in all_results.values())
print(f"\n{'='*60}")
print(f"TOTAL ISSUES: {total_issues}")
for label, v in all_results.items():
    if v.get("issues"):
        print(f"\n  [{label}]")
        for i in v["issues"]: print(f"    • {i}")
    if v.get("errors"):
        print(f"\n  [{label}] JS errors:")
        for e in v["errors"]: print(f"    ! {e}")
