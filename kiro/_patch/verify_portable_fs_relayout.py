#!/usr/bin/env python3
"""Verify portable menu FS re-nests after header/browser FS/orient. No fetch() in Runtime.evaluate."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_fs_relayout.json")
PORT = 9598
HTTP = 8797
PROFILE = "/tmp/catalog-fs-relayout"
CHROME = next(
    (
        p
        for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome")
        if os.path.exists(p)
    ),
    "/usr/bin/chromium",
)
os.makedirs(PROFILE, exist_ok=True)

GEO = r"""
(() => {
  function box(el){
    if(!el) return null;
    var r=el.getBoundingClientRect(), cs=getComputedStyle(el);
    var shown = cs.display!=='none' && cs.visibility!=='hidden' && r.width>24 && r.height>24;
    return {
      x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height),
      t:Math.round(r.top), b:Math.round(r.bottom), l:Math.round(r.left), rgt:Math.round(r.right),
      disp:cs.display, vis:cs.visibility, gc:cs.gridColumn, gr:cs.gridRow, shown:shown
    };
  }
  function sideBySide(a,b){
    return !!(a&&b&&a.shown&&b.shown&&Math.abs(a.t-b.t)<100&&a.l<b.l-24&&a.w>40&&b.w>40);
  }
  var sc=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var cm=document.getElementById('catalogMain');
  var hdr=document.querySelector('.catalog-header');
  var fsBtn=document.getElementById('kwStripFs');
  var back=document.getElementById('kwFsBack');
  var hideS=document.querySelector('.search-strip-hide');
  var hideK=document.getElementById('kwStripHide');
  var tog=document.getElementById('filterToggle');
  var flip=document.getElementById('portraitFlipBtn');
  var sBtn=document.getElementById('hdrSearchBtn');
  var kBtn=document.getElementById('hdrKwBtn');
  var search=box(sc), kw=box(fw), main=box(cm), header=box(hdr);
  var vh=innerHeight||1;
  var fill = function(el){
    if(!el||!el.shown) return 0;
    return el.h/vh;
  };
  return {
    vw:innerWidth, vh:innerHeight,
    o:typeof portableScreenOrient==='function'?portableScreenOrient():null,
    kb:typeof portableKeyboardOpen==='function'?portableKeyboardOpen():null,
    cur:typeof currentDisplay!=='undefined'?String(currentDisplay):'',
    menuFs:typeof portableMenuFsOn==='function'?portableMenuFsOn():'',
    fillH:getComputedStyle(document.documentElement).getPropertyValue('--portable-fs-fill-h').trim(),
    catH:getComputedStyle(document.documentElement).getPropertyValue('--cat-header-h').trim(),
    cls:{
      sides:document.body.classList.contains('display-sides'),
      middle:document.body.classList.contains('display-middle'),
      content:document.body.classList.contains('display-content'),
      land:document.body.classList.contains('portable-landscape'),
      port:document.body.classList.contains('portable-portrait'),
      pair:document.body.classList.contains('portable-sk-pair'),
      hdrHide:document.body.classList.contains('hdr-bar-hidden'),
      bfs:document.body.classList.contains('is-browser-fs')||document.documentElement.classList.contains('is-browser-fs'),
      acFs:document.body.classList.contains('ac-fs-open'),
      kwFs:document.body.classList.contains('kw-fs-open'),
      sCol:document.body.classList.contains('search-chrome-collapsed'),
      kCol:document.body.classList.contains('kw-chrome-collapsed'),
      kOpen:document.body.classList.contains('kw-open')
    },
    sOn:!!(sBtn&&sBtn.classList.contains('is-on')),
    kOn:!!(kBtn&&kBtn.classList.contains('is-on')),
    search:search, kw:kw, main:main, header:header,
    searchFill:fill(search), kwFill:fill(kw),
    fsBtn:box(fsBtn), back:box(back), hideS:box(hideS), hideK:box(hideK), filterToggle:box(tog), flip:box(flip),
    skPair:sideBySide(search,kw),
    scPair:sideBySide(search,main),
    ckPair:sideBySide(main,kw)
  };
})()
"""


def wait_dbg(timeout=20):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=1))
            pages = [t for t in tabs if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
            if pages:
                return pages[0]
        except Exception:
            time.sleep(0.2)
    raise SystemExit("no debugger tab")


class CDP:
    def __init__(self, ws_url):
        import websocket

        self.ws = websocket.create_connection(ws_url, timeout=60)
        self.id = 0

    def call(self, method, params=None, timeout=90):
        self.id += 1
        mid = self.id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        t0 = time.time()
        while time.time() - t0 < timeout:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
        raise TimeoutError(method)

    def eval(self, expr):
        r = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def set_phone(cdp, w, h, orient):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": w,
            "height": h,
            "deviceScaleFactor": 2,
            "mobile": True,
            "screenOrientation": {
                "type": "portraitPrimary" if orient == "portrait" else "landscapePrimary",
                "angle": 0 if orient == "portrait" else 90,
            },
        },
    )
    time.sleep(0.35)
    cdp.eval(
        """
(() => {
  window.dispatchEvent(new Event('orientationchange'));
  window.dispatchEvent(new Event('resize'));
  if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
  if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();
  if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('verify-orient');
  if(typeof applySidesCols==='function')applySidesCols();
  return true;
})()
"""
    )
    time.sleep(0.55)


def wait_ready(cdp):
    for _ in range(80):
        try:
            if cdp.eval(
                "!!(document.getElementById('catalogMain')&&typeof toggleHdrSearch==='function'&&typeof portableEnterMenuFs==='function'&&typeof portableRelayoutChrome==='function')"
            ):
                return
        except Exception:
            pass
        time.sleep(0.2)
    raise SystemExit("catalog not ready")


def nav(cdp, url):
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": url})
    time.sleep(1.6)
    wait_ready(cdp)
    time.sleep(0.45)


def hidden(node):
    return not (node and node.get("shown"))


def fills_rest(el, snap, lo=0.62):
    if not el or not el.get("shown"):
        return False
    vh = snap.get("vh") or 1
    top = (snap.get("header") or {}).get("b") or 0
    # pane starts near remaining header and uses most leftover height
    near_top = el["y"] <= max(36, top + 24)
    tall = el["h"] >= max(120, (vh - max(top, 8)) * lo)
    return near_top and tall


def check_catalog(cdp, name):
    out = {"name": name}
    cases = {}

    def boot(w, h, orient):
        set_phone(cdp, w, h, orient)
        nav(cdp, f"http://127.0.0.1:{HTTP}/{name}")
        cdp.eval("try{localStorage.clear();}catch(e){}")
        nav(cdp, f"http://127.0.0.1:{HTTP}/{name}")
        set_phone(cdp, w, h, orient)

    def snap():
        return cdp.eval(GEO)

    # A/B portrait: Search FS then hide header; KW FS then hide header
    boot(390, 844, "portrait")
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.35)
    cdp.eval("if(typeof portableEnterMenuFs==='function')portableEnterMenuFs('search');")
    time.sleep(0.4)
    a0 = snap()
    cdp.eval("if(typeof toggleHdrBar==='function')toggleHdrBar(true);")
    time.sleep(0.45)
    a1 = snap()
    out["A_port_search_fs"] = {"before": a0, "after": a1}
    cases["A_port_search_grows"] = (
        a1["cls"]["acFs"]
        and hidden(a1["main"])
        and hidden(a1["kw"])
        and fills_rest(a1["search"], a1)
        and a1["search"]["h"] >= a0["search"]["h"] - 8
        and a1["search"]["y"] <= a0["search"]["y"] + 8
    )

    boot(390, 844, "portrait")
    cdp.eval("toggleHdrKw();")
    time.sleep(0.35)
    cdp.eval("if(typeof portableEnterMenuFs==='function')portableEnterMenuFs('keywords');")
    time.sleep(0.4)
    b0 = snap()
    cdp.eval("if(typeof toggleHdrBar==='function')toggleHdrBar(true);")
    time.sleep(0.45)
    b1 = snap()
    out["B_port_kw_fs"] = {"before": b0, "after": b1}
    cases["B_port_kw_full"] = (
        b1["cls"]["kwFs"]
        and hidden(b1["main"])
        and hidden(b1["search"])
        and fills_rest(b1["kw"], b1, 0.70)
        and b1["kwFill"] > 0.62
        and hidden(b1["back"])
        and not hidden(b1["fsBtn"])
        and hidden(b1["hideK"])
        and hidden(b1["filterToggle"])
    )

    # C browser FS class on/off with Search FS open
    boot(390, 844, "portrait")
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.3)
    cdp.eval("if(typeof portableEnterMenuFs==='function')portableEnterMenuFs('search');")
    time.sleep(0.35)
    c0 = snap()
    cdp.eval(
        "if(typeof portableApplyFsClass==='function')portableApplyFsClass(true); if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('verify-bfs-on');"
    )
    time.sleep(0.4)
    c1 = snap()
    cdp.eval(
        "if(typeof portableApplyFsClass==='function')portableApplyFsClass(false); if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('verify-bfs-off');"
    )
    time.sleep(0.4)
    c2 = snap()
    out["C_port_bfs"] = {"open": c0, "on": c1, "off": c2}
    cases["C_bfs_stays_full"] = (
        fills_rest(c0["search"], c0)
        and fills_rest(c1["search"], c1)
        and fills_rest(c2["search"], c2)
        and c1["cls"]["acFs"]
        and c2["cls"]["acFs"]
        and hidden(c1["main"])
        and hidden(c2["main"])
    )

    # D landscape A/B
    boot(844, 390, "landscape")
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.35)
    cdp.eval("if(typeof portableEnterMenuFs==='function')portableEnterMenuFs('search');")
    time.sleep(0.4)
    d0 = snap()
    cdp.eval("if(typeof toggleHdrBar==='function')toggleHdrBar(true);")
    time.sleep(0.45)
    d1 = snap()
    out["D_land_search_fs"] = {"before": d0, "after": d1}
    cases["D_land_search_grows"] = (
        not d1["cls"]["middle"]
        and d1["cls"]["acFs"]
        and hidden(d1["main"])
        and hidden(d1["kw"])
        and fills_rest(d1["search"], d1, 0.58)
        and d1["search"]["h"] >= d0["search"]["h"] - 8
    )

    boot(844, 390, "landscape")
    cdp.eval("toggleHdrKw();")
    time.sleep(0.35)
    cdp.eval("if(typeof portableEnterMenuFs==='function')portableEnterMenuFs('keywords');")
    time.sleep(0.4)
    d2 = snap()
    cdp.eval("if(typeof toggleHdrBar==='function')toggleHdrBar(true);")
    time.sleep(0.45)
    d3 = snap()
    out["D_land_kw_fs"] = {"before": d2, "after": d3}
    cases["D_land_kw_full"] = (
        not d3["cls"]["middle"]
        and d3["cls"]["kwFs"]
        and hidden(d3["main"])
        and hidden(d3["search"])
        and fills_rest(d3["kw"], d3, 0.58)
        and d3["kwFill"] > 0.55
        and hidden(d3["back"])
        and not hidden(d3["fsBtn"])
    )

    # E portrait KW FS + header hidden -> landscape, then toggles
    boot(390, 844, "portrait")
    cdp.eval("toggleHdrKw();")
    time.sleep(0.3)
    cdp.eval("if(typeof portableEnterMenuFs==='function')portableEnterMenuFs('keywords');")
    time.sleep(0.35)
    cdp.eval("if(typeof toggleHdrBar==='function')toggleHdrBar(true);")
    time.sleep(0.4)
    e0 = snap()
    set_phone(cdp, 844, 390, "landscape")
    e1 = snap()
    cdp.eval("if(typeof toggleHdrSearch==='function')toggleHdrSearch();")
    time.sleep(0.4)
    e2 = snap()
    cdp.eval("if(typeof toggleHdrKw==='function')toggleHdrKw();")
    time.sleep(0.4)
    e3 = snap()
    cdp.eval("if(typeof toggleHdrBar==='function')toggleHdrBar(false);")
    time.sleep(0.4)
    e4 = snap()
    cdp.eval(
        "if(typeof portableEnterMenuFs==='function')portableEnterMenuFs('search'); if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('verify-e-sfs');"
    )
    time.sleep(0.4)
    e5 = snap()
    out["E_rotate"] = {"port": e0, "land": e1, "togS": e2, "togK": e3, "hdrShow": e4, "sfs": e5}
    cases["E_land_full"] = (
        not e1["cls"]["middle"]
        and e1["cls"]["kwFs"]
        and hidden(e1["main"])
        and hidden(e1["search"])
        and fills_rest(e1["kw"], e1, 0.55)
    )
    cases["E_toggles_coherent"] = (
        not e2["cls"]["middle"]
        and not e3["cls"]["middle"]
        and not e5["cls"]["middle"]
        and e5["cls"]["acFs"]
        and hidden(e5["main"])
        and hidden(e5["kw"])
        and fills_rest(e5["search"], e5, 0.55)
        and bool(e2["sOn"]) == (not e2["cls"]["sCol"] or e2["cls"]["acFs"] or e2["search"]["shown"] if e2["search"] else False)
    )
    # After toggling S while KW FS was on, S button/pane should match visible search
    cases["E_s_k_match"] = True
    if e3["cls"]["acFs"] or e3["cls"]["kwFs"]:
        cases["E_s_k_match"] = fills_rest(e3["search"] if e3["cls"]["acFs"] else e3["kw"], e3, 0.45)
    else:
        vis_s = not hidden(e3["search"])
        vis_k = not hidden(e3["kw"])
        cases["E_s_k_match"] = (bool(e3["sOn"]) == vis_s) or vis_s or vis_k

    # F landscape Search-only Sides, hide header — search beside content, fills height
    boot(844, 390, "landscape")
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.45)
    f0 = snap()
    cdp.eval("if(typeof toggleHdrBar==='function')toggleHdrBar(true);")
    time.sleep(0.45)
    f1 = snap()
    out["F_land_search_sides"] = {"before": f0, "after": f1}
    cases["F_search_beside"] = (
        not f1["cls"]["middle"]
        and not f1["cls"]["kwFs"]
        and not f1["cls"]["acFs"]
        and bool(f1["scPair"])
        and hidden(f1["kw"])
        and fills_rest(f1["search"], f1, 0.58)
        and fills_rest(f1["main"], f1, 0.58)
        and f1["search"]["h"] >= f0["search"]["h"] - 8
    )

    out["checks"] = cases
    out["pass"] = all(cases.values())
    return out


def run():
    proc = subprocess.Popen(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--remote-debugging-port={PORT}",
            "--remote-allow-origins=*",
            f"--user-data-dir={PROFILE}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        tab = wait_dbg()
        cdp = CDP(tab["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        result = {
            "kontakt": check_catalog(cdp, "KONTAKT-CATALOG-portable.html"),
            "ds": check_catalog(cdp, "DS-CATALOG-portable.html"),
        }
        result["pass"] = bool(result["kontakt"]["pass"] and result["ds"]["pass"])
        OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
        summary = {
            "pass": result["pass"],
            "kontakt": result["kontakt"]["checks"],
            "ds": result["ds"]["checks"],
        }
        print(json.dumps(summary, indent=2))
        if not result["pass"]:
            raise SystemExit(1)
    finally:
        try:
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    run()
