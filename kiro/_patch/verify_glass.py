#!/usr/bin/env python3
"""Exercise magnifying-glass Search open at desktop + mobile viewports."""
import json, time, urllib.request, subprocess, os, sys

OUT = '/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_glass_results.json'
PORT = 9347
PROFILE = '/tmp/catalog-glass-verify'
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(['pkill', '-f', 'remote-debugging-port=9347'], check=False)
time.sleep(0.4)
proc = subprocess.Popen([
    '/usr/lib/chromium/chromium', '--headless=new', '--disable-gpu', '--no-first-run',
    '--disable-extensions', f'--remote-debugging-port={PORT}', '--remote-allow-origins=*',
    f'--user-data-dir={PROFILE}', '--noerrdialogs', '--ozone-platform=headless',
    '--ozone-override-screen-size=1280,800', '--use-angle=swiftshader-webgl', 'about:blank'
], stdout=open('/tmp/catalog-glass.log', 'w'), stderr=subprocess.STDOUT)

for _ in range(60):
    try:
        urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json/version', timeout=1).read()
        break
    except Exception:
        time.sleep(0.25)
else:
    open(OUT, 'w').write(json.dumps({'err': 'cdp'}))
    sys.exit(1)

import websocket

def new_tab(url):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(
            f'http://127.0.0.1:{PORT}/json/new?' + url, method='PUT')))
    except Exception:
        return json.load(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json/new?' + url))

class CDP:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=60)
        self.id = 0
    def call(self, method, params=None, timeout=120):
        self.id += 1
        mid = self.id
        self.ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            msg = json.loads(self.ws.recv())
            if msg.get('id') == mid:
                if 'error' in msg:
                    raise RuntimeError(msg['error'])
                return msg.get('result', {})
        raise TimeoutError(method)

EXPR = r'''
(async function(){
  function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
  function vis(sel){
    var el=document.querySelector(sel);
    if(!el) return {exists:false};
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    return {exists:true, display:cs.display, visibility:cs.visibility,
      w:Math.round(r.width), h:Math.round(r.height),
      shown: cs.display!=='none' && cs.visibility!=='hidden' && r.width>2 && r.height>2};
  }
  var out={vw:innerWidth, vh:innerHeight, portable:!!window.CATALOG_PORTABLE};
  if(typeof setMode==='function') setMode('search');
  await sleep(250);
  out.afterSearch={
    searchMode: document.body.classList.contains('search-mode'),
    acFsAvailable: typeof acFsAvailable==='function'?acFsAvailable():null,
    glass: vis('#acCompanionBtn'),
    hide: vis('.search-strip-hide'),
    fsBtn: vis('#searchStripFs')
  };
  var fw=document.getElementById('filterWrap');
  if(fw && !fw.classList.contains('open') && typeof toggleFilter==='function') toggleFilter();
  await sleep(200);
  if(typeof setKwFullscreen==='function') setKwFullscreen(true);
  await sleep(300);
  out.kwFs={
    kwFs: document.body.classList.contains('kw-fs-open'),
    glass: vis('#acCompanionBtn'),
    acFs: document.body.classList.contains('ac-fs-open'),
    dual: document.body.classList.contains('dual-fs-open')
  };
  var btn=document.getElementById('acCompanionBtn');
  if(btn){ btn.click(); }
  else if(typeof toggleAcFsCompanion==='function') toggleAcFsCompanion();
  await sleep(400);
  var sh=document.getElementById('acShell');
  var ac=document.getElementById('acList');
  var si=document.getElementById('searchInput');
  out.afterGlass={
    acFs: document.body.classList.contains('ac-fs-open'),
    dual: document.body.classList.contains('dual-fs-open'),
    collapsed: document.body.classList.contains('search-chrome-collapsed'),
    shellOpen: !!(sh && sh.classList.contains('open')),
    shellFs: !!(sh && sh.classList.contains('ac-fs')),
    acOpen: !!(ac && ac.classList.contains('open')),
    acH: ac?Math.round(ac.getBoundingClientRect().height):0,
    acScroll: ac?ac.scrollHeight:0,
    acOverflow: ac?getComputedStyle(ac).overflowY:'',
    focused: document.activeElement && document.activeElement.id,
    inputFocused: !!(si && document.activeElement===si),
    shellRect: sh?{w:Math.round(sh.getBoundingClientRect().width),h:Math.round(sh.getBoundingClientRect().height)}:null
  };
  if(typeof setKwFullscreen==='function') setKwFullscreen(false);
  if(typeof setAcFullscreen==='function') setAcFullscreen(false);
  await sleep(200);
  if(typeof toggleFilter==='function'){
    var w=document.getElementById('filterWrap');
    if(w && w.classList.contains('open')) toggleFilter();
  }
  await sleep(150);
  if(typeof toggleAcFsCompanion==='function') toggleAcFsCompanion();
  await sleep(350);
  ac=document.getElementById('acList');
  sh=document.getElementById('acShell');
  out.independent={
    kwOpen: document.body.classList.contains('kw-open'),
    searchMode: document.body.classList.contains('search-mode'),
    acOpen: !!(ac && ac.classList.contains('open')),
    shellOpen: !!(sh && sh.classList.contains('open')),
    acFs: document.body.classList.contains('ac-fs-open'),
    acH: ac?Math.round(ac.getBoundingClientRect().height):0,
    glass: vis('#acCompanionBtn')
  };
  if(typeof collapseSearchMenu==='function') collapseSearchMenu();
  await sleep(150);
  if(typeof toggleAcFsCompanion==='function') toggleAcFsCompanion();
  await sleep(300);
  out.fromHidden={
    collapsed: document.body.classList.contains('search-chrome-collapsed'),
    acOpen: !!(document.getElementById('acList')&&document.getElementById('acList').classList.contains('open')),
    searchMode: document.body.classList.contains('search-mode')
  };
  return out;
})()
'''

def run_at(cdp, url, w, h):
    cdp.call('Emulation.setDeviceMetricsOverride', {
        'width': w, 'height': h, 'deviceScaleFactor': 1, 'mobile': w < 900
    })
    cdp.call('Page.navigate', {'url': url})
    for _ in range(120):
        ready = cdp.call('Runtime.evaluate', {
            'expression': 'typeof setMode==="function" && typeof toggleAcFsCompanion==="function" && document.querySelectorAll(".entry").length>20',
            'returnByValue': True
        }).get('result', {}).get('value')
        if ready:
            break
        time.sleep(0.4)
    return cdp.call('Runtime.evaluate', {
        'expression': EXPR, 'awaitPromise': True, 'returnByValue': True
    }).get('result', {}).get('value')

tab = new_tab('about:blank')
cdp = CDP(tab['webSocketDebuggerUrl'])
cdp.call('Page.enable')
results = {}
try:
    results['ds_desktop'] = run_at(cdp, 'http://127.0.0.1:8788/DS-CATALOG.html', 1280, 800)
    results['ds_portrait'] = run_at(cdp, 'http://127.0.0.1:8788/DS-CATALOG-portable.html', 390, 844)
    results['ds_landscape'] = run_at(cdp, 'http://127.0.0.1:8788/DS-CATALOG-portable.html', 844, 390)
    results['kontakt_portrait'] = run_at(cdp, 'http://127.0.0.1:8788/KONTAKT-CATALOG-portable.html', 390, 844)
except Exception as e:
    results['err'] = str(e)
open(OUT, 'w').write(json.dumps(results, indent=2))
proc.terminate()
print('WROTE', OUT)
