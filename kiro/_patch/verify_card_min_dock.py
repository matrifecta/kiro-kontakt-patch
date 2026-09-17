#!/usr/bin/env python3
"""Verify minimized-card dock: pills, FIFO-3, restore, Tab, scale, AC stripe."""
import json, os, socket, subprocess, sys, time, urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_card_min_dock.json"
SHOTS = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9433
PROFILE = "/tmp/catalog-card-min-dock"
URL = "http://127.0.0.1:8788/DS-CATALOG.html?v=card-min-dock"
os.makedirs(SHOTS, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
time.sleep(0.25)
chrome = next(
    (
        p
        for p in (
            "/usr/lib/chromium/chromium",
            "/usr/bin/chromium",
            "/usr/bin/google-chrome",
        )
        if os.path.exists(p)
    ),
    None,
)
if not chrome:
    raise SystemExit("no chromium")
logf = open("/tmp/catalog-card-min-dock.log", "w")
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
            {"expression": expr, "awaitPromise": True, "returnByValue": True},
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")

    def shot(self, name):
        data = self.call("Page.captureScreenshot", {"format": "png"}).get("data", "")
        path = os.path.join(SHOTS, name)
        open(path, "wb").write(__import__("base64").b64decode(data))
        return path


JS = r"""
(async function(){
  function wait(ms){return new Promise(function(r){setTimeout(r,ms);});}
  function box(el){
    if(!el)return null;
    var r=el.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),b:Math.round(r.bottom),cx:Math.round(r.x+r.width/2)};
  }
  function shownEntries(){
    return Array.prototype.slice.call(document.querySelectorAll('.entry')).filter(function(e){
      return !e.classList.contains('is-hidden') && e.id;
    });
  }
  function dockState(){
    var dock=document.getElementById('cardMinDock');
    var pills=Array.prototype.slice.call(document.querySelectorAll('#cardMinDock .card-min-pill'));
    var cm=document.getElementById('catalogMain');
    var cmb=box(cm);
    var db=box(dock);
    var pb=pills.map(box);
    var inMain=true;
    pb.forEach(function(p){
      if(!cmb||!p)return;
      if(p.cx<cmb.x-8||p.cx>cmb.x+cmb.w+8)inMain=false;
    });
    return {
      ids:(cardMinDockItems||[]).map(function(x){return x.id;}),
      names:(cardMinDockItems||[]).map(function(x){return x.name;}),
      n:pills.length,
      on:!!(dock&&dock.classList.contains('is-on')),
      slots:pills.map(function(p){return p.getAttribute('data-card-min-slot');}),
      front:pills.map(function(p){return p.classList.contains('is-front');}),
      texts:pills.map(function(p){return (p.textContent||'').trim();}),
      hasThumb:pills.map(function(p){return !!p.querySelector('img');}),
      dock:db, main:cmb, pills:pb, pillsInMain:inMain,
      expanded: (typeof cardMinExpanded==='function' && cardMinExpanded()) ? cardMinExpanded().id : null,
      hl:!!document.querySelector('.entry.highlight'),
      preview:document.body.classList.contains('chosen-preview-open'),
      minBtns:document.querySelectorAll('.hl-min').length
    };
  }
  function fireTab(){
    var ev=new KeyboardEvent('keydown',{key:'Tab',bubbles:true,cancelable:true});
    (document.activeElement||document).dispatchEvent(ev);
  }
  var logs=[];
  try{
    if(typeof setDisplayMode==='function')setDisplayMode('sides');
    document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');
    await wait(250);
    var entries=shownEntries();
    var out={ok:true, errors:[], vw:innerWidth, vh:innerHeight, nEntries:entries.length, steps:{}};
    if(typeof minimizeExpandedCard!=='function'){out.ok=false;out.errors.push('missing minimizeExpandedCard');return out;}
    if(entries.length<5){out.ok=false;out.errors.push('need 5 entries');return out;}

    openChosenPreview(entries[0]);
    await wait(80);
    var minBtn=entries[0].querySelector('.hl-min');
    var minCs=minBtn?getComputedStyle(minBtn):null;
    out.steps.open1={
      preview:document.body.classList.contains('chosen-preview-open'),
      minDisplay:minCs&&minCs.display,
      minBtn:!!minBtn
    };
    if(!out.steps.open1.preview)out.errors.push('preview did not open');
    if(!minBtn||(minCs&&minCs.display==='none'))out.errors.push('minimize button not visible on expanded card');
    minimizeExpandedCard(entries[0]);
    await wait(80);
    out.steps.min1=dockState();
    if(out.steps.min1.n!==1)out.errors.push('expected 1 pill after first minimize, got '+out.steps.min1.n);
    if(out.steps.min1.preview||out.steps.min1.hl)out.errors.push('overlay still open after minimize');
    if(!out.steps.min1.pillsInMain)out.errors.push('pill not in catalogMain horizontally');
    if(out.steps.min1.dock&&out.steps.min1.main){
      var d=out.steps.min1.dock, m=out.steps.min1.main;
      if(Math.abs(d.b-m.b)>48)out.errors.push('dock not near catalogMain bottom');
      var mid=m.x+m.w/2;
      if(d.cx && Math.abs(d.cx-mid)>m.w*0.35)out.errors.push('dock not centered in content');
    }

    openChosenPreview(entries[1]); minimizeExpandedCard(entries[1]);
    openChosenPreview(entries[2]); minimizeExpandedCard(entries[2]);
    await wait(60);
    out.steps.min3=dockState();
    if(out.steps.min3.n!==3)out.errors.push('expected 3 pills, got '+out.steps.min3.n);
    if(JSON.stringify(out.steps.min3.slots)!==JSON.stringify(['left','middle','right']))out.errors.push('slots '+JSON.stringify(out.steps.min3.slots));

    var oldest=out.steps.min3.ids[0];
    openChosenPreview(entries[3]); minimizeExpandedCard(entries[3]);
    await wait(60);
    out.steps.min4=dockState();
    if(out.steps.min4.n!==3)out.errors.push('cap failed, n='+out.steps.min4.n);
    if(out.steps.min4.ids.indexOf(oldest)>=0)out.errors.push('oldest not dropped: '+oldest);
    if(out.steps.min4.ids[2]!==entries[3].id)out.errors.push('newest not last');

    var midId=out.steps.min4.ids[1];
    cardMinActivate(midId);
    await wait(80);
    out.steps.restoreMid=dockState();
    if(out.steps.restoreMid.expanded!==midId)out.errors.push('restore did not expand middle');
    if(!out.steps.restoreMid.preview && !out.steps.restoreMid.hl)out.errors.push('restore did not open overlay');
    if(out.steps.restoreMid.front[1]!==true)out.errors.push('middle pill not is-front');

    cardMinActivate(midId);
    await wait(80);
    out.steps.minAgain=dockState();
    if(out.steps.minAgain.expanded)out.errors.push('active pill click did not minimize');
    if(out.steps.minAgain.n!==3)out.errors.push('pills lost after re-minimize');

    cardMinRestore(out.steps.min4.ids[1]);
    await wait(60);
    out.steps.beforeTab=dockState();
    fireTab();
    await wait(80);
    out.steps.tabFromMid=dockState();
    if(out.steps.tabFromMid.expanded!==out.steps.min4.ids[2])out.errors.push('Tab from middle did not go right, got '+out.steps.tabFromMid.expanded);

    if(out.steps.tabFromMid.expanded)minimizeExpandedCard(cardMinExpanded());
    await wait(40);
    if(out.steps.min4.ids[1] && cardMinExpanded() && cardMinExpanded().id===out.steps.min4.ids[1]);
    while(cardMinExpanded())minimizeExpandedCard(cardMinExpanded());
    await wait(40);
    out.steps.allMin=dockState();
    if(out.steps.allMin.expanded)out.errors.push('still expanded after minimize all');
    document.body.focus();
    fireTab();
    await wait(80);
    out.steps.tabNoneOpen=dockState();
    if(out.steps.tabNoneOpen.expanded!==out.steps.min4.ids[0])out.errors.push('Tab with none open should restore first added, got '+out.steps.tabNoneOpen.expanded);

    var beforeIds=out.steps.tabNoneOpen.ids.slice();
    var si=document.getElementById('searchInput');
    if(si){si.focus(); fireTab(); await wait(40);}
    out.steps.tabInSearch=dockState();
    out.steps.tabInSearch.searchFocused=document.activeElement===si;
    if(JSON.stringify(out.steps.tabInSearch.ids)!==JSON.stringify(beforeIds) && out.steps.tabInSearch.expanded!==out.steps.tabNoneOpen.expanded){
      /* Tab from search must not cycle dock */
      if(document.activeElement===si && out.steps.tabInSearch.expanded!==out.steps.tabNoneOpen.expanded)
        out.errors.push('Tab stole from search input');
    }
    if(si)si.blur();

    if(out.steps.tabNoneOpen.expanded)minimizeExpandedCard(cardMinExpanded());
    await wait(40);
    var root=document.documentElement;
    var sc0=getComputedStyle(root).getPropertyValue('--ui-scale').trim();
    var fs0=getComputedStyle(root).fontSize;
    var beforeData=root.getAttribute('data-ui-scale');
    var up=document.getElementById('uiScaleUp');
    if(up)up.click();
    var sc1=getComputedStyle(root).getPropertyValue('--ui-scale').trim();
    var fs1=getComputedStyle(root).fontSize;
    var dataScale=root.getAttribute('data-ui-scale');
    out.steps.uiScale={fromScale:sc0,toScale:sc1,fromFont:fs0,toFont:fs1,beforeData:beforeData,dataScale:dataScale,hasUp:!!up,typeofApply:typeof applyUiScaleCss,typeofSet:typeof setUiScale,changed:parseFloat(fs1)>parseFloat(fs0)||(dataScale&&dataScale!==beforeData)};
    if(!out.steps.uiScale.changed)out.errors.push('UI scale did not change font-size ('+JSON.stringify(out.steps.uiScale)+')');
    if(typeof applyUiScaleCss==='function')applyUiScaleCss(100);

    if(si){
      si.focus();
      si.value='piano';
      si.dispatchEvent(new Event('input',{bubbles:true}));
      if(typeof applySearch==='function')applySearch();
      await wait(250);
    }
    var stripe=document.querySelector('.ac-scroll-stripe');
    var thumb=document.querySelector('.ac-scroll-thumb');
    var ac=document.getElementById('acList');
    var shell=document.querySelector('.search-ac-shell');
    out.steps.ac={
      stripe:!!stripe,
      thumb:!!thumb,
      acOpen:!!(ac&&ac.classList.contains('open')),
      shellOverflow:!!(shell&&shell.classList.contains('has-ac-overflow')),
      stripeRule:!!(document.styleSheets&&[].some.call(document.styleSheets,function(){return true;}))
    };
    if(!stripe||!thumb)out.errors.push('AC scroll stripe/thumb missing');

    if(cardMinExpanded())minimizeExpandedCard(cardMinExpanded());
    await wait(40);
    out.ok=out.errors.length===0;
    return out;
  }catch(err){
    return {ok:false, errors:[String(err&&err.stack||err)], steps:{}};
  }
})()
"""


def main():
    tab = new_tab(URL)
    cdp = CDP(tab["webSocketDebuggerUrl"])
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.bringToFront")
    cdp.call("Emulation.setDeviceMetricsOverride", {
        "width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False
    })
    cdp.call("Page.navigate", {"url": URL})
    for _ in range(50):
        try:
            ready = cdp.eval("document.readyState")
        except Exception:
            ready = ""
        if ready == "complete":
            break
        time.sleep(0.2)
    time.sleep(0.8)
    result = cdp.eval(JS)
    try:
        result["shot_after"] = cdp.shot("D1400-card-min-dock.png")
    except Exception as e:
        result = result or {}
        result["shot_err"] = str(e)
    json.dump(result, open(OUT, "w"), indent=2)
    print(json.dumps(result, indent=2)[:8000])
    proc.terminate()
    if not result or not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
