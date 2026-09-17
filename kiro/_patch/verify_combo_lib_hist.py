#!/usr/bin/env python3
"""Verify saved combos (12), AC library wrap+[-], history erase, Sides keywords flush."""
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
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_combo_lib_hist.json"
SHOTS = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9463
HTTP_PORT = 8791
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
URL = "http://127.0.0.1:8791/DS-CATALOG.html?v=combo13"
PROFILE = "/tmp/catalog-combo-lib-hist"
os.makedirs(SHOTS, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)


def ensure_http():
    try:
        urllib.request.urlopen(URL.split("?")[0], timeout=1).read(64)
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
    for _ in range(30):
        try:
            urllib.request.urlopen(URL.split("?")[0], timeout=1).read(64)
            return httpd
        except Exception:
            time.sleep(0.1)
    raise SystemExit("http 8791 failed")


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

    def eval(self, expr, await_promise=True):
        r = self.call(
            "Runtime.evaluate",
            {"expression": expr, "awaitPromise": await_promise, "returnByValue": True},
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


JS = r"""
(async function(){
  function wait(ms){return new Promise(function(r){setTimeout(r,ms);});}
  var out={ok:true, errors:[], steps:{}};
  try{
    if(typeof setDisplayMode==='function')setDisplayMode('sides');
    document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','search-extras-collapsed');
    var fw=document.getElementById('filterWrap');
    if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
    await wait(120);

    var vh=window.innerHeight||900;
    function box(el){if(!el)return null;var r=el.getBoundingClientRect();return {t:Math.round(r.top),b:Math.round(r.bottom),h:Math.round(r.height),l:Math.round(r.left),w:Math.round(r.width)};}
    var kw=document.getElementById('kwbar');
    var fp=fw&&fw.querySelector('.filter-panel');
    var st=document.getElementById('kwstatus')||(fw&&fw.querySelector('.kwstatus'));
    out.steps.kwBottom={
      vh:vh,
      fw:box(fw),
      fp:box(fp),
      kw:box(kw),
      st:box(st),
      fwGap:fw?Math.round(vh-fw.getBoundingClientRect().bottom):null,
      fpGap:fp?Math.round(vh-fp.getBoundingClientRect().bottom):null,
      kwGap:kw?Math.round(vh-kw.getBoundingClientRect().bottom):null,
      stGap:st?Math.round(vh-st.getBoundingClientRect().bottom):null,
      open:!!(fw&&fw.classList.contains('open')),
      kwOpen:document.body.classList.contains('kw-open')
    };
    if(out.steps.kwBottom.fwGap==null||out.steps.kwBottom.fwGap>4)out.errors.push('keywords pane gap '+out.steps.kwBottom.fwGap);
    if(out.steps.kwBottom.stGap!=null&&out.steps.kwBottom.stGap>4)out.errors.push('keywords status gap '+out.steps.kwBottom.stGap);

    kwComboStore=[];
    persistKwCombos();
    if(typeof setMode==='function')setMode('search');
    searchKeywords=['piano','bass'];
    if(typeof renderPills==='function')renderPills();
    if(typeof applySearch==='function')applySearch();
    await wait(40);
    if(typeof parkKwComboSave==='function')parkKwComboSave();
    var saveBtn=document.getElementById('kwComboSave');
    out.steps.saveUi={btn:!!saveBtn, hidden:!!(saveBtn&&saveBtn.hidden), host:saveBtn&&saveBtn.parentElement&&(saveBtn.parentElement.id||saveBtn.parentElement.className||'')};
    if(!saveBtn||saveBtn.hidden)out.errors.push('combo Save button missing/hidden with pills');

    var ok=saveKwCombo('verify-combo');
    var saved=kwSavedCombos();
    out.steps.savedOne={ok:!!ok, n:saved.length, name:saved[0]&&saved[0].name, pills:saved[0]&&saved[0].pills, key:KW_COMBO_KEY};
    if(!ok)out.errors.push('saveKwCombo failed');
    if(saved.length!==1)out.errors.push('saved n '+saved.length+' expected 1');

    for(var i=0;i<13;i++){
      searchKeywords=['piano','cap'+i];
      saveKwCombo('cap-'+i);
    }
    saved=kwSavedCombos();
    out.steps.cap={n:saved.length, names:saved.map(function(o){return o.name;})};
    if(saved.length>12)out.errors.push('saved cap '+saved.length+' > 12');
    if(saved.length!==12)out.errors.push('saved cap '+saved.length+' expected 12');

    searchKeywords=[];
    if(typeof renderPills==='function')renderPills();
    if(typeof applySearch==='function')applySearch();
    await wait(30);
    var keepName='verify-combo';
    var keep=(kwSavedCombos()||[]).filter(function(o){return o&&o.name===keepName;})[0];
    if(!keep)keep=kwSavedCombos()[0];
    if(typeof showAc==='function')showAc('',{force:true});
    await wait(40);
    var ac=document.getElementById('acList');
    var item=null;
    if(ac){
      [].slice.call(ac.querySelectorAll('.ac-combo-saved[data-cat="combo"]')).forEach(function(el){
        if(!item&&keep&&(el.textContent||'').indexOf(keep.name)>=0)item=el;
      });
    }
    if(!item){
      item=document.createElement('div');
      item.className='ac-item ac-combo ac-combo-saved';
      item.setAttribute('data-cat','combo');
      item.setAttribute('onclick',"applyKwCombo('"+(keep&&(keep.id||keep.key))+"',event)");
      (ac||document.body).appendChild(item);
    }
    item.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));
    await wait(80);
    out.steps.loaded={
      pills:searchKeywords.slice(),
      expect:keep&&keep.pills,
      clicked:(item.textContent||'').slice(0,40),
      preview:document.body.classList.contains('chosen-preview-open')
    };
    if(keep&&JSON.stringify(searchKeywords)!==JSON.stringify(keep.pills))out.errors.push('applyKwCombo pills '+JSON.stringify(searchKeywords));

    if(typeof showHistoryCloud==='function')showHistoryCloud();
    await wait(40);
    var picks=document.getElementById('historyPicks');
    function histState(){
      var m={};
      if(picks)picks.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){m[cb.getAttribute('data-hist')]=!!cb.checked;});
      return m;
    }
    var def=histState();
    out.steps.histDef=def;
    if(def.savedCombos)out.errors.push('Saved combinations checked by default');
    if(def.sessions)out.errors.push('Saved sessions checked by default');
    if(!def.combos)out.errors.push('Keyword combos not checked by default');
    var searchAll=document.getElementById('historySearchAll');
    if(searchAll)searchAll.click();
    await wait(20);
    var allSearch=histState();
    out.steps.histAllSearch=allSearch;
    if(allSearch.savedCombos||allSearch.sessions)out.errors.push('All search included saved slots');
    var all=document.getElementById('historyAll');
    if(all)all.click();
    await wait(20);
    var allOn=histState();
    out.steps.histAll=allOn;
    if(!allOn.savedCombos||!allOn.sessions)out.errors.push('All did not include saved slots');

    picks.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){cb.checked=cb.getAttribute('data-hist')==='savedCombos';});
    if(typeof clearSearchHistoryData==='function')clearSearchHistoryData();
    out.steps.afterErase={saved:kwSavedCombos().length, auto:kwAutoCombos().length};
    if(kwSavedCombos().length!==0)out.errors.push('saved combos not erased');

    var longEl=[].slice.call(document.querySelectorAll('.entry[data-name]')).map(function(el){return el.getAttribute('data-name')||'';}).filter(function(n){return n.length>28;})[0];
    if(!longEl){
      var any=document.querySelector('.entry[data-name]');
      longEl=any&&any.getAttribute('data-name');
    }
    var q=(longEl||'piano').slice(0,12).toLowerCase();
    if(searchInput){searchInput.value=q;searchInput.dispatchEvent(new Event('input',{bubbles:true}));}
    if(typeof showAc==='function')showAc(q,{force:true});
    await wait(80);
    var lib=document.querySelector('#acList .ac-item.ac-lib');
    var mark=lib&&lib.querySelector('.ac-lib-mark');
    var lab=lib&&lib.querySelector('.ac-label');
    var comboMark=document.querySelector('#acList .ac-item.ac-combo .ac-lib-mark');
    var sessMark=document.querySelector('#acList .ac-item.ac-session .ac-lib-mark');
    var lb=lib&&lib.getBoundingClientRect();
    var ls=lab&&getComputedStyle(lab);
    out.steps.lib={
      q:q, name:longEl, found:!!lib, mark:mark&&mark.textContent, wrap:ls&&ls.whiteSpace,
      h:lb?Math.round(lb.height):0, w:lb?Math.round(lb.width):0,
      comboHasMark:!!comboMark, sessHasMark:!!sessMark
    };
    if(!lib)out.errors.push('no library AC row for q='+q);
    if(mark&&mark.textContent.indexOf('[-]')<0)out.errors.push('lib mark '+JSON.stringify(mark&&mark.textContent));
    if(!mark)out.errors.push('missing [-] on library row');
    if(comboMark)out.errors.push('[-] on combo row');
    if(sessMark)out.errors.push('[-] on session row');
    if(ls&&ls.whiteSpace==='nowrap')out.errors.push('library label nowrap');

    out.ok=out.errors.length===0;
    return out;
  }catch(err){
    return {ok:false, errors:[String(err&&err.stack||err)], steps:{}};
  }
})()
"""

NARROW_JS = r"""
(async function(){
  function wait(ms){return new Promise(function(r){setTimeout(r,ms);});}
  if(typeof setDisplayMode==='function')setDisplayMode('sides');
  document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','search-extras-collapsed');
  var fw=document.getElementById('filterWrap');
  if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
  await wait(80);
  var longEl=[].slice.call(document.querySelectorAll('.entry[data-name]')).map(function(el){return el.getAttribute('data-name')||'';}).filter(function(n){return n.length>28;})[0];
  var q=(longEl||'piano').slice(0,12).toLowerCase();
  if(typeof showAc==='function')showAc(q,{force:true});
  await wait(80);
  var lib=document.querySelector('#acList .ac-item.ac-lib');
  var ac=document.getElementById('acList');
  var lb=lib&&lib.getBoundingClientRect();
  var ab=ac&&ac.getBoundingClientRect();
  var lab=lib&&lib.querySelector('.ac-label');
  return {
    q:q,
    found:!!lib,
    mark:!!(lib&&lib.querySelector('.ac-lib-mark')),
    itemH:lb?Math.round(lb.height):0,
    itemW:lb?Math.round(lb.width):0,
    acW:ab?Math.round(ab.width):0,
    overflow:!!(lb&&ab&&lb.width>ab.width+2),
    wrap:lab?getComputedStyle(lab).whiteSpace:'',
    vw:window.innerWidth
  };
})()
"""


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png"}).get("data", "")
    open(os.path.join(SHOTS, name), "wb").write(base64.b64decode(data))


def wait_entries(cdp):
    for _ in range(80):
        try:
            n = cdp.eval("document.querySelectorAll('.entry').length", await_promise=False)
        except Exception:
            n = 0
        if n and n > 20:
            return
        time.sleep(0.25)
    raise SystemExit("catalog did not load")


def main():
    httpd = ensure_http()
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
    logf = open("/tmp/catalog-combo-lib-hist.log", "w")
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
    try:
        for _ in range(80):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
                break
            except Exception:
                time.sleep(0.2)
        else:
            json.dump({"err": "cdp"}, open(OUT, "w"))
            sys.exit(1)
        tab = new_tab("about:blank")
        cdp = CDP(tab["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        cdp.call("Page.navigate", {"url": URL})
        wait_entries(cdp)
        result = cdp.eval(JS)
        shot(cdp, "D1400-combo-lib-hist.png")
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 900, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        time.sleep(0.35)
        narrow = cdp.eval(NARROW_JS)
        result["narrow"] = narrow
        if narrow and narrow.get("overflow"):
            result.setdefault("errors", []).append("lib row overflows AC at 900")
            result["ok"] = False
        if narrow and not narrow.get("found"):
            result.setdefault("errors", []).append("no lib row at 900")
            result["ok"] = False
        shot(cdp, "D900-combo-lib-wrap.png")
        json.dump(result, open(OUT, "w"), indent=2)
        print(json.dumps(result, indent=2)[:8000])
        if not result or not result.get("ok"):
            sys.exit(1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        if httpd:
            httpd.shutdown()


if __name__ == "__main__":
    main()
