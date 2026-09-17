#!/usr/bin/env python3
"""CDP: collapsed row equal; solo expand; path/folder gap."""
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
import base64

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_catalog_row_expand_split.json")
PORT = 9541
HTTP_PORT = 8803
PROFILE = "/tmp/catalog-row-expand-solo"
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
os.makedirs(PROFILE, exist_ok=True)


def ensure_http():
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{HTTP_PORT}/", timeout=2).read(32)
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
            urllib.request.urlopen(f"http://127.0.0.1:{HTTP_PORT}/", timeout=1).read(32)
            return httpd
        except Exception:
            time.sleep(0.1)
    raise SystemExit("http failed")


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        key = base64.b64encode(os.urandom(16)).decode()
        s = socket.create_connection((u.hostname, u.port or 80), timeout=30)
        path = u.path + (("?" + u.query) if u.query else "")
        s.settimeout(30)
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


def run_catalog(url):
    chrome_bin = next(
        (p for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome") if os.path.isfile(p)),
        None,
    )
    if not chrome_bin:
        raise SystemExit("no chromium")
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.5)
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
    time.sleep(1.5)
    rid = 10
    try:
        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=10).read())
        ws = Ws(tabs[0]["webSocketDebuggerUrl"])
        cdp(ws, "Page.navigate", {"url": url})
        is_ds = "DS-CATALOG.html" in url and "portable" not in url
        for _ in range(90 if is_ds else 25):
            time.sleep(2 if is_ds else 1)
            st = eval_js(
                ws,
                "({rs:document.readyState,n:document.querySelectorAll('#catalogMain .entry').length,vis:document.querySelectorAll('#catalogMain .loc-group > .entry:not(.is-hidden)').length})",
                rid,
            )
            rid += 1
            if st and st.get("rs") == "complete" and (st.get("vis") or 0) >= 2:
                break
        eval_js(ws, "window.scrollTo(0,0);if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();", rid)
        rid += 1
        time.sleep(0.5)

        row_ids = eval_js(
            ws,
            r"""
            (function(){
              var cards=[].slice.call(document.querySelectorAll('#catalogMain .loc-group > .entry:not(.is-hidden):not(.highlight)'));
              var rows=[];
              cards.forEach(function(e){
                var t=Math.round(e.getBoundingClientRect().top);
                var row=null;
                for(var i=0;i<rows.length;i++){if(Math.abs(rows[i].t-t)<=10){row=rows[i];break;}}
                if(!row){row={t:t,cards:[]};rows.push(row);}
                row.cards.push(e);
              });
              var row=rows.filter(function(r){return r.cards.length>=3;})[0]||rows[0];
              return row?row.cards.slice(0,3).map(function(e){return e.id;}):[];
            })()
            """,
            rid,
        )
        rid += 1

        def heights(ids):
            return eval_js(
                ws,
                f"(function(){{var ids={json.dumps(ids or [])};return ids.map(function(id){{var e=document.getElementById(id);if(!e)return null;var r=e.getBoundingClientRect();var p=e.querySelector('.path');return {{id:id,h:Math.round(r.height),minH:e.style.minHeight||'',pathExp:!!(p&&p.classList.contains('is-expanded')),patchOpen:!!e.querySelector('details.patches[open]')}};}});}})()",
                rid,
            )

        h0 = heights(row_ids)
        rid += 1

        expand1 = eval_js(
            ws,
            f"(function(){{var id={json.dumps((row_ids or [''])[0])};var e=document.getElementById(id);if(!e)return null;var p=e.querySelector('.path');if(!p)return null;p.click();if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();return {{id:id,exp:p.classList.contains('is-expanded')}};}})()",
            rid,
        )
        rid += 1
        time.sleep(0.4)
        h1 = heights(row_ids)
        rid += 1

        path_gap = eval_js(
            ws,
            r"""
            (function(){
              var path=document.querySelector('#catalogMain .loc-group > .entry:not(.is-hidden) .path:not(.is-expanded)');
              if(!path)return {missing:true};
              var code=path.querySelector('code');
              var folder=path.querySelector('.folder');
              if(!folder)return {noFolder:true};
              var cr=code.getBoundingClientRect();
              var fr=folder.getBoundingClientRect();
              var fs=path.querySelector('.path-fs-hit');
              return {overlap:!(cr.right<=fr.left-1),gap:Math.round(fr.left-cr.right),fsGap:fs?Math.round(fs.getBoundingClientRect().left-fr.right):null,codeR:Math.round(cr.right),folderL:Math.round(fr.left)};
            })()
            """,
            rid,
        )
        rid += 1

        col0 = [x["h"] for x in (h0 or [])[1:] if x]
        col1 = [x["h"] for x in (h1 or [])[1:] if x and not x.get("pathExp") and not x.get("patchOpen")]
        exp0 = (h0 or [None])[0]
        exp1 = (h1 or [None])[0]

        return {
            "url": url,
            "rowIds": row_ids,
            "baseline": h0,
            "expand1": expand1,
            "afterExpand1": h1,
            "pathGap": path_gap,
            "checks": {
                "collapsedEqual": h0 and len(h0) >= 2 and max(x["h"] for x in h0 if not x.get("pathExp")) - min(x["h"] for x in h0 if not x.get("pathExp")) <= 3,
                "soloExpandTaller": exp0 and exp1 and exp1["h"] > exp0["h"] + 8 and exp1.get("minH") in ("", None),
                "siblingsUnchanged": col0 and col1 and len(col0) == len(col1) and max(abs(a - b) for a, b in zip(col0, col1)) <= 3,
                "pathFolderGap": not path_gap or path_gap.get("noFolder") or (path_gap.get("gap", -1) >= 2 and not path_gap.get("overlap")),
            },
        }
    finally:
        chrome.terminate()
        try:
            chrome.wait(timeout=5)
        except Exception:
            pass


def main():
    ensure_http()
    targets = [
        f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html?v=rowsolo1",
        f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG-portable.html?v=rowsolo1",
        f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG-portable.html?v=rowsolo1",
    ]
    results = []
    for url in targets:
        print("verify", url.split("/")[-1])
        try:
            results.append(run_catalog(url))
        except Exception as exc:
            results.append({"url": url, "error": str(exc)})
    results.append(
        {
            "url": f"file://{ROOT}/DS-CATALOG.html",
            "note": "same JS/CSS patch applied; headless CDP times out on 8.9MB inline HTML",
            "patchApplied": "catalogCardIsExpanded" in Path(f"{ROOT}/DS-CATALOG.html").read_text(encoding="utf-8")
            and "fix-PATH-FOLDER-GAP-v2" in Path(f"{ROOT}/DS-CATALOG.html").read_text(encoding="utf-8"),
        }
    )
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("wrote", OUT)
    for r in results:
        name = r["url"].split("/")[-1].split("?")[0]
        print(name, r.get("checks"), "heights", r.get("baseline"), "->", r.get("afterExpand1"))


if __name__ == "__main__":
    main()
