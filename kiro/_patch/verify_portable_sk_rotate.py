#!/usr/bin/env python3
"""Verify portable portrait→landscape Sides 2-pane. No fetch() in Runtime.evaluate."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_sk_rotate.json")
PORT = 9594
HTTP = 8797
PROFILE = "/tmp/catalog-sk-rotate"
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
  var flip=document.getElementById('portraitFlipBtn');
  var hideS=document.querySelector('.search-strip-hide');
  var hideK=document.getElementById('kwStripHide');
  var tog=document.getElementById('filterToggle');
  var sBtn=document.getElementById('hdrSearchBtn');
  var kBtn=document.getElementById('hdrKwBtn');
  var search=box(sc), kw=box(fw), main=box(cm);
  return {
    vw:innerWidth, vh:innerHeight,
    o:typeof portableScreenOrient==='function'?portableScreenOrient():null,
    kb:typeof portableKeyboardOpen==='function'?portableKeyboardOpen():null,
    cur:typeof currentDisplay!=='undefined'?String(currentDisplay):'',
    wanted:typeof portableMenuWanted==='object'&&portableMenuWanted?{s:!!portableMenuWanted.search,k:!!portableMenuWanted.kw}:null,
    cls:{
      sides:document.body.classList.contains('display-sides'),
      middle:document.body.classList.contains('display-middle'),
      content:document.body.classList.contains('display-content'),
      land:document.body.classList.contains('portable-landscape'),
      port:document.body.classList.contains('portable-portrait'),
      pair:document.body.classList.contains('portable-sk-pair'),
      flipOn:document.body.classList.contains('portable-flip-on'),
      kb:document.body.classList.contains('portable-kb-open'),
      sCol:document.body.classList.contains('search-chrome-collapsed'),
      kCol:document.body.classList.contains('kw-chrome-collapsed'),
      kOpen:document.body.classList.contains('kw-open')
    },
    sOn:!!(sBtn&&sBtn.classList.contains('is-on')),
    kOn:!!(kBtn&&kBtn.classList.contains('is-on')),
    search:search, kw:kw, main:main,
    flip:box(flip), hideS:box(hideS), hideK:box(hideK), filterToggle:box(tog),
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
  if(typeof applySidesCols==='function')applySidesCols();
  return true;
})()
"""
    )
    time.sleep(0.5)


def wait_ready(cdp):
    for _ in range(80):
        try:
            if cdp.eval("!!(document.getElementById('catalogMain')&&typeof toggleHdrSearch==='function'&&typeof syncDisplayForOrientation==='function')"):
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
    time.sleep(0.5)


def hidden(node):
    return not (node and node.get("shown"))


def check_catalog(cdp, name):
    out = {"name": name}
    set_phone(cdp, 390, 844, "portrait")
    nav(cdp, f"http://127.0.0.1:{HTTP}/{name}")
    cdp.eval("try{localStorage.clear();}catch(e){}")
    nav(cdp, f"http://127.0.0.1:{HTTP}/{name}")
    set_phone(cdp, 390, 844, "portrait")
    out["boot"] = cdp.eval(GEO)

    cdp.eval("toggleHdrSearch();")
    time.sleep(0.45)
    out["port_s"] = cdp.eval(GEO)

    set_phone(cdp, 844, 390, "landscape")
    out["land_s"] = cdp.eval(GEO)

    # fresh portrait for S then K
    set_phone(cdp, 390, 844, "portrait")
    nav(cdp, f"http://127.0.0.1:{HTTP}/{name}")
    set_phone(cdp, 390, 844, "portrait")
    cdp.eval("toggleHdrSearch();")
    time.sleep(0.4)
    cdp.eval("toggleHdrKw();")
    time.sleep(0.45)
    out["port_sk"] = cdp.eval(GEO)
    set_phone(cdp, 844, 390, "landscape")
    out["land_sk"] = cdp.eval(GEO)

    # keyboard-like CSS portrait, screen stays landscape
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": 500,
            "height": 620,
            "deviceScaleFactor": 2,
            "mobile": True,
            "screenOrientation": {"type": "landscapePrimary", "angle": 90},
        },
    )
    time.sleep(0.4)
    cdp.eval("window.dispatchEvent(new Event('resize')); if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();")
    time.sleep(0.4)
    out["kb_css"] = cdp.eval(GEO)

    # KW only
    set_phone(cdp, 390, 844, "portrait")
    nav(cdp, f"http://127.0.0.1:{HTTP}/{name}")
    set_phone(cdp, 390, 844, "portrait")
    cdp.eval("toggleHdrKw();")
    time.sleep(0.45)
    out["port_k"] = cdp.eval(GEO)
    set_phone(cdp, 844, 390, "landscape")
    out["land_k"] = cdp.eval(GEO)

    land_s = out["land_s"]
    land_sk = out["land_sk"]
    land_k = out["land_k"]
    kb = out["kb_css"]
    boot = out["boot"]

    checks = {
        "boot_content": bool(boot["cls"]["content"]) and not boot["cls"]["middle"],
        "land_s_no_middle": not land_s["cls"]["middle"] and bool(land_s["cls"]["sides"]),
        "land_s_header": bool(land_s["sOn"]) and not land_s["kOn"],
        "land_s_geo": bool(land_s["scPair"]) and hidden(land_s["kw"]),
        "land_s_flip": bool(land_s["cls"]["flipOn"]) and not hidden(land_s["flip"]),
        "land_sk_no_middle": not land_sk["cls"]["middle"] and bool(land_sk["cls"]["sides"]),
        "land_sk_header": bool(land_sk["sOn"]) and bool(land_sk["kOn"]),
        "land_sk_geo": bool(land_sk["skPair"]) and hidden(land_sk["main"]),
        "land_sk_pair_cls": bool(land_sk["cls"]["pair"]),
        "land_sk_flip": bool(land_sk["cls"]["flipOn"]) and not hidden(land_sk["flip"]),
        "land_sk_no_hide": hidden(land_sk["hideS"]) and hidden(land_sk["hideK"]) and hidden(land_sk["filterToggle"]),
        "kb_keeps_sk": bool(kb["cls"]["pair"]) and bool(kb["skPair"]) and not kb["cls"]["middle"],
        "land_k_no_middle": not land_k["cls"]["middle"] and bool(land_k["cls"]["sides"]),
        "land_k_header": (not land_k["sOn"]) and bool(land_k["kOn"]),
        "land_k_geo": bool(land_k["ckPair"]) and hidden(land_k["search"]),
        "boot_no_hide": hidden(boot["hideK"]) and hidden(boot["filterToggle"]),
    }
    out["checks"] = checks
    out["pass"] = all(checks.values())
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
