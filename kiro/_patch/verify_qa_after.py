#!/usr/bin/env python3
"""Post-fix QA: mode independence, persist, Pick, mobile. runId qa-after."""
import json, os, socket, subprocess, sys, time, urllib.request, base64
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_qa_after.json"
PORT = 9371
PROFILE = "/tmp/catalog-qa-after-verify"
INGEST = "http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51"
URLS = [
    ("ds", "http://127.0.0.1:8788/DS-CATALOG.html?v=qa-after"),
    ("kontakt", "http://127.0.0.1:8788/KONTAKT-CATALOG.html?v=qa-after"),
]
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(["pkill", "-f", "remote-debugging-port=9371"], check=False)
time.sleep(0.3)
chrome = "/usr/lib/chromium/chromium" if os.path.exists("/usr/lib/chromium/chromium") else "/usr/bin/chromium"
proc = subprocess.Popen(
    [
        chrome, "--headless=new", "--disable-gpu", "--no-first-run",
        "--disable-extensions", f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
        f"--user-data-dir={PROFILE}", "--noerrdialogs", "--ozone-platform=headless",
        "--ozone-override-screen-size=1400,900", "--use-angle=swiftshader-webgl", "about:blank",
    ],
    stdout=open("/tmp/catalog-qa-after.log", "w"),
    stderr=subprocess.STDOUT,
)
for _ in range(60):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
        break
    except Exception:
        time.sleep(0.25)
else:
    open(OUT, "w").write(json.dumps({"err": "cdp"}))
    sys.exit(1)


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        host, port = u.hostname, u.port or 80
        path = u.path + (("?" + u.query) if u.query else "")
        key = base64.b64encode(os.urandom(16)).decode()
        s = socket.create_connection((host, port), timeout=20)
        req = (
            f"GET {path} HTTP/1.1\r\nHost:{host}:{port}\r\nUpgrade: websocket\r\n"
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
            b1 = self.buf[1]
            ln = b1 & 0x7F
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
            return payload.decode(errors="replace")

    def _fill(self):
        chunk = self.s.recv(65536)
        if not chunk:
            raise RuntimeError("ws eof")
        self.buf += chunk

    def close(self):
        try:
            self.s.close()
        except OSError:
            pass


def new_tab(url):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + url, method="PUT")))
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
        r = self.call("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True})
        if r.get("exceptionDetails"):
            raise RuntimeError(json.dumps(r["exceptionDetails"])[:500])
        return r.get("result", {}).get("value")


EXPR = r"""
(async function(){
  window.__QA_RUNID='qa-after';
  function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
  function box(id){var el=typeof id==='string'?document.getElementById(id):id;if(!el)return null;var b=el.getBoundingClientRect();return{x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),disp:getComputedStyle(el).display};}
  function ingest(hid,loc,msg,data){
    try{fetch('INGEST_URL',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'qa-after',hypothesisId:hid,location:loc,message:msg,data:data,timestamp:Date.now()})}).catch(function(){});}catch(e){}
  }
  function snapMode(){
    var il=document.getElementById('catalogIndexList');
    var cs=il&&getComputedStyle(il);
    var last=il&&il.querySelector('li:last-child');
    var sep=document.getElementById('dualFsSep');
    var hdr=document.querySelector('.catalog-header');
    var sw=document.getElementById('displaySwitch');
    var colN=cs?String(cs.columnCount):'';
    var colCount=parseInt(colN,10);
    var xs=[];
    if(il){
      var lis=il.querySelectorAll('li');
      var step=Math.max(1,Math.floor(lis.length/24));
      for(var i=0;i<lis.length;i+=step)xs.push(Math.round(lis[i].getBoundingClientRect().x));
    }
    var uniq=xs.filter(function(x,i,a){return a.indexOf(x)===i;}).length;
    return {
      display:typeof currentDisplay!=='undefined'?currentDisplay:'',
      cls:document.body.className,
      upper:document.body.classList.contains('display-upper'),
      sides:document.body.classList.contains('display-sides'),
      fs:document.body.classList.contains('display-fs'),
      dual:document.body.classList.contains('dual-fs-open'),
      acFs:document.body.classList.contains('ac-fs-open'),
      kwFs:document.body.classList.contains('kw-fs-open'),
      parents:{
        fw:function(){var el=document.getElementById('filterWrap');return el&&el.parentElement?(el.parentElement.id||el.parentElement.tagName):'';}(),
        ch:function(){var el=document.getElementById('searchChrome');return el&&el.parentElement?(el.parentElement.id||el.parentElement.tagName):'';}(),
        ix:function(){var el=document.getElementById('catalogIndex');return el&&el.parentElement?(el.parentElement.id||el.parentElement.tagName):'';}()
      },
      ch:box('searchChrome'), fw:box('filterWrap'), ix:box('catalogIndex'), cm:box('catalogMain'),
      hdr:hdr?box(hdr):null, sw:sw?box(sw):null,
      lw:(getComputedStyle(document.body).getPropertyValue('--sides-lw')||'').trim(),
      rw:(getComputedStyle(document.body).getPropertyValue('--sides-rw')||'').trim(),
      indexH:(getComputedStyle(document.body).getPropertyValue('--sides-index-h')||'').trim(),
      il:{
        cols:cs?(cs.columnCount+'/'+cs.columnWidth):'',
        colW:cs?cs.columnWidth:'',
        usedCols:uniq,
        colCount:isFinite(colCount)?colCount:(uniq||null),
        ov:cs?cs.overflowY:'',
        sh:il?il.scrollHeight:null, ch:il?il.clientHeight:null,
        inline:(il&&il.getAttribute('style'))||''
      },
      last:last?box(last):null,
      sepDisp:sep?getComputedStyle(sep).display:'missing',
      editLabel:(document.getElementById('layoutEditBtn')||{}).textContent||'',
      lockLabel:(document.getElementById('modePinBtn')||{}).textContent||'',
      shade:!!document.body.textContent&&/\bShade\b/.test((document.getElementById('layoutEditBtn')||{}).textContent||'')
    };
  }

  localStorage.removeItem((window.MODE_LAYOUT_KEY)||('catalog-layout-'+(window.CATALOG_NS||'catalog')));
  var out={title:document.title,vw:innerWidth,vh:innerHeight};

  if(typeof setDisplayMode==='function')setDisplayMode('upper');
  await sleep(280);
  if(typeof setMode==='function')setMode('search');
  await sleep(80);
  var w=document.getElementById('filterWrap');
  if(w&&!w.classList.contains('open')&&typeof toggleFilter==='function')toggleFilter();
  await sleep(160);
  out.upper=snapMode();
  ingest('H2','verify','upper',out.upper);

  var pageH=Math.max(document.documentElement.scrollHeight,document.body.scrollHeight);
  window.scrollTo(0,pageH);
  await sleep(80);
  var last=document.querySelector('#catalogIndexList li:last-child');
  var lastR=last&&last.getBoundingClientRect();
  out.upperScroll={
    pageH:pageH,
    lastBottom:lastR?Math.round(lastR.bottom):null,
    lastReachable:!!(lastR&&lastR.bottom<=innerHeight+8||lastR&&lastR.top<innerHeight)
  };
  window.scrollTo(0,0);
  await sleep(40);

  if(typeof setDisplayMode==='function')setDisplayMode('fs',{menu:'search'});
  await sleep(280);
  out.full=snapMode();
  ingest('H1','verify','full',out.full);

  if(typeof toggleAcFsCompanion==='function')toggleAcFsCompanion();
  await sleep(200);
  if(typeof toggleKwFsCompanion==='function')toggleKwFsCompanion();
  await sleep(220);
  out.fullCompanion=snapMode();
  ingest('H4','verify','full-companion',out.fullCompanion);

  if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();
  await sleep(240);
  out.fullBack=snapMode();
  ingest('H1','verify','full-back',out.fullBack);

  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  await sleep(300);
  out.sides=snapMode();
  ingest('H5','verify','sides',out.sides);

  if(typeof collapseSearchMenu==='function')collapseSearchMenu();
  await sleep(140);
  if(typeof collapseKwMenu==='function')collapseKwMenu();
  await sleep(140);
  out.sidesHidden=snapMode();
  ingest('H4','verify','sides-hidden',out.sidesHidden);

  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  await sleep(260);
  out.sidesRestore=snapMode();
  var il=document.getElementById('catalogIndexList');
  if(il){il.scrollTop=il.scrollHeight;await sleep(80);}
  var last2=document.querySelector('#catalogIndexList li:last-child');
  var ix=document.getElementById('catalogIndex');
  var last2r=last2&&last2.getBoundingClientRect();
  var ixr=ix&&ix.getBoundingClientRect();
  var lir=il&&il.getBoundingClientRect();
  out.sidesIxEnd={
    lastVis:!!(last2r&&ixr&&last2r.bottom<=ixr.bottom+6),
    lastInList:!!(last2r&&lir&&last2r.bottom<=lir.bottom+6),
    sideways:!!(out.sidesRestore.il.colCount&&out.sidesRestore.il.colCount>1),
    sh:il?il.scrollHeight:null, ch:il?il.clientHeight:null
  };
  ingest('H2','verify','sides-ix',out.sidesIxEnd);

  if(typeof setDisplayMode==='function')setDisplayMode('upper');
  await sleep(240);
  out.upperAfterSides=snapMode();
  ingest('H2','verify','upper-after-sides',out.upperAfterSides);

  if(!document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();
  await sleep(60);
  var ch=document.getElementById('searchChrome');
  if(ch){
    ch.style.height='240px';
    ch.classList.add('search-height-set');
    document.body.style.setProperty('--upper-chrome-probe','240px');
  }
  try{localStorage.setItem((typeof liveLayoutKey==='function'?liveLayoutKey('catalog-search-height-'):'catalog-search-height-'+(window.CATALOG_NS||'catalog'))+'-l','0.42');}catch(e){}
  if(typeof snapshotLiveToMode==='function')snapshotLiveToMode('upper');
  if(typeof writeModeSlot==='function')writeModeSlot({chromeH:'0.42',pinned:true},'upper');
  if(typeof toggleModeLock==='function'&&!(typeof modeLayoutPinned==='function'&&modeLayoutPinned()))toggleModeLock();
  await sleep(80);
  out.upperLock={slot:typeof readModeSlot==='function'?readModeSlot('upper'):null, labels:{edit:(document.getElementById('layoutEditBtn')||{}).textContent,lock:(document.getElementById('modePinBtn')||{}).textContent}};
  if(document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();

  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  await sleep(200);
  if(!document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();
  document.body.style.setProperty('--sides-lw','300px');
  document.body.style.setProperty('--sides-rw','320px');
  document.body.style.setProperty('--sides-index-h','200px');
  if(typeof writeSidesCols==='function')writeSidesCols(300,320);
  if(typeof writeModeSlot==='function')writeModeSlot({lw:300,rw:320,indexH:200,pinned:true},'sides');
  if(typeof toggleModeLock==='function'&&!(typeof modeLayoutPinned==='function'&&modeLayoutPinned()))toggleModeLock();
  await sleep(60);
  out.sidesLock={slot:typeof readModeSlot==='function'?readModeSlot('sides'):null};
  if(document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();

  if(typeof setDisplayMode==='function')setDisplayMode('fs',{menu:'search'});
  await sleep(200);
  document.documentElement.style.setProperty('--fs-ac-h','400px');
  if(typeof writeModeSlot==='function')writeModeSlot({acH:'0.55',pinned:true},'fs');
  out.fsLock={slot:typeof readModeSlot==='function'?readModeSlot('fs'):null, upperSlot:typeof readModeSlot==='function'?readModeSlot('upper'):null};

  var store=null;
  try{store=JSON.parse(localStorage.getItem(typeof MODE_LAYOUT_KEY!=='undefined'?MODE_LAYOUT_KEY:('catalog-layout-'+(window.CATALOG_NS||'catalog')))||'{}');}catch(e){store={};}
  out.persistBeforeReload={store:store, upper:out.upperLock, sides:out.sidesLock, fs:out.fsLock};

  if(typeof setMode==='function')setMode('pick');
  await sleep(140);
  var pills=[].slice.call(document.querySelectorAll('#kwbar .kw:not(.clear):not(.active):not(.disabled)'));
  var sel0=typeof getSel==='function'?getSel().length:0;
  if(pills[0])pills[0].click();
  await sleep(80);
  out.pick={mode:typeof getCurrentMode==='function'?getCurrentMode():'',sel0:sel0,sel1:typeof getSel==='function'?getSel().length:0};
  if(typeof setMode==='function')setMode('search');
  await sleep(80);
  var si=document.getElementById('searchInput');
  if(si){
    si.value='piano';
    si.dispatchEvent(new Event('input',{bubbles:true}));
  }
  await sleep(160);
  var ac=document.getElementById('acList');
  out.search={q:si?si.value:'', acOpen:!!(ac&&ac.classList.contains('open')), acItems:ac?ac.querySelectorAll('.ac-item').length:0};

  out.dupLabels={
    customize:document.querySelectorAll('#layoutEditBtn').length,
    lock:document.querySelectorAll('#modePinBtn').length,
    pinVisible:function(){var el=document.getElementById('dualFsSepPin');return el&&getComputedStyle(el).display!=='none'&&el.getBoundingClientRect().width>0;}()
  };

  out.checks={
    upperLayout: !!(out.upper.upper&&!out.upper.sides&&!out.upper.fs&&out.upper.parents.fw==='searchChrome'),
    upperSearchLeft: !!(out.upper.ch&&out.upper.fw&&out.upper.ch.x<out.upper.fw.x),
    upperKwRight: !!(out.upper.fw&&out.upper.ch&&out.upper.fw.x>=out.upper.ch.x+out.upper.ch.w-8||(out.upper.fw&&out.upper.ch&&out.upper.fw.x>out.upper.ch.x)),
    upperIndexBelow: !!(out.upper.ix&&out.upper.ch&&out.upper.ix.y>=out.upper.ch.y+out.upper.ch.h-8),
    upperCols13: !!(out.upper.il.usedCols>=1&&out.upper.il.usedCols<=3&&out.upper.il.colW&&out.upper.il.colW!=='auto'),
    upperNoDockInline: !(out.upper.il.inline&&out.upper.il.inline.indexOf('columns')>=0&&out.upper.il.inline.indexOf('unset')>=0),
    upperHeader: !!(out.upper.hdr&&out.upper.hdr.y<80&&out.upper.hdr.w>200),
    upperSwitch: !!(out.upper.sw&&out.upper.sw.y<80&&out.upper.sw.disp!=='none'),
    fullIsFs: !!(out.full.fs&&!out.full.sides&&out.full.acFs&&!out.full.kwFs),
    fullNotSidesGrid: !(out.full.lw&&out.full.lw!=='0px'&&out.full.fs),
    companionNotSides: !!(out.fullCompanion.fs&&!out.fullCompanion.sides),
    fullBackUpper: !!(out.fullBack.upper&&!out.fullBack.fs&&!out.fullBack.sides),
    sidesThree: !!(out.sides.sides&&out.sides.ch&&out.sides.fw&&out.sides.cm&&out.sides.ch.w>80&&out.sides.fw.w>80&&out.sides.cm.w>80),
    hideSearch: !!(out.sidesHidden.cls.indexOf('search-chrome-collapsed')>=0),
    hideKw: !!(out.sidesHidden.cls.indexOf('kw-chrome-collapsed')>=0&&out.sidesHidden.fw&&(out.sidesHidden.fw.disp==='none'||out.sidesHidden.fw.w===0)),
    restoreBoth: !!(out.sidesRestore.sides&&out.sidesRestore.cls.indexOf('search-chrome-collapsed')<0&&out.sidesRestore.cls.indexOf('kw-chrome-collapsed')<0&&out.sidesRestore.fw&&out.sidesRestore.fw.w>80&&out.sidesRestore.ch&&out.sidesRestore.ch.w>80),
    sidesIxVertical: !out.sidesIxEnd.sideways&&!!(out.sidesIxEnd.sh>out.sidesIxEnd.ch+4),
    sidesIxLast: !!(out.sidesIxEnd.lastVis||out.sidesIxEnd.lastInList),
    upperColsAfterSides: !!(out.upperAfterSides.upper&&!(out.upperAfterSides.il.inline&&out.upperAfterSides.il.inline.indexOf('unset')>=0)),
    persistUpper: !!(out.upperLock.slot&&out.upperLock.slot.chromeH),
    persistSides: !!(out.sidesLock.slot&&out.sidesLock.slot.lw===300&&out.sidesLock.slot.indexH===200),
    persistFsNoWipeUpper: !!(out.fsLock.upperSlot&&out.fsLock.upperSlot.chromeH&&out.fsLock.slot&&out.fsLock.slot.acH),
    pickWorks: out.pick.mode==='pick'&&out.pick.sel1>out.pick.sel0,
    searchTypes: out.search.q==='piano'&&(out.search.acItems>0||out.search.acOpen),
    oneCustomize: out.dupLabels.customize===1,
    oneLock: out.dupLabels.lock===1,
    noSepFloatUpper: out.upper.sepDisp==='none'||out.upper.sepDisp==='missing',
    hideSearchAc: typeof hideSearchAc==='function'
  };
  ingest('QA','verify','checks',out.checks);
  return out;
})()
""".replace("INGEST_URL", INGEST)


RELOAD_EXPR = r"""
(async function(){
  window.__QA_RUNID='qa-after';
  function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
  if(typeof setDisplayMode==='function')setDisplayMode('upper');
  await sleep(200);
  var us=typeof readModeSlot==='function'?readModeSlot('upper'):null;
  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  await sleep(220);
  var ss=typeof readModeSlot==='function'?readModeSlot('sides'):null;
  var lw=(getComputedStyle(document.body).getPropertyValue('--sides-lw')||'').trim();
  var ih=(getComputedStyle(document.body).getPropertyValue('--sides-index-h')||'').trim();
  if(typeof setDisplayMode==='function')setDisplayMode('fs',{menu:'search'});
  await sleep(200);
  var fs=typeof readModeSlot==='function'?readModeSlot('fs'):null;
  var acH=(getComputedStyle(document.documentElement).getPropertyValue('--fs-ac-h')||'').trim();
  if(typeof setDisplayMode==='function')setDisplayMode('upper');
  await sleep(180);
  var us2=typeof readModeSlot==='function'?readModeSlot('upper'):null;
  return {
    upper:us, sides:ss, fs:fs, upperAfter:us2,
    applied:{lw:lw,ih:ih,acH:acH},
    ok:!!(us&&us.chromeH&&ss&&(ss.lw===300||ss.lw==='300')&&ss.indexH===200&&fs&&fs.acH&&us2&&us2.chromeH)
  };
})()
"""


MOBILE_EXPR = r"""
(function(){
  var btn=document.querySelector('[data-display="sides"]');
  var well=document.getElementById('filterWrap');
  var ch=document.getElementById('searchChrome');
  var hdr=document.querySelector('.catalog-header');
  var sw=document.getElementById('displaySwitch');
  function box(el){if(!el)return null;var b=el.getBoundingClientRect();return{x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),disp:getComputedStyle(el).display};}
  if(typeof setDisplayMode==='function')setDisplayMode('upper');
  var upper={
    mode:typeof currentDisplay!=='undefined'?currentDisplay:'',
    sidesBtn:btn?getComputedStyle(btn).display:'missing',
    hdr:box(hdr), sw:box(sw), ch:box(ch), fw:box(well),
    sides:document.body.classList.contains('display-sides'),
    upper:document.body.classList.contains('display-upper')
  };
  if(typeof setDisplayMode==='function')setDisplayMode('fs',{menu:'search'});
  var full={
    fs:document.body.classList.contains('display-fs'),
    sides:document.body.classList.contains('display-sides'),
    acFs:document.body.classList.contains('ac-fs-open'),
    hdr:box(hdr), sw:box(sw)
  };
  var blackWell=!!(well&&getComputedStyle(well).backgroundColor==='rgb(0, 0, 0)'&&well.getBoundingClientRect().height>120&&getComputedStyle(well).display!=='none'&&!document.body.classList.contains('display-fs'));
  return {
    upper:upper, full:full, blackWell:blackWell,
    ok: upper.sidesBtn==='none' && !upper.sides && !!upper.upper && !!full.fs && !full.sides && !blackWell
      && upper.hdr && upper.hdr.y<90 && upper.sw && upper.sw.disp!=='none'
  };
})()
"""


def wait_ready(cdp):
    ready = None
    for _ in range(50):
        ready = cdp.eval("typeof setDisplayMode==='function'&&typeof hideSearchAc==='function'&&document.querySelectorAll('.entry').length")
        if isinstance(ready, int) and ready > 5:
            return ready
        time.sleep(0.25)
    return ready


all_out = {}
try:
    for key, url in URLS:
        tab = new_tab(url)
        cdp = CDP(tab["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        time.sleep(1.6)
        cdp.call("Emulation.setDeviceMetricsOverride", {"width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False})
        ready = wait_ready(cdp)
        result = cdp.eval(EXPR)
        if isinstance(result, dict):
            result["readyEntries"] = ready
            cdp.call("Page.reload", {"ignoreCache": True})
            time.sleep(2.0)
            wait_ready(cdp)
            result["persistAfterReload"] = cdp.eval(RELOAD_EXPR)
            if isinstance(result.get("checks"), dict) and isinstance(result.get("persistAfterReload"), dict):
                result["checks"]["persistReload"] = bool(result["persistAfterReload"].get("ok"))
        cdp.call("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})
        cdp.eval("window.dispatchEvent(new Event('resize'))")
        time.sleep(0.4)
        mobile = cdp.eval(MOBILE_EXPR)
        if isinstance(result, dict):
            result["mobile"] = mobile
            result.setdefault("checks", {})["mobileNoSides"] = bool(isinstance(mobile, dict) and mobile.get("ok"))
        all_out[key] = result
        try:
            cdp.ws.close()
        except Exception:
            pass
    open(OUT, "w").write(json.dumps(all_out, indent=2))
    print("WROTE", OUT)
    ok = True
    for key, result in all_out.items():
        if not isinstance(result, dict):
            print(key, result)
            ok = False
            continue
        checks = result.get("checks") or {}
        print(key, json.dumps(checks, indent=2))
        if not all(checks.values()):
            ok = False
            print(key, "FAIL keys", [k for k, v in checks.items() if not v])
    sys.exit(0 if ok else 2)
finally:
    proc.terminate()
