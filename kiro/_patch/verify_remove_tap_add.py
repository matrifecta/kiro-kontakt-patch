#!/usr/bin/env python3
"""CDP: Tap button gone; KW pill still adds; search types; Embed Index sep remains."""
import base64
import http.server
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_remove_tap_add.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9585
HTTP = 8797
ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
PROFILE = "/tmp/catalog-tap-remove"
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

KEEP = (
    "c00e3e",
    "fix-INDEX-EMBED-SEP-v1",
    "fix-TAP-ADD-REMOVE-v1",
)
FILES = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]


def integrity():
    rows = []
    ok = True
    for p in FILES:
        t = p.read_text(encoding="utf-8")
        row = {"file": p.name, "endswith": t.strip().endswith("</html>"), "size": len(t.encode("utf-8"))}
        for k in KEEP:
            row[k] = k in t
            if k not in t:
                ok = False
        row["tapBtn"] = "tapAddBtnPanel" in t
        row["toggle"] = "toggleTapToAdd" in t
        if row["tapBtn"] or row["toggle"] or not row["endswith"]:
            ok = False
        rows.append(row)
    return {"ok": ok, "files": rows}


def ensure_http():
    url = f"http://127.0.0.1:{HTTP}/DS-CATALOG.html"
    try:
        urllib.request.urlopen(url, timeout=1).read(64)
        return None
    except Exception:
        pass
    os.chdir(ROOT)

    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", HTTP), H)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    for _ in range(40):
        try:
            urllib.request.urlopen(url, timeout=1).read(64)
            return httpd
        except Exception:
            time.sleep(0.1)
    raise SystemExit("http 8797 failed")


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        host, port = u.hostname, u.port or 80
        path = u.path + (("?" + u.query) if u.query else "")
        key = base64.b64encode(os.urandom(16)).decode()
        s = socket.create_connection((host, port), timeout=30)
        s.settimeout(120)
        req = (
            f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        s.sendall(req.encode())
        hdr = b""
        while b"\r\n\r\n" not in hdr:
            chunk = s.recv(4096)
            if not chunk:
                raise RuntimeError("no ws handshake")
            hdr += chunk
        self.s = s
        self.buf = hdr.split(b"\r\n\r\n", 1)[1]

    def send(self, text):
        data = text.encode()
        flen = len(data)
        hdr = bytearray([0x81])
        mask = os.urandom(4)
        if flen < 126:
            hdr.append(0x80 | flen)
        elif flen < 65536:
            hdr.append(0x80 | 126)
            hdr.extend(flen.to_bytes(2, "big"))
        else:
            hdr.append(0x80 | 127)
            hdr.extend(flen.to_bytes(8, "big"))
        hdr.extend(mask)
        self.s.sendall(bytes(hdr) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        while True:
            if len(self.buf) < 2:
                self._fill()
                continue
            ln = self.buf[1] & 0x7F
            off = 2
            if ln == 126:
                if len(self.buf) < 4:
                    self._fill()
                    continue
                ln = int.from_bytes(self.buf[2:4], "big")
                off = 4
            elif ln == 127:
                if len(self.buf) < 10:
                    self._fill()
                    continue
                ln = int.from_bytes(self.buf[2:10], "big")
                off = 10
            if len(self.buf) < off + ln:
                self._fill()
                continue
            payload = self.buf[off : off + ln]
            self.buf = self.buf[off + ln :]
            return payload.decode()

    def _fill(self):
        chunk = self.s.recv(65536)
        if not chunk:
            raise RuntimeError("ws eof")
        self.buf += chunk


def new_tab(url):
    try:
        return json.load(
            urllib.request.urlopen(
                urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + url, method="PUT")
            )
        )
    except Exception:
        return json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/new?" + url))


class CDP:
    def __init__(self, url):
        self.ws = Ws(url)
        self.id = 0

    def call(self, method, params=None, timeout=180):
        self.id += 1
        mid = self.id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})
        raise TimeoutError(method)

    def eval(self, expr, await_promise=False):
        r = self.call(
            "Runtime.evaluate",
            {"expression": expr, "awaitPromise": await_promise, "returnByValue": True},
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def nav(cdp, url):
    cdp.call("Page.navigate", {"url": url})
    for _ in range(80):
        try:
            n = cdp.eval("document.querySelectorAll('.entry').length")
        except Exception:
            n = 0
        if n and n > 3:
            return n
        time.sleep(0.25)
    return 0


def set_view(cdp, w, h, mobile=False):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {"width": w, "height": h, "deviceScaleFactor": 1 if not mobile else 2, "mobile": mobile},
    )


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png"}).get("data", "")
    path = SHOT / name
    path.write_bytes(base64.b64decode(data))
    return str(path)


JS_FLOW = r"""
(() => {
  function vis(n){
    if(!n)return false;
    var r=n.getBoundingClientRect(), cs=getComputedStyle(n);
    return cs.display!=='none'&&cs.visibility!=='hidden'&&r.width>1&&r.height>1;
  }
  if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
  if(typeof setMode==='function')setMode('search');
  var taps=[].slice.call(document.querySelectorAll('.tap-add-btn,#tapAddBtnPanel'));
  var tapVis=taps.filter(vis).length;
  var tapDom=taps.length;
  var kw=null;
  var kws=document.querySelectorAll('#kwbar .kw:not(.active):not(.on):not(.clear):not(.disabled)');
  for(var i=0;i<kws.length;i++){if(vis(kws[i])){kw=kws[i];break;}}
  if(!kw){
    var kbtn=document.getElementById('hdrKwBtn');
    if(kbtn)kbtn.click();
    document.body.classList.add('kw-open');
    var fw=document.getElementById('filterWrap');
    if(fw)fw.classList.add('open');
    if(typeof toggleKwStripMore==='function'&&typeof isPhoneViewport==='function'&&isPhoneViewport()){
      try{toggleKwStripMore();}catch(eMore){}
    }
    kws=document.querySelectorAll('#kwbar .kw:not(.active):not(.on):not(.clear):not(.disabled)');
    for(i=0;i<kws.length;i++){if(vis(kws[i])||kws[i].getAttribute('data-kw')){kw=kws[i];break;}}
  }
  var before=(typeof window.searchKeywords!=='undefined'&&window.searchKeywords)?window.searchKeywords.slice():[];
  var pills0=document.querySelectorAll('#searchPills .pill-tag,.search-active-pills .pill-tag').length;
  var via='none';
  if(kw){kw.click();via='kw';}
  var after=(typeof window.searchKeywords!=='undefined'&&window.searchKeywords)?window.searchKeywords.slice():[];
  var pills1=document.querySelectorAll('#searchPills .pill-tag,.search-active-pills .pill-tag').length;
  var si=document.getElementById('searchInput');
  var typed=false, acOpen=false, acClicked=false;
  if(si){
    si.focus();
    si.value='piano';
    si.dispatchEvent(new Event('input',{bubbles:true}));
    typed=si.value==='piano';
    var ac=document.getElementById('acList');
    acOpen=!!(ac&&(ac.classList.contains('open')||ac.childNodes.length));
    if(pills1<=pills0){
      var item=ac&&ac.querySelector('.ac-item:not(.ac-lib):not(.ac-session):not(.ac-combo)');
      if(!item)item=ac&&ac.querySelector('.ac-item');
      if(item){item.click();acClicked=true;via=via==='kw'?via:'ac';}
    }
  }
  pills1=document.querySelectorAll('#searchPills .pill-tag,.search-active-pills .pill-tag').length;
  var ix=document.getElementById('catalogIndex');
  if(ix&&!ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();
  if(ix&&ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();
  if(typeof syncIndexEmbedFull==='function')syncIndexEmbedFull();
  var il=document.getElementById('catalogIndexList');
  var ilCs=il?getComputedStyle(il):null;
  return {
    tapDom:tapDom, tapVis:tapVis,
    kwLabel:kw?(kw.getAttribute('data-kw')||kw.textContent||'').slice(0,40):null,
    before:before.length, after:after.length, pills0:pills0, pills1:pills1,
    added:after.length>before.length || pills1>pills0,
    via:via, acClicked:acClicked,
    typed:typed, acOpen:acOpen,
    embedded:!!(ix&&ix.classList.contains('is-embedded')),
    collapsed:!!(ix&&ix.classList.contains('is-collapsed')),
    sep:ilCs?ilCs.borderBottomWidth:'',
    padB:ilCs?Math.round(parseFloat(ilCs.paddingBottom)||0):0,
    ixOv:ix?getComputedStyle(ix).overflowY:'',
    bodyOv:(function(){var cb=document.querySelector('#catalogMain>.catalog-body');return cb?getComputedStyle(cb).overflowY:'';})()
  };
})()
"""


def judge(rep, prefix):
    errs = []
    if not rep or rep.get("err"):
        return [f"{prefix}: {rep}"]
    if rep.get("tapVis"):
        errs.append(f"{prefix}.tap still visible n={rep.get('tapVis')}")
    if rep.get("tapDom"):
        errs.append(f"{prefix}.tap still in DOM n={rep.get('tapDom')}")
    if not rep.get("added"):
        errs.append(f"{prefix}.kw pill did not add {rep.get('before')}->{rep.get('after')} pills {rep.get('pills0')}->{rep.get('pills1')}")
    if not rep.get("typed"):
        errs.append(f"{prefix}.search typing failed")
    if not (rep.get("embedded") and not rep.get("collapsed")):
        errs.append(f"{prefix}.embed index not expanded")
    bb = str(rep.get("sep") or "")
    try:
        if abs(float(bb.replace("px", "") or "0") - 1) > 0.2:
            errs.append(f"{prefix}.index sep={bb}")
    except Exception:
        errs.append(f"{prefix}.index sep={bb}")
    return errs


def main():
    integ = integrity()
    ensure_http()
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.25)
    chrome = next(
        (
            p
            for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome")
            if os.path.exists(p)
        ),
        None,
    )
    if not chrome:
        raise SystemExit("no chromium")
    logf = open("/tmp/catalog-tap-remove.log", "w")
    proc = subprocess.Popen(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--disable-extensions",
            f"--remote-debugging-port={PORT}",
            "--remote-allow-origins=*",
            f"--user-data-dir={PROFILE}",
            "--noerrdialogs",
            "--ozone-platform=headless",
            "--ozone-override-screen-size=1400,900",
            "--use-angle=swiftshader-webgl",
            "about:blank",
        ],
        stdout=logf,
        stderr=subprocess.STDOUT,
    )
    out = {"ok": True, "integrity": integ, "errors": [], "shots": []}
    try:
        for _ in range(80):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
                break
            except Exception:
                time.sleep(0.2)
        else:
            json.dump({"err": "cdp"}, open(OUT, "w"))
            sys.exit(1)
        tab = new_tab("about:blank")
        cdp = CDP(tab["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")

        set_view(cdp, 1400, 900, False)
        nav(cdp, f"http://127.0.0.1:{HTTP}/DS-CATALOG.html?v=taprm")
        ds = cdp.eval(JS_FLOW)
        out["ds"] = ds
        out["errors"].extend(judge(ds, "DS-desk"))
        out["shots"].append(shot(cdp, "D1400-ds-tap-removed.png"))

        set_view(cdp, 390, 844, True)
        nav(cdp, f"http://127.0.0.1:{HTTP}/DS-CATALOG-portable.html?v=taprm-p")
        port = cdp.eval(JS_FLOW)
        out["port"] = port
        out["errors"].extend(judge(port, "DS-port"))
        out["shots"].append(shot(cdp, "D390-ds-port-tap-removed.png"))

        if not integ.get("ok"):
            out["errors"].append("integrity")
        out["ok"] = len(out["errors"]) == 0
    except Exception as e:
        out["ok"] = False
        out["errors"].append(str(e))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
    OUT.write_text(json.dumps(out, indent=2))
    print(
        json.dumps(
            {
                "ok": out.get("ok"),
                "errors": out.get("errors"),
                "integrity": integ,
                "shots": out.get("shots"),
                "ds": out.get("ds"),
                "port": out.get("port"),
            },
            indent=2,
        )[:12000]
    )
    sys.exit(0 if out.get("ok") else 1)


if __name__ == "__main__":
    main()
