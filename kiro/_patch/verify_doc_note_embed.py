#!/usr/bin/env python3
"""Prove About Window/Embed matches Index: dock, in-flow, pref, fill, jump."""
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

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_doc_note_embed.json"
SHOT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9491
HTTP_PORT = 8797
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
PROFILE = "/tmp/catalog-doc-note-embed"
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
      id: el.id||'', cls: (el.className||'').toString().slice(0,90),
      x: Math.round(r.left), y: Math.round(r.top),
      r: Math.round(r.right), b: Math.round(r.bottom),
      w: Math.round(r.width), h: Math.round(r.height),
      parent: el.parentElement ? (el.parentElement.id||el.parentElement.className||el.parentElement.tagName) : '',
      pos: cs.position, flex: cs.flex, ov: cs.overflowY
    };
  }
  var main=document.getElementById('catalogMain');
  var note=document.getElementById('catalogDocNote');
  var notes=document.querySelectorAll('#catalogDocNote,.catalog-doc-note');
  var cb=document.querySelector('#catalogMain > .catalog-body')||document.querySelector('.catalog-body');
  var ix=document.getElementById('catalogIndex');
  var stack=document.getElementById('catalogJumpStack');
  var btn=document.getElementById('catalogDocNoteEmbed');
  var ixBtn=document.getElementById('catalogIndexEmbed');
  var bodyEl=document.getElementById('catalogDocNoteBody');
  var paras=[].map.call((bodyEl&&bodyEl.querySelectorAll('p'))||[], function(p){
    return (p.textContent||'').replace(/\s+/g,' ').trim();
  });
  var entries=[].filter.call(document.querySelectorAll('.catalog-body .entry'), function(e){
    var cs=getComputedStyle(e);
    return cs.display!=='none' && e.getBoundingClientRect().height>8 && e!==note;
  });
  var last=entries[entries.length-1];
  var nb=box(note), mb=box(main), ib=box(ix), jb=box(stack);
  var cbx=box(cb);
  var lastB=box(last);
  var jumpBot=box(stack&&stack.querySelector('a.bottom'));
  var pref=null;try{pref=localStorage.getItem('catalog-doc-note-embed-'+(window.CATALOG_NS||'catalog'));}catch(e){}
  var ixPref=null;try{ixPref=localStorage.getItem('catalog-index-embed-'+(window.CATALOG_NS||'catalog'));}catch(e){}
  return {
    title: document.title,
    vw: innerWidth, vh: innerHeight,
    cls: document.body.className,
    portable: !!window.CATALOG_PORTABLE,
    fill: document.body.classList.contains('index-fill-doc'),
    ixWindow: document.body.classList.contains('index-window-open'),
    docWindow: document.body.classList.contains('doc-note-window-open'),
    docEmbeddedCls: document.body.classList.contains('doc-note-embedded'),
    ixCollapsed: !!(ix&&ix.classList.contains('is-collapsed')),
    ixEmbed: !!(ix&&ix.classList.contains('is-embedded')),
    noteCollapsed: !!(note&&note.classList.contains('is-collapsed')),
    noteEmbed: !!(note&&note.classList.contains('is-embedded')),
    noteCount: notes.length,
    noteParent: note&&note.parentElement&&(note.parentElement.id||note.parentElement.className||''),
    prev: note&&note.previousElementSibling&&(note.previousElementSibling.id||note.previousElementSibling.className||''),
    next: note&&note.nextElementSibling&&(note.nextElementSibling.id||note.nextElementSibling.className||''),
    mainOv: main?getComputedStyle(main).overflowY:'',
    bodyOv: cb?getComputedStyle(cb).overflowY:'',
    bodyH: cb?Math.round(cb.getBoundingClientRect().height):0,
    noteFlex: note?getComputedStyle(note).flex:'',
    main: mb, note: nb, catalogBody: cbx, index: ib, jump: jb,
    jumpBot: jumpBot, lastCard: lastB,
    visEntries: entries.length,
    btnText: btn?btn.textContent:'',
    btnPressed: btn?btn.getAttribute('aria-pressed'):'',
    btnHidden: !!(btn&&btn.hidden),
    ixBtnHidden: !!(ixBtn&&ixBtn.hidden),
    pref: pref,
    ixPref: ixPref,
    paras: paras,
    addedCount: paras.filter(function(p){return /Added libraries/i.test(p);}).length,
    gapMainNote: (nb&&mb)?(mb.b-nb.b):null,
    noteAtBottom: !!(nb&&mb&&Math.abs(mb.b-nb.b)<=8),
    lastAboveNote: !!(lastB&&nb&&lastB.b<=nb.y+8),
    ixNoteGap: (ib&&nb&&ib.shown&&nb.shown)?(nb.y-ib.b):null,
    ixMainBotGap: (ib&&mb&&ib.shown&&mb.shown)?(mb.b-ib.b):null,
    jumpBotAboveNote: (jumpBot&&nb&&jumpBot.shown&&nb.shown)?(nb.y-jumpBot.b):null
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
    for _ in range(120):
        try:
            n = cdp.eval(
                "!!(window.toggleDocNoteEmbed&&document.getElementById('catalogDocNoteEmbed')&&document.getElementById('catalogDocNote')&&document.querySelectorAll('.entry').length>3)"
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
    time.sleep(0.5)
    wait_ready(cdp)


def js(cdp, code):
    cdp.eval(code)
    time.sleep(0.25)


def prep_desktop(cdp, query="", *, sides=True, middle=False, content_only=False):
    mode = "middle" if middle else "sides"
    cdp.eval(
        f"""
(() => {{
  try{{localStorage.setItem('catalog-doc-note-embed-ds','0');}}catch(e){{}}
  try{{localStorage.setItem('catalog-doc-note-embed-kontakt','0');}}catch(e){{}}
  try{{localStorage.setItem('catalog-index-embed-ds','0');}}catch(e){{}}
  try{{localStorage.setItem('catalog-index-embed-kontakt','0');}}catch(e){{}}
  if(typeof setDisplayMode==='function') setDisplayMode({json.dumps(mode)},{{pick:true}});
  var b=document.body;
  if({str(content_only).lower()}){{
    b.classList.add('search-chrome-collapsed','kw-chrome-collapsed');
    b.classList.remove('kw-open');
  }}
  var ix=document.getElementById('catalogIndex');
  if(ix){{ix.classList.remove('is-embedded');ix.classList.add('is-collapsed');}}
  if(typeof applyCatalogDocNoteOpen==='function') applyCatalogDocNoteOpen(false);
  if(typeof applyDocNoteEmbedPref==='function') applyDocNoteEmbedPref();
  if(typeof parkCatalogDocNote==='function') parkCatalogDocNote();
  if(typeof placeCatalogJumpStack==='function') placeCatalogJumpStack();
}})()
"""
    )
    time.sleep(0.25)
    if query:
        cdp.eval(
            f"""
(() => {{
  var inp=document.getElementById('searchInput');
  if(!inp) return;
  inp.value={json.dumps(query)};
  inp.dispatchEvent(new Event('input',{{bubbles:true}}));
  if(typeof filterEntries==='function') filterEntries();
  if(typeof applySearch==='function') applySearch();
  if(typeof runSearch==='function') runSearch();
}})()
"""
        )
        time.sleep(0.3)


def prep_portable(cdp, *, kw_off=False, index_open=False, content_only=False, about_embed=False, index_embed=False):
    js_code = f"""
(() => {{
  try{{localStorage.setItem('catalog-doc-note-embed-'+(window.CATALOG_NS||'catalog'), {json.dumps('1' if about_embed else '0')});}}catch(e){{}}
  try{{localStorage.setItem('catalog-index-embed-'+(window.CATALOG_NS||'catalog'), {json.dumps('1' if index_embed else '0')});}}catch(e){{}}
  var b=document.body;
  if(typeof setDisplayMode==='function') setDisplayMode('sides',{{pick:true}});
  if({str(content_only).lower()}){{
    b.classList.add('search-chrome-collapsed','kw-chrome-collapsed');
    b.classList.remove('kw-open');
  }}else{{
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
    if({str(index_embed).lower()}) ix.classList.add('is-embedded');
    else ix.classList.remove('is-embedded');
    if({str(index_open).lower()}) ix.classList.remove('is-collapsed');
    else ix.classList.add('is-collapsed');
  }}
  if(typeof applyCatalogDocNoteOpen==='function') applyCatalogDocNoteOpen(false);
  if(typeof applyDocNoteEmbedPref==='function') applyDocNoteEmbedPref();
  if(typeof parkCatalogDocNote==='function') parkCatalogDocNote();
  if(typeof syncIndexWindowDock==='function') syncIndexWindowDock();
  if(typeof applyIndexFillDocStyles==='function') applyIndexFillDocStyles();
  if(typeof placeCatalogJumpStack==='function') placeCatalogJumpStack();
}})()
"""
    cdp.eval(js_code)
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


def set_about_embed(cdp, on):
    cdp.eval(
        f"""
(() => {{
  var note=document.getElementById('catalogDocNote');
  if(!note) return;
  var want={str(on).lower()};
  var has=note.classList.contains('is-embedded');
  if(want!==has && typeof toggleDocNoteEmbed==='function') toggleDocNoteEmbed();
  if(typeof parkCatalogDocNote==='function') parkCatalogDocNote();
  if(typeof applyIndexFillDocStyles==='function') applyIndexFillDocStyles();
  if(typeof placeCatalogJumpStack==='function') placeCatalogJumpStack();
}})()
"""
    )
    time.sleep(0.25)


def judge_window(name, st, errors, *, expect_fill=False, title=None, added=None):
    if not st:
        errors.append(name + ": no state")
        return
    if title and st.get("title") != title:
        errors.append(f"{name}.title={st.get('title')!r}")
    if added is not None and st.get("addedCount") != added:
        errors.append(f"{name}.added={st.get('addedCount')} paras={st.get('paras')}")
    if st.get("noteCount") != 1:
        errors.append(f"{name}.noteCount={st.get('noteCount')}")
    if st.get("noteEmbed"):
        errors.append(f"{name}.expectedWindow embed={st.get('noteEmbed')}")
    if st.get("noteParent") != "catalogMain":
        errors.append(f"{name}.noteParent={st.get('noteParent')}")
    if not st.get("noteAtBottom"):
        errors.append(f"{name}.notAtBottom gap={st.get('gapMainNote')}")
    if st.get("btnHidden"):
        errors.append(f"{name}.embedBtn hidden")
    if st.get("btnText") not in ("Embed",):
        errors.append(f"{name}.btnText={st.get('btnText')!r}")
    jump_clear = st.get("jumpBotAboveNote")
    if jump_clear is not None and jump_clear < -2 and (st.get("jumpBot") or {}).get("shown"):
        errors.append(f"{name}.jumpOverlap={jump_clear}")
    if expect_fill:
        if not st.get("fill"):
            errors.append(name + ": expected index-fill-doc")
        gap = st.get("ixNoteGap")
        if gap is None or gap < 2 or gap > 16:
            errors.append(f"{name}.ixGap={gap}")


def judge_embed(name, st, errors, *, title=None):
    if not st:
        errors.append(name + ": no state")
        return
    if title and st.get("title") != title:
        errors.append(f"{name}.title={st.get('title')!r}")
    if st.get("noteCount") != 1:
        errors.append(f"{name}.noteCount={st.get('noteCount')}")
    if not st.get("noteEmbed"):
        errors.append(f"{name}.expectedEmbed")
    parent = st.get("noteParent") or ""
    if parent == "catalogMain":
        errors.append(f"{name}.stillDocked parent={parent}")
    if "catalog-body" not in parent and parent != "catalog-body":
        errors.append(f"{name}.noteParent={parent}")
    if st.get("btnText") not in ("Window",):
        errors.append(f"{name}.btnText={st.get('btnText')!r}")
    if st.get("pref") != "1":
        errors.append(f"{name}.pref={st.get('pref')!r}")


def judge_fill_embed(name, st, errors):
    if not st:
        errors.append(name + ": no state")
        return
    if not st.get("fill"):
        errors.append(name + ": expected fill")
    if st.get("noteParent") == "catalogMain":
        errors.append(f"{name}.aboutStillDocked")
    gap = st.get("ixMainBotGap")
    if gap is None or gap < 0 or gap > 16:
        errors.append(f"{name}.ixToMainBot={gap}")
    if st.get("bodyH", 0) > 8:
        errors.append(f"{name}.bodyNotCollapsed h={st.get('bodyH')}")


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
    logf = open("/tmp/catalog-doc-note-embed.log", "w")
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

        nav(cdp, f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html?v=doc-embed")
        set_view(cdp, 1400, 900, mobile=False)
        prep_desktop(cdp, "domra")
        st = cdp.eval(MEASURE)
        results["DS1400-win-closed"] = st
        shot(cdp, "D1400-doc-embed-win-closed.png")
        judge_window("DS1400-win-closed", st, errors, title="Decent Library", added=1)

        toggle_note(cdp, True)
        st = cdp.eval(MEASURE)
        results["DS1400-win-open"] = st
        shot(cdp, "D1400-doc-embed-win-open.png")
        judge_window("DS1400-win-open", st, errors, title="Decent Library", added=1)
        closed_top = (results["DS1400-win-closed"].get("note") or {}).get("y")
        open_top = (st.get("note") or {}).get("y") if st else None
        if closed_top is not None and open_top is not None and open_top >= closed_top - 2:
            errors.append(f"DS1400-win-open did not grow up closedY={closed_top} openY={open_top}")

        scroll_end(cdp)
        st = cdp.eval(MEASURE)
        results["DS1400-win-scrolled"] = st
        shot(cdp, "D1400-doc-embed-win-scrolled.png")
        judge_window("DS1400-win-scrolled", st, errors, title="Decent Library", added=1)
        if st and not st.get("lastAboveNote") and st.get("lastCard"):
            errors.append(
                f"DS1400-win-scrolled last not above note lastB={(st.get('lastCard') or {}).get('b')} noteY={(st.get('note') or {}).get('y')}"
            )

        set_about_embed(cdp, True)
        cdp.eval(
            """
(() => {
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())
    || document.querySelector('#catalogMain > .catalog-body')
    || document.getElementById('catalogMain');
  if(sc) sc.scrollTop=0;
})()
"""
        )
        time.sleep(0.2)
        st = cdp.eval(MEASURE)
        results["DS1400-embed"] = st
        shot(cdp, "D1400-doc-embed-on.png")
        judge_embed("DS1400-embed", st, errors, title="Decent Library")
        if st and st.get("noteAtBottom") and st.get("visEntries", 0) > 4:
            errors.append("DS1400-embed stuck to pane bottom while cards remain above")

        set_about_embed(cdp, False)
        st = cdp.eval(MEASURE)
        results["DS1400-win-again"] = st
        shot(cdp, "D1400-doc-embed-off.png")
        judge_window("DS1400-win-again", st, errors, title="Decent Library", added=1)
        if st and st.get("pref") not in ("0", None):
            errors.append(f"DS1400-win-again.pref={st.get('pref')!r}")

        set_about_embed(cdp, True)
        nav(cdp, f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html?v=doc-embed-reload")
        set_view(cdp, 1400, 900, mobile=False)
        js(
            cdp,
            "if(typeof setDisplayMode==='function') setDisplayMode('sides',{pick:true});"
            "if(typeof parkCatalogDocNote==='function') parkCatalogDocNote();",
        )
        st = cdp.eval(MEASURE)
        results["DS1400-pref-reload"] = st
        shot(cdp, "D1400-doc-embed-reload.png")
        if not st or not st.get("noteEmbed") or st.get("pref") != "1":
            errors.append(f"DS1400-pref-reload embed={st and st.get('noteEmbed')} pref={st and st.get('pref')}")
        if st and st.get("noteParent") == "catalogMain":
            errors.append("DS1400-pref-reload still docked")

        set_about_embed(cdp, False)
        prep_desktop(cdp, "")
        set_view(cdp, 1400, 900, mobile=False)
        js(
            cdp,
            """
(() => {
  var ix=document.getElementById('catalogIndex');
  if(ix){ix.classList.remove('is-embedded','is-collapsed');}
  if(typeof applyIndexScrollFit==='function') applyIndexScrollFit();
  if(typeof parkCatalogDocNote==='function') parkCatalogDocNote();
  if(typeof placeCatalogJumpStack==='function') placeCatalogJumpStack();
})()
""",
        )
        st = cdp.eval(MEASURE)
        results["DS1400-ixwin-aboutwin"] = st
        shot(cdp, "D1400-doc-ixwin-aboutwin.png")
        judge_window("DS1400-ixwin-aboutwin", st, errors, title="Decent Library", added=1)
        if st:
            ixb = (st.get("index") or {}).get("y")
            notey = (st.get("note") or {}).get("y")
            if ixb is not None and notey is not None and ixb > notey:
                errors.append(f"DS1400-ixwin-aboutwin index below about ixY={ixb} noteY={notey}")

        prep_desktop(cdp, "", middle=True)
        st = cdp.eval(MEASURE)
        results["DS1400-middle-win"] = st
        shot(cdp, "D1400-doc-middle-win.png")
        if st and st.get("btnHidden"):
            errors.append("DS1400-middle embed btn hidden")
        if st and st.get("noteCount") != 1:
            errors.append("DS1400-middle noteCount")

        nav(cdp, f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html?v=doc-embed")
        set_view(cdp, 1400, 900, mobile=False)
        prep_desktop(cdp, "piano")
        st = cdp.eval(MEASURE)
        results["K1400-win"] = st
        shot(cdp, "K1400-doc-embed-win.png")
        judge_window("K1400-win", st, errors, title="Kontakt Library", added=0)
        set_about_embed(cdp, True)
        st = cdp.eval(MEASURE)
        results["K1400-embed"] = st
        shot(cdp, "K1400-doc-embed-on.png")
        judge_embed("K1400-embed", st, errors, title="Kontakt Library")
        set_about_embed(cdp, False)

        set_view(cdp, 900, 1400, mobile=False)
        prep_desktop(cdp, "")
        st = cdp.eval(MEASURE)
        results["K900-portrait-win"] = st
        shot(cdp, "K900-doc-embed-portrait.png")
        judge_window("K900-portrait-win", st, errors, title="Kontakt Library", added=0)

        nav(cdp, f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG-portable.html?v=doc-embed")
        set_view(cdp, 390, 844, mobile=True)
        prep_portable(cdp, kw_off=True, index_open=False)
        st = cdp.eval(MEASURE)
        results["PDS390-win"] = st
        shot(cdp, "PDS390-doc-embed-win.png")
        judge_window("PDS390-win", st, errors, title="DS Lib", added=0)
        if st and st.get("btnHidden"):
            errors.append("PDS390-win embed btn hidden on portable")

        prep_portable(cdp, kw_off=True, index_open=True)
        st = cdp.eval(MEASURE)
        results["PDS390-fill-win"] = st
        shot(cdp, "PDS390-doc-fill-win.png")
        judge_window("PDS390-fill-win", st, errors, expect_fill=True, title="DS Lib", added=0)

        prep_portable(cdp, kw_off=True, index_open=True, about_embed=True)
        st = cdp.eval(MEASURE)
        results["PDS390-fill-embed"] = st
        shot(cdp, "PDS390-doc-fill-embed.png")
        judge_fill_embed("PDS390-fill-embed", st, errors)

        prep_portable(cdp, content_only=True, index_open=False)
        st = cdp.eval(MEASURE)
        results["PDS390-content"] = st
        shot(cdp, "PDS390-doc-content-win.png")
        if st and st.get("btnHidden"):
            errors.append("PDS390-content embed btn hidden")
        judge_window("PDS390-content", st, errors, title="DS Lib", added=0)

        set_view(cdp, 844, 390, mobile=True)
        prep_portable(cdp, kw_off=True, index_open=True)
        st = cdp.eval(MEASURE)
        results["PDS844-fill-win"] = st
        shot(cdp, "PDS844-doc-fill-win.png")
        judge_window("PDS844-fill-win", st, errors, expect_fill=True, title="DS Lib", added=0)

        prep_portable(cdp, kw_off=True, index_open=True, about_embed=True)
        st = cdp.eval(MEASURE)
        results["PDS844-fill-embed"] = st
        shot(cdp, "PDS844-doc-fill-embed.png")
        judge_fill_embed("PDS844-fill-embed", st, errors)

        prep_portable(cdp, content_only=True, index_open=False, about_embed=True)
        st = cdp.eval(MEASURE)
        results["PDS844-content-embed"] = st
        shot(cdp, "PDS844-doc-content-embed.png")
        judge_embed("PDS844-content-embed", st, errors, title="DS Lib")

        nav(cdp, f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG-portable.html?v=doc-embed")
        set_view(cdp, 390, 844, mobile=True)
        prep_portable(cdp, kw_off=True, index_open=True)
        st = cdp.eval(MEASURE)
        results["PK390-fill-win"] = st
        shot(cdp, "PK390-doc-fill-win.png")
        judge_window("PK390-fill-win", st, errors, expect_fill=True, title="Kontakt Lib", added=0)

        prep_portable(cdp, kw_off=True, index_open=True, about_embed=True)
        st = cdp.eval(MEASURE)
        results["PK390-fill-embed"] = st
        shot(cdp, "PK390-doc-fill-embed.png")
        judge_fill_embed("PK390-fill-embed", st, errors)

        set_view(cdp, 844, 390, mobile=True)
        prep_portable(cdp, content_only=True, index_open=False)
        st = cdp.eval(MEASURE)
        results["PK844-content-win"] = st
        shot(cdp, "PK844-doc-content-win.png")
        judge_window("PK844-content-win", st, errors, title="Kontakt Lib", added=0)

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
            "parent",
            st.get("noteParent"),
            "embed",
            st.get("noteEmbed"),
            "atBot",
            st.get("noteAtBottom"),
            "gap",
            st.get("gapMainNote"),
            "ixGap",
            st.get("ixNoteGap"),
            "ixBot",
            st.get("ixMainBotGap"),
            "bodyH",
            st.get("bodyH"),
            "btn",
            st.get("btnText"),
            "hidden",
            st.get("btnHidden"),
            "pref",
            st.get("pref"),
            "fill",
            st.get("fill"),
            "jump",
            st.get("jumpBotAboveNote"),
            "count",
            st.get("noteCount"),
        )
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
