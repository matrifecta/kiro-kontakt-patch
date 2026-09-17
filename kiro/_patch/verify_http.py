import json, urllib.request, time, subprocess, os, sys
OUT='/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_results.json'
PORT=9342
PROFILE='/tmp/catalog-yt-verify-profile5'
os.makedirs(PROFILE, exist_ok=True)
subprocess.run(['pkill','-f','remote-debugging-port=9342'], check=False)
time.sleep(0.5)
proc=subprocess.Popen([
  '/usr/lib/chromium/chromium','--headless=new','--disable-gpu','--no-first-run','--disable-extensions',
  f'--remote-debugging-port={PORT}', '--remote-allow-origins=*',
  f'--user-data-dir={PROFILE}',
  '--noerrdialogs','--ozone-platform=headless','--ozone-override-screen-size=1280,800',
  '--use-angle=swiftshader-webgl','about:blank'
], stdout=open('/tmp/chromeyt5.log','w'), stderr=subprocess.STDOUT)
for i in range(60):
  try:
    urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json/version', timeout=1).read(); break
  except Exception:
    time.sleep(0.25)
else:
    open(OUT,'w').write(json.dumps({'err':'cdp'})); sys.exit(1)
import websocket

def new_tab(url):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{PORT}/json/new?'+url, method='PUT')))
    except Exception:
        return json.load(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json/new?'+url))

class CDP:
    def __init__(self, url):
        self.ws=websocket.create_connection(url, timeout=60)
        self.id=0
    def call(self, method, params=None, timeout=180):
        self.id+=1; mid=self.id
        self.ws.send(json.dumps({'id':mid,'method':method,'params':params or {}}))
        end=time.time()+timeout
        while time.time()<end:
            msg=json.loads(self.ws.recv())
            if msg.get('id')==mid:
                if 'error' in msg: raise RuntimeError(msg['error'])
                return msg.get('result',{})
        raise TimeoutError(method)

results={}
tab=new_tab('about:blank')
cdp=CDP(tab['webSocketDebuggerUrl']); cdp.call('Page.enable')
cdp.call('Page.navigate', {'url':'http://127.0.0.1:8788/DS-CATALOG-portable.html'})
n=0
for i in range(120):
    n=cdp.call('Runtime.evaluate',{'expression':'document.querySelectorAll(".entry").length','returnByValue':True}).get('result',{}).get('value') or 0
    if n>100: break
    time.sleep(1)
results['ds_entries']=n
yt=cdp.call('Runtime.evaluate',{'expression':r'''
(async function(){
  function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
  const el=[...document.querySelectorAll('.entry')].find(e=>(e.getAttribute('data-name')||'').toLowerCase()==='plasma drive kalimba');
  if(!el) return {err:'missing'};
  openChosenPreview(el); await sleep(800);
  const btn=el.querySelector('.search-popup-btn');
  openCardSearchEmbed('yt', btn.dataset.yt); await sleep(14000);
  const frame=document.getElementById('cardSearchFrame');
  const src=frame?frame.src:'';
  const rows=[...document.querySelectorAll('#cardYtList .card-yt-row-title')].map(r=>r.textContent.trim()).slice(0,6);
  return {name:el.getAttribute('data-name'), src, hidden:!!(frame&&frame.classList.contains('is-hidden')),
    bad:/listType=search|\/results\?|\/watch\?|videoseries/.test(src),
    good:/youtube-nocookie\.com\/embed\/[A-Za-z0-9_-]{6,}/.test(src),
    ytId:cardSearchState.ytId, rows};
})()
''','awaitPromise':True,'returnByValue':True}).get('result',{}).get('value')
results['yt_ds']=yt
if yt and yt.get('src'):
    req=urllib.request.Request(yt['src'], headers={'User-Agent':'Mozilla/5.0','Referer':'http://127.0.0.1:8788/DS-CATALOG-portable.html'})
    with urllib.request.urlopen(req, timeout=20) as r:
        body=r.read(400000).decode('utf-8','ignore')
        results['yt_ds_embed']={'status':r.status,'err153':any(x in body for x in ['Error 153','Napaka 153','ytp-error-content']),'player':'html5-video-player' in body or 'ytcfg' in body}

cdp.call('Page.navigate', {'url':'http://127.0.0.1:8788/KONTAKT-CATALOG.html'})
for i in range(60):
    n=cdp.call('Runtime.evaluate',{'expression':'document.querySelectorAll(".entry").length','returnByValue':True}).get('result',{}).get('value') or 0
    if n>=40: break
    time.sleep(0.5)
results['kontakt_entries']=n
cloud=cdp.call('Runtime.evaluate',{'expression':r'''
(async function(){
  function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
  const el=[...document.querySelectorAll('.entry')].find(e=>e.getAttribute('data-name')==='Cloud Supply');
  if(!el) return {err:'no'};
  openChosenPreview(el); await sleep(600);
  const btn=el.querySelector('.search-popup-btn');
  openCardSearchEmbed('web', btn.dataset.web); await sleep(12000);
  const reader=document.getElementById('cardSearchReader');
  const titles=[...reader.querySelectorAll('.card-search-row-title')].map(t=>t.textContent.trim());
  const status=(reader.innerText||'').slice(0,500);
  const cia=titles.some(t=>/cia|arctic|soviet/i.test(t))||/cia|arctic|soviet/i.test(status);
  openCardSearchEmbed('img', btn.dataset.img); await sleep(12000);
  const reader2=document.getElementById('cardSearchReader');
  const imgs=[...reader2.querySelectorAll('.card-search-tile img')].map(i=>({alt:i.alt||'',src:(i.getAttribute('src')||'').slice(0,120)}));
  const status2=(reader2.innerText||'').slice(0,500);
  const junk=imgs.some(i=>/histolog|tire|tyre|microscope|anatomy|cia/i.test(i.alt+' '+i.src))||/histolog|tire|tyre|cia|arctic/i.test(status2);
  openCardSearchEmbed('yt', btn.dataset.yt); await sleep(14000);
  const frame=document.getElementById('cardSearchFrame');
  const ytsrc=frame?frame.src:'';
  const rows=[...document.querySelectorAll('#cardYtList .card-yt-row-title')].map(r=>r.textContent.trim()).slice(0,5);
  return {webTitles:titles, webStatus:status, webHasCia:cia, imgCount:imgs.length, imgs, imgStatus:status2, imgJunk:junk,
    ytSrc:ytsrc, ytGood:/youtube-nocookie\.com\/embed\/[A-Za-z0-9_-]{6,}/.test(ytsrc), ytBad:/listType=search|\/results\?|\/watch\?/.test(ytsrc), ytRows:rows, ytId:cardSearchState.ytId};
})()
''','awaitPromise':True,'returnByValue':True}).get('result',{}).get('value')
results['cloud']=cloud
if cloud and cloud.get('ytSrc'):
    req=urllib.request.Request(cloud['ytSrc'], headers={'User-Agent':'Mozilla/5.0','Referer':'http://127.0.0.1:8788/KONTAKT-CATALOG.html'})
    with urllib.request.urlopen(req, timeout=20) as r:
        body=r.read(400000).decode('utf-8','ignore')
        results['cloud_embed']={'status':r.status,'err153':any(x in body for x in ['Error 153','Napaka 153','ytp-error-content']),'player':'html5-video-player' in body or 'ytcfg' in body}

open(OUT,'w').write(json.dumps(results, indent=2))
proc.terminate()
print('WROTE', OUT)
