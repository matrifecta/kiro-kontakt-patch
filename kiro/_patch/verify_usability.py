#!/usr/bin/env python3
"""Usability sweep: glass, scroll, collapse, YouTube, toolbar."""
import json, time, urllib.request, subprocess, os, sys

OUT = '/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_usability_results.json'
PORT = 9348
PROFILE = '/tmp/catalog-use-verify'
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(['pkill', '-f', 'remote-debugging-port=9348'], check=False)
time.sleep(0.3)
proc = subprocess.Popen([
    '/usr/lib/chromium/chromium', '--headless=new', '--disable-gpu', '--no-first-run',
    '--disable-extensions', f'--remote-debugging-port={PORT}', '--remote-allow-origins=*',
    f'--user-data-dir={PROFILE}', '--noerrdialogs', '--ozone-platform=headless',
    '--ozone-override-screen-size=1280,800', '--use-angle=swiftshader-webgl', 'about:blank'
], stdout=open('/tmp/catalog-use.log', 'w'), stderr=subprocess.STDOUT)
for _ in range(60):
    try:
        urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json/version', timeout=1).read()
        break
    except Exception:
        time.sleep(0.25)
else:
    open(OUT, 'w').write(json.dumps({'err': 'cdp'})); sys.exit(1)

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
    def call(self, method, params=None, timeout=180):
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
    var cs=getComputedStyle(el); var r=el.getBoundingClientRect();
    return {exists:true, display:cs.display, w:Math.round(r.width), h:Math.round(r.height),
      shown: cs.display!=='none' && r.width>2 && r.height>2};
  }
  var out={title:document.title, href:location.href, vw:innerWidth, vh:innerHeight, portable:!!window.CATALOG_PORTABLE};
  if(typeof setMode==='function') setMode('search');
  await sleep(200);
  var fw=document.getElementById('filterWrap');
  if(fw && !fw.classList.contains('open') && typeof toggleFilter==='function') toggleFilter();
  await sleep(150);
  if(typeof setKwFullscreen==='function') setKwFullscreen(true);
  await sleep(200);
  var btn=document.getElementById('acCompanionBtn');
  if(btn) btn.click(); else if(typeof toggleAcFsCompanion==='function') toggleAcFsCompanion();
  await sleep(450);
  var ac=document.getElementById('acList');
  var sh=document.getElementById('acShell');
  var items=ac?ac.querySelectorAll('.ac-item').length:0;
  out.glass={
    searchMode: document.body.classList.contains('search-mode'),
    kwFs: document.body.classList.contains('kw-fs-open'),
    acFs: document.body.classList.contains('ac-fs-open'),
    dual: document.body.classList.contains('dual-fs-open'),
    glassShown: vis('#acCompanionBtn').shown,
    acOpen: !!(ac&&ac.classList.contains('open')),
    items: items,
    acH: ac?Math.round(ac.getBoundingClientRect().height):0,
    acScroll: ac?ac.scrollHeight:0,
    overflow: ac?getComputedStyle(ac).overflowY:'',
    nested: !!(sh&&ac&&sh.contains(ac)),
    inputFocused: document.activeElement&&document.activeElement.id==='searchInput',
    wrapBar: (function(){var b=document.querySelector('.ac-fs-bar'); return b?getComputedStyle(b).flexWrap:'';})(),
    wrapKw: (function(){var t=document.querySelector('.filter-top'); return t?getComputedStyle(t).flexWrap:'';})(),
    hist: vis('#searchHistory'),
    clearMiss: vis('#clearMissBtn'),
    editLayout: vis('#layoutEditBtn'),
    narrowAc: document.body.classList.contains('dual-ac-narrow'),
    narrowKw: document.body.classList.contains('dual-kw-narrow')
  };
  if(ac){ ac.scrollTop=80; }
  await sleep(80);
  out.scrollCollapse={
    collapsed: !!(sh&&sh.classList.contains('toolbar-scroll-collapsed')),
    acScrollTop: ac?ac.scrollTop:0
  };
  if(ac){ ac.scrollTop=0; }
  await sleep(80);
  out.scrollRestore={collapsed: !!(sh&&sh.classList.contains('toolbar-scroll-collapsed'))};

  if(typeof setKwFullscreen==='function') setKwFullscreen(false);
  if(typeof setAcFullscreen==='function') setAcFullscreen(false);
  await sleep(150);
  if(typeof toggleFilter==='function'){
    var w=document.getElementById('filterWrap');
    if(w&&w.classList.contains('open')) toggleFilter();
  }
  await sleep(100);
  if(typeof toggleAcFsCompanion==='function') toggleAcFsCompanion();
  await sleep(250);
  ac=document.getElementById('acList');
  out.independent={
    kwOpen: document.body.classList.contains('kw-open'),
    acOpen: !!(ac&&ac.classList.contains('open')),
    items: ac?ac.querySelectorAll('.ac-item').length:0,
    acFs: document.body.classList.contains('ac-fs-open'),
    glassShown: vis('#acCompanionBtn').shown
  };

  if(typeof collapseSearchMenu==='function') collapseSearchMenu();
  await sleep(80);
  if(typeof toggleAcFsCompanion==='function') toggleAcFsCompanion();
  await sleep(200);
  out.fromHidden={
    collapsed: document.body.classList.contains('search-chrome-collapsed'),
    acOpen: !!(document.getElementById('acList')&&document.getElementById('acList').classList.contains('open'))
  };

  // Expanded card + YouTube (skip if no known entry)
  var el=[].slice.call(document.querySelectorAll('.entry')).find(function(e){
    var n=(e.getAttribute('data-name')||'').toLowerCase();
    return n==='plasma drive kalimba' || n==='cloud supply' || n.indexOf('kalimba')>=0;
  }) || document.querySelector('.entry');
  out.yt={};
  if(el && typeof openChosenPreview==='function'){
    try{
      if(typeof setAcFullscreen==='function') setAcFullscreen(false);
      openChosenPreview(el);
      await sleep(400);
      var pbtn=el.querySelector('.search-popup-btn');
      out.yt.preview=true;
      out.yt.name=el.getAttribute('data-name');
      if(pbtn && typeof openCardSearchEmbed==='function' && pbtn.dataset.yt){
        openCardSearchEmbed('yt', pbtn.dataset.yt);
        await sleep(8000);
        var frame=document.getElementById('cardSearchFrame');
        var src=frame?frame.src:'';
        var popupBtns=[].slice.call(document.querySelectorAll('.card-search-popup, #cardSearchFallback button')).map(function(b){return (b.textContent||'').trim();});
        out.yt.src=src.slice(0,180);
        out.yt.embedGood=/youtube-nocookie\.com\/embed\/[A-Za-z0-9_-]{6,}/.test(src);
        out.yt.embedBad=/listType=search|\/results\?|\/watch\?/.test(src);
        out.yt.popupLabels=popupBtns.slice(0,4);
        out.yt.switchBar=vis('#cardSearchSwitch');
      }
    }catch(err){ out.yt.err=String(err); }
  }
  return out;
})()
'''

def run_at(cdp, url, w, h):
    cdp.call('Emulation.setDeviceMetricsOverride', {
        'width': w, 'height': h, 'deviceScaleFactor': 1, 'mobile': w < 900
    })
    cdp.call('Page.navigate', {'url': url})
    # wait for this URL's JS
    for _ in range(150):
        ready = cdp.call('Runtime.evaluate', {
            'expression': 'location.href.includes(%r) && typeof toggleAcFsCompanion==="function" && typeof setMode==="function" && document.querySelectorAll(".entry").length>10' % url.rsplit('/',1)[-1],
            'returnByValue': True
        }).get('result', {}).get('value')
        if ready:
            break
        time.sleep(0.35)
    return cdp.call('Runtime.evaluate', {
        'expression': EXPR, 'awaitPromise': True, 'returnByValue': True
    }).get('result', {}).get('value')

tab = new_tab('about:blank')
cdp = CDP(tab['webSocketDebuggerUrl'])
cdp.call('Page.enable')
results = {}
try:
    results['ds_portrait'] = run_at(cdp, 'http://127.0.0.1:8788/DS-CATALOG-portable.html', 390, 844)
    results['ds_landscape'] = run_at(cdp, 'http://127.0.0.1:8788/DS-CATALOG-portable.html', 844, 390)
    results['ds_desktop'] = run_at(cdp, 'http://127.0.0.1:8788/DS-CATALOG.html', 1280, 800)
    results['kontakt_portrait'] = run_at(cdp, 'http://127.0.0.1:8788/KONTAKT-CATALOG-portable.html', 390, 844)
except Exception as e:
    results['err'] = str(e)
open(OUT, 'w').write(json.dumps(results, indent=2))
proc.terminate()
print('WROTE', OUT)
