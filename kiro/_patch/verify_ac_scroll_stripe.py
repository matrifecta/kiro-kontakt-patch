#!/usr/bin/env python3
"""Verify Search AC list scrolls first→last with theme hovering stripe (no native bar)."""
import json, os, time, subprocess, urllib.request, base64
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_ac_scroll_stripe.json"
SHOT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9477
PROFILE = "/tmp/catalog-ac-stripe-verify"
os.makedirs(SHOT, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
time.sleep(0.4)

chrome = next((p for p in ["/usr/lib/chromium/chromium", "/usr/bin/chromium"] if os.path.exists(p)), None)
proc = subprocess.Popen(
    [
        chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-extensions",
        f"--remote-debugging-port={PORT}", "--remote-allow-origins=*",
        f"--user-data-dir={PROFILE}", "--noerrdialogs", "--ozone-platform=headless",
        "--ozone-override-screen-size=1400,900", "--use-angle=swiftshader-webgl", "about:blank",
    ],
    stdout=open("/tmp/catalog-ac-stripe.log", "w"),
    stderr=subprocess.STDOUT,
)
for _ in range(80):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
        break
    except Exception:
        time.sleep(0.25)
else:
    open(OUT, "w").write(json.dumps({"err": "cdp_timeout"}))
    raise SystemExit(1)

import websocket


def new_tab(url):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + url, method="PUT")))
    except Exception:
        return json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/new?" + url))


class CDP:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=60)
        self.id = 0

    def call(self, method, params=None, timeout=120):
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
        if "exceptionDetails" in r:
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")

    def shot(self, name):
        data = self.call("Page.captureScreenshot", {"format": "png"}).get("data")
        path = os.path.join(SHOT, name)
        open(path, "wb").write(base64.b64decode(data))
        return path


PROBE = r"""
(function(){
  function box(el){
    if(!el)return null;
    var r=el.getBoundingClientRect(), cs=getComputedStyle(el);
    return {
      w:Math.round(r.width), h:Math.round(r.height), t:Math.round(r.top), b:Math.round(r.bottom),
      l:Math.round(r.left), r:Math.round(r.right),
      ov:cs.overflowY, mh:cs.maxHeight, ht:cs.height, disp:cs.display, fs:cs.fontSize,
      sh:el.scrollHeight, ch:el.clientHeight, st:el.scrollTop, sw:cs.scrollbarWidth,
      pe:cs.pointerEvents, pos:cs.position, flex:cs.flex, color:cs.color, bg:cs.backgroundColor
    };
  }
  var ac=document.getElementById('acList');
  var sh=document.getElementById('acShell');
  var st=document.getElementById('acScrollStripe');
  var th=document.getElementById('acScrollThumb');
  var sc=document.getElementById('searchChrome');
  var main=document.getElementById('catalogMain');
  var first=ac&&ac.querySelector('.ac-item');
  var last=ac&&ac.querySelector('.ac-item:last-of-type, .ac-group-label:last-child, .ac-item:last-child');
  var labels=ac?[].slice.call(ac.querySelectorAll('.ac-group-label,.ac-item')):[];
  var lastEl=labels.length?labels[labels.length-1]:null;
  var lastB=lastEl&&lastEl.getBoundingClientRect();
  var acb=ac&&ac.getBoundingClientRect();
  var scb=sc&&sc.getBoundingClientRect();
  var stb=st&&!st.hidden?st.getBoundingClientRect():null;
  var thb=th&&st&&!st.hidden?th.getBoundingClientRect():null;
  var thcs=th?getComputedStyle(th):null;
  var nativeBar=false;
  if(ac){
    nativeBar = (ac.offsetWidth-ac.clientWidth)>4;
  }
  return {
    body:document.body.className,
    theme:document.documentElement.getAttribute('data-theme'),
    scale:document.documentElement.getAttribute('data-ui-scale'),
    rootFs:getComputedStyle(document.documentElement).fontSize,
    acOpen:!!(ac&&ac.classList.contains('open')),
    acItems:ac?ac.querySelectorAll('.ac-item').length:0,
    groups:ac?ac.querySelectorAll('.ac-group-label').length:0,
    lastText:lastEl?(lastEl.textContent||'').trim().slice(0,80):null,
    firstText:first?(first.textContent||'').trim().slice(0,80):null,
    ac:box(ac), shell:box(sh), search:box(sc), stripe:box(st), thumb:box(th),
    hasOverflowClass:!!(sh&&sh.classList.contains('has-ac-overflow')),
    stripeHidden:!!(st&&st.hidden),
    stripeDisp:st?getComputedStyle(st).display:null,
    thumbW:thcs?thcs.width:null,
    thumbOp:thcs?thcs.opacity:null,
    thumbBg:thcs?thcs.backgroundColor:null,
    thumbTransform:thcs?thcs.transform:null,
    nativeBar:nativeBar,
    acCanScroll:!!(ac&&ac.scrollHeight>ac.clientHeight+2),
    lastInList:!!(lastB&&acb&&lastB.bottom<=acb.bottom+3&&lastB.top>=acb.top-3),
    lastClippedByChrome:!!(lastB&&scb&&lastB.bottom>scb.bottom+2),
    lastBelowList:!!(lastB&&acb&&lastB.bottom>acb.bottom+2),
    stripeInsideChrome:!!(stb&&scb&&stb.right<=scb.right+2&&stb.left>=scb.left-2),
    stripeNotOnMain:!!(stb&&main&&stb.right<=main.getBoundingClientRect().left+1),
    stripeRightGap:stb&&scb?Math.round(scb.right-stb.right):null,
    firstVis:!!(first&&acb&&first.getBoundingClientRect().top>=acb.top-2&&first.getBoundingClientRect().top<acb.bottom),
    lastLabel:lastEl&&lastEl.className
  };
})()
"""


def run_catalog(cdp, url, tag):
    cdp.call("Page.enable")
    cdp.call("Network.enable")
    cdp.call("Network.setCacheDisabled", {"cacheDisabled": True})
    cdp.call("Emulation.setDeviceMetricsOverride", {
        "width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False
    })
    cdp.call("Page.navigate", {"url": url})
    time.sleep(2.2)
    cdp.call("Page.reload", {"ignoreCache": True})
    time.sleep(2.4)
    cdp.eval("""
      (function(){
        if(typeof setDisplayMode==='function')setDisplayMode('sides');
        var inp=document.getElementById('searchInput');
        if(inp){inp.focus(); inp.value='';}
        if(typeof showAc==='function')showAc('',{force:true});
        else if(inp){inp.dispatchEvent(new Event('focus'));}
        if(window.syncAcScrollStripe)window.syncAcScrollStripe();
      })()
    """)
    time.sleep(0.6)
    top = cdp.eval(PROBE)
    shot_top = cdp.shot(f"{tag}-ac-top.png")
    # Hover stripe via CDP mouse move over thumb/stripe
    hover = None
    stripe = top.get("stripe") or {}
    if stripe and stripe.get("w"):
        x = stripe["l"] + max(2, stripe["w"] - 3)
        y = stripe["t"] + max(8, stripe["h"] // 3)
        cdp.call("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
        time.sleep(0.25)
        hover = cdp.eval("""
          (function(){
            var th=document.getElementById('acScrollThumb');
            var st=document.getElementById('acScrollStripe');
            var cs=th&&getComputedStyle(th);
            return {w:cs&&cs.width, op:cs&&cs.opacity, tr:cs&&cs.transform, dragging:!!(st&&st.classList.contains('is-dragging'))};
          })()
        """)
        shot_hover = cdp.shot(f"{tag}-ac-hover.png")
    else:
        shot_hover = None
    # Drag stripe toward bottom
    drag = None
    if stripe and stripe.get("h"):
        x = stripe["l"] + max(2, stripe["w"] - 3)
        y0 = stripe["t"] + 12
        y1 = stripe["t"] + stripe["h"] - 12
        cdp.call("Input.dispatchMouseEvent", {"type": "mousePressed", "x": x, "y": y0, "button": "left", "clickCount": 1})
        time.sleep(0.05)
        cdp.call("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y1, "button": "left"})
        time.sleep(0.12)
        cdp.call("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": x, "y": y1, "button": "left", "clickCount": 1})
        time.sleep(0.25)
        drag = cdp.eval(PROBE)
        shot_drag = cdp.shot(f"{tag}-ac-drag.png")
    else:
        shot_drag = None
    # Native list scroll to last
    cdp.eval("""
      (function(){
        var ac=document.getElementById('acList');
        if(ac)ac.scrollTop=ac.scrollHeight;
        if(window.syncAcScrollStripe)window.syncAcScrollStripe();
      })()
    """)
    time.sleep(0.25)
    bottom = cdp.eval(PROBE)
    shot_bot = cdp.shot(f"{tag}-ac-bottom.png")
    # UI scale larger
    scale = cdp.eval("""
      (function(){
        var before=getComputedStyle(document.documentElement).fontSize;
        var item=document.querySelector('#acList .ac-item');
        var itemBefore=item?getComputedStyle(item).fontSize:null;
        if(typeof stepUiScale==='function'){stepUiScale(1);stepUiScale(1);}
        var after=getComputedStyle(document.documentElement).fontSize;
        item=document.querySelector('#acList .ac-item');
        return {
          rootBefore:before, rootAfter:after,
          itemBefore:itemBefore, itemAfter:item?getComputedStyle(item).fontSize:null,
          scale:document.documentElement.getAttribute('data-ui-scale')
        };
      })()
    """)
    return {
        "top": top,
        "hover": hover,
        "drag": drag,
        "bottom": bottom,
        "scale": scale,
        "shots": {"top": shot_top, "hover": shot_hover, "drag": shot_drag, "bottom": shot_bot},
    }


results = {}
try:
    tab = new_tab("about:blank")
    cdp = CDP(tab["webSocketDebuggerUrl"])
    results["ds"] = run_catalog(cdp, "http://127.0.0.1:8788/DS-CATALOG.html?acstripe=v2", "D1400-acstripe")
    try:
        urllib.request.urlopen("http://127.0.0.1:8788/KONTAKT-CATALOG.html", timeout=3)
        results["kontakt"] = run_catalog(cdp, "http://127.0.0.1:8788/KONTAKT-CATALOG.html?acstripe=v2", "K1400-acstripe")
    except Exception as e:
        results["kontakt_err"] = str(e)
finally:
    proc.terminate()

# Pass/fail summary
def judge(block, name):
    t = block["top"]
    b = block["bottom"]
    d = block.get("drag") or {}
    h = block.get("hover") or {}
    s = block["scale"]
    checks = {
        "ac_open": t.get("acOpen"),
        "has_items": (t.get("acItems") or 0) > 5,
        "can_scroll": t.get("acCanScroll"),
        "stripe_shown": (not t.get("stripeHidden")) and t.get("hasOverflowClass"),
        "no_native_bar": not t.get("nativeBar"),
        "last_reachable": b.get("lastInList") and not b.get("lastClippedByChrome") and not b.get("lastBelowList"),
        "stripe_inside": t.get("stripeInsideChrome"),
        "theme_thumb": bool(t.get("thumbBg") and t.get("thumbBg") not in ("rgba(0, 0, 0, 0)", "transparent")),
        "hover_grew": bool(h.get("w") and t.get("thumbW") and h.get("w") != t.get("thumbW") or (h.get("tr") and h.get("tr") != "none")),
        "drag_moved": bool(d.get("ac") and t.get("ac") and d["ac"].get("st", 0) > t["ac"].get("st", 0) + 20),
        "scale_up": s.get("rootAfter") != s.get("rootBefore") or s.get("itemAfter") != s.get("itemBefore"),
    }
    return checks

summary = {}
for k in ("ds", "kontakt"):
    if k in results:
        summary[k] = judge(results[k], k)

out = {"summary": summary, "results": results}
open(OUT, "w").write(json.dumps(out, indent=2))
print(json.dumps(summary, indent=2))
print("wrote", OUT)
