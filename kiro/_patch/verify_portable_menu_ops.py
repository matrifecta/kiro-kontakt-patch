#!/usr/bin/env python3
"""Verify portable Search/KW FS exit and landscape Sides 2-pane. No fetch() in Runtime.evaluate."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_menu_ops.json")
PORT = 9612
HTTP = 8797
PROFILE = "/tmp/catalog-menu-ops"
CHROME = next(
    (
        p
        for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome")
        if os.path.exists(p)
    ),
    "/usr/bin/chromium",
)
os.makedirs(PROFILE, exist_ok=True)

SNAP = r"""
(() => {
  function box(el){
    if(!el) return null;
    var r=el.getBoundingClientRect(), cs=getComputedStyle(el);
    var shown = cs.display!=='none' && cs.visibility!=='hidden' && r.width>24 && r.height>24;
    return {
      x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height),
      t:Math.round(r.top), b:Math.round(r.bottom), l:Math.round(r.left), rgt:Math.round(r.right),
      disp:cs.display, vis:cs.visibility, shown:shown,
      parent:el.parentElement?(el.parentElement.id||el.parentElement.tagName):''
    };
  }
  function hit(id){
    var el=document.getElementById(id);
    if(!el) return {id:id, missing:true, self:false};
    var r=el.getBoundingClientRect();
    var cx=Math.round(r.left+Math.max(4,r.width/2)), cy=Math.round(r.top+Math.max(4,r.height/2));
    var top=document.elementFromPoint(cx,cy);
    var self=!!(top && (top===el || el.contains(top)));
    return {id:id, cx:cx, cy:cy, w:Math.round(r.width), h:Math.round(r.height), shown:r.width>8&&r.height>8, self:self, top:(top&&(top.id||top.tagName))||''};
  }
  function sideBySide(a,b){
    return !!(a&&b&&a.shown&&b.shown&&Math.abs(a.t-b.t)<120&&a.l<b.l-24&&a.w>40&&b.w>40);
  }
  var sc=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var cm=document.getElementById('catalogMain');
  var hdr=document.querySelector('.catalog-header');
  var sBtn=document.getElementById('hdrSearchBtn');
  var kBtn=document.getElementById('hdrKwBtn');
  var search=box(sc), kw=box(fw), main=box(cm), header=box(hdr);
  return {
    vw:innerWidth, vh:innerHeight,
    o:typeof portableScreenOrient==='function'?portableScreenOrient():null,
    cur:typeof currentDisplay!=='undefined'?String(currentDisplay):'',
    menuFs:typeof portableMenuFsOn==='function'?portableMenuFsOn():'',
    vis:typeof portableMiddleVisible==='function'?portableMiddleVisible():'',
    cls:{
      sides:document.body.classList.contains('display-sides'),
      middle:document.body.classList.contains('display-middle'),
      content:document.body.classList.contains('display-content'),
      land:document.body.classList.contains('portable-landscape'),
      pair:document.body.classList.contains('portable-sk-pair'),
      hdrHide:document.body.classList.contains('hdr-bar-hidden'),
      acFs:document.body.classList.contains('ac-fs-open'),
      kwFs:document.body.classList.contains('kw-fs-open'),
      sCol:document.body.classList.contains('search-chrome-collapsed'),
      kCol:document.body.classList.contains('kw-chrome-collapsed'),
      kOpen:document.body.classList.contains('kw-open')
    },
    sOn:!!(sBtn&&sBtn.classList.contains('is-on')),
    kOn:!!(kBtn&&kBtn.classList.contains('is-on')),
    fwOpen:!!(fw&&fw.classList.contains('open')),
    search:search, kw:kw, main:main, header:header,
    skPair:sideBySide(search,kw),
    scPair:sideBySide(search,main),
    ckPair:sideBySide(main,kw),
    hitS:hit('hdrSearchBtn'),
    hitK:hit('hdrKwBtn'),
    hitKwFs:hit('kwStripFs'),
    hitSfs:hit('searchStripFs')
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
    time.sleep(0.3)
    cdp.eval(
        """
(() => {
  window.dispatchEvent(new Event('orientationchange'));
  window.dispatchEvent(new Event('resize'));
  if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
  if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();
  if(typeof applySidesCols==='function')applySidesCols();
  return true;
})()
"""
    )
    time.sleep(0.5)


def wait_ready(cdp):
    for _ in range(80):
        try:
            if cdp.eval(
                "!!(document.getElementById('catalogMain')&&typeof toggleHdrSearch==='function'&&typeof toggleKwFullscreen==='function'&&typeof portableExitMenuFs==='function')"
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
    time.sleep(0.4)


def boot(cdp, name, w, h, orient):
    set_phone(cdp, w, h, orient)
    nav(cdp, f"http://127.0.0.1:{HTTP}/{name}?v=menu-ops")
    cdp.eval("try{localStorage.clear();}catch(e){}")
    nav(cdp, f"http://127.0.0.1:{HTTP}/{name}?v=menu-ops")
    set_phone(cdp, w, h, orient)


def shown(node):
    return bool(node and node.get("shown"))


def hidden(node):
    return not shown(node)


def fills_rest(el, snap, lo=0.55):
    if not shown(el):
        return False
    vh = snap.get("vh") or 1
    top = (snap.get("header") or {}).get("b") or 0
    near_top = el["y"] <= max(40, top + 28)
    tall = el["h"] >= max(120, (vh - max(top, 8)) * lo)
    return near_top and tall


def check_catalog(cdp, name):
    out = {"name": name}
    cases = {}

    def snap():
        return cdp.eval(SNAP)

    # 1 portrait Search FS then header S
    boot(cdp, name, 390, 844, "portrait")
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.3)
    out["p_s"] = snap()
    cdp.eval("if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();")
    time.sleep(0.4)
    out["p_s_fs"] = snap()
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.45)
    out["p_s_hdr"] = snap()
    sfs = out["p_s_fs"]
    sh = out["p_s_hdr"]
    cases["port_search_fs"] = sfs["menuFs"] == "search" and sfs["cls"]["acFs"] and fills_rest(sfs["search"], sfs)
    cases["port_search_hdr_exit"] = (
        sh["menuFs"] == ""
        and not sh["cls"]["acFs"]
        and shown(sh["search"])
        and hidden(sh["kw"])
        and bool(sh["sOn"])
        and not fills_rest(sh["search"], sh, 0.72)
    )
    cases["port_search_partial_s_hit"] = bool(sh["hitS"]["self"])

    # 2 portrait KW: docked visible, FS, ⛶ back to docked
    boot(cdp, name, 390, 844, "portrait")
    cdp.eval("toggleHdrKw();")
    time.sleep(0.4)
    out["p_k"] = snap()
    pk = out["p_k"]
    cases["port_kw_docked"] = (
        pk["menuFs"] == ""
        and not pk["cls"]["kwFs"]
        and shown(pk["kw"])
        and hidden(pk["search"])
        and bool(pk["kOn"])
        and pk["kw"]["parent"] == "BODY"
    )
    cdp.eval("if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();")
    time.sleep(0.4)
    out["p_k_fs"] = snap()
    kfs = out["p_k_fs"]
    cases["port_kw_fs"] = kfs["menuFs"] == "keywords" and kfs["cls"]["kwFs"] and fills_rest(kfs["kw"], kfs)
    cdp.eval("if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();")
    time.sleep(0.5)
    out["p_k_fs2"] = snap()
    k2 = out["p_k_fs2"]
    cases["port_kw_fs_exit"] = (
        k2["menuFs"] == ""
        and not k2["cls"]["kwFs"]
        and shown(k2["kw"])
        and hidden(k2["search"])
        and bool(k2["kOn"])
        and k2["kw"]["parent"] == "BODY"
        and not fills_rest(k2["kw"], k2, 0.72)
    )

    # 3 portrait S then K, rotate landscape — SK pair, no FS
    boot(cdp, name, 390, 844, "portrait")
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.3)
    cdp.eval("toggleHdrKw();")
    time.sleep(0.4)
    out["p_sk"] = snap()
    set_phone(cdp, 844, 390, "landscape")
    out["land_from_sk"] = snap()
    lf = out["land_from_sk"]
    cases["land_from_sk_pair"] = (
        lf["menuFs"] == ""
        and not lf["cls"]["kwFs"]
        and not lf["cls"]["acFs"]
        and not lf["cls"]["middle"]
        and bool(lf["cls"]["sides"])
        and bool(lf["skPair"])
        and bool(lf["sOn"])
        and bool(lf["kOn"])
        and bool(lf["hitS"]["self"])
        and bool(lf["hitK"]["self"])
    )
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.35)
    out["land_from_sk_tapS"] = snap()
    lfs = out["land_from_sk_tapS"]
    cases["land_from_sk_tapS"] = (
        hidden(lfs["search"])
        and shown(lfs["kw"])
        and not lfs["sOn"]
        and bool(lfs["kOn"])
        and not lfs["cls"]["kwFs"]
    )

    # 4 landscape open S then K, no FS
    boot(cdp, name, 844, 390, "landscape")
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.3)
    out["land_s"] = snap()
    cdp.eval("toggleHdrKw();")
    time.sleep(0.4)
    out["land_sk"] = snap()
    ls = out["land_sk"]
    cases["land_open_sk"] = (
        ls["menuFs"] == ""
        and not ls["cls"]["kwFs"]
        and not ls["cls"]["middle"]
        and bool(ls["skPair"])
        and bool(ls["sOn"])
        and bool(ls["kOn"])
        and bool(ls["hitS"]["self"])
        and bool(ls["hitK"]["self"])
    )
    cdp.eval("toggleHdrKw();")
    time.sleep(0.35)
    out["land_sk_tapK"] = snap()
    ltk = out["land_sk_tapK"]
    cases["land_sk_tapK"] = shown(ltk["search"]) and hidden(ltk["kw"]) and bool(ltk["sOn"]) and not ltk["kOn"]

    # 5 header hide during Search FS still fills leftover (no nest regress)
    boot(cdp, name, 390, 844, "portrait")
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.3)
    cdp.eval("if(typeof portableEnterMenuFs==='function')portableEnterMenuFs('search');")
    time.sleep(0.35)
    a0 = snap()
    cdp.eval("if(typeof toggleHdrBar==='function')toggleHdrBar(true);")
    time.sleep(0.45)
    a1 = snap()
    out["hdr_hide_fs"] = {"before": a0, "after": a1}
    cases["hdr_hide_search_fs"] = (
        a1["cls"]["acFs"]
        and a1["cls"]["hdrHide"]
        and hidden(a1["main"])
        and hidden(a1["kw"])
        and fills_rest(a1["search"], a1)
        and a1["search"]["h"] >= a0["search"]["h"] - 12
    )

    # 6 KW FS then rotate landscape must NOT keep kw-fs-open
    boot(cdp, name, 390, 844, "portrait")
    cdp.eval("toggleHdrKw();")
    time.sleep(0.3)
    cdp.eval("if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();")
    time.sleep(0.35)
    set_phone(cdp, 844, 390, "landscape")
    out["land_from_kw_fs"] = snap()
    lkf = out["land_from_kw_fs"]
    cases["land_from_kw_fs_no_hold"] = (
        lkf["menuFs"] == ""
        and not lkf["cls"]["kwFs"]
        and not lkf["cls"]["middle"]
        and shown(lkf["kw"])
        and bool(lkf["kOn"])
        and bool(lkf["hitK"]["self"])
        and bool(lkf["hitS"]["self"])
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
