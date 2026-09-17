#!/usr/bin/env python3
"""CDP: jump stack above About; scroll preserved after equalize."""
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

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_catalog_scroll_jump.json")
PORT = 9545
HTTP_PORT = 8797
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"


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


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        s = socket.create_connection((u.hostname, u.port or 80), timeout=120)
        path = u.path + (("?" + u.query) if u.query else "")
        s.settimeout(120)
        import base64

        key = base64.b64encode(os.urandom(16)).decode()
        s.sendall(
            (
                f"GET {path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\nUpgrade: websocket\r\n"
                f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
            ).encode()
        )
        hdr = b""
        while b"\r\n\r\n" not in hdr:
            hdr += s.recv(4096)
        self.s = s
        self.buf = hdr.split(b"\r\n\r\n", 1)[1]

    def send(self, text):
        import base64

        data = text.encode()
        mask = os.urandom(4)
        hdr = bytearray([0x81, 0x80 | min(len(data), 125)])
        if len(data) >= 126:
            hdr = bytearray([0x81, 0x80 | 126]) + len(data).to_bytes(2, "big")
        hdr.extend(mask)
        self.s.sendall(bytes(hdr) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        while True:
            if len(self.buf) < 2:
                self.buf += self.s.recv(65536)
            ln = self.buf[1] & 0x7F
            off = 2
            if ln == 126:
                ln = int.from_bytes(self.buf[2:4], "big")
                off = 4
            if len(self.buf) < off + ln:
                self.buf += self.s.recv(65536)
                continue
            payload = self.buf[off : off + ln]
            self.buf = self.buf[off + ln :]
            return payload.decode("utf-8", "replace")


def cdp(ws, method, params=None, _id=1):
    ws.send(json.dumps({"id": _id, "method": method, "params": params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == _id:
            return msg.get("result", {})


def eval_js(ws, expr, _id):
    r = cdp(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True}, _id)
    v = r.get("result", {})
    return v.get("value") if v.get("type") == "object" else v


def run_test(url: str) -> dict:
    chrome_bin = next((p for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium") if os.path.isfile(p)), None)
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.5)
    chrome = subprocess.Popen(
        [chrome_bin, "--headless=new", "--disable-gpu", f"--remote-debugging-port={PORT}", "--user-data-dir=/tmp/scroll-jump-v", "about:blank"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    rid = 10
    try:
        time.sleep(1.5)
        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=10).read())
        ws = Ws(tabs[0]["webSocketDebuggerUrl"])
        cdp(ws, "Page.navigate", {"url": url})
        for _ in range(120):
            time.sleep(2)
            st = eval_js(ws, "({rs:document.readyState,vis:document.querySelectorAll('#catalogMain .loc-group > .entry:not(.is-hidden)').length})", rid)
            rid += 1
            if st and st.get("rs") == "complete" and (st.get("vis") or 0) >= 2:
                break
        eval_js(
            ws,
            "if(typeof ensureCatalogMain==='function')ensureCatalogMain();if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});if(typeof bindCatalogJumpScroll==='function')bindCatalogJumpScroll();",
            rid,
        )
        rid += 1
        prep = eval_js(
            ws,
            """
(function(){
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');
  var card=document.querySelector('.entry.selected')||document.querySelector('#catalogMain .entry:not(.is-hidden)');
  if(card&&typeof markSelected==='function')markSelected(card);
  if(sc)sc.scrollTop=Math.max(0,sc.scrollHeight-sc.clientHeight-40);
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  return {st:sc?Math.round(sc.scrollTop):0,sel:card&&card.id};
})()
""",
            rid,
        )
        rid += 1
        jump_about = eval_js(
            ws,
            """
(function(){
  var stack=document.getElementById('catalogJumpStack');
  var note=document.getElementById('catalogDocNote');
  var bot=stack&&stack.querySelector('a.bottom');
  var sr=stack?stack.getBoundingClientRect():null;
  var nr=note?note.getBoundingClientRect():null;
  var br=bot?bot.getBoundingClientRect():null;
  var gap=nr&&br?Math.round(nr.top-br.bottom):null;
  return {
    noteTop: nr?Math.round(nr.top):0,
    jumpBottom: br?Math.round(br.bottom):0,
    gap: gap,
    inset: typeof catalogJumpStackBottomInset==='function'?catalogJumpStackBottomInset():null
  };
})()
""",
            rid,
        )
        rid += 1
        before = prep.get("st") if isinstance(prep, dict) else 0
        sel = prep.get("sel") if isinstance(prep, dict) else ""
        after_eq = eval_js(
            ws,
            f"""
(function(){{
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');
  var y0=sc?sc.scrollTop:0;
  var card=document.getElementById({json.dumps(sel)})||document.querySelector('.entry.selected');
  var t0=card?card.getBoundingClientRect().top:null;
  if(typeof equalizeCatalogCardRows==='function')equalizeCatalogCardRows();
  var y1=sc?sc.scrollTop:0;
  var t1=card?card.getBoundingClientRect().top:null;
  return {{y0:Math.round(y0),y1:Math.round(y1),dY:Math.round(y1-y0),dScroll:Math.round(y1-y0),st:Math.round(y1||0),scrollDrift:Math.round(y1-y0),topDrift:t0!=null&&t1!=null?Math.round(t1-t0):999,stillSel:!!(card&&card.classList.contains('selected'))}};
}})()
""",
            rid,
        )
        return {"prep": prep, "jumpAbout": jump_about, "scroll": after_eq}
    finally:
        chrome.terminate()
        chrome.wait(timeout=10)


def main():
    httpd = ensure_http()
    data = run_test(f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html?cb=scroll-jump")
    jump_ok = isinstance(data.get("jumpAbout"), dict) and (data["jumpAbout"].get("gap") or 0) >= 8
    scroll_ok = isinstance(data.get("scroll"), dict) and abs(data["scroll"].get("topDrift", 999)) <= 4 and data["scroll"].get("stillSel")
    summary = {"data": data, "jumpOk": jump_ok, "scrollOk": scroll_ok, "pass": jump_ok and scroll_ok}
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if httpd:
        httpd.shutdown()


if __name__ == "__main__":
    main()
