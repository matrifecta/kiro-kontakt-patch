#!/usr/bin/env python3
"""Dump live Index <li> HTML + icon counts (research before/after nuke)."""
import base64
import json
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/dump_index_path_dupes.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9567
HTTP = "http://127.0.0.1:8797"
PROFILE = "/tmp/catalog-index-dupe-dump"
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

JS = r"""
(() => {
  function openIndex(mode){
    var ix=document.getElementById('catalogIndex');
    if(!ix)return {err:'no-index'};
    if(typeof setDisplayMode==='function')try{setDisplayMode('sides',{pick:true});}catch(e){}
    document.body.classList.add('display-sides');
    document.body.classList.remove('display-middle','display-upper','display-fs');
    if(ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();
    var embedOn=ix.classList.contains('is-embedded');
    if(mode==='embed'&&!embedOn&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();
    if(mode==='window'&&embedOn&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();
    ix.classList.remove('is-collapsed');
    if(typeof applyIndexScrollFit==='function')try{applyIndexScrollFit();}catch(e3){}
  }
  function glyph(el){
    if(!el)return null;
    var r=el.getBoundingClientRect();
    var cs=getComputedStyle(el);
    var bef=getComputedStyle(el,'::before');
    return {
      tag:el.tagName,cls:String(el.className||'').slice(0,120),
      href:(el.getAttribute&&el.getAttribute('href'))||'',
      aria:el.getAttribute&&el.getAttribute('aria-label'),
      vis:cs.display!=='none'&&cs.visibility!=='hidden'&&parseFloat(cs.opacity||'1')>0.05&&r.width>2&&r.height>2,
      d:cs.display,v:cs.visibility,op:cs.opacity,pos:cs.position,z:cs.zIndex,
      w:Math.round(r.width),h:Math.round(r.height),l:Math.round(r.left),t:Math.round(r.top),
      mask:(bef.maskImage||bef.webkitMaskImage||'').slice(0,80),
      html:String(el.outerHTML||'').slice(0,400)
    };
  }
  function dump(mode){
    openIndex(mode);
    var ix=document.getElementById('catalogIndex');
    var list=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));
    if(list){list.scrollTop=mode==='embed'?list.scrollHeight:0;}
    var lis=list?[].slice.call(list.querySelectorAll('li')):[];
    var dirty=lis.filter(function(li){
      return li.querySelector('.path-icon-btn,a.folder,.path-action-row,.path-label,.path-fs-hit,.path-copy-hit,svg,img,button,.path')
        || (li.querySelector('a')&&((li.querySelector('a').className||'').toString().match(/folder|path-icon|path-fs|path-copy/)));
    }).slice(0,6);
    var sample=(dirty.length?dirty:lis.slice(0,3)).map(function(li){
      var a=li.querySelector('a[href^="#"]');
      return {
        childN:li.children.length,childTags:[].slice.call(li.children).map(function(c){return c.tagName+'.'+String(c.className||'').slice(0,60);}),
        html:String(li.innerHTML||'').slice(0,800),
        aCls:a?String(a.className||''):null,
        aKids:a?a.innerHTML.slice(0,300):null
      };
    });
    var inside=list?list.querySelectorAll('.path-icon-btn,a.folder,.path-action-row,.path-label,.path-fs-hit,.path-copy-hit,svg.path-icon-glyph,img.path-icon-glyph'):[];
    var visInside=[].slice.call(inside).map(glyph).filter(function(g){return g&&g.vis;});
    var ixR=ix?ix.getBoundingClientRect():{left:0,top:0,right:0,bottom:0};
    var overlap=[];
    var punch=[];
    document.querySelectorAll('.path-icon-btn,a.folder,.path-fs-hit,.path-copy-hit').forEach(function(el){
      if(el.closest&&el.closest('#catalogIndex,#catalogIndexList,ul.index'))return;
      var r=el.getBoundingClientRect();
      if(r.width<4||r.height<4)return;
      var hit=!(r.right<ixR.left||r.left>ixR.right||r.bottom<ixR.top||r.top>ixR.bottom);
      if(!hit)return;
      var rec={cls:String(el.className||'').slice(0,80),inEntry:!!(el.closest&&el.closest('.entry')),l:Math.round(r.left),t:Math.round(r.top)};
      overlap.push(rec);
      var cx=Math.round(r.left+r.width/2),cy=Math.round(r.top+r.height/2);
      var topEl=document.elementFromPoint(cx,cy);
      var painted=!!(topEl&&(topEl===el||(el.contains&&el.contains(topEl))));
      if(painted)punch.push(rec);
    });
    var card=document.querySelector('#catalogMain .entry:not(.highlight) .path-action-row, #catalogMain .entry:not(.highlight) .path');
    var cardIcons=card?card.querySelectorAll('.path-icon-btn,a.folder').length:0;
    function visBtn(sel){
      var els=[].slice.call(document.querySelectorAll('#catalogMain .loc-group > .entry:not(.highlight) '+sel));
      var vis=els.filter(function(el){var r=el.getBoundingClientRect();var cs=getComputedStyle(el);return cs.display!=='none'&&cs.visibility!=='hidden'&&r.width>4&&r.height>4;});
      return {n:els.length,vis:vis.length};
    }
    var a0=lis[0]&&lis[0].querySelector('a[href^="#"]');
    var clickable=false;
    if(a0){
      var ar=a0.getBoundingClientRect();
      var hit=document.elementFromPoint(ar.left+Math.min(12,ar.width/2),ar.top+Math.min(8,ar.height/2));
      clickable=!!(hit&&(hit===a0||a0.contains(hit)||(hit.closest&&hit.closest('#catalogIndex'))));
    }
    var kwFs=document.getElementById('kwStripFs');
    var kwCs=kwFs?getComputedStyle(kwFs):null;
    return {
      mode:mode,title:document.title,
      h1:(document.querySelector('h1#top')||{}).textContent||'',
      lead:(document.querySelector('.hdr-title-lead')||{}).textContent||null,
      tail:(document.querySelector('.hdr-title-tail')||{}).textContent||null,
      portable:!!window.CATALOG_PORTABLE,
      ixCls:ix?ix.className:'',
      bodyCls:document.body.className,
      embedBtn:(document.getElementById('catalogIndexEmbed')||{}).textContent||'',
      liN:lis.length,dirtyN:dirty.length,
      insideN:inside.length,visInsideN:visInside.length,visInside:visInside.slice(0,8),
      overlapN:overlap.length,overlap:overlap.slice(0,8),
      punchN:punch.length,punch:punch.slice(0,8),
      sample:sample,
      cardIcons:cardIcons,
      cardFolder:visBtn('.path-icon-btn[data-act="folder"], a.folder'),
      cardFs:visBtn('.path-icon-btn[data-act="fs"], .path-fs-hit'),
      cardCopy:visBtn('.path-icon-btn[data-act="copy"], .path-copy-hit'),
      cardPathLabel:visBtn('.path-label'),
      ixOverflow:(ix&&getComputedStyle(ix).overflow)+'/'+(ix&&getComputedStyle(ix).overflowY),
      listOverflow:list?getComputedStyle(list).overflowY:null,
      listScroll:{ch:list&&list.clientHeight,sh:list&&list.scrollHeight,can:!!(list&&list.scrollHeight>list.clientHeight+8)},
      ixRect:{t:Math.round(ixR.top),b:Math.round(ixR.bottom),h:Math.round(ixR.height),w:Math.round(ixR.width)},
      clickable:clickable,
      ixParent:ix&&ix.parentElement?(ix.parentElement.id||'')+'.'+(ix.parentElement.className||'').toString().slice(0,60):null,
      ixInline:ix&&ix.getAttribute('style'),
      ixHcss:ix&&getComputedStyle(ix).height,
      ixMaxH:ix&&getComputedStyle(ix).maxHeight,
      ixMinH:ix&&getComputedStyle(ix).minHeight,
      mainScroll:(function(){var m=document.getElementById('catalogMain');return m?{ch:m.clientHeight,sh:m.scrollHeight,st:m.scrollTop,ov:getComputedStyle(m).overflowY}:null;})(),
      bodyScroll:(function(){var b=document.querySelector('#catalogMain .catalog-body');return b?{ch:b.clientHeight,sh:b.scrollHeight,st:b.scrollTop,ov:getComputedStyle(b).overflowY}:null;})(),
      kwFs:{exists:!!kwFs,display:kwCs&&kwCs.display,w:kwFs?Math.round(kwFs.getBoundingClientRect().width):0}
    };
  }
  return {embed:dump('embed'),window:dump('window')};
})()
"""


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        key = base64.b64encode(os.urandom(16)).decode()
        s = socket.create_connection((u.hostname, u.port or 80), timeout=30)
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
        self.id = 0

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
            return payload.decode("utf-8", "replace")

    def _fill(self):
        chunk = self.s.recv(65536)
        if not chunk:
            raise RuntimeError("ws eof")
        self.buf += chunk

    def call(self, method, params=None, timeout=120):
        self.id += 1
        mid = self.id
        self.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            msg = json.loads(self.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})
        raise TimeoutError(method)


def eval_js(cdp, expr, await_promise=False):
    r = cdp.call(
        "Runtime.evaluate",
        {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": await_promise,
            "timeout": 60000,
        },
        timeout=90,
    )
    return (r.get("result") or {}).get("value")


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png"})["data"]
    path = SHOT / name
    path.write_bytes(base64.b64decode(data))
    return str(path)


def wait_ready(cdp):
    for _ in range(80):
        n = eval_js(cdp, "document.querySelectorAll('.entry').length") or 0
        if n > 20:
            return n
        time.sleep(0.25)
    return 0


def run_page(cdp, url, tag, w=1400, h=900):
    cdp.call("Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False})
    cdp.call("Page.navigate", {"url": url})
    time.sleep(1.5)
    wait_ready(cdp)
    data = eval_js(cdp, JS)
    shots = {}
    try:
        eval_js(cdp, "(function(){if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});var ix=document.getElementById('catalogIndex');if(ix&&ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();if(ix&&!ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();ix&&ix.classList.remove('is-collapsed');var list=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));if(list){list.scrollTop=list.scrollHeight;var last=list.lastElementChild;if(last)last.scrollIntoView({block:'nearest',inline:'nearest'});}})()")
        time.sleep(0.6)
        shots["embed"] = shot(cdp, f"D{w}-{tag}-index-embed-retest.png")
        eval_js(cdp, "(function(){var ix=document.getElementById('catalogIndex');var list=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));if(list)list.scrollTop=0;var body=document.querySelector('#catalogMain .catalog-body');if(body)body.scrollTop=0;})()")
        time.sleep(0.25)
        shots["embedTop"] = shot(cdp, f"D{w}-{tag}-index-embed-top-retest.png")
        eval_js(cdp, "(function(){var ix=document.getElementById('catalogIndex');if(ix&&ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();ix&&ix.classList.remove('is-collapsed');})()")
        time.sleep(0.5)
        shots["window"] = shot(cdp, f"D{w}-{tag}-index-window-retest.png")
    except Exception as e:
        shots["err"] = str(e)
    return {"url": url, "data": data, "shots": shots}


def main():
    urllib.request.urlopen(f"{HTTP}/DS-CATALOG.html", timeout=5).read(64)
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.4)
    log = open("/tmp/catalog-index-dupe-dump.log", "w")
    proc = subprocess.Popen(
        [
            "/usr/lib/chromium/chromium",
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--disable-extensions",
            f"--remote-debugging-port={PORT}",
            "--remote-allow-origins=*",
            f"--user-data-dir={PROFILE}",
            "--ozone-platform=headless",
            "about:blank",
        ],
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
                break
            except Exception:
                time.sleep(0.2)
        else:
            raise SystemExit("cdp down")
        ver = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version"))
        ws = Ws(ver["webSocketDebuggerUrl"])
        ws.call("Target.setDiscoverTargets", {"discover": True})
        pages = {
            "ds": f"{HTTP}/DS-CATALOG.html?cb=ixdump",
            "ds-port": f"{HTTP}/DS-CATALOG-portable.html?cb=ixdump",
            "kt": f"{HTTP}/KONTAKT-CATALOG.html?cb=ixdump",
            "kt-port": f"{HTTP}/KONTAKT-CATALOG-portable.html?cb=ixdump",
        }
        out = {}
        for tag, url in pages.items():
            info = json.load(urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?{url}", method="PUT")))
            cdp = Ws(info["webSocketDebuggerUrl"])
            cdp.call("Page.enable")
            w = 390 if "port" in tag else 1400
            h = 844 if "port" in tag else 900
            out[tag] = run_page(cdp, url, tag, w, h)
            try:
                cdp.s.close()
            except Exception:
                pass
        OUT.write_text(json.dumps(out, indent=2)[:200000])
        print("WROTE", OUT)
        for tag, rec in out.items():
            d = rec.get("data") or {}
            for mode in ("embed", "window"):
                m = d.get(mode) or {}
                print(
                    tag,
                    mode,
                    "inside",
                    m.get("insideN"),
                    "vis",
                    m.get("visInsideN"),
                    "overlap",
                    m.get("overlapN"),
                    "punch",
                    m.get("punchN"),
                    "dirty",
                    m.get("dirtyN"),
                    "title",
                    m.get("title"),
                    "h1",
                    (m.get("h1") or "")[:24],
                    "kwFs",
                    (m.get("kwFs") or {}).get("display"),
                    "folderVis",
                    (m.get("cardFolder") or {}).get("vis"),
                    "fsVis",
                    (m.get("cardFs") or {}).get("vis"),
                    "copyVis",
                    (m.get("cardCopy") or {}).get("vis"),
                    "ixH",
                    (m.get("ixRect") or {}).get("h"),
                    "click",
                    m.get("clickable"),
                    "canScroll",
                    (m.get("listScroll") or {}).get("can"),
                    "mainSh",
                    (m.get("mainScroll") or {}).get("sh"),
                    "mainCh",
                    (m.get("mainScroll") or {}).get("ch"),
                    "ixOv",
                    m.get("ixOverflow"),
                    "parent",
                    m.get("ixParent"),
                    "inline",
                    (m.get("ixInline") or "")[:80],
                    "hcss",
                    m.get("ixHcss"),
                )
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
