#!/usr/bin/env python3
"""Render a staged, content-replaceable social animation spec into a local MP4.

No downloading, provider generation, automatic transcription or implicit fallback.
"""
import argparse
import base64
import functools
import hashlib
import http.server
import json
from pathlib import Path
import shutil
import socketserver
import subprocess
import tempfile
import threading

SKILL=Path(__file__).resolve().parents[1]
ENGINE=SKILL/'assets/social-grammars'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

class Server(socketserver.ThreadingTCPServer):
    daemon_threads=True
    allow_reuse_address=True

def render(spec_path,output,overwrite=False):
    from playwright.sync_api import sync_playwright
    spec_path=Path(spec_path).resolve();output=Path(output).resolve()
    spec=json.loads(spec_path.read_text())
    for field,limit in (('title',16),('detail',40)):
        if not isinstance(spec.get(field),str) or not spec[field].strip() or len(spec[field])>limit:
            raise ValueError(f'{field} must be a non-empty short phrase (at most {limit} characters)')
    if spec.get('grammar') in ('d24_concept_presenter','d26_film_frame') and len(spec['title'])>8:
        raise ValueError('Vertical titles support at most 8 characters; split the phrase')
    if 'items' in spec and (not isinstance(spec['items'],list) or not 1<=len(spec['items'])<=4 or any(not isinstance(v,str) or not v.strip() or len(v)>12 for v in spec['items'])):
        raise ValueError('items must contain 1–4 non-empty short phrases of at most 12 characters')
    expected_items={'d05_focus_pip':2,'d09_editorial_type':3,'d12_type_depth':3}.get(spec.get('grammar'))
    if expected_items and 'items' in spec and len(spec['items'])!=expected_items:
        raise ValueError(f'This layout requires exactly {expected_items} items')
    if spec.get('grammar')=='d19_corner_keywords' and len(spec.get('items',[])) not in (0,4):
        raise ValueError('Corner keyword layout requires four items')
    if 'values' in spec and (not isinstance(spec['values'],list) or not 2<=len(spec['values'])<=5 or any(not isinstance(v,(int,float)) or not 0<=v<=1 for v in spec['values'])):
        raise ValueError('Chart values must contain 2–5 numbers in the range 0–1')
    if 'selected' in spec and (not isinstance(spec['selected'],int) or not 0<=spec['selected']<=8):
        raise ValueError('selected must be a grid index from 0 to 8')
    if not 1<=float(spec.get('duration',4))<=8:raise ValueError('Use a 1–8 second animation shot')
    fps=int(spec.get('fps',24))
    if float(spec.get('fps',24))!=fps:raise ValueError('fps must be an integer')
    if fps not in (24,25,30,60):raise ValueError('Supported fps: 24,25,30,60')
    if float(spec.get('video_start',0))<0:raise ValueError('video_start must be non-negative')
    assets={}
    for field in ('portrait','cutout','presenter_video'):
        if spec.get(field):
            p=(spec_path.parent/spec[field]).resolve()
            if not p.is_file():raise ValueError(f'Missing local asset: {field}')
            assets[field]=p
    if 'portrait' not in assets:raise ValueError('Stage an authorized portrait before rendering')
    alpha_grammars={'d01_three_band','d13_cutout_outline','d15_behind_type','d18_radial_orbit','d24_concept_presenter','d27_wavy_frame'}
    if spec.get('grammar') in alpha_grammars:
        if 'cutout' not in assets:raise ValueError('This grammar requires an actual transparent foreground cutout')
        from PIL import Image
        with Image.open(assets['cutout']) as im:
            if 'A' not in im.getbands():raise ValueError('Cutout has no transparency')
            alpha_min,alpha_max=im.getchannel('A').getextrema()
            if alpha_min==255 or alpha_max==0:raise ValueError('Cutout must contain visible pixels and transparency')
        if 'presenter_video' in assets:raise ValueError('Animated foreground segmentation is required; a still cutout cannot replace a moving presenter')
    if 'presenter_video' in assets:
        info=json.loads(subprocess.run(['ffprobe','-v','error','-show_format','-of','json',str(assets['presenter_video'])],capture_output=True,text=True,check=True).stdout)
        if float(info['format']['duration']) < float(spec.get('video_start',0))+float(spec.get('duration',4)):raise ValueError('Presenter video is shorter than the requested window; frozen-frame fallback rejected')
    images=[]
    for value in spec.get('images',[]):
        p=(spec_path.parent/value).resolve()
        if not p.is_file():raise ValueError('Missing evidence image; no empty-card fallback')
        images.append(p)
    if output==spec_path or output in assets.values() or output in images:
        raise ValueError('Output would overwrite an input asset or spec')
    engine_files=[ENGINE/'social.js',ENGINE/'index.html']+[SKILL/'assets/huashu-engine/lib/fonts'/f for f in ('NotoSansSC-800.woff','NotoSerifSC-sub.woff')]
    identity={'spec_sha256':sha(spec_path),'engine_sha256':hashlib.sha256(''.join(sha(p) for p in engine_files).encode()).hexdigest(),
              'asset_hashes':{field:sha(p) for field,p in assets.items()},'images_sha256':[sha(p) for p in images]}
    manifest=output.with_suffix('.manifest.json')
    if output.exists() and not overwrite:
        if manifest.exists():
            previous=json.loads(manifest.read_text())
            if all(previous.get(k)==v for k,v in identity.items()) and previous.get('output_sha256')==sha(output):return {**previous,'cache_used':True}
        raise ValueError('Output exists with different or unverified inputs; use another output or --overwrite')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='social-grammar-',dir=output.parent) as temp:
        work=Path(temp)
        for filename in ('index.html','social.js'):shutil.copyfile(ENGINE/filename,work/filename)
        (work/'fonts').mkdir()
        for font in ('NotoSansSC-800.woff','NotoSerifSC-sub.woff'):
            shutil.copyfile(SKILL/'assets/huashu-engine/lib/fonts'/font,work/'fonts'/font)
        for field,path in assets.items():
            name=field+path.suffix.lower();shutil.copyfile(path,work/name);spec[field]=name
        spec['images']=[]
        for i,path in enumerate(images):
            name=f'evidence-{i}{path.suffix.lower()}';shutil.copyfile(path,work/name);spec['images'].append(name)
        server=Server(('127.0.0.1',0),functools.partial(Handler,directory=str(work)))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        errors=[];frames=round(float(spec.get('duration',4))*fps)
        raw=work/'frames.h264';encoded=work/'output.mp4'
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch()
                page=browser.new_page(viewport={'width':1080,'height':1920},device_scale_factor=1)
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
                page.add_init_script('window.SOCIAL_SPEC='+json.dumps(spec,ensure_ascii=False)+';')
                page.goto(f'http://127.0.0.1:{server.server_address[1]}/index.html')
                page.wait_for_function('window.__ready===true||!!window.__bootFailed',timeout=60000)
                if page.evaluate('window.__bootFailed||null'):raise RuntimeError(page.evaluate('window.__bootFailed'))
                deterministic=[]
                for t in (.35,1.3,2.4):
                    if t>=float(spec.get('duration',4)):continue
                    a=page.evaluate('async(t)=>{await prepare(t);renderFrame(t);return __canvas.toDataURL("image/png")}',t)
                    page.evaluate('async(t)=>{await prepare(t);renderFrame(t)}',.05)
                    b=page.evaluate('async(t)=>{await prepare(t);renderFrame(t);return __canvas.toDataURL("image/png")}',t)
                    deterministic.append({'time':t,'equal':a==b})
                if not all(x['equal'] for x in deterministic):raise RuntimeError('Non-deterministic seek result')
                page.evaluate("""(fps)=>{window.chunks=[];window.encoderError=null;window.count=0;window.encoder=new VideoEncoder({output(c){let a=new Uint8Array(c.byteLength);c.copyTo(a);let s='';for(let i=0;i<a.length;i+=32768)s+=String.fromCharCode(...a.subarray(i,i+32768));chunks.push(btoa(s));count++;},error(e){encoderError=String(e);}});encoder.configure({codec:'avc1.64002a',width:1080,height:1920,framerate:fps,bitrate:12000000,latencyMode:'realtime',avc:{format:'annexb'}});}""",fps)
                with raw.open('wb') as f:
                    for start in range(0,frames,48):
                        batch=page.evaluate("""async ([a,b,fps])=>{for(let i=a;i<b;i++){await prepare(i/fps);renderFrame(i/fps);while(encoder.encodeQueueSize>3)await new Promise(r=>encoder.addEventListener('dequeue',r,{once:true}));if(encoderError)throw Error(encoderError);let v=new VideoFrame(__canvas,{timestamp:Math.round(i*1e6/fps),duration:Math.round(1e6/fps)});encoder.encode(v,{keyFrame:i%fps===0});v.close();}await encoder.flush();if(encoderError)throw Error(encoderError);return{chunks:chunks.splice(0),count};}""",[start,min(frames,start+48),fps])
                        for data in batch['chunks']:f.write(base64.b64decode(data))
                if batch['count']!=frames:raise RuntimeError('Encoded frame count mismatch')
                page.evaluate('encoder.close()');browser.close()
            if errors:raise RuntimeError('Browser render errors: '+'; '.join(errors[:3]))
            subprocess.run(['ffmpeg','-nostdin','-y','-v','error','-r',str(fps),'-i',str(raw),'-c:v','copy','-movflags','+faststart',str(encoded)],check=True)
            subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(encoded),'-f','null','-'],check=True)
            probe=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(encoded)],capture_output=True,text=True,check=True).stdout)
            video=next(s for s in probe['streams'] if s['codec_type']=='video')
            if int(video['nb_frames'])!=frames:raise RuntimeError('Container frame count mismatch')
            shutil.copyfile(encoded,output)
            result={**identity,'grammar':spec['grammar'],'width':1080,'height':1920,'fps':fps,'frames':frames,'duration':frames/fps,
                    'output_sha256':sha(output),'full_decode':'passed','seek_determinism':deterministic,'browser_errors':errors,
                    'audio':'none; animation mechanism preview','visual_review':'pending','replica_scope':'composition and motion mechanisms with replacement content'}
            manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            return result
        finally:server.shutdown();server.server_close()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--spec',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--overwrite',action='store_true');a=p.parse_args()
    print(json.dumps(render(a.spec,a.output,a.overwrite),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
