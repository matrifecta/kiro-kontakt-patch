#!/usr/bin/env python3
"""Phone pin sheet + overflow menus vs desktop pyramid. Does not commit."""
import json, os, socket, subprocess, sys, time, urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_mobile_pin_sheet.json"
SHOTS = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9447
PROFILE = "/tmp/catalog-mobile-pin-sheet"
URL = "http://127.0.0.1:8797/DS-CATALOG.html?v=mob-pin"
os.makedirs(SHOTS, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
time.sleep(0.2)
chrome = next((p for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome") if os.path.exists(p)), None)
if not chrome:
    raise SystemExit("no chromium")
logf = open("/tmp/catalog-mobile-pin-sheet.log", "w")
proc = subprocess.Popen(
    [chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-extensions",
     f"--remote-debugging-port={PORT}", "--remote-allow-origins=*", f"--user-data-dir={PROFILE}",
     "--noerrdialogs", "--ozone-platform=headless", "--ozone-override-screen-size=1400,900",
     "--use-angle=swiftshader-webgl", "about:blank"],
    stdout=logf, stderr=subprocess.STDOUT,
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
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")

    def shot(self, name):
        data = self.call("Page.captureScreenshot", {"format": "png"}).get("data", "")
        path = os.path.join(SHOTS, name)
        open(path, "wb").write(__import__("base64").b64decode(data))
        return path


def new_tab(url):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + url, method="PUT")))
    except Exception:
        return json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/new?" + url))


PROBE = r"""
(function(){
  function vis(el){
    if(!el)return false;
    var cs=getComputedStyle(el);
    if(cs.display==='none'||cs.visibility==='hidden')return false;
    var r=el.getBoundingClientRect();
    return r.width>2&&r.height>2;
  }
  function overflow(el){
    if(!el)return false;
    return el.scrollWidth>el.clientWidth+8;
  }
  var nWant=arguments.length?0:12;
  if(window.__pinProbeCount){
    var entries=Array.prototype.slice.call(document.querySelectorAll('.entry')).filter(function(e){return e.id;}).slice(0,window.__pinProbeCount);
    window.__pinProbeCount=0;
    entries.forEach(function(el){if(typeof minimizeExpandedCard==='function'){openChosenPreview(el);minimizeExpandedCard(el);}});
  }
  var dock=document.getElementById('cardMinDock');
  var handle=document.getElementById('cardMinSheetHandle');
  var list=document.getElementById('cardMinList');
  var pills=document.querySelectorAll('#cardMinDock .card-min-pill');
  var save=document.getElementById('cardMinDockSave');
  var hdrMore=document.getElementById('hdrMoreBtn');
  var kwMore=document.getElementById('kwStripMore');
  var stripMore=document.getElementById('searchStripMore');
  var layout=document.getElementById('hdrLayoutBtns');
  var miss=document.getElementById('clearMissBtn');
  var theme=document.getElementById('themePicker');
  var fs=document.getElementById('searchStripFs');
  var kwfs=document.getElementById('kwStripFs');
  var stack=document.querySelector('#cardMinDock .card-min-stack');
  return {
    phone:typeof isPhoneViewport==='function'&&isPhoneViewport(),
    vw:window.innerWidth,vh:window.innerHeight,
    nItems:typeof cardMinDockItems!=='undefined'?cardMinDockItems.length:0,
    nPills:pills.length,
    cap:typeof cardMinCap==='function'?cardMinCap():null,
    dockOn:!!(dock&&dock.classList.contains('is-on')),
    phoneClass:!!(dock&&dock.classList.contains('card-min-phone')),
    sheetOpen:!!(dock&&dock.classList.contains('is-sheet-open')),
    handleVis:vis(handle),
    listVis:vis(list),
    stackVis:vis(stack),
    saveVis:vis(save),
    hdrMore:vis(hdrMore),
    kwMore:vis(kwMore),
    stripMore:vis(stripMore),
    layoutVis:vis(layout),
    missVis:vis(miss),
    themeVis:vis(theme),
    searchFs:vis(fs),
    kwFs:vis(kwfs),
    hdrOverflow:overflow(document.querySelector('.catalog-header')),
    clusterOverflow:overflow(document.getElementById('hdrCluster')),
    stripOverflow:overflow(document.getElementById('searchStrip')),
    sides:document.body.classList.contains('display-sides'),
    middle:document.body.classList.contains('display-middle'),
    saveLeft:save?save.style.left||getComputedStyle(save).left:'',
    handleText:handle?(handle.innerText||handle.textContent||''):''
  };
})()
"""


def emulate(cdp, w, h):
    cdp.call("Emulation.setDeviceMetricsOverride", {
        "width": w, "height": h, "deviceScaleFactor": 1, "mobile": w < 900,
        "screenWidth": w, "screenHeight": h,
    })
    cdp.eval(f"window.dispatchEvent(new Event('resize'));")
    time.sleep(0.35)


def main():
    page = new_tab(URL)
    cdp = CDP(page["webSocketDebuggerUrl"])
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": URL})
    time.sleep(1.4)
    out = {"errors": []}

    emulate(cdp, 390, 844)
    time.sleep(0.4)
    cdp.eval("window.__pinProbeCount=12;true;")
    phone = cdp.eval(PROBE)
    out["phone_closed"] = phone
    cdp.shot("M390-pin-sheet-closed.png")
    if not phone.get("phone"):
        out["errors"].append("390 not isPhoneViewport")
    if phone.get("nItems", 0) < 10:
        out["errors"].append("phone did not keep >9 pins, n=" + str(phone.get("nItems")))
    if not phone.get("phoneClass") or not phone.get("handleVis"):
        out["errors"].append("phone sheet handle missing")
    if phone.get("stackVis"):
        out["errors"].append("phone still showing pyramid stack")
    if phone.get("listVis"):
        out["errors"].append("sheet list visible while collapsed")
    if not phone.get("hdrMore") or phone.get("layoutVis") or phone.get("missVis"):
        out["errors"].append("phone header overflow not applied")
    if not phone.get("stripMore"):
        out["errors"].append("phone search more hidden")
    if not phone.get("searchFs"):
        out["errors"].append("phone search FS missing")

    opened = cdp.eval("""
    (function(){
      var h=document.getElementById('cardMinSheetHandle');
      if(h)h.click();
      var list=document.getElementById('cardMinList');
      var pills=document.querySelectorAll('#cardMinList .card-min-pill');
      var vis=0;
      pills.forEach(function(p){var r=p.getBoundingClientRect();if(r.height>4)vis++;});
      return {
        open:document.body.classList.contains('card-min-sheet-open'),
        listH:list?Math.round(list.getBoundingClientRect().height):0,
        nPills:pills.length,
        visPills:vis,
        scroll:list?list.scrollHeight>list.clientHeight+4:false
      };
    })()
    """)
    out["phone_open"] = opened
    cdp.shot("M390-pin-sheet-open.png")
    if not opened.get("open"):
        out["errors"].append("sheet did not open")
    if opened.get("nPills", 0) < 10:
        out["errors"].append("open sheet missing pins")

    more = cdp.eval("""
    (function(){
      if(typeof toggleHdrMore==='function')toggleHdrMore();
      var pop=document.getElementById('hdrMorePop');
      var vis=pop&&!pop.hasAttribute('hidden');
      var n=pop?pop.querySelectorAll('button').length:0;
      if(typeof toggleSearchStripMore==='function')toggleSearchStripMore();
      var sp=document.getElementById('searchStripMorePop');
      var svis=sp&&!sp.hasAttribute('hidden');
      var sl=sp?Array.prototype.map.call(sp.querySelectorAll('button'),function(b){return b.textContent;}):[];
      return {hdrOpen:!!vis,hdrN:n,searchOpen:!!svis,searchLabels:sl};
    })()
    """)
    out["phone_more"] = more
    cdp.shot("M390-toolbar-more.png")
    if not more.get("hdrOpen") or more.get("hdrN", 0) < 4:
        out["errors"].append("hdr more pop empty")
    if "Clear search" not in (more.get("searchLabels") or []):
        out["errors"].append("search more missing Clear search")

    cdp.call("Page.navigate", {"url": URL + "-desk"})
    time.sleep(1.2)
    emulate(cdp, 1400, 900)
    time.sleep(0.5)
    cdp.eval("window.__pinProbeCount=12;true;")
    desk = cdp.eval(PROBE)
    out["desk"] = desk
    cdp.shot("D1400-pin-sheet-desktop.png")
    if desk.get("phone"):
        out["errors"].append("1400 still phone viewport")
    if desk.get("phoneClass") or desk.get("handleVis"):
        out["errors"].append("desktop grew a phone sheet")
    if desk.get("hdrMore"):
        out["errors"].append("desktop showing hdr more")
    if desk.get("nItems", 0) > 9:
        out["errors"].append("desktop cap broken n=" + str(desk.get("nItems")))
    if not desk.get("layoutVis"):
        out["errors"].append("desktop layout chrome hidden")

    out["ok"] = not out["errors"]
    json.dump(out, open(OUT, "w"), indent=2)
    print(json.dumps(out, indent=2)[:4000])
    proc.kill()
    sys.exit(0 if out["ok"] else 1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        json.dump({"err": str(e)}, open(OUT, "w"))
        raise
