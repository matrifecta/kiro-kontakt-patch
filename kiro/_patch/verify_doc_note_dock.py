#!/usr/bin/env python3
"""Measure About/Document bottom-dock and desktop portrait title clearance."""
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

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_doc_note_dock.json"
SHOT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9488
HTTP_PORT = 8797
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
PROFILE = "/tmp/catalog-doc-note-dock"
os.makedirs(SHOT, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

MEASURE = r"""
(() => {
  function box(el){
    if(!el) return null;
    var cs=getComputedStyle(el);
    if(cs.display==='none') return {shown:false,id:el.id||''};
    var r=el.getBoundingClientRect();
    return {
      shown: r.width>0 && r.height>0 && cs.visibility!=='hidden',
      id: el.id||'', cls: (el.className||'').toString().slice(0,80),
      x: Math.round(r.left), y: Math.round(r.top),
      r: Math.round(r.right), b: Math.round(r.bottom),
      w: Math.round(r.width), h: Math.round(r.height),
      parent: el.parentElement ? (el.parentElement.id||el.parentElement.tagName) : ''
    };
  }
  function overlap(a,b){
    if(!a||!b||!a.shown||!b.shown) return false;
    return a.x < b.r-1 && a.r > b.x+1 && a.y < b.b-1 && a.b > b.y+1;
  }
  var main=document.getElementById('catalogMain');
  var note=document.getElementById('catalogDocNote');
  var cb=document.querySelector('#catalogMain > .catalog-body')||document.querySelector('.catalog-body');
  var ix=document.getElementById('catalogIndex');
  var stack=document.getElementById('catalogJumpStack');
  var h1=document.querySelector('h1#top');
  var cluster=document.getElementById('hdrCluster');
  var layouts=document.getElementById('hdrLayoutBtns');
  var s=document.getElementById('hdrSearchBtn');
  var k=document.getElementById('hdrKwBtn');
  var disp=document.getElementById('displaySwitch');
  var collapse=document.getElementById('collapseCardsBtn');
  var custom=document.getElementById('layoutEditBtn');
  var bodyEl=document.getElementById('catalogDocNoteBody');
  var paras=[].map.call((bodyEl&&bodyEl.querySelectorAll('p'))||[], function(p){
    return (p.textContent||'').replace(/\s+/g,' ').trim();
  });
  var entries=[].filter.call(document.querySelectorAll('.catalog-body .entry'), function(e){
    var cs=getComputedStyle(e);
    return cs.display!=='none' && e.getBoundingClientRect().height>8;
  });
  var last=entries[entries.length-1];
  var nb=box(note), mb=box(main), ib=box(ix), jb=box(stack), hb=box(h1);
  var cbx=box(cb);
  var lastB=box(last);
  var jumpTop=box(stack&&stack.querySelector('a.top'));
  var jumpBot=box(stack&&stack.querySelector('a.bottom'));
  return {
    title: document.title,
    h1: (h1&&(h1.getAttribute('aria-label')||h1.textContent)||'').replace(/\s+/g,' ').trim(),
    vw: innerWidth, vh: innerHeight,
    cls: document.body.className,
    portable: !!window.CATALOG_PORTABLE,
    fill: document.body.classList.contains('index-fill-doc'),
    ixWindow: document.body.classList.contains('index-window-open'),
    ixCollapsed: !!(ix&&ix.classList.contains('is-collapsed')),
    ixEmbed: !!(ix&&ix.classList.contains('is-embedded')),
    noteCollapsed: !!(note&&note.classList.contains('is-collapsed')),
    paras: paras,
    addedCount: paras.filter(function(p){return /Added libraries/i.test(p);}).length,
    noteParent: note&&note.parentElement&&note.parentElement.id,
    prev: note&&note.previousElementSibling&&(note.previousElementSibling.id||note.previousElementSibling.className||''),
    mainOv: main?getComputedStyle(main).overflowY:'',
    bodyOv: cb?getComputedStyle(cb).overflowY:'',
    bodyFlex: cb?getComputedStyle(cb).flex:'',
    noteFlex: note?getComputedStyle(note).flex:'',
    main: mb, note: nb, catalogBody: cbx, index: ib, jump: jb,
    jumpTop: jumpTop, jumpBot: jumpBot, lastCard: lastB,
    visEntries: entries.length,
    h1b: hb, cluster: box(cluster), layouts: box(layouts),
    search: box(s), kw: box(k), disp: box(disp),
    collapse: box(collapse), custom: box(custom),
    gapMainNote: (nb&&mb)?(mb.b-nb.b):null,
    noteAtBottom: !!(nb&&mb&&Math.abs(mb.b-nb.b)<=8),
    lastAboveNote: !!(lastB&&nb&&lastB.b<=nb.y+4),
    ixNoteGap: (ib&&nb&&ib.shown&&nb.shown)?(nb.y-ib.b):null,
    jumpAboveNote: (jb&&nb&&jb.shown&&nb.shown)?(nb.y-jb.b):null,
    jumpBotAboveNote: (jumpBot&&nb&&jumpBot.shown&&nb.shown)?(nb.y-jumpBot.b):null,
    h1OverlapCluster: overlap(hb, box(cluster)),
    h1OverlapLayouts: overlap(hb, box(layouts)),
    h1OverlapS: overlap(hb, box(s)),
    h1OverlapK: overlap(hb, box(k)),
    h1OverlapDisp: overlap(hb, box(disp)),
    h1RightToCluster: (hb&&cluster)?Math.round(cluster.getBoundingClientRect().left-h1.getBoundingClientRect().right):null,
    h1RightToS: (hb&&s)?Math.round(s.getBoundingClientRect().left-h1.getBoundingClientRect().right):null
  };
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

    def eval(self, expr, await_promise=False):
        r = self.call(
            "Runtime.evaluate",
            {"expression": expr, "awaitPromise": await_promise, "returnByValue": True},
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def wait_ready(cdp):
    for _ in range(100):
        try:
            n = cdp.eval(
                "!!(window.setDisplayMode&&document.getElementById('catalogDocNote')&&document.querySelectorAll('.entry').length>3)"
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
    time.sleep(0.35)


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png"})
    raw = data.get("data")
    if raw:
        Path(SHOT, name).write_bytes(base64.b64decode(raw))


def nav(cdp, url):
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": url})
    time.sleep(0.4)
    wait_ready(cdp)


def prep_desktop(cdp, query=""):
    cdp.eval(
        """
(() => {
  try{localStorage.setItem('catalog-doc-note-open-ds','0');}catch(e){}
  try{localStorage.setItem('catalog-doc-note-open-kontakt','0');}catch(e){}
  if(typeof setDisplayMode==='function') setDisplayMode('sides',{pick:true});
  if(typeof applyCatalogDocNoteOpen==='function') applyCatalogDocNoteOpen(false);
  if(typeof parkCatalogDocNote==='function') parkCatalogDocNote();
  if(typeof placeCatalogJumpStack==='function') placeCatalogJumpStack();
})()
"""
    )
    time.sleep(0.25)
    if query:
        cdp.eval(
            f"""
(() => {{
  var inp=document.getElementById('searchInput');
  if(!inp) return;
  inp.focus();
  inp.value={json.dumps(query)};
  inp.dispatchEvent(new Event('input',{{bubbles:true}}));
  if(typeof filterEntries==='function') filterEntries();
  if(typeof applySearch==='function') applySearch();
  if(typeof runSearch==='function') runSearch();
}})()
"""
        )
        time.sleep(0.35)


def prep_portable(cdp, *, kw_off=False, index_open=False, content_only=False):
    js = f"""
(() => {{
  if(typeof applyCatalogDocNoteOpen==='function') applyCatalogDocNoteOpen(false);
  if(typeof parkCatalogDocNote==='function') parkCatalogDocNote();
  var b=document.body;
  if({str(content_only).lower()}){{
    if(typeof setDisplayMode==='function') setDisplayMode('sides',{{pick:true}});
    b.classList.add('search-chrome-collapsed','kw-chrome-collapsed');
    b.classList.remove('kw-open');
  }}else{{
    if(typeof setDisplayMode==='function') setDisplayMode('sides',{{pick:true}});
    b.classList.remove('search-chrome-collapsed');
    if({str(kw_off).lower()}){{
      b.classList.add('kw-chrome-collapsed');
      b.classList.remove('kw-open');
    }}else{{
      b.classList.remove('kw-chrome-collapsed');
      b.classList.add('kw-open');
    }}
  }}
  var ix=document.getElementById('catalogIndex');
  if(ix){{
    ix.classList.remove('is-embedded');
    if({str(index_open).lower()}) ix.classList.remove('is-collapsed');
    else ix.classList.add('is-collapsed');
  }}
  if(typeof syncIndexWindowDock==='function') syncIndexWindowDock();
  if(typeof applyIndexFillDocStyles==='function') applyIndexFillDocStyles();
  if(typeof applySidesCols==='function') applySidesCols();
  if(typeof placeCatalogJumpStack==='function') placeCatalogJumpStack();
}})()
"""
    cdp.eval(js)
    time.sleep(0.35)


def scroll_end(cdp):
    cdp.eval(
        """
(() => {
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())
    || document.querySelector('#catalogMain > .catalog-body')
    || document.getElementById('catalogMain');
  if(sc) sc.scrollTop=sc.scrollHeight;
})()
"""
    )
    time.sleep(0.25)


def toggle_note(cdp, open_it):
    cdp.eval(
        f"if(typeof applyCatalogDocNoteOpen==='function') applyCatalogDocNoteOpen({str(open_it).lower()});"
        "if(typeof placeCatalogJumpStack==='function') placeCatalogJumpStack();"
    )
    time.sleep(0.2)


def judge_dock(name, st, errors, *, expect_fill=False, title=None, added=None):
    if not st:
        errors.append(name + ": no state")
        return
    if title and st.get("title") != title:
        errors.append(f"{name}.title={st.get('title')!r}")
    if added is not None and st.get("addedCount") != added:
        errors.append(f"{name}.added={st.get('addedCount')} paras={st.get('paras')}")
    if st.get("noteParent") != "catalogMain":
        errors.append(f"{name}.noteParent={st.get('noteParent')}")
    if not st.get("noteAtBottom"):
        errors.append(
            f"{name}.notAtBottom gap={st.get('gapMainNote')} mainB={(st.get('main') or {}).get('b')} noteB={(st.get('note') or {}).get('b')} noteY={(st.get('note') or {}).get('y')}"
        )
    if st.get("mainOv") not in ("hidden", "clip"):
        errors.append(f"{name}.mainOv={st.get('mainOv')}")
    jump_clear = st.get("jumpBotAboveNote")
    if jump_clear is not None and jump_clear < -2 and (st.get("jumpBot") or {}).get("shown"):
        errors.append(f"{name}.jumpOverlap={jump_clear}")
    if expect_fill:
        if not st.get("fill"):
            errors.append(name + ": expected index-fill-doc")
        gap = st.get("ixNoteGap")
        if gap is None or gap < 2 or gap > 16:
            errors.append(f"{name}.ixGap={gap}")
    if st.get("h1OverlapS") or st.get("h1OverlapK") or st.get("h1OverlapDisp") or st.get("h1OverlapLayouts"):
        errors.append(
            f"{name}.h1Overlap s={st.get('h1OverlapS')} k={st.get('h1OverlapK')} disp={st.get('h1OverlapDisp')} lay={st.get('h1OverlapLayouts')} gapC={st.get('h1RightToCluster')} gapS={st.get('h1RightToS')}"
        )


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
    logf = open("/tmp/catalog-doc-note-dock.log", "w")
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

        # Desktop DS landscape short cards
        nav(cdp, f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html?v=doc-dock")
        set_view(cdp, 1400, 900, mobile=False)
        prep_desktop(cdp, "domra")
        st = cdp.eval(MEASURE)
        results["DS1400-closed"] = st
        shot(cdp, "D1400-doc-note-closed.png")
        judge_dock("DS1400-closed", st, errors, title="Decent Library", added=1)

        toggle_note(cdp, True)
        st = cdp.eval(MEASURE)
        results["DS1400-open"] = st
        shot(cdp, "D1400-doc-note-open.png")
        judge_dock("DS1400-open", st, errors, title="Decent Library", added=1)
        if st and st.get("noteCollapsed"):
            errors.append("DS1400-open still collapsed")
        closed_top = (results["DS1400-closed"].get("note") or {}).get("y")
        open_top = (st.get("note") or {}).get("y") if st else None
        if closed_top is not None and open_top is not None and open_top >= closed_top - 2:
            errors.append(f"DS1400-open did not grow up closedY={closed_top} openY={open_top}")

        scroll_end(cdp)
        st = cdp.eval(MEASURE)
        results["DS1400-scrolled"] = st
        shot(cdp, "D1400-doc-note-scrolled.png")
        judge_dock("DS1400-scrolled", st, errors, title="Decent Library", added=1)
        if st and not st.get("lastAboveNote") and st.get("lastCard"):
            errors.append(
                f"DS1400-scrolled last not above note lastB={(st.get('lastCard') or {}).get('b')} noteY={(st.get('note') or {}).get('y')}"
            )

        toggle_note(cdp, False)
        # Desktop DS portrait title
        set_view(cdp, 900, 1400, mobile=False)
        prep_desktop(cdp, "")
        st = cdp.eval(MEASURE)
        results["DS900-portrait"] = st
        shot(cdp, "D900-doc-title-portrait.png")
        judge_dock("DS900-portrait", st, errors, title="Decent Library", added=1)

        set_view(cdp, 1400, 900, mobile=False)
        prep_desktop(cdp, "")
        st = cdp.eval(MEASURE)
        results["DS1400-land-title"] = st
        shot(cdp, "D1400-doc-title-land.png")
        judge_dock("DS1400-land-title", st, errors, title="Decent Library", added=1)

        # Desktop Kontakt
        nav(cdp, f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html?v=doc-dock")
        set_view(cdp, 1400, 900, mobile=False)
        prep_desktop(cdp, "piano")
        st = cdp.eval(MEASURE)
        results["K1400-closed"] = st
        shot(cdp, "K1400-doc-note-closed.png")
        judge_dock("K1400-closed", st, errors, title="Kontakt Library", added=0)
        set_view(cdp, 900, 1400, mobile=False)
        prep_desktop(cdp, "")
        st = cdp.eval(MEASURE)
        results["K900-portrait"] = st
        shot(cdp, "K900-doc-title-portrait.png")
        judge_dock("K900-portrait", st, errors, title="Kontakt Library", added=0)

        # Portable DS portrait
        nav(cdp, f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG-portable.html?v=doc-dock")
        set_view(cdp, 390, 844, mobile=True)
        prep_portable(cdp, kw_off=True, index_open=False)
        st = cdp.eval(MEASURE)
        results["PDS390-ixcol"] = st
        shot(cdp, "PDS390-doc-ixcol.png")
        judge_dock("PDS390-ixcol", st, errors, title="DS Lib", added=0)

        prep_portable(cdp, kw_off=True, index_open=True)
        st = cdp.eval(MEASURE)
        results["PDS390-ixopen-fill"] = st
        shot(cdp, "PDS390-doc-ixopen.png")
        judge_dock("PDS390-ixopen-fill", st, errors, expect_fill=True, title="DS Lib", added=0)

        prep_portable(cdp, content_only=True, index_open=False)
        st = cdp.eval(MEASURE)
        results["PDS390-content"] = st
        shot(cdp, "PDS390-doc-content.png")
        judge_dock("PDS390-content", st, errors, title="DS Lib", added=0)

        set_view(cdp, 844, 390, mobile=True)
        prep_portable(cdp, kw_off=True, index_open=False)
        st = cdp.eval(MEASURE)
        results["PDS844-ixcol"] = st
        shot(cdp, "PDS844-doc-ixcol.png")
        judge_dock("PDS844-ixcol", st, errors, title="DS Lib", added=0)

        prep_portable(cdp, kw_off=True, index_open=True)
        st = cdp.eval(MEASURE)
        results["PDS844-ixopen-fill"] = st
        shot(cdp, "PDS844-doc-ixopen.png")
        judge_dock("PDS844-ixopen-fill", st, errors, expect_fill=True, title="DS Lib", added=0)

        prep_portable(cdp, content_only=True, index_open=False)
        st = cdp.eval(MEASURE)
        results["PDS844-content"] = st
        shot(cdp, "PDS844-doc-content.png")
        judge_dock("PDS844-content", st, errors, title="DS Lib", added=0)

        # Portable Kontakt sample
        nav(cdp, f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG-portable.html?v=doc-dock")
        set_view(cdp, 390, 844, mobile=True)
        prep_portable(cdp, kw_off=True, index_open=True)
        st = cdp.eval(MEASURE)
        results["PK390-ixopen-fill"] = st
        shot(cdp, "PK390-doc-ixopen.png")
        judge_dock("PK390-ixopen-fill", st, errors, expect_fill=True, title="Kontakt Lib", added=0)

        set_view(cdp, 844, 390, mobile=True)
        prep_portable(cdp, kw_off=True, index_open=False)
        st = cdp.eval(MEASURE)
        results["PK844-ixcol"] = st
        shot(cdp, "PK844-doc-ixcol.png")
        judge_dock("PK844-ixcol", st, errors, title="Kontakt Lib", added=0)

    finally:
        proc.terminate()
        if httpd:
            httpd.shutdown()

    payload = {"errors": errors, "results": results}
    Path(OUT).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("errors", len(errors))
    for e in errors:
        print("ERR", e)
    for k, st in results.items():
        if not st:
            print(k, "NONE")
            continue
        print(
            k,
            "title",
            st.get("title"),
            "h1",
            st.get("h1"),
            "gap",
            st.get("gapMainNote"),
            "atBot",
            st.get("noteAtBottom"),
            "ixGap",
            st.get("ixNoteGap"),
            "jump",
            st.get("jumpBotAboveNote"),
            "h1gapS",
            st.get("h1RightToS"),
            "added",
            st.get("addedCount"),
            "fill",
            st.get("fill"),
            "noteY/B",
            (st.get("note") or {}).get("y"),
            (st.get("note") or {}).get("b"),
            "mainB",
            (st.get("main") or {}).get("b"),
        )
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
