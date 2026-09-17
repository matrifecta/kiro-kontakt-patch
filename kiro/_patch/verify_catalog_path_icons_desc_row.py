#!/usr/bin/env python3
"""CDP verify: path icon ink, hidden path code, desc tops aligned by tallest cover row."""
from __future__ import annotations

import http.server
import json
import os
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_catalog_path_icons_desc_row.json")
PORT = 9530
HTTP_PORT = 8797
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
PROFILE = "/tmp/catalog-path-icons-desc-row"
MARK = "fix-PATH-ICONS-DESC-ROW-v3"
MARK2 = "fix-PATH-ICONS-DESC-ROW-v2"
MARK1 = "fix-PATH-ICONS-DESC-ROW-v1"
os.makedirs(PROFILE, exist_ok=True)


def ensure_http():
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html", timeout=2).read(64)
        return None
    except Exception:
        pass
    os.chdir(ROOT)

    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), H)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    for _ in range(40):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html", timeout=1).read(64)
            return httpd
        except Exception:
            time.sleep(0.1)
    raise SystemExit("http failed")


MEASURE = r"""
(() => {
  if(typeof bindCatalogPathHits==='function')bindCatalogPathHits();
  if(typeof equalizeCatalogCardRows==='function')equalizeCatalogCardRows();
  var cards=[].slice.call(document.querySelectorAll('#catalogMain .loc-group > .entry:not(.is-hidden):not(.highlight)'));
  cards=cards.filter(function(e){var r=e.getBoundingClientRect();return r.width>20&&r.height>20;});
  if(!cards.length)return {missing:true};
  var iconSamples=[];
  var pathCodeVisible=0;
  cards.slice(0,12).forEach(function(e){
    var path=e.querySelector('.path');
    if(!path)return;
    var code=path.querySelector('code');
    if(code){
      var cs=getComputedStyle(code);
      var r=code.getBoundingClientRect();
      var vis=r.width>2&&r.height>2&&cs.opacity!=='0'&&cs.clip==='auto'&&cs.visibility!=='hidden';
      if(vis&&parseFloat(cs.opacity||'1')>0.05)pathCodeVisible++;
    }
    var act=path.querySelector('.path-action-row');
    if(!act)return;
    [act.querySelector('.path-fs-hit'),act.querySelector('.path-copy-hit'),act.querySelector('a.folder')].forEach(function(btn,ix){
      if(!btn)return;
      var img=btn.querySelector('.path-icon-glyph');
      var ink=0;
      if(img){
        var ir=img.getBoundingClientRect();
        ink=Math.round(Math.min(ir.width,ir.height));
      }
      iconSamples.push({idx:ix,ink:ink,hasImg:!!img,src:img&&img.getAttribute('src')?img.getAttribute('src').slice(0,32):null});
    });
  });
  var rows=[];
  cards.forEach(function(e){
    var t=Math.round(e.getBoundingClientRect().top);
    var row=null;
    for(var i=0;i<rows.length;i++){if(Math.abs(rows[i].t-t)<=10){row=rows[i];break;}}
    if(!row){row={t:t,cards:[]};rows.push(row);}
    row.cards.push(e);
  });
  var descRows=[];
  rows.forEach(function(row){
    if(row.cards.length<2)return;
    var tops=row.cards.map(function(e){
      var sp=e.querySelector('.summary-panel');
      return sp?Math.round(sp.getBoundingClientRect().top):null;
    }).filter(function(v){return v!=null;});
    if(tops.length<2)return;
    var minT=Math.min.apply(null,tops),maxT=Math.max.apply(null,tops);
    var covers=row.cards.map(function(e){
      var c=e.querySelector('.cover');
      return c?Math.round(c.getBoundingClientRect().height):0;
    });
    var covSpread=Math.max.apply(null,covers)-Math.min.apply(null,covers);
    if(covers.some(function(h){return h<8;}))return;
    descRows.push({n:row.cards.length,spread:maxT-minT,covSpread:covSpread,covers:covers,tops:tops});
  });
  descRows.sort(function(a,b){return b.covSpread-a.covSpread;});
  var worst=descRows[0]||null;
  return {
    mark:document.documentElement.innerHTML.indexOf('""" + MARK + r"""')>=0||document.documentElement.innerHTML.indexOf('""" + MARK2 + r"""')>=0||document.documentElement.innerHTML.indexOf('""" + MARK1 + r"""')>=0,
    hasIconSrc:!!(window.CATALOG_PATH_ICON_SRC&&window.CATALOG_PATH_ICON_SRC.fullscreen),
    iconSamples:iconSamples.slice(0,18),
    allIconsInk:iconSamples.length>0&&iconSamples.every(function(s){return s.ink>=4;}),
    pathCodeVisible:pathCodeVisible,
    descRowCount:descRows.length,
    worstDescRow:worst,
    descAligned:!worst||worst.spread<=4,
    mixedRowChecked:!!(worst&&worst.covSpread>=8),
    coverCenterOk:(function(){
      var ok=true;
      cards.slice(0,6).forEach(function(e){
        var c=e.querySelector('.cover');
        var img=c&&c.querySelector('img');
        if(!c||!img)return;
        if((c.style.minHeight||'').trim())ok=false;
        var cs=getComputedStyle(img);
        var op=(cs.objectPosition||'').replace(/\s+/g,' ').trim();
        var centered=op==='center center'||op==='center'||op==='50% 50%';
        if(cs.objectFit!=='contain'||!centered)ok=false;
      });
      return ok;
    })()
  };
})()
"""


class Ws:
    def __init__(self, url):
        import base64

        u = urlparse(url)
        key = base64.b64encode(os.urandom(16)).decode()
        s = socket.create_connection((u.hostname, u.port or 80), timeout=120)
        path = u.path + (("?" + u.query) if u.query else "")
        s.sendall(
            (
                f"GET {path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\nUpgrade: websocket\r\n"
                f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
            ).encode()
        )
        hdr = b""
        while b"\r\n\r\n" not in hdr:
            chunk = s.recv(4096)
            if not chunk:
                raise RuntimeError("no ws handshake")
            hdr += chunk
        self.s = s
        self.buf = hdr.split(b"\r\n\r\n", 1)[1]

    def send(self, text):
        import base64

        data = text.encode()
        mask = os.urandom(4)
        hdr = bytearray([0x81])
        flen = len(data)
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
                ln = int.from_bytes(self.buf[2:4], "big")
                off = 4
            elif ln == 127:
                ln = int.from_bytes(self.buf[2:10], "big")
                off = 10
            if len(self.buf) < off + ln:
                self._fill()
                continue
            payload = self.buf[off : off + ln]
            self.buf = self.buf[off + ln :]
            return payload.decode("utf-8", "replace")

    def _fill(self):
        chunk = self.s.recv(65536)
        if not chunk:
            raise RuntimeError("ws closed")
        self.buf += chunk


def cdp(ws, method, params=None, _id=1):
    ws.send(json.dumps({"id": _id, "method": method, "params": params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == _id:
            if "error" in msg:
                raise RuntimeError(msg["error"])
            return msg.get("result", {})


def eval_js(ws, expr, _id):
    r = cdp(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True}, _id)
    v = r.get("result", {})
    if v.get("type") == "object" and "value" in v:
        return v["value"]
    if "exceptionDetails" in r:
        raise RuntimeError(r["exceptionDetails"])
    return v


def run_catalog(url: str) -> dict:
    import base64

    chrome_bin = next(
        (p for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome") if os.path.isfile(p)),
        None,
    )
    if not chrome_bin:
        raise SystemExit("no chromium")
    chrome = subprocess.Popen(
        [
            chrome_bin,
            "--headless=new",
            "--disable-gpu",
            f"--remote-debugging-port={PORT}",
            f"--user-data-dir={PROFILE}",
            "--no-first-run",
            "--no-default-browser-check",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.2)
    try:
        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=5).read())
        ws = Ws(tabs[0]["webSocketDebuggerUrl"])
        cdp(ws, "Page.navigate", {"url": url})
        wait = 12 if "DS-CATALOG" in url else 4
        time.sleep(wait)
        cdp(ws, "Runtime.enable")
        rid = 10
        min_entries = 10 if "DS-CATALOG" not in url else 50
        for _ in range(90 if "DS-CATALOG" in url else 60):
            st = eval_js(
                ws,
                "({rs:document.readyState,n:document.querySelectorAll('.entry').length,m:typeof bindCatalogPathHits==='function',vis:document.querySelectorAll('#catalogMain .loc-group > .entry:not(.is-hidden):not(.highlight)').length})",
                rid,
            )
            rid += 1
            if (
                st
                and st.get("rs") == "complete"
                and (st.get("n") or 0) > min_entries
                and (st.get("vis") or 0) > 5
                and st.get("m")
            ):
                break
            time.sleep(1)
        eval_js(ws, "window.scrollTo(0,0)", rid)
        rid += 1
        time.sleep(0.5)
        m = eval_js(ws, MEASURE, rid)
        return {"url": url, "mark": MARK, "measure": m}
    finally:
        chrome.terminate()
        chrome.wait(timeout=5)


def main() -> None:
    ensure_http()
    targets = [
        f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html",
        f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html",
        f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG-portable.html",
        f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG-portable.html",
    ]
    results = {"mark": MARK, "catalogs": [], "ok": True}
    for url in targets:
        print("verify", url)
        r = run_catalog(url)
        m = r.get("measure") or {}
        ok = bool(
            m.get("mark")
            and m.get("hasIconSrc")
            and m.get("allIconsInk")
            and (m.get("pathCodeVisible") or 0) == 0
            and m.get("descAligned")
            and m.get("coverCenterOk")
        )
        r["ok"] = ok
        if not ok:
            results["ok"] = False
        results["catalogs"].append(r)
        print(
            url.split("/")[-1],
            "icons",
            m.get("allIconsInk"),
            "pathHidden",
            (m.get("pathCodeVisible") or 0) == 0,
            "desc",
            m.get("descAligned"),
            "cover",
            m.get("coverCenterOk"),
            "worst",
            (m.get("worstDescRow") or {}).get("spread"),
        )
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("wrote", OUT)
    if not results["ok"]:
        raise SystemExit("verify failed")
    print("OK verify")


if __name__ == "__main__":
    main()
