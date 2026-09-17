#!/usr/bin/env python3
"""CDP verify: folder glyph size, Index window chrome, empty-card select, embed Back."""
import base64
import json
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_card_select_index_embed_back.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9531
HTTP_PORT = 8797
PROFILE = "/tmp/catalog-four-fixes"
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)


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
    for _ in range(150):
        try:
            n = cdp.eval(
                "!!(document.getElementById('catalogIndex')&&document.querySelectorAll('.entry').length>2&&typeof rememberViewed==='function')"
            )
        except Exception:
            n = False
        if n:
            return
        time.sleep(0.2)
    raise SystemExit("catalog JS not ready")


def set_view(cdp, w, h):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": w,
            "height": h,
            "deviceScaleFactor": 1,
            "mobile": w < 900,
            "screenOrientation": {
                "type": "portraitPrimary" if h > w else "landscapePrimary",
                "angle": 0 if h > w else 90,
            },
        },
    )
    time.sleep(0.3)


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png"})
    raw = data.get("data")
    path = SHOT / name
    if raw:
        path.write_bytes(base64.b64decode(raw))
    return str(path)


def nav(cdp, url):
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": url})
    time.sleep(0.7)
    wait_ready(cdp)


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


MEASURE = r"""
(() => {
  if(typeof bindCatalogPathHits==='function')bindCatalogPathHits();
  var entry=document.querySelector('.entry:not(.is-hidden)')||document.querySelector('.entry');
  var path=entry&&entry.querySelector('.path');
  function glyph(sel){
    var btn=path&&path.querySelector(sel);
    var svg=btn&&btn.querySelector('svg.path-icon-glyph');
    if(!svg)return null;
    var r=svg.getBoundingClientRect();
    var cs=getComputedStyle(svg);
    return {w:Math.round(r.width*10)/10,h:Math.round(r.height*10)/10,cssW:cs.width,cssH:cs.height};
  }
  return {
    folder:glyph('a.folder,.path-icon-btn.folder'),
    copy:glyph('.path-copy-hit'),
    fs:glyph('.path-fs-hit'),
    marks:{
      folderCss:!!document.querySelector('style,head') && /fix-FOLDER-GLYPH-SIZE/.test(document.documentElement.innerHTML),
      isolateV2:/fix-INDEX-ISOLATE-v2/.test(document.documentElement.innerHTML),
      popEmbed:typeof cardSearchPopEmbed==='function',
      emptySel:typeof selectCardFromEmpty==='function'
    }
  };
})()
"""

INDEX_WIN = r"""
(() => {
  if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
  var ix=document.getElementById('catalogIndex');
  if(ix){
    ix.classList.remove('is-embedded','is-collapsed');
  }
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof stripIndexCardChrome==='function')stripIndexCardChrome(ix);
  var list=document.getElementById('catalogIndexList');
  var chrome=ix?ix.querySelectorAll('.path-icon-btn,.path-action-row,a.folder,.path-fs-hit,.path-copy-hit,.fav-btn'):[];
  var vis=0;
  chrome.forEach(function(el){
    var cs=getComputedStyle(el);
    if(cs.display!=='none'&&cs.visibility!=='hidden'&&el.offsetWidth>0)vis++;
  });
  var cs=ix?getComputedStyle(ix):null;
  return {
    windowOpen:document.body.classList.contains('index-window-open'),
    embed:!!(ix&&ix.classList.contains('is-embedded')),
    parent:ix&&ix.parentElement&&ix.parentElement.id,
    z:cs&&cs.zIndex,
    bg:cs&&cs.backgroundColor,
    iso:cs&&cs.isolation,
    ov:cs&&cs.overflow,
    chromeCount:chrome.length,
    chromeVisible:vis,
    liCount:list?list.querySelectorAll('li').length:0,
    liHasPath:list?!!list.querySelector('.path-icon-btn,a.folder,.path-action-row'):false
  };
})()
"""

SELECT = r"""
(() => {
  var cards=[].slice.call(document.querySelectorAll('.entry')).filter(function(e){return !e.classList.contains('is-hidden');});
  var a=cards[0], b=cards[1]||cards[0];
  if(!a||!b)return {err:'no-cards'};
  document.querySelectorAll('.entry.selected').forEach(function(e){e.classList.remove('selected');});
  var body=a.querySelector('.hl-body');
  var name=a.querySelector('.lib-name,h3');
  var br=body.getBoundingClientRect();
  var hitX=br.left+8, hitY=br.bottom-6;
  if(name){
    var nr=name.getBoundingClientRect();
    hitX=nr.left+8;
    hitY=nr.bottom+10;
    if(hitY>br.bottom-2)hitY=nr.top-6;
    if(hitY<br.top+2){hitX=br.left+10;hitY=br.top+8;}
  }
  var ev=new MouseEvent('click',{bubbles:true,cancelable:true,clientX:hitX,clientY:hitY,view:window});
  (document.elementFromPoint(hitX,hitY)||body||a).dispatchEvent(ev);
  var afterA=a.classList.contains('selected');
  var preview=document.body.classList.contains('chosen-preview-open');
  document.querySelectorAll('.entry.selected').forEach(function(e){e.classList.remove('selected');});
  if(typeof rememberViewed==='function')rememberViewed(b);
  var afterB=b.classList.contains('selected');
  var search=a.querySelector('.search-popup-btn,.search-link');
  var nearMiss=false;
  if(search){
    var sr=search.getBoundingClientRect();
    var nx=sr.left-6, ny=sr.top+sr.height/2;
    var before=a.classList.contains('selected');
    a.classList.remove('selected');
    var ev2=new MouseEvent('click',{bubbles:true,cancelable:true,clientX:nx,clientY:ny,view:window});
    var tgt=document.elementFromPoint(nx,ny)||search;
    tgt.dispatchEvent(ev2);
    nearMiss=a.classList.contains('selected')&&tgt.closest&&tgt.closest('.search-popup-btn,.search-link,.card-actions');
  }
  return {
    emptySelected:afterA,
    previewStolen:preview,
    rememberWorks:afterB,
    nearSearchSelected:nearMiss,
    hit:{x:Math.round(hitX),y:Math.round(hitY)},
    a:a.id,b:b.id
  };
})()
"""

EMBED = r"""
(() => {
  var card=document.querySelector('.entry:not(.is-hidden)')||document.querySelector('.entry');
  if(!card)return {err:'no-card'};
  if(typeof rememberViewed==='function')rememberViewed(card);
  if(typeof openChosenPreview==='function')openChosenPreview(card);
  var btn=card.querySelector('.search-popup-btn');
  var yt=(btn&&btn.dataset.yt)||'https://www.youtube.com/results?search_query=kontakt';
  var opened=typeof openCardSearchEmbed==='function'&&openCardSearchEmbed('yt',yt);
  var landN=(cardSearchState.history||[]).length;
  var land0=cardSearchState.history&&cardSearchState.history[0];
  if(typeof cardSearchPlayYt==='function'){
    cardSearchState.ytItems=cardSearchState.ytItems&&cardSearchState.ytItems.length?cardSearchState.ytItems:[{id:'dQw4w9WgXcQ',title:'t1',thumb:''},{id:'9bZkp7q19f0',title:'t2',thumb:''}];
    cardSearchPlayYt(1);
  }
  var afterNav=(cardSearchState.history||[]).length;
  var embedOpen=document.body.classList.contains('card-embed-open');
  if(typeof cardSearchBack==='function')cardSearchBack();
  var afterBack=(cardSearchState.history||[]).length;
  var stillEmbed=document.body.classList.contains('card-embed-open');
  if(typeof cardSearchBack==='function')cardSearchBack();
  var afterExit=(cardSearchState.history||[]).length;
  var exited=!document.body.classList.contains('card-embed-open');
  return {
    opened:!!opened,
    landN:landN,
    landKind:land0&&land0.kind,
    afterNav:afterNav,
    embedAfterNav:embedOpen,
    afterBack:afterBack,
    stillEmbed:stillEmbed,
    afterExit:afterExit,
    exited:exited,
    hasPop:typeof cardSearchPopEmbed==='function'
  };
})()
"""


def run_page(cdp, url, w, h, tag):
    nav(cdp, url)
    set_view(cdp, w, h)
    cdp.eval(
        """
(() => {
  try{localStorage.setItem('catalog-index-embed-'+(window.CATALOG_NS||'catalog'),'0');}catch(e){}
  if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
})()
"""
    )
    time.sleep(0.25)
    folder = cdp.eval(MEASURE)
    shot_folder = shot(cdp, f"{tag}-folder.png")
    index = cdp.eval(INDEX_WIN)
    shot_ix = shot(cdp, f"{tag}-index-window.png")
    select = cdp.eval(SELECT)
    shot_sel = shot(cdp, f"{tag}-select.png")
    embed = cdp.eval(EMBED)
    shot_em = shot(cdp, f"{tag}-embed.png")
    return {
        "url": url,
        "vw": w,
        "folder": folder,
        "index": index,
        "select": select,
        "embed": embed,
        "shots": [shot_folder, shot_ix, shot_sel, shot_em],
    }


def judge(rep, errors, prefix):
    f = (rep.get("folder") or {}).get("folder") or {}
    c = (rep.get("folder") or {}).get("copy") or {}
    fs = (rep.get("folder") or {}).get("fs") or {}
    if f.get("w") and c.get("w") and f["w"] <= c["w"] * 1.08:
        errors.append(f"{prefix}.folder {f.get('w')} not > copy {c.get('w')}")
    if f.get("w") and fs.get("w") and f["w"] <= fs["w"] * 1.08:
        errors.append(f"{prefix}.folder {f.get('w')} not > fs {fs.get('w')}")
    marks = (rep.get("folder") or {}).get("marks") or {}
    if not marks.get("folderCss"):
        errors.append(f"{prefix}: missing fix-FOLDER-GLYPH-SIZE")
    if not marks.get("isolateV2"):
        errors.append(f"{prefix}: missing isolate-v2")
    ix = rep.get("index") or {}
    if ix.get("chromeVisible"):
        errors.append(f"{prefix}.index chromeVisible={ix.get('chromeVisible')}")
    if ix.get("liHasPath"):
        errors.append(f"{prefix}.index li still has path chrome")
    if not ix.get("windowOpen"):
        errors.append(f"{prefix}.index window not open")
    sel = rep.get("select") or {}
    if not sel.get("emptySelected") and not sel.get("rememberWorks"):
        errors.append(f"{prefix}.select failed {sel}")
    if sel.get("previewStolen"):
        errors.append(f"{prefix}.select opened preview")
    em = rep.get("embed") or {}
    if em.get("landN") != 1:
        errors.append(f"{prefix}.embed landN={em.get('landN')} want 1")
    if em.get("afterNav") is None or em.get("afterNav") < 2:
        errors.append(f"{prefix}.embed afterNav={em.get('afterNav')} want >=2")
    if em.get("afterBack") != 1:
        errors.append(f"{prefix}.embed afterBack={em.get('afterBack')} want 1")
    if not em.get("stillEmbed"):
        errors.append(f"{prefix}.embed Back from page2 exited")
    if not em.get("exited"):
        errors.append(f"{prefix}.embed Back from landing did not exit")


def main():
    if not port_open(HTTP_PORT):
        raise SystemExit("http://127.0.0.1:8797 not serving")
    chrome = next(
        (
            p
            for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium")
            if os.path.exists(p)
        ),
        None,
    )
    if not chrome:
        raise SystemExit("no chromium")
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.2)
    logf = open("/tmp/catalog-four-fixes.log", "w")
    proc = subprocess.Popen(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--disable-extensions",
            "--disable-background-networking",
            f"--user-data-dir={PROFILE}",
            f"--remote-debugging-port={PORT}",
            "about:blank",
        ],
        stdout=logf,
        stderr=logf,
    )
    try:
        for _ in range(50):
            if port_open(PORT):
                break
            time.sleep(0.1)
        else:
            raise SystemExit("chromium debug port failed")
        tab = new_tab("about:blank")
        cdp = CDP(tab["webSocketDebuggerUrl"])
        reports = {}
        reports["kontakt1400"] = run_page(
            cdp, "http://127.0.0.1:8797/KONTAKT-CATALOG.html?v=fourfix-cdp", 1400, 900, "D1400-fourfix"
        )
        reports["kontaktPortable"] = run_page(
            cdp,
            "http://127.0.0.1:8797/KONTAKT-CATALOG-portable.html?v=fourfix-cdp",
            1400,
            900,
            "P1400-fourfix",
        )
        errors = []
        judge(reports["kontakt1400"], errors, "K1400")
        judge(reports["kontaktPortable"], errors, "KP1400")
        payload = {"ok": not errors, "errors": errors, "reports": reports}
        OUT.write_text(json.dumps(payload, indent=2))
        print(json.dumps({"ok": payload["ok"], "errors": errors}, indent=2))
        if errors:
            raise SystemExit(1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
