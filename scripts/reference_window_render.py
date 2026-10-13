#!/usr/bin/env python3
"""Render an explicitly measured native PTS window without changing source frame intervals.

This renderer reconstructs authored layers; it does not infer them from a video.
Reference media and extracted artwork stay in the local study project.
Frames are neither duplicated nor resampled. The canvas is rendered once per
original frame and lossless PNG intermediates are encoded at exact source PTS.
"""
import argparse
import base64
from fractions import Fraction
import hashlib
import http.server
import json
import math
from pathlib import Path
import shutil
import socketserver
import subprocess
import tempfile
import threading
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/'assets/reference-engine'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def read_spec(path):
    path=Path(path).resolve();s=json.loads(path.read_text());inputs={path}
    for key in ('width','height','frames'):
        if type(s.get(key)) is not int or s[key]<=0:raise ValueError(f'{key} must be a positive integer')
    if s['width']%2 or s['height']%2:raise ValueError('H.264 requires even dimensions')
    fps=Fraction(str(s['fps']))
    if not 1<=float(fps)<=120:raise ValueError('Invalid native frame rate')
    times=s.get('times',[])
    if len(times)!=s['frames'] or any(not math.isfinite(float(t)) for t in times):raise ValueError('One finite timestamp per output frame is required')
    if abs(times[0])>1e-7 or any(times[i]>=times[i+1] for i in range(len(times)-1)):
        raise ValueError('Native output frame times must start at zero and increase strictly')
    if not s.get('reference') or not s.get('layers'):raise ValueError('Reference identity and measured layers are required')
    ref=s['reference'];source=(path.parent/ref['path']).resolve();inputs.add(source)
    if not source.is_file() or sha(source)!=ref.get('sha256'):raise ValueError('Complete reference source is missing or changed')
    first=ref.get('first_frame')
    if type(first) is not int or first<0:raise ValueError('Native first frame is required')
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_streams','-of','json',str(source)]))['streams'][0]
    if (probe['width'],probe['height'])!=(s['width'],s['height']):
        raise ValueError('Canvas must match the complete original reference')
    if s.get('timestamp_mode')!='native_window':
        raise ValueError('This entry point requires explicit native_window mode')
    if int(probe.get('nb_frames',0))<first+s['frames']:
        raise ValueError('Reference window exceeds the decoded native source frame range')
    # Average frame rate alone cannot establish CFR. Inspect the actual source
    # timestamps; a uniform spec must never silently replace a VFR timeline.
    native=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp','-of','json',str(source)]))['frames']
    time_base=Fraction(probe['time_base'])
    if len(native)!=int(probe['nb_frames']) or any('best_effort_timestamp' not in row for row in native):raise ValueError('Native source timestamps are missing or incomplete')
    pts=[int(row['best_effort_timestamp'])*time_base for row in native]
    if any(pts[i]>=pts[i+1] for i in range(len(pts)-1)):
        raise ValueError('Native source PTS must be strictly increasing')
    selected=pts[first:first+s['frames']]
    declared=ref.get('frame_times',[])
    if len(declared)!=s['frames'] or any(not isinstance(t,(int,float)) or not math.isfinite(t) for t in declared):
        raise ValueError('Every selected source frame needs its absolute native timestamp')
    if any(abs(float(t)-declared[i])>1e-7 for i,t in enumerate(selected)):
        raise ValueError('Declared source frame times differ from the original native PTS')
    if any(abs(float(t-selected[0])-times[i])>1e-7 for i,t in enumerate(selected)):
        raise ValueError('Output times must preserve every selected native source interval')
    if Fraction(ref.get('time_base','0'))!=time_base:
        raise ValueError('Reference time base must match the original native stream')
    if ref.get('native_pts')!=[int(native[first+i]['best_effort_timestamp']) for i in range(s['frames'])]:
        raise ValueError('Every declared integer native PTS must match the source')
    final_duration=(pts[first+s['frames']]-selected[-1]) if first+s['frames']<len(pts) else Fraction(1,1)/fps
    durations=[selected[i+1]-selected[i] for i in range(len(selected)-1)]+[final_duration]
    if len(s.get('frame_durations',[]))!=s['frames'] or any(abs(float(t)-s['frame_durations'][i])>1e-7 for i,t in enumerate(durations)):
        raise ValueError('Every original frame hold interval must be declared accurately')
    for layer in s['layers']:
        if not layer.get('id') or layer.get('kind') not in ('image','sequence','text','rect','gradient'):raise ValueError('Invalid or unsupported layer')
        if layer.get('blend_mode','source-over') not in ('source-over','screen','multiply','overlay','lighten'):raise ValueError('Unsupported layer blend mode')
        if layer.get('start_frame',0)<0 or layer.get('end_frame',s['frames'])>s['frames']:raise ValueError('Layer exceeds the reference window')
        if layer['kind'] in ('image','sequence') and layer.get('asset') not in s['assets']:raise ValueError('Layer asset is missing')
        if layer.get('matrix') and (len(layer['matrix'])!=s['frames'] or any(len(m)!=6 or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in m) for m in layer['matrix'])):
            raise ValueError('A measured transform needs six finite numbers for every native frame')
        sampled={'x','y','width','height','rotation','skew','opacity','blur','radius','clip_x','clip_y','clip_width','clip_height','outline_width','font_size','reveal'}
        for property_name,track in layer.items():
            if property_name in sampled and isinstance(track,list) and (len(track)!=s['frames'] or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in track)):
                raise ValueError('Sampled property tracks need one finite numeric value per frame')
            if isinstance(track,dict) and 'keys' in track:
                keys=track['keys']
                if not keys or any(len(k)!=2 or not isinstance(k[1],(int,float)) or not math.isfinite(k[1]) for k in keys):raise ValueError('Invalid keyframe track')
                if any(keys[i][0]>=keys[i+1][0] for i in range(len(keys)-1)):raise ValueError('Keyframes must be strictly ordered')
    resolved={}
    for key,asset in s['assets'].items():
        a=dict(asset)
        if a.get('source_video'):
            original=(path.parent/a['source_video']).resolve();inputs.add(original)
            if not original.is_file() or sha(original)!=a.get('source_sha256'):raise ValueError('Layer source video identity failed')
        if 'paths' in a:
            if len(a.get('times',[]))!=len(a['paths']) or not a['paths']:raise ValueError('A sequence needs a native timestamp for every frame')
            if any(a['times'][i]>=a['times'][i+1] for i in range(len(a['times'])-1)):raise ValueError('Sequence timestamps must be ordered')
            a['paths']=[(path.parent/p).resolve() for p in a['paths']]
            if a.get('role')=='dynamic_foreground':
                if not a.get('source_video') or not a.get('method'):raise ValueError('Dynamic matte source and method must be recorded')
                from PIL import Image
                for frame in (a['paths'][0],a['paths'][len(a['paths'])//2],a['paths'][-1]):
                    with Image.open(frame) as im:
                        if 'A' not in im.getbands():raise ValueError('Dynamic foreground frames need an alpha channel')
                        lo,hi=im.getchannel('A').getextrema()
                        if lo==255 or hi==0:raise ValueError('Dynamic foreground cannot be opaque or empty')
            paths=a['paths']
        else:
            a['path']=(path.parent/a['path']).resolve();paths=[a['path']]
        for p in paths:
            if not p.is_file():raise ValueError('Missing frame or artwork: '+str(p))
            if p==source:raise ValueError('Original reference video replay cannot be a reconstruction layer')
            inputs.add(p)
        resolved[key]=a
    return s,resolved,inputs,fps

def encode_native_pngs(work,mp4,s):
    import av
    from PIL import Image
    tb=Fraction(s['reference']['time_base'])
    ticks=[p-s['reference']['native_pts'][0] for p in s['reference']['native_pts']]
    durations={ticks[i]:round(s['frame_durations'][i]/float(tb)) for i in range(s['frames'])}
    with av.open(str(mp4),'w',options={'movflags':'+faststart'}) as out:
        stream=out.add_stream('libx264',rate=Fraction(str(s['fps'])))
        stream.width=s['width'];stream.height=s['height'];stream.pix_fmt='yuv420p'
        stream.time_base=tb;stream.codec_context.time_base=tb
        stream.codec_context.thread_count=1
        stream.codec_context.color_range=1;stream.codec_context.colorspace=1
        stream.codec_context.color_primaries=1;stream.codec_context.color_trc=1
        stream.options={'crf':'12','preset':'fast','bf':'0','tune':'zerolatency'}
        def mux(packet):
            source_tick=round(packet.pts*packet.time_base/tb)
            if source_tick not in durations:raise RuntimeError('Encoder returned an unknown native PTS')
            packet.duration=round(Fraction(durations[source_tick])*tb/packet.time_base)
            out.mux(packet)
        for i,tick in enumerate(ticks):
            with Image.open(work/f'frame-{i:07d}.png') as im:
                frame=av.VideoFrame.from_image(im.convert('RGB'))
            frame=frame.reformat(format='yuv420p',src_colorspace='ITU709',dst_colorspace='ITU709')
            frame.pts=tick;frame.time_base=tb
            for packet in stream.encode(frame):mux(packet)
        for packet in stream.encode():mux(packet)

def verify_native_pts(mp4,s):
    import av
    decoded=[];holds=[]
    with av.open(str(mp4)) as source:
        for frame in source.decode(video=0):
            decoded.append(float(frame.pts*frame.time_base))
            holds.append(float(frame.duration*frame.time_base))
    if len(decoded)!=s['frames'] or any(abs(t-s['times'][i])>1e-7 for i,t in enumerate(decoded)):
        raise RuntimeError('Encoded native PTS changed; output was not accepted')
    if any(abs(t-s['frame_durations'][i])>1e-7 for i,t in enumerate(holds)):
        raise RuntimeError('Encoded frame holds changed; output was not accepted')

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address=True;daemon_threads=True

def render(spec_path,output,overwrite=False):
    from playwright.sync_api import sync_playwright
    spec_path=Path(spec_path).resolve();output=Path(output).resolve()
    s,assets,inputs,fps=read_spec(spec_path)
    engine_files=[p.resolve() for p in [ENGINE/'index.html',ENGINE/'reference.js',Path(__file__).resolve(),ROOT/'assets/huashu-engine/lib/fonts/NotoSansSC-800.woff']]
    manifest=output.with_suffix('.manifest.json').resolve()
    if output in inputs or manifest in inputs or output in engine_files or manifest in engine_files:raise ValueError('Output or manifest would overwrite an input/engine file')
    sources={str(p):sha(p) for p in inputs if p.suffix.lower() in ('.mp4','.mov','.mkv','.webm','.avi')}
    identity={'spec_sha256':sha(spec_path),'engine_sha256':hashlib.sha256(''.join(sha(p) for p in engine_files).encode()).hexdigest(),
              'assets_sha256':{key:[sha(p) for p in (a['paths'] if 'paths' in a else [a['path']])] for key,a in assets.items()},'sources_sha256':sources}
    if output.exists() and not overwrite:
        if manifest.exists():
            old=json.loads(manifest.read_text())
            if all(old.get(k)==v for k,v in identity.items()) and old.get('output_sha256')==sha(output):return {**old,'cache_used':True}
        raise ValueError('Output differs or is unverified; use another output or --overwrite')
    output.parent.mkdir(parents=True,exist_ok=True);files={'/index.html':ENGINE/'index.html','/reference.js':ENGINE/'reference.js','/fonts/NotoSansSC-800.woff':engine_files[-1]}
    staged=json.loads(json.dumps(s))
    for key,a in assets.items():
        paths=a['paths'] if 'paths' in a else [a['path']];urls=[]
        for i,p in enumerate(paths):
            url=f'/media/{key}-{i:05}{p.suffix}';files[url]=p;urls.append(url)
        if 'paths' in a:staged['assets'][key]['paths']=urls
        else:staged['assets'][key]['path']=urls[0]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            file=files.get(urlsplit(self.path).path)
            if file is None:return self.send_error(404)
            self.send_response(200);self.send_header('Content-Length',str(file.stat().st_size));self.end_headers()
            try:
                with file.open('rb') as f:shutil.copyfileobj(f,self.wfile)
            except (BrokenPipeError,ConnectionResetError):pass
    server=Server(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
    errors=[]
    try:
        with tempfile.TemporaryDirectory(prefix='reference-render-',dir=output.parent) as temp:
            work=Path(temp);raw=work/'stream.h264';mp4=work/'video.mp4';checks=[]
            with sync_playwright() as pw:
                browser=pw.chromium.launch();page=browser.new_page(viewport={'width':s['width'],'height':s['height']},device_scale_factor=1)
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('console',lambda message:errors.append(message.text) if message.type=='error' else None)
                page.add_init_script('window.REFERENCE_SPEC='+json.dumps(staged,ensure_ascii=False)+';')
                page.goto(f'http://127.0.0.1:{server.server_address[1]}/index.html');page.wait_for_function('window.__ready||window.__bootFailed',timeout=60000)
                if page.evaluate('window.__bootFailed||null'):raise RuntimeError(page.evaluate('window.__bootFailed'))
                for frame in sorted({0,s['frames']//3,s['frames']*2//3,s['frames']-1}):
                    first=page.evaluate('async f=>{await prepare(f);renderFrame(f);return __canvas.toDataURL()}',frame)
                    page.evaluate('async()=>{await prepare(0);renderFrame(0)}')
                    again=page.evaluate('async f=>{await prepare(f);renderFrame(f);return __canvas.toDataURL()}',frame)
                    checks.append({'frame':frame,'equal':first==again})
                    if first!=again:raise RuntimeError('Non-deterministic frame rendering')
                for frame in range(s['frames']):
                    encoded=page.evaluate('async f=>{await prepare(f);renderFrame(f);return __canvas.toDataURL("image/png")}',frame)
                    (work/f'frame-{frame:07d}.png').write_bytes(base64.b64decode(encoded.split(',',1)[1]))
                browser.close()
            if errors:raise RuntimeError('; '.join(errors[:3]))
            encode_native_pngs(work,mp4,s)
            verify_native_pts(mp4,s)
            subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(mp4),'-f','null','-'],check=True)
            probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(mp4)]));video=next(v for v in probe['streams'] if v['codec_type']=='video')
            if int(video['nb_frames'])!=s['frames']:raise RuntimeError('Container frame count differs')
            # Local artwork is served directly. Reject a render if any source,
            # layer, specification or engine file was edited while encoding.
            final_identity={'spec_sha256':sha(spec_path),'engine_sha256':hashlib.sha256(''.join(sha(p) for p in engine_files).encode()).hexdigest(),
                            'assets_sha256':{key:[sha(p) for p in (a['paths'] if 'paths' in a else [a['path']])] for key,a in assets.items()},'sources_sha256':{p:sha(p) for p in sources}}
            if final_identity!=identity or sha((spec_path.parent/s['reference']['path']).resolve())!=s['reference']['sha256']:
                raise RuntimeError('Render inputs changed during encoding; no output was accepted. Freeze inputs and render again.')
            shutil.copyfile(mp4,output)
            result={**identity,'width':s['width'],'height':s['height'],'fps':str(fps),'frames':s['frames'],'duration':s['times'][-1]+s['frame_durations'][-1],'reference':s['reference'],
                    'output_sha256':sha(output),'full_decode':'passed','seek_determinism':checks,'browser_errors':errors,
                    'timestamp_mode':s['timestamp_mode'],'source_frame_times':s['reference']['frame_times'],'frame_times':s['times'],'frame_durations':s['frame_durations'],'native_pts_verified':True,
                    'audio':'none; real footage animation reconstruction, no fabricated lip-sync','reference_fidelity':{'status':'pending_encoded_frame_review','unresolved':s.get('unresolved',[])}}
            manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result
    finally:server.shutdown();server.server_close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--spec',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--overwrite',action='store_true');args=parser.parse_args()
    result=render(args.spec,args.output,args.overwrite)
    print(json.dumps({k:v for k,v in result.items() if k!='assets_sha256'},ensure_ascii=False,indent=2))
