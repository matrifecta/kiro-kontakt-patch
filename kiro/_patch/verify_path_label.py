#!/usr/bin/env python3
"""CDP verify: PATH label above path icons; hidden in Index Window."""
from __future__ import annotations

import base64
import json
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_path_label.json")
SHOT_DIR = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9541
HTTP_PORT = 8797
PROFILE = "/tmp/catalog-path-label"
MARK = "fix-PATH-LABEL-v1"

MEASURE = r"""
(() => {
  if(typeof bindCatalogPathHits==='function')bindCatalogPathHits();
  var cards=[].slice.call(document.querySelectorAll('#catalogMain .loc-group > .entry:not(.is-hidden):not(.highlight)'));
  cards=cards.filter(function(e){var r=e.getBoundingClientRect();return r.width>20&&r.height>20;});
  var samples=cards.slice(0,8).map(function(e){
    var row=e.querySelector('.path-action-row');
    var lab=row&&row.querySelector('.path-label');
    var btns=row?[].slice.call(row.querySelectorAll('.path-icon-btn')):[];
    var lr=lab&&lab.getBoundingClientRect();
    var brs=btns.map(function(b){return b.getBoundingClientRect();});
    var cs=lab?getComputedStyle(lab):null;
    var rowR=row&&row.getBoundingClientRect();
    var btnL=brs.length?Math.min.apply(null,brs.map(function(r){return r.left;})):null;
    var btnR=brs.length?Math.max.apply(null,brs.map(function(r){return r.right;})):null;
    var btnC=(btnL!=null&&btnR!=null)?(btnL+btnR)/2:null;
    var labC=lr?(lr.left+lr.right)/2:null;
    return {
      id:e.id,
      text:lab&&(lab.textContent||'').trim(),
      firstChild:row&&row.firstElementChild&&row.firstElementChild.className,
      btnN:btns.length,
      visible:!!(lab&&cs&&cs.display!=='none'&&cs.visibility!=='hidden'&&lr&&lr.height>0),
      fw:cs&&cs.fontWeight,
      fs:cs&&cs.fontSize,
      ta:cs&&cs.textAlign,
      tt:cs&&cs.textTransform,
      color:cs&&cs.color,
      above:!!(lr&&brs[0]&&lr.bottom<=brs[0].top+1),
      centerDelta:(labC!=null&&btnC!=null)?Math.round(Math.abs(labC-btnC)):null,
      rowW:rowR&&Math.round(rowR.width),
      labW:lr&&Math.round(lr.width)
    };
  });
  return {
    mark:document.documentElement.innerHTML.indexOf('fix-PATH-LABEL-v1')>=0,
    n:samples.length,
    samples:samples,
    allText:samples.every(function(s){return s.text==='PATH';}),
    allVisible:samples.every(function(s){return s.visible;}),
    allAbove:samples.every(function(s){return s.above;}),
    allCentered:samples.every(function(s){return s.centerDelta!=null&&s.centerDelta<=6;}),
    allBold:samples.every(function(s){return parseInt(s.fw,10)>=700;}),
    allCaps:samples.every(function(s){return s.text==='PATH'&&s.tt==='uppercase';})
  };
})()
"""

INDEX_WIN = r"""
(() => {
  if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
  var ix=document.getElementById('catalogIndex');
  if(ix)ix.classList.remove('is-embedded','is-collapsed');
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof stripIndexCardChrome==='function')stripIndexCardChrome(ix);
  var labs=ix?[].slice.call(ix.querySelectorAll('.path-label')):[];
  var vis=0;
  labs.forEach(function(el){
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    if(cs.display!=='none'&&cs.visibility!=='hidden'&&r.width>0&&r.height>0)vis++;
  });
  var rows=ix?[].slice.call(ix.querySelectorAll('.path-action-row')):[];
  var rowVis=0;
  rows.forEach(function(el){
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    if(cs.display!=='none'&&cs.visibility!=='hidden'&&r.width>0&&r.height>0)rowVis++;
  });
  return {
    windowOpen:document.body.classList.contains('index-window-open'),
    embed:!!(ix&&ix.classList.contains('is-embedded')),
    labelCount:labs.length,
    labelVisible:vis,
    rowVisible:rowVis
  };
})()
"""


class Ws:
    def __init__(self, url):
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
            b1 = self.buf[1]
            ln = b1 & 0x7F
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


def shot(ws, name: str, clip=None, _id=90) -> str:
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    params = {"format": "png"}
    if clip:
        params["clip"] = clip
    data = cdp(ws, "Page.captureScreenshot", params, _id)
    raw = base64.b64decode(data["data"])
    path = SHOT_DIR / name
    path.write_bytes(raw)
    return str(path)


def run_url(url: str, tag: str) -> dict:
    chrome_bin = next(
        (p for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome") if os.path.isfile(p)),
        None,
    )
    if not chrome_bin:
        raise SystemExit("no chromium")
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    chrome = subprocess.Popen(
        [
            chrome_bin,
            "--headless=new",
            "--disable-gpu",
            f"--remote-debugging-port={PORT}",
            f"--user-data-dir={PROFILE}-{tag}",
            "--window-size=1400,900",
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
        cdp(ws, "Emulation.setDeviceMetricsOverride", {"width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False})
        cdp(ws, "Page.navigate", {"url": url})
        wait = 8 if "DS-CATALOG" in url else 4
        time.sleep(wait)
        cdp(ws, "Runtime.enable")
        rid = 10
        for _ in range(60):
            st = eval_js(
                ws,
                "({rs:document.readyState,n:document.querySelectorAll('.entry').length,m:typeof bindCatalogPathHits==='function'})",
                rid,
            )
            rid += 1
            if st and st.get("rs") == "complete" and (st.get("n") or 0) > 10 and st.get("m"):
                break
            time.sleep(1)
        eval_js(ws, "window.scrollTo(0,0);if(typeof bindCatalogPathHits==='function')bindCatalogPathHits();", rid)
        rid += 1
        time.sleep(0.4)
        measure = eval_js(ws, MEASURE, rid)
        print("  measure", json.dumps({k: measure.get(k) for k in ("n", "allText", "allVisible", "allAbove", "allCentered", "allBold", "allCaps")}, default=str))
        rid += 1
        clip = eval_js(
            ws,
            """(() => {
              var e=document.querySelector('.entry .path-action-row')||document.querySelector('.entry');
              if(!e)return null;
              var r=e.getBoundingClientRect();
              if(!r.width||!r.height)return {x:0,y:0,width:640,height:480,scale:1};
              return {x:Math.max(0,r.left-16),y:Math.max(0,r.top-16),width:Math.min(480,r.width+32),height:Math.min(260,r.height+32),scale:1};
            })()""",
            rid,
        )
        rid += 1
        card_shot = shot(ws, f"D1400-path-label-{tag}.png", clip or None, rid)
        rid += 1
        index = eval_js(ws, INDEX_WIN, rid)
        rid += 1
        time.sleep(0.3)
        ix_clip = eval_js(
            ws,
            """(() => {
              var ix=document.getElementById('catalogIndex');
              var r=ix?ix.getBoundingClientRect():{left:0,top:0,width:640,height:360};
              return {x:Math.max(0,r.left),y:Math.max(0,r.top),width:Math.min(720,Math.max(320,r.width)),height:Math.min(420,Math.max(220,r.height)),scale:1};
            })()""",
            rid,
        )
        rid += 1
        ix_shot = shot(ws, f"D1400-path-label-index-{tag}.png", ix_clip, rid)
        return {
            "url": url,
            "measure": measure,
            "index": index,
            "shots": [card_shot, ix_shot],
        }
    finally:
        chrome.terminate()
        try:
            chrome.wait(timeout=5)
        except Exception:
            chrome.kill()


def main() -> None:
    os.makedirs(PROFILE, exist_ok=True)
    results = {"mark": MARK, "catalogs": []}
    targets = [
        (f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html?pathlabel=1", "kontakt"),
        (f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG-portable.html?pathlabel=1", "portable"),
    ]
    for url, tag in targets:
        print("verify", url)
        results["catalogs"].append(run_url(url, tag))
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("wrote", OUT)
    for r in results["catalogs"]:
        m = r.get("measure") or {}
        i = r.get("index") or {}
        print(
            r["url"].split("/")[-1].split("?")[0],
            "text",
            m.get("allText"),
            "vis",
            m.get("allVisible"),
            "above",
            m.get("allAbove"),
            "center",
            m.get("allCentered"),
            "bold",
            m.get("allBold"),
            "ixVis",
            i.get("labelVisible"),
            "ixOpen",
            i.get("windowOpen"),
        )


if __name__ == "__main__":
    main()
