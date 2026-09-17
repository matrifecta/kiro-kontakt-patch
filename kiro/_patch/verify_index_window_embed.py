#!/usr/bin/env python3
"""CDP: Index Window/Embed scroll semantics + description inner scroll."""
import base64
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_index_window_embed.json"
SHOT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9517
HTTP_PORT = 8797
PROFILE = "/tmp/catalog-index-window-embed"
os.makedirs(SHOT, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

MEASURE_INDEX = r"""
(() => {
  function info(el){
    if(!el) return null;
    var r=el.getBoundingClientRect();
    var cs=getComputedStyle(el);
    var p=el.parentElement;
    return {
      parent: p ? (p.id || (p.className||'').toString().split(/\s+/)[0] || p.tagName) : '',
      parentId: p && p.id || '',
      pos: cs.position,
      top: Math.round(r.top),
      h: Math.round(r.height),
      ov: cs.overflowY
    };
  }
  var ix=document.getElementById('catalogIndex');
  var main=document.getElementById('catalogMain');
  var cb=main && (main.querySelector(':scope > .catalog-body') || main.querySelector('.catalog-body'));
  var sc=(typeof catalogContentScroller==='function' && catalogContentScroller()) || cb || main;
  var card=cb && cb.querySelector('.entry:not(.is-hidden), .entry');
  var note=document.getElementById('catalogDocNote');
  var before={ix:info(ix), card:info(card), scTop:sc?sc.scrollTop:0, mainTop:main?main.scrollTop:0, cbTop:cb?cb.scrollTop:0};
  var want=200;
  if(sc) sc.scrollTop = before.scTop + want;
  var after={ix:info(ix), card:info(card), scTop:sc?sc.scrollTop:0, mainTop:main?main.scrollTop:0, cbTop:cb?cb.scrollTop:0};
  var scrolled=Math.round((after.scTop||0)-(before.scTop||0));
  var ixDrift=(after.ix&&before.ix)?(after.ix.top-before.ix.top):null;
  var cardDelta=(after.card&&before.card)?(after.card.top-before.card.top):null;
  if(sc) sc.scrollTop=before.scTop;
  var btn=document.getElementById('catalogIndexEmbed');
  var aboutBtn=document.getElementById('catalogDocNoteEmbed');
  var h1=(document.querySelector('h1#top')||{}).textContent||'';
  var paras=[].map.call((document.querySelectorAll('#catalogDocNoteBody p')||[]), function(p){
    return (p.textContent||'').replace(/\s+/g,' ').trim();
  });
  return {
    title: document.title,
    h1: h1,
    vw: innerWidth, vh: innerHeight,
    portable: !!window.CATALOG_NS && !!window.CATALOG_PORTABLE,
    cls: document.body.className,
    embed: !!(ix&&ix.classList.contains('is-embedded')),
    collapsed: !!(ix&&ix.classList.contains('is-collapsed')),
    ixWindow: document.body.classList.contains('index-window-open'),
    fill: document.body.classList.contains('index-fill-doc'),
    ixParent: before.ix && before.ix.parent,
    ixParentId: before.ix && before.ix.parentId,
    ixPos: before.ix && before.ix.pos,
    mainOv: main?getComputedStyle(main).overflowY:'',
    bodyOv: cb?getComputedStyle(cb).overflowY:'',
    scroller: sc ? (sc.id || (sc.className||'').toString().split(/\s+/)[0]) : '',
    scrolled: scrolled,
    ixDrift: ixDrift,
    cardDelta: cardDelta,
    btn: btn?btn.textContent:'',
    noteParent: note&&note.parentElement&&(note.parentElement.id||note.parentElement.className||''),
    noteEmbed: !!(note&&note.classList.contains('is-embedded')),
    noteH: note?Math.round(note.getBoundingClientRect().height):0,
    addedCount: paras.filter(function(p){return /Added libraries/i.test(p);}).length,
    aboutBtn: aboutBtn?aboutBtn.textContent:''
  };
})()
"""

MEASURE_DESC = r"""
(() => {
  var best=document.querySelector('.entry.highlight')||document.querySelector('.entry.selected');
  var bestN=0;
  if(best){
    var d0=best.querySelector('.summary-panel .desc, .desc');
    bestN=d0?((d0.textContent||'').trim().length):0;
  }else{
    [].slice.call(document.querySelectorAll('.entry')).forEach(function(el){
      var d=el.querySelector('.summary-panel .desc, .desc');
      var n=d?((d.textContent||'').trim().length):0;
      if(n>bestN){bestN=n;best=el;}
    });
    if(best) best.classList.add('selected');
  }
  if(!best) return {err:'no-entry'};
  var panel=best.querySelector('.summary-panel');
  var desc=best.querySelector('.summary-panel .desc, .desc');
  if(desc){
    desc.appendChild(document.createTextNode(' ' + Array(28).join('Overflow probe for the description window. ')));
  }
  var path=best.querySelector('.path');
  var patches=best.querySelector('details.patches, .patches');
  function box(el){
    if(!el) return null;
    var r=el.getBoundingClientRect();
    var cs=getComputedStyle(el);
    return {
      ovY: cs.overflowY, ovX: cs.overflowX,
      h: Math.round(r.height), t: Math.round(r.top), b: Math.round(r.bottom),
      client: el.clientHeight, scroll: el.scrollHeight,
      maxH: cs.maxHeight, pos: cs.position
    };
  }
  var pb=box(panel);
  var st0=panel?panel.scrollTop:0;
  if(panel) panel.scrollTop=Math.min(40, Math.max(0,(panel.scrollHeight-panel.clientHeight)));
  var st1=panel?panel.scrollTop:0;
  if(panel) panel.scrollTop=st0;
  var db=box(desc), pathB=box(path), patB=box(patches);
  return {
    name: best.getAttribute('data-name')||best.id||'',
    descLen: bestN,
    selected: best.classList.contains('selected'),
    highlight: best.classList.contains('highlight'),
    preview: document.body.classList.contains('chosen-preview-open'),
    hlOpen: document.body.classList.contains('hl-open'),
    panel: pb, desc: db, path: pathB, patches: patB,
    panelCanScroll: !!(pb && pb.scroll > pb.client + 1),
    scrollTopChanged: st1!==st0 && st1>0,
    pathBelowPanel: !!(pb && pathB && pathB.t >= pb.b - 2),
    patchesBelowPath: !!(pathB && patB && patB.t >= pathB.b - 4),
    id: best.id
  };
})()
"""


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        host, port = u.hostname, u.port or 80
        path = u.path + (("?" + u.query) if u.query else "")
        key = base64.b64encode(os.urandom(16)).decode()
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
                "!!(window.toggleIndexEmbed&&document.getElementById('catalogIndex')&&document.querySelectorAll('.entry').length>3)"
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
    time.sleep(0.6)
    wait_ready(cdp)


def prep(cdp, *, portable=False, index_embed=False, index_open=False):
    cdp.eval(
        f"""
(() => {{
  try{{localStorage.setItem('catalog-index-embed-'+(window.CATALOG_NS||'catalog'), {json.dumps('1' if index_embed else '0')});}}catch(e){{}}
  try{{localStorage.setItem('catalog-doc-note-embed-'+(window.CATALOG_NS||'catalog'), '0');}}catch(e){{}}
  if(typeof setDisplayMode==='function') setDisplayMode('sides',{{pick:true}});
  var ix=document.getElementById('catalogIndex');
  if(ix){{
    ix.classList.toggle('is-embedded', {str(index_embed).lower()});
    if({str(index_open).lower()}) ix.classList.remove('is-collapsed');
    else ix.classList.add('is-collapsed');
  }}
  if(typeof parkCatalogDocNote==='function') parkCatalogDocNote();
  if(typeof syncIndexWindowDock==='function') syncIndexWindowDock();
  if(typeof applyIndexScrollFit==='function') applyIndexScrollFit();
  if(typeof applyIndexFillDocStyles==='function') applyIndexFillDocStyles();
  if(typeof syncIndexEmbedBtn==='function') syncIndexEmbedBtn();
}})()
"""
    )
    time.sleep(0.3)


def near(val, target, tol):
    return val is not None and abs(val - target) <= tol


def judge_window(name, st, errors):
    if not st:
        errors.append(name + ": no state")
        return
    parent = (st.get("ixParentId") or st.get("ixParent") or "").lower()
    if parent != "catalogmain":
        errors.append(f"{name}.parent={st.get('ixParentId') or st.get('ixParent')!r} want catalogMain")
    if st.get("embed"):
        errors.append(name + ": still embedded")
    drift = st.get("ixDrift")
    if drift is None or abs(drift) > 6:
        errors.append(f"{name}.ixDrift={drift} want ~0")
    card = st.get("cardDelta")
    if card is None or card > -40:
        errors.append(f"{name}.cardDelta={card} want cards moving under")
    if st.get("scrolled", 0) < 40:
        errors.append(f"{name}.scrolled={st.get('scrolled')}")


def judge_embed(name, st, errors):
    if not st:
        errors.append(name + ": no state")
        return
    parent = (st.get("ixParentId") or st.get("ixParent") or "").lower()
    if parent in ("catalogmain", "catalog-main"):
        errors.append(f"{name}.parent still catalogMain")
    if "catalog-body" not in parent and parent not in ("catalog-body",):
        # parent may be the class token catalog-body
        if "body" not in parent:
            errors.append(f"{name}.parent={st.get('ixParentId') or st.get('ixParent')!r} want catalog-body")
    if not st.get("embed"):
        errors.append(name + ": not embedded")
    drift = st.get("ixDrift")
    scrolled = st.get("scrolled") or 0
    if scrolled < 40:
        errors.append(f"{name}.scrolled={scrolled}")
    elif drift is None or abs(abs(drift) - scrolled) > 24:
        errors.append(f"{name}.ixDrift={drift} scrolled={scrolled} want delta≈scroll")


def judge_desc(name, st, errors):
    if not st or st.get("err"):
        errors.append(name + ": " + str(st))
        return
    pb = st.get("panel") or {}
    if pb.get("ovY") not in ("auto", "scroll"):
        errors.append(f"{name}.panel.ovY={pb.get('ovY')}")
    if not st.get("panelCanScroll"):
        errors.append(f"{name}.panel cannot scroll client={pb.get('client')} scroll={pb.get('scroll')}")
    if not st.get("scrollTopChanged"):
        errors.append(name + ": scrollTop did not change")
    if st.get("path") and not st.get("pathBelowPanel"):
        errors.append(name + ": path overlaps/above panel")


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


def main():
    if not port_open(HTTP_PORT):
        raise SystemExit("http://127.0.0.1:8797 not serving")
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
    logf = open("/tmp/catalog-index-window-embed.log", "w")
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

        cases = [
            ("K1400", "KONTAKT-CATALOG.html", 1400, 900, False),
            ("DS1400", "DS-CATALOG.html", 1400, 900, False),
            ("K390", "KONTAKT-CATALOG-portable.html", 390, 844, True),
            ("DS390", "DS-CATALOG-portable.html", 390, 844, True),
        ]
        for tag, page, w, h, portable in cases:
            nav(cdp, f"http://127.0.0.1:{HTTP_PORT}/{page}?v=ix-embed")
            set_view(cdp, w, h, mobile=portable)

            prep(cdp, portable=portable, index_embed=False, index_open=False)
            st = cdp.eval(MEASURE_INDEX)
            results[f"{tag}-win-col"] = st
            shot(cdp, f"{tag}-ix-win-col.png")
            judge_window(f"{tag}-win-col", st, errors)

            prep(cdp, portable=portable, index_embed=False, index_open=True)
            st = cdp.eval(MEASURE_INDEX)
            results[f"{tag}-win-open"] = st
            shot(cdp, f"{tag}-ix-win-open.png")
            judge_window(f"{tag}-win-open", st, errors)

            prep(cdp, portable=portable, index_embed=True, index_open=False)
            st = cdp.eval(MEASURE_INDEX)
            results[f"{tag}-emb-col"] = st
            shot(cdp, f"{tag}-ix-emb-col.png")
            judge_embed(f"{tag}-emb-col", st, errors)

            prep(cdp, portable=portable, index_embed=True, index_open=True)
            st = cdp.eval(MEASURE_INDEX)
            results[f"{tag}-emb-open"] = st
            shot(cdp, f"{tag}-ix-emb-open.png")
            judge_embed(f"{tag}-emb-open", st, errors)

            # descriptions: outlined, preview, fullscreen
            prep(cdp, portable=portable, index_embed=False, index_open=False)
            st = cdp.eval(MEASURE_DESC)
            results[f"{tag}-desc-sel"] = st
            shot(cdp, f"{tag}-desc-sel.png")
            judge_desc(f"{tag}-desc-sel", st, errors)

            eid = (st or {}).get("id")
            if eid:
                cdp.eval(
                    f"""
(() => {{
  var el=document.getElementById({json.dumps(eid)});
  if(el&&typeof openChosenPreview==='function') openChosenPreview(el);
}})()
"""
                )
                time.sleep(0.35)
                st = cdp.eval(MEASURE_DESC)
                results[f"{tag}-desc-preview"] = st
                shot(cdp, f"{tag}-desc-preview.png")
                judge_desc(f"{tag}-desc-preview", st, errors)

                cdp.eval(
                    f"""
(() => {{
  var el=document.getElementById({json.dumps(eid)});
  if(typeof closeChosenPreview==='function') closeChosenPreview({{skipJumpExit:true}});
  if(el&&typeof openOverlay==='function') openOverlay(el);
}})()
"""
                )
                time.sleep(0.35)
                st = cdp.eval(MEASURE_DESC)
                results[f"{tag}-desc-hl"] = st
                shot(cdp, f"{tag}-desc-hl.png")
                judge_desc(f"{tag}-desc-hl", st, errors)
                cdp.eval("if(typeof closeOverlay==='function') closeOverlay({skipScroll:true});")
                time.sleep(0.2)

        out = {"errors": errors, "results": results, "ok": not errors}
        json.dump(out, open(OUT, "w"), indent=2)
        print("errors", len(errors))
        for e in errors:
            print(" -", e)
        if errors:
            sys.exit(1)
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
