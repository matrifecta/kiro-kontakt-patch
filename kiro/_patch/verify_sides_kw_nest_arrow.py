#!/usr/bin/env python3
"""Verify landscape Sides KW nest arrow: nested ▲, full-side ▼. No fetch() in evaluate."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_sides_kw_nest_arrow.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9591
HTTP = 8797
PROFILE = "/tmp/catalog-sides-kw-nest-arrow"
CHROME = next(
    (
        p
        for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome")
        if os.path.exists(p)
    ),
    "/usr/bin/chromium",
)
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

ARROW = r"""
(() => {
  var a=document.querySelector('#filterToggle .toggle-arrow');
  var ft=document.getElementById('filterToggle');
  var cs=a?getComputedStyle(a):null;
  var tr=cs?cs.transform:'';
  var rot=cs?cs.rotate:'';
  return {
    vw:innerWidth, vh:innerHeight,
    nested:document.body.classList.contains('kw-nested-search'),
    land:document.body.classList.contains('desk-landscape'),
    sides:document.body.classList.contains('display-sides'),
    middle:document.body.classList.contains('display-middle'),
    hidden:document.body.classList.contains('kw-chrome-collapsed'),
    open:!!(document.getElementById('filterWrap')&&document.getElementById('filterWrap').classList.contains('open')),
    arrow:a?String(a.textContent||'').trim():'',
    tr:tr, rot:rot,
    aria:ft?ft.getAttribute('aria-expanded'):null,
    title:ft?ft.getAttribute('title'):null,
    label:(ft?String(ft.textContent||''):'').replace(/\s+/g,' ').trim(),
    canNest:typeof sidesKwCanNest==='function'?sidesKwCanNest():null
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


def set_view(cdp, w, h):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": w,
            "height": h,
            "deviceScaleFactor": 1,
            "mobile": False,
            "screenOrientation": {
                "type": "portraitPrimary" if h >= w else "landscapePrimary",
                "angle": 0 if h >= w else 90,
            },
        },
    )
    time.sleep(0.35)


def wait_ready(cdp):
    for _ in range(80):
        try:
            if cdp.eval("!!(document.getElementById('catalogMain')&&typeof applySidesCols==='function')"):
                return
        except Exception:
            pass
        time.sleep(0.2)
    raise SystemExit("catalog not ready")


def nav(cdp, url):
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": url})
    time.sleep(1.4)
    wait_ready(cdp)
    time.sleep(0.4)


def shot(cdp, name):
    import base64

    data = cdp.call("Page.captureScreenshot", {"format": "png", "fromSurface": True})
    raw = data.get("data")
    if not raw:
        return None
    path = SHOT / name
    path.write_bytes(base64.b64decode(raw))
    return str(path)


def rotated(tr):
    if not tr or tr == "none":
        return False
    t = tr.replace(" ", "")
    return t not in ("none", "matrix(1,0,0,1,0,0)", "matrix3d(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1)")


def run_file(cdp, filename, tag):
    errors = []
    out = {"file": filename, "errors": errors, "shots": []}
    nav(cdp, f"http://127.0.0.1:{HTTP}/{filename}?kwnestarrow=1")
    set_view(cdp, 1400, 900)
    cdp.eval(
        """
(() => {
  if(typeof setDisplayMode==='function') setDisplayMode('sides');
  document.body.classList.remove('display-middle','kw-nested-search');
  if(typeof expandSearchMenu==='function') expandSearchMenu();
  if(typeof expandKwMenu==='function') expandKwMenu();
  if(typeof applySidesCols==='function') applySidesCols();
  if(typeof syncKwHideBtn==='function') syncKwHideBtn();
  return true;
})()
"""
    )
    time.sleep(0.4)
    full = cdp.eval(ARROW)
    out["full"] = full
    out["shots"].append(shot(cdp, f"D1400-{tag}-kw-arrow-full.png"))
    if not full.get("land") or not full.get("sides") or full.get("middle"):
        errors.append("not-land-sides")
    if full.get("nested") or full.get("hidden"):
        errors.append("full-not-unnested")
    if full.get("arrow") != "▼":
        errors.append(f"full-arrow-not-down:{full.get('arrow')!r}")
    if rotated(full.get("tr")):
        errors.append(f"full-arrow-rotated:{full.get('tr')}")
    if full.get("aria") != "true":
        errors.append(f"full-aria:{full.get('aria')}")

    cdp.eval("document.getElementById('filterToggle')&&document.getElementById('filterToggle').click();true")
    time.sleep(0.45)
    nested = cdp.eval(ARROW)
    out["nested"] = nested
    out["shots"].append(shot(cdp, f"D1400-{tag}-kw-arrow-nested.png"))
    if not nested.get("nested"):
        errors.append("nest-class-missing")
    if nested.get("arrow") != "▲":
        errors.append(f"nested-arrow-not-up:{nested.get('arrow')!r}")
    if rotated(nested.get("tr")):
        errors.append(f"nested-arrow-rotated:{nested.get('tr')}")
    if nested.get("aria") != "false":
        errors.append(f"nested-aria:{nested.get('aria')}")

    cdp.eval("document.getElementById('filterToggle')&&document.getElementById('filterToggle').click();true")
    time.sleep(0.4)
    unnested = cdp.eval(ARROW)
    out["unnested"] = unnested
    out["shots"].append(shot(cdp, f"D1400-{tag}-kw-arrow-unnest.png"))
    if unnested.get("nested"):
        errors.append("unnest-still-nested")
    if unnested.get("arrow") != "▼":
        errors.append(f"unnest-arrow-not-down:{unnested.get('arrow')!r}")
    if rotated(unnested.get("tr")):
        errors.append(f"unnest-arrow-rotated:{unnested.get('tr')}")

    help_txt = cdp.eval(
        """
(() => {
  var lg=document.getElementById('catalogHelpLegend');
  var ug=document.getElementById('catalogHelpUser');
  var t=((lg&&lg.textContent)||'')+' '+((ug&&ug.textContent)||'');
  return {
    downNest:t.indexOf('▼')>=0 && t.indexOf('nests under Search')>=0,
    upReturn:t.indexOf('▲')>=0 && (t.indexOf('returns to the full')>=0 || t.indexOf('return to the full')>=0),
    portraitNoUp:t.indexOf('no up-arrow nest-toggle there')>=0,
    portraitOne:t.indexOf('one-step hide/show')>=0
  };
})()
"""
    )
    out["help"] = help_txt
    if not help_txt or not help_txt.get("downNest"):
        errors.append("help-missing-down-nest")
    if not help_txt or not help_txt.get("upReturn"):
        errors.append("help-missing-up-return")
    if not help_txt or not help_txt.get("portraitNoUp"):
        errors.append("help-missing-portrait-no-up")
    if not help_txt or not help_txt.get("portraitOne"):
        errors.append("help-missing-portrait-onestep")

    out["ok"] = not errors
    return out


def main():
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.2)
    proc = subprocess.Popen(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--remote-debugging-port={PORT}",
            "--remote-allow-origins=*",
            f"--user-data-dir={PROFILE}",
            "--window-size=1400,900",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    results = {"ok": True, "files": [], "errors": []}
    try:
        page = wait_dbg()
        cdp = CDP(page["webSocketDebuggerUrl"])
        for filename, tag in (("KONTAKT-CATALOG.html", "KONTAKT"), ("DS-CATALOG.html", "DS")):
            one = run_file(cdp, filename, tag)
            results["files"].append(one)
            if not one.get("ok"):
                results["ok"] = False
                results["errors"].extend([f"{tag}:{e}" for e in one.get("errors") or []])
    finally:
        try:
            os.kill(proc.pid, signal.SIGTERM)
        except Exception:
            pass
    OUT.write_text(json.dumps(results, indent=2))
    print(json.dumps({"ok": results["ok"], "errors": results["errors"]}, indent=2))
    if not results["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
