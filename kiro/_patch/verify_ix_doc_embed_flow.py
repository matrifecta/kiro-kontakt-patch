#!/usr/bin/env python3
"""Prove Index/About Window hover vs Embed in-flow scroll-away."""
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

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_ix_doc_embed_flow.json"
PORT = 9493
HTTP_PORT = 8797
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
PROFILE = "/tmp/catalog-ix-doc-embed-flow"
os.makedirs(PROFILE, exist_ok=True)

MEASURE = r"""
(() => {
  function box(el){
    if(!el) return null;
    var r=el.getBoundingClientRect();
    var cs=getComputedStyle(el);
    return {
      shown: r.height>0 && cs.visibility!=='hidden' && cs.display!=='none',
      y: Math.round(r.top), b: Math.round(r.bottom), h: Math.round(r.height),
      parent: el.parentElement ? (el.parentElement.id || el.parentElement.className || el.parentElement.tagName) : '',
      pos: cs.position
    };
  }
  var ix=document.getElementById('catalogIndex');
  var note=document.getElementById('catalogDocNote');
  var main=document.getElementById('catalogMain');
  var cb=document.querySelector('#catalogMain > .catalog-body')||document.querySelector('.catalog-body');
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||cb||main;
  return {
    title: document.title,
    vw: innerWidth, vh: innerHeight,
    portable: !!window.CATALOG_PORTABLE,
    cls: document.body.className,
    ixEmbed: !!(ix&&ix.classList.contains('is-embedded')),
    ixCollapsed: !!(ix&&ix.classList.contains('is-collapsed')),
    noteEmbed: !!(note&&note.classList.contains('is-embedded')),
    noteCollapsed: !!(note&&note.classList.contains('is-collapsed')),
    ixParent: ix&&ix.parentElement&&(ix.parentElement.id||ix.parentElement.className||''),
    noteParent: note&&note.parentElement&&(note.parentElement.id||note.parentElement.className||''),
    ixInBody: !!(ix&&cb&&cb.contains(ix)&&ix.parentElement===cb),
    noteInBody: !!(note&&cb&&cb.contains(note)&&note.parentElement===cb),
    ixOnMain: !!(ix&&main&&ix.parentElement===main),
    noteOnMain: !!(note&&main&&note.parentElement===main),
    scrollId: sc&&sc.id||(sc&&sc.className)||'',
    scrollTop: sc?Math.round(sc.scrollTop):null,
    scrollMax: sc?Math.round(Math.max(0,sc.scrollHeight-sc.clientHeight)):null,
    ix: box(ix), note: box(note), main: box(main), body: box(cb)
  };
})()
"""

SCROLL = r"""
(() => {
  var cb=document.querySelector('#catalogMain > .catalog-body')||document.querySelector('.catalog-body');
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||cb||document.getElementById('catalogMain');
  if(!sc) return 0;
  var before=sc.scrollTop;
  sc.scrollTop=Math.min(sc.scrollHeight, before+220);
  return Math.round(sc.scrollTop-before);
})()
"""


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def port_open(port):
    s = socket.socket()
    s.settimeout(0.3)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def ensure_http():
    if port_open(HTTP_PORT):
        return None
    os.chdir(ROOT)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), H)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    for _ in range(30):
        if port_open(HTTP_PORT):
            return httpd
        time.sleep(0.1)
    raise SystemExit("http bind failed")


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        host, port = u.hostname, u.port or 80
        path = u.path + (("?" + u.query) if u.query else "")
        key = __import__("base64").b64encode(os.urandom(16)).decode()
        s = socket.create_connection((host, port), timeout=20)
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

    def eval(self, expr):
        r = self.call(
            "Runtime.evaluate",
            {"expression": expr, "returnByValue": True},
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def wait_ready(cdp):
    for _ in range(120):
        try:
            n = cdp.eval(
                "!!(window.toggleIndexEmbed&&window.toggleDocNoteEmbed&&document.getElementById('catalogIndex')&&document.querySelectorAll('.entry').length>5)"
            )
        except Exception:
            n = False
        if n:
            return
        time.sleep(0.2)
    raise SystemExit("catalog JS not ready")


def set_view(cdp, w, h, mobile=None):
    if mobile is None:
        mobile = w < 900
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": w,
            "height": h,
            "deviceScaleFactor": 1,
            "mobile": mobile,
            "screenOrientation": {
                "type": "portraitPrimary" if h > w else "landscapePrimary",
                "angle": 0 if h > w else 90,
            },
        },
    )
    time.sleep(0.3)


def nav(cdp, url):
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": url})
    time.sleep(0.5)
    wait_ready(cdp)


def prep(cdp, *, mode="sides", portable=False, content_only=False):
    cdp.eval(
        f"""
(() => {{
  try{{localStorage.setItem('catalog-index-embed-'+(window.CATALOG_NS||'catalog'),'0');}}catch(e){{}}
  try{{localStorage.setItem('catalog-doc-note-embed-'+(window.CATALOG_NS||'catalog'),'0');}}catch(e){{}}
  if(typeof setDisplayMode==='function') setDisplayMode({json.dumps(mode)},{{pick:true}});
  var b=document.body;
  if({str(content_only).lower()}){{
    b.classList.add('search-chrome-collapsed','kw-chrome-collapsed');
    b.classList.remove('kw-open');
  }}else if(!{str(portable).lower()}){{
    b.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');
  }}
  var ix=document.getElementById('catalogIndex');
  if(ix){{ix.classList.remove('is-embedded');ix.classList.add('is-collapsed');}}
  var note=document.getElementById('catalogDocNote');
  if(note) note.classList.remove('is-embedded');
  if(typeof applyCatalogDocNoteOpen==='function') applyCatalogDocNoteOpen(false);
  if(typeof applyDocNoteEmbedPref==='function') applyDocNoteEmbedPref();
  if(typeof parkCatalogDocNote==='function') parkCatalogDocNote();
  if(typeof syncIndexWindowDock==='function') syncIndexWindowDock();
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller());
  if(sc) sc.scrollTop=0;
}})()
"""
    )
    time.sleep(0.3)


def set_ix(cdp, *, embed=False, open_list=False):
    cdp.eval(
        f"""
(() => {{
  var ix=document.getElementById('catalogIndex');
  if(!ix) return;
  var wantEmbed={str(embed).lower()};
  if(ix.classList.contains('is-embedded')!==wantEmbed && typeof toggleIndexEmbed==='function') toggleIndexEmbed();
  if({str(open_list).lower()}) ix.classList.remove('is-collapsed');
  else ix.classList.add('is-collapsed');
  if(typeof parkCatalogDocNote==='function') parkCatalogDocNote();
  if(typeof applyIndexScrollFit==='function') applyIndexScrollFit();
  if(typeof syncIndexWindowDock==='function') syncIndexWindowDock();
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller());
  if(sc) sc.scrollTop=0;
}})()
"""
    )
    time.sleep(0.25)


def set_about(cdp, *, embed=False, open_doc=False):
    cdp.eval(
        f"""
(() => {{
  var note=document.getElementById('catalogDocNote');
  if(!note) return;
  var want={str(embed).lower()};
  if(note.classList.contains('is-embedded')!==want && typeof toggleDocNoteEmbed==='function') toggleDocNoteEmbed();
  if(typeof applyCatalogDocNoteOpen==='function') applyCatalogDocNoteOpen({str(open_doc).lower()});
  if(typeof parkCatalogDocNote==='function') parkCatalogDocNote();
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller());
  if(sc) sc.scrollTop=0;
}})()
"""
    )
    time.sleep(0.25)


def pair(cdp):
    before = cdp.eval(MEASURE)
    dy = cdp.eval(SCROLL) or 0
    time.sleep(0.15)
    after = cdp.eval(MEASURE)
    ix0 = (before.get("ix") or {}).get("y")
    ix1 = (after.get("ix") or {}).get("y")
    n0 = (before.get("note") or {}).get("y")
    n1 = (after.get("note") or {}).get("y")
    return {
        "before": before,
        "after": after,
        "scrolled": dy,
        "ixDrift": None if ix0 is None or ix1 is None else ix1 - ix0,
        "noteDrift": None if n0 is None or n1 is None else n1 - n0,
        "ixParent": before.get("ixParent"),
        "noteParent": before.get("noteParent"),
        "ixOnMain": before.get("ixOnMain"),
        "ixInBody": before.get("ixInBody"),
        "noteOnMain": before.get("noteOnMain"),
        "noteInBody": before.get("noteInBody"),
        "scrollMax": before.get("scrollMax"),
    }


def judge_window(name, p, errors, who="ix"):
    if p.get("scrolled", 0) < 80:
        errors.append(f"{name}: not enough scroll {p.get('scrolled')} max={p.get('scrollMax')}")
        return
    if who == "ix":
        if not p.get("ixOnMain"):
            errors.append(f"{name}: Index not on catalogMain parent={p.get('ixParent')}")
        if p.get("ixInBody"):
            errors.append(f"{name}: Index still in catalog-body")
        d = p.get("ixDrift")
        if d is None or abs(d) > 4:
            errors.append(f"{name}: Index window drift {d} (want ~0)")
    else:
        if not p.get("noteOnMain"):
            errors.append(f"{name}: About not on catalogMain parent={p.get('noteParent')}")
        if p.get("noteInBody"):
            errors.append(f"{name}: About still in catalog-body")
        d = p.get("noteDrift")
        if d is None or abs(d) > 4:
            errors.append(f"{name}: About window drift {d} (want ~0)")


def judge_embed(name, p, errors, who="ix"):
    if p.get("scrolled", 0) < 80:
        errors.append(f"{name}: not enough scroll {p.get('scrolled')} max={p.get('scrollMax')}")
        return
    if who == "ix":
        if not p.get("ixInBody"):
            errors.append(f"{name}: Index not in catalog-body parent={p.get('ixParent')}")
        if p.get("ixOnMain"):
            errors.append(f"{name}: Index still on catalogMain")
        d = p.get("ixDrift")
        if d is None or d > -40:
            errors.append(f"{name}: Index embed did not scroll away drift={d}")
    else:
        if not p.get("noteInBody"):
            errors.append(f"{name}: About not in catalog-body parent={p.get('noteParent')}")
        if p.get("noteOnMain"):
            errors.append(f"{name}: About still on catalogMain")
        d = p.get("noteDrift")
        if d is None or d > -40:
            errors.append(f"{name}: About embed did not scroll away drift={d}")


def main():
    httpd = ensure_http()
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
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.2)
    logf = open("/tmp/catalog-ix-doc-embed-flow.log", "w")
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
    for _ in range(80):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
            break
        except Exception:
            time.sleep(0.2)
    else:
        json.dump({"err": "cdp"}, open(OUT, "w"))
        sys.exit(1)

    results = {}
    errors = []
    try:
        tab = new_tab("about:blank")
        cdp = CDP(tab["webSocketDebuggerUrl"])

        def run_matrix(prefix, url, *, portable, views, modes):
            nav(cdp, url)
            for vw, vh, mobile in views:
                set_view(cdp, vw, vh, mobile=mobile)
                for mode in modes:
                    layout = "sides" if mode == "content" else mode
                    prep(cdp, mode=layout, portable=portable, content_only=(mode == "content"))
                    tag = f"{prefix}-{vw}x{vh}-{mode}"

                    set_ix(cdp, embed=False, open_list=False)
                    set_about(cdp, embed=False, open_doc=False)
                    p = pair(cdp)
                    results[tag + "-ixWinCol"] = p
                    judge_window(tag + "-ixWinCol", p, errors, "ix")
                    judge_window(tag + "-aboutWinCol", p, errors, "note")

                    set_ix(cdp, embed=False, open_list=True)
                    p = pair(cdp)
                    results[tag + "-ixWinOpen"] = p
                    judge_window(tag + "-ixWinOpen", p, errors, "ix")

                    set_ix(cdp, embed=True, open_list=False)
                    p = pair(cdp)
                    results[tag + "-ixEmbCol"] = p
                    judge_embed(tag + "-ixEmbCol", p, errors, "ix")

                    set_ix(cdp, embed=True, open_list=True)
                    p = pair(cdp)
                    results[tag + "-ixEmbOpen"] = p
                    judge_embed(tag + "-ixEmbOpen", p, errors, "ix")

                    set_ix(cdp, embed=False, open_list=False)
                    set_about(cdp, embed=True, open_doc=False)
                    p = pair(cdp)
                    results[tag + "-aboutEmbCol"] = p
                    judge_window(tag + "-ixWin-withAboutEmb", p, errors, "ix")
                    judge_embed(tag + "-aboutEmbCol", p, errors, "note")

                    set_about(cdp, embed=True, open_doc=True)
                    p = pair(cdp)
                    results[tag + "-aboutEmbOpen"] = p
                    judge_embed(tag + "-aboutEmbOpen", p, errors, "note")

                    set_about(cdp, embed=False, open_doc=True)
                    p = pair(cdp)
                    results[tag + "-aboutWinOpen"] = p
                    judge_window(tag + "-aboutWinOpen", p, errors, "note")

        run_matrix(
            "DS",
            f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html?v=ix-flow",
            portable=False,
            views=[(1400, 900, False), (900, 1400, False)],
            modes=["sides", "middle"],
        )
        run_matrix(
            "K",
            f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html?v=ix-flow",
            portable=False,
            views=[(1400, 900, False)],
            modes=["sides", "middle"],
        )
        run_matrix(
            "PDS",
            f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG-portable.html?v=ix-flow",
            portable=True,
            views=[(390, 844, True), (844, 390, True)],
            modes=["sides", "content"],
        )
        run_matrix(
            "PK",
            f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG-portable.html?v=ix-flow",
            portable=True,
            views=[(390, 844, True), (844, 390, True)],
            modes=["sides"],
        )
    finally:
        proc.terminate()
        if httpd:
            httpd.shutdown()

    slim = {"errors": errors, "results": {}}
    for k, v in results.items():
        slim["results"][k] = {
            "ixParent": v.get("ixParent"),
            "noteParent": v.get("noteParent"),
            "ixOnMain": v.get("ixOnMain"),
            "ixInBody": v.get("ixInBody"),
            "noteOnMain": v.get("noteOnMain"),
            "noteInBody": v.get("noteInBody"),
            "ixDrift": v.get("ixDrift"),
            "noteDrift": v.get("noteDrift"),
            "scrolled": v.get("scrolled"),
            "scrollMax": v.get("scrollMax"),
            "ixEmbed": (v.get("before") or {}).get("ixEmbed"),
            "noteEmbed": (v.get("before") or {}).get("noteEmbed"),
            "ixCollapsed": (v.get("before") or {}).get("ixCollapsed"),
        }
    Path(OUT).write_text(json.dumps(slim, indent=2), encoding="utf-8")
    print("errors", len(errors))
    for e in errors:
        print("ERR", e)
    for k, st in slim["results"].items():
        print(
            k,
            "ixP",
            st.get("ixParent"),
            "noteP",
            st.get("noteParent"),
            "ixD",
            st.get("ixDrift"),
            "noteD",
            st.get("noteDrift"),
            "sc",
            st.get("scrolled"),
            "ixMain/Body",
            st.get("ixOnMain"),
            st.get("ixInBody"),
            "noteMain/Body",
            st.get("noteOnMain"),
            st.get("noteInBody"),
        )
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
