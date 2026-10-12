#!/usr/bin/env python3
"""Native portrait full films; deterministic Canvas → H264 → one accepted AAC master.
Only localhost source assets. Resume only hash-matching accepted metadata. No slicing/retiming.
"""
import argparse,base64,concurrent.futures,functools,hashlib,http.server,json,math,os,subprocess,socketserver,threading,time
from pathlib import Path
from playwright.sync_api import sync_playwright
SKILL=Path(__file__).resolve().parents[1]
ROOT=ENGINE=AUDIO=OUTPUT=None; FPS=24
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a): pass
class Server(socketserver.ThreadingTCPServer):
 allow_reuse_address=True; daemon_threads=True; request_queue_size=128

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def js_hash():
 h=hashlib.sha256()
 for p in sorted(x for x in ENGINE.rglob('*') if x.is_file() and x.suffix.lower() in ['.js','.html','.json','.woff','.woff2','.png','.jpg','.jpeg','.webp','.svg']):h.update(str(p.relative_to(ENGINE)).encode());h.update(p.read_bytes())
 return h.hexdigest()

def run_one(id,port,args,revision):
 start=time.time(); out=OUTPUT/'renders'/f'{id}.mp4'; meta=OUTPUT/'renders'/f'{id}.json'
 if args.resume and out.exists() and meta.exists():
  old=json.loads(meta.read_text())
  if old.get('engine_sha256')==revision and old.get('video_sha256')==sha(out) and old.get('complete')==bool(not args.to) and old.get('audio_sha256')==sha(AUDIO) and old.get('preview_to')==args.to:
   print(json.dumps({'id':id,'status':'resume','path':str(out)},ensure_ascii=False),flush=True);return old
 errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(args=['--disable-web-security'])
  page=browser.new_page(viewport={'width':1080,'height':1920},device_scale_factor=1)
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.goto(f'http://127.0.0.1:{port}/{args.page}?render=1&style={id}')
  page.wait_for_function('window.__ready===true||!!window.__bootFailed',timeout=120000)
  if page.evaluate('window.__bootFailed||null'):raise RuntimeError(page.evaluate('window.__bootFailed'))
  metadata=page.evaluate('({id:__style.id,name:__style.name,palette:__style.palette,metadata:__style.metadata})')
  duration=page.evaluate('window.__total')
  dims=page.evaluate('[__canvas.width,__canvas.height]')
  if dims!=[1080,1920]:raise ValueError('Style batch contract requires native 1080x1920 canvas')
  audio_seconds=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(AUDIO)]))
  if abs(duration-audio_seconds)>1/FPS:raise ValueError('Scene duration must match the accepted audio master within one frame')
  n=math.ceil(duration*FPS); n=min(n,round(args.to*FPS)) if args.to else n
  grab="""async ({t,fmt='jpeg'})=>{await window.prepare(t);window.renderFrame(t);return window.__canvas.toDataURL('image/'+fmt,0.96).split(',')[1];}"""
  if args.stills:
   dest=OUTPUT/'review'/'stills'/id;dest.mkdir(parents=True,exist_ok=True)
   times=[0.4,3.5,7.1,16.9,20.85,23.5,32.8,36.9,43.25,47.95,62.7,64.0,66.6,70.5,74.8]
   hashes=[]
   for t in times:
    img=base64.b64decode(page.evaluate(grab,{'t':t,'fmt':'png'}));(dest/f'{t:05.2f}.png').write_bytes(img)
    if t in [16.9,23.5,43.25,66.6]:
     again=base64.b64decode(page.evaluate(grab,{'t':t,'fmt':'png'}))
     hashes.append({'t':t,'equal':hashlib.sha256(img).digest()==hashlib.sha256(again).digest()})
   metadata.update(determinism=hashes,pageerrors=errors,engine_sha256=revision)
   (dest/'style.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
   browser.close()
   if errors or not all(x['equal'] for x in hashes):raise RuntimeError(f'{id} failed errors/determinism: {metadata}')
   print(json.dumps({'id':id,'status':'stills','seconds':round(time.time()-start,1)},ensure_ascii=False),flush=True);return metadata
  silent=out.with_suffix('.silent.mp4');log=OUTPUT/'renders'/f'{id}.ffmpeg.log'
  if args.codec=='webcodecs':
   rawfile=out.with_suffix('.h264')
   page.evaluate("""()=>{window.encodedChunks=[];window.encodeError=null;window.encodedFrames=0;window.encoder=new VideoEncoder({output(chunk){let a=new Uint8Array(chunk.byteLength);chunk.copyTo(a);let text='';for(let i=0;i<a.length;i+=32768)text+=String.fromCharCode(...a.subarray(i,i+32768));encodedChunks.push(btoa(text));encodedFrames++;},error(e){encodeError=String(e);}});encoder.configure({codec:'avc1.64002a',width:1080,height:1920,framerate:24,bitrate:16000000,latencyMode:'realtime',hardwareAcceleration:'no-preference',avc:{format:'annexb'}});}""")
   with rawfile.open('wb') as raw:
    for a in range(0,n,48):
     end=min(n,a+48)
     batch=page.evaluate("""async ([a,b])=>{for(let i=a;i<b;i++){await prepare(i/24);renderFrame(i/24);while(encoder.encodeQueueSize>3)await new Promise(r=>encoder.addEventListener('dequeue',r,{once:true}));if(encodeError)throw Error(encodeError);const f=new VideoFrame(__canvas,{timestamp:Math.round(i*1000000/24),duration:Math.round(1000000/24)});encoder.encode(f,{keyFrame:i%24===0});f.close();}await encoder.flush();if(encodeError)throw Error(encodeError);return{chunks:encodedChunks.splice(0),count:encodedFrames};}""",[a,end])
     for chunk in batch['chunks']:raw.write(base64.b64decode(chunk))
     if end%240==0 or end==n:print(json.dumps({'id':id,'frame':end,'total':n,'seconds':round(time.time()-start,1),'codec':'webcodecs'},ensure_ascii=False),flush=True)
   if batch['count']!=n:raise RuntimeError(f"Encoded {batch['count']} != {n} frames")
   subprocess.run(['ffmpeg','-y','-v','error','-r',str(FPS),'-i',str(rawfile),'-c:v','copy','-movflags','+faststart',str(silent)],check=True)
   rawfile.unlink();page.evaluate('encoder.close()')
   metadata['video_encoding']={'mode':'WebCodecs H264 annexb','codec':'avc1.64002a','bitrate':16000000,'frames':n,'hardwareAcceleration':'no-preference','frame_timestamp_us':'round(i*1e6/24)'}
  else:
   with log.open('w') as lf:
    cmd=['ffmpeg','-y','-v','error','-f','image2pipe','-framerate',str(FPS),'-c:v','mjpeg','-threads','1','-i','-','-an','-c:v','libx264','-preset','veryfast','-threads','2','-crf','17','-pix_fmt','yuv420p','-g','24','-keyint_min','24','-sc_threshold','0','-movflags','+faststart',str(silent)]
    ff=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=lf)
    try:
     for i in range(n):
      raw=base64.b64decode(page.evaluate(grab,{'t':i/FPS}));ff.stdin.write(raw)
      if i%240==0:print(json.dumps({'id':id,'frame':i,'total':n,'seconds':round(time.time()-start,1)},ensure_ascii=False),flush=True)
     ff.stdin.close();code=ff.wait()
     if code:raise RuntimeError(log.read_text())
    finally:
     if ff.poll() is None:ff.kill();ff.wait()
  browser.close()
 if errors:raise RuntimeError(f'{id} browser errors {errors}')
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(silent),'-i',str(OUTPUT/'accepted-audio.m4a'),'-map','0:v:0','-map','1:a:0','-c','copy',*(['-t',str(n/FPS)] if args.to else []),'-movflags','+faststart',str(out)],check=True)
 silent.unlink()
 metadata.update(path=str(out),duration=n/FPS,frames=n,fps=FPS,width=1080,height=1920,engine_sha256=revision,video_sha256=sha(out),audio_sha256=sha(AUDIO),pageerrors=errors,render_seconds=round(time.time()-start,1),status='rendered_pending_audit',complete=bool(not args.to),source_duration=duration,preview_to=args.to)
 meta.write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
 print(json.dumps({'id':id,'status':'rendered','seconds':metadata['render_seconds'],'bytes':out.stat().st_size},ensure_ascii=False),flush=True)
 return metadata

def main():
 global ROOT,ENGINE,AUDIO,OUTPUT
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--project',required=True);ap.add_argument('--engine',help='Explicit source engine directory for a frozen local revision; defaults to <project>/engine');ap.add_argument('--audio',required=True);ap.add_argument('--out');ap.add_argument('--ids');ap.add_argument('--codec',choices=['webcodecs','jpeg'],default='webcodecs');ap.add_argument('--page',default='index.html');ap.add_argument('--jobs',type=int,default=3);ap.add_argument('--stills',action='store_true');ap.add_argument('--to',type=float);ap.add_argument('--resume',action='store_true');args=ap.parse_args()
 ROOT=Path(args.project).expanduser().resolve();ENGINE=Path(args.engine).expanduser().resolve() if args.engine else ROOT/'engine';AUDIO=Path(args.audio).expanduser().resolve();OUTPUT=Path(args.out).expanduser().resolve() if args.out else ROOT
 if not AUDIO.is_file() or not (ENGINE/args.page).is_file():raise ValueError('Accepted audio or project engine page missing')
 for folder in ['renders','review']: (OUTPUT/folder).mkdir(parents=True,exist_ok=True)
 cards=json.loads((SKILL/'assets/style-batch/catalog.json').read_text());ids=[x['id'] for x in cards]
 if args.ids:ids=args.ids.split(',')
 if any(id not in {x['id'] for x in cards} for id in ids):raise ValueError('Unknown style ID')
 if args.jobs<1 or args.jobs>4:raise ValueError('Use 1–4 jobs')
 audio_record=OUTPUT/'accepted-audio.json';audio_hash=sha(AUDIO)
 if not args.stills and (OUTPUT/'accepted-audio.m4a').exists():
  if not audio_record.exists() or json.loads(audio_record.read_text()).get('sha256')!=audio_hash:raise ValueError('Existing AAC belongs to another or unrecorded master; use a new --out directory')
 if not args.stills and not (OUTPUT/'accepted-audio.m4a').exists():subprocess.run(['ffmpeg','-y','-v','error','-i',str(AUDIO),'-c:a','aac','-b:a','256k',str(OUTPUT/'accepted-audio.m4a')],check=True)
 if not args.stills:audio_record.write_text(json.dumps({'source':str(AUDIO),'sha256':audio_hash,'aac_sha256':sha(OUTPUT/'accepted-audio.m4a')},indent=2))
 srv=Server(('127.0.0.1',0),functools.partial(Handler,directory=str(ENGINE)));threading.Thread(target=srv.serve_forever,daemon=True).start();revision=js_hash()
 print(json.dumps({'styles':len(ids),'jobs':args.jobs,'engine_sha256':revision,'stage':'stills' if args.stills else 'fullfilms'},ensure_ascii=False),flush=True)
 results=[]
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
   futures={pool.submit(run_one,id,srv.server_address[1],args,revision):id for id in ids}
   for f in concurrent.futures.as_completed(futures):results.append(f.result())
 finally:srv.shutdown();srv.server_close()
 dest=OUTPUT/'review'/('stills-manifest.json' if args.stills else 'render-manifest.json');dest.write_text(json.dumps(sorted(results,key=lambda x:x['id']),ensure_ascii=False,indent=2))
 print('BATCH COMPLETE '+str(dest),flush=True)
if __name__=='__main__':main()
