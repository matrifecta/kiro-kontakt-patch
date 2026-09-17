#!/usr/bin/env python3
"""Probe portable Search/KW FS and landscape SK operations. No fetch() in Runtime.evaluate."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/probe_portable_menu_ops.json")
PORT = 9611
HTTP = 8797
PROFILE = "/tmp/catalog-menu-ops-probe"
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
      disp:cs.display, vis:cs.visibility, pe:cs.pointerEvents, z:cs.zIndex,
      gc:cs.gridColumn, gr:cs.gridRow, shown:shown, parent:el.parentElement?(el.parentElement.id||el.parentElement.tagName):''
    };
  }
  function hit(id){
    var el=document.getElementById(id);
    if(!el) return {id:id, missing:true};
    var r=el.getBoundingClientRect();
    var cx=Math.round(r.left+r.width/2), cy=Math.round(r.top+r.height/2);
    var top=document.elementFromPoint(cx,cy);
    var chain=[];
    var n=top;
    for(var i=0;i<6 && n;i++){ chain.push((n.id||n.className||n.tagName||'').toString().slice(0,48)); n=n.parentElement; }
    var self = !!(top && (top===el || el.contains(top)));
    return {id:id, cx:cx, cy:cy, w:Math.round(r.width), h:Math.round(r.height), shown:r.width>8&&r.height>8, self:self, top:(top&&(top.id||top.tagName))||'', chain:chain};
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
  var fsBtn=document.getElementById('kwStripFs');
  var sfs=document.getElementById('searchStripFs');
  var search=box(sc), kw=box(fw), main=box(cm);
  return {
    vw:innerWidth, vh:innerHeight,
    o:typeof portableScreenOrient==='function'?portableScreenOrient():null,
    cur:typeof currentDisplay!=='undefined'?String(currentDisplay):'',
    menuFs:typeof portableMenuFsOn==='function'?portableMenuFsOn():'',
    hold:typeof portableMenuFsHold==='string'?portableMenuFsHold:'',
    vis:typeof portableMiddleVisible==='function'?portableMiddleVisible():'',
    wanted:typeof portableMenuWanted==='object'&&portableMenuWanted?{s:!!portableMenuWanted.search,k:!!portableMenuWanted.kw}:null,
    cls:{
      sides:document.body.classList.contains('display-sides'),
      middle:document.body.classList.contains('display-middle'),
      content:document.body.classList.contains('display-content'),
      dfs:document.body.classList.contains('display-fs'),
      land:document.body.classList.contains('portable-landscape'),
      port:document.body.classList.contains('portable-portrait'),
      pair:document.body.classList.contains('portable-sk-pair'),
      acFs:document.body.classList.contains('ac-fs-open'),
      kwFs:document.body.classList.contains('kw-fs-open'),
      dual:document.body.classList.contains('dual-fs-open'),
      sCol:document.body.classList.contains('search-chrome-collapsed'),
      kCol:document.body.classList.contains('kw-chrome-collapsed'),
      kOpen:document.body.classList.contains('kw-open')
    },
    sOn:!!(sBtn&&sBtn.classList.contains('is-on')),
    kOn:!!(kBtn&&kBtn.classList.contains('is-on')),
    fwOpen:!!(fw&&fw.classList.contains('open')),
    search:search, kw:kw, main:main, header:box(hdr),
    sfs:box(sfs), kwFsBtn:box(fsBtn),
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
    time.sleep(0.45)


def wait_ready(cdp):
    for _ in range(80):
        try:
            if cdp.eval(
                "!!(document.getElementById('catalogMain')&&typeof toggleHdrSearch==='function'&&typeof toggleKwFullscreen==='function')"
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


def slim(s):
    if not s:
        return None
    return {
        "o": s.get("o"),
        "cur": s.get("cur"),
        "menuFs": s.get("menuFs"),
        "hold": s.get("hold"),
        "vis": s.get("vis"),
        "wanted": s.get("wanted"),
        "cls": s.get("cls"),
        "sOn": s.get("sOn"),
        "kOn": s.get("kOn"),
        "fwOpen": s.get("fwOpen"),
        "skPair": s.get("skPair"),
        "search": s.get("search"),
        "kw": s.get("kw"),
        "main": s.get("main"),
        "hitS": s.get("hitS"),
        "hitK": s.get("hitK"),
        "hitKwFs": s.get("hitKwFs"),
        "sfs": s.get("sfs"),
        "kwFsBtn": s.get("kwFsBtn"),
    }


def probe(cdp, name):
    out = {"name": name}

    boot(cdp, name, 390, 844, "portrait")
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.35)
    out["p_s"] = slim(cdp.eval(SNAP))
    cdp.eval("if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();")
    time.sleep(0.4)
    out["p_s_fs"] = slim(cdp.eval(SNAP))
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.45)
    out["p_s_hdr"] = slim(cdp.eval(SNAP))

    boot(cdp, name, 390, 844, "portrait")
    cdp.eval("toggleHdrKw();")
    time.sleep(0.35)
    out["p_k"] = slim(cdp.eval(SNAP))
    cdp.eval("if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();")
    time.sleep(0.4)
    out["p_k_fs"] = slim(cdp.eval(SNAP))
    cdp.eval("if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();")
    time.sleep(0.45)
    out["p_k_fs2"] = slim(cdp.eval(SNAP))

    boot(cdp, name, 390, 844, "portrait")
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.3)
    cdp.eval("toggleHdrKw();")
    time.sleep(0.35)
    out["p_sk"] = slim(cdp.eval(SNAP))
    set_phone(cdp, 844, 390, "landscape")
    out["land_from_sk"] = slim(cdp.eval(SNAP))
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.35)
    out["land_from_sk_tapS"] = slim(cdp.eval(SNAP))

    boot(cdp, name, 844, 390, "landscape")
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.35)
    out["land_s"] = slim(cdp.eval(SNAP))
    cdp.eval("toggleHdrKw();")
    time.sleep(0.4)
    out["land_sk"] = slim(cdp.eval(SNAP))
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.35)
    out["land_sk_tapS"] = slim(cdp.eval(SNAP))

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
            "kontakt": probe(cdp, "KONTAKT-CATALOG-portable.html"),
        }
        OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
        k = result["kontakt"]
        summary = {}
        for key in (
            "p_s",
            "p_s_fs",
            "p_s_hdr",
            "p_k",
            "p_k_fs",
            "p_k_fs2",
            "p_sk",
            "land_from_sk",
            "land_from_sk_tapS",
            "land_s",
            "land_sk",
            "land_sk_tapS",
        ):
            s = k[key]
            summary[key] = {
                "menuFs": s["menuFs"],
                "cls": {x: s["cls"][x] for x in ("middle", "sides", "acFs", "kwFs", "pair", "sCol", "kOpen")},
                "sOn": s["sOn"],
                "kOn": s["kOn"],
                "skPair": s["skPair"],
                "searchShown": bool(s["search"] and s["search"]["shown"]),
                "kwShown": bool(s["kw"] and s["kw"]["shown"]),
                "kwParent": (s["kw"] or {}).get("parent"),
                "searchH": (s["search"] or {}).get("h"),
                "kwH": (s["kw"] or {}).get("h"),
                "hitS": s["hitS"],
                "hitK": s["hitK"],
            }
        print(json.dumps(summary, indent=2))
    finally:
        try:
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    run()
