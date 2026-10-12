#!/usr/bin/env python3
"""Local, inspectable narration-motion production helpers."""
import argparse
import difflib
import hashlib
import html
import json
import math
import re
import shutil
import subprocess
import sys
import unicodedata
from fractions import Fraction
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
RUNTIME = SKILL / 'assets/runtime'
CLI = RUNTIME / 'node_modules/hyperframes/dist/cli.js'
COMPONENTS = {'kinetic-title', 'steps', 'quote', 'split-compare', 'evidence', 'broll'}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    temp = p.with_name(p.name + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    temp.replace(p)


def run(args, **kwargs):
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True, **kwargs)
    if result.returncode:
        raise RuntimeError(f'{args[0]} failed ({result.returncode}): {result.stderr[-2400:]} {result.stdout[-800:]}')
    return result.stdout


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path]))


def media_duration(metadata):
    value = metadata.get('format', {}).get('duration')
    if value is None:
        values = [float(s['duration']) for s in metadata['streams'] if s.get('duration')]
        value = max(values) if values else 0
    return float(value)


def fps_value(value):
    a, _, b = str(value).partition('/')
    return float(a) / float(b or 1)


def existing(value, base=None):
    p = Path(value).expanduser()
    if not p.is_absolute() and base: p = base / p
    p = p.resolve()
    if not p.is_file(): raise ValueError(f'Missing input file: {p}')
    return p


def state(project, **updates):
    path = project / 'project.json'; config = read(path); config.update(updates); write(path, config)


def canonical(text):
    return ''.join(c for c in unicodedata.normalize('NFKC', text).lower() if c.isalnum())


def validate_words(words, duration):
    if not isinstance(words, list): raise ValueError('words.json must be a flat array')
    previous = -1.0
    for word in words:
        word['text'] = str(word.get('text', word.get('word', '')))
        start, end = float(word['start']), float(word['end'])
        if not word['text'].strip() or not (0 <= start < end <= duration + .1) or start < previous:
            raise ValueError(f'Invalid or unsorted word timing: {word}')
        word['start'], word['end'] = start, end; previous = start
    return words


def anchor_time(anchor, words):
    needle = canonical(anchor['text']); text = ''; times = []
    if not needle: raise ValueError('Empty normalized anchor')
    for word in words:
        chars = canonical(word['text'])
        for i, char in enumerate(chars):
            text += char; times.append(word['start'] + (word['end'] - word['start']) * i / len(chars))
    hits = []; offset = 0
    while True:
        index = text.find(needle, offset)
        if index < 0: break
        hits.append(index); offset = index + len(needle)
    occurrence = int(anchor.get('occurrence', 1))
    if occurrence < 1 or occurrence > len(hits):
        raise ValueError(f'Anchor {anchor["text"]!r}, occurrence {occurrence}, has {len(hits)} matches')
    return times[hits[occurrence - 1]] + float(anchor.get('offset', 0))


def resolve_events(events, words, duration, project):
    result = []; ids = set()
    for index, item in enumerate(events):
        event = dict(item); event['id'] = str(event.get('id', f'event-{index+1}'))
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', event['id']) or event['id'] in ids:
            raise ValueError(f'Invalid/duplicate event ID: {event["id"]}')
        ids.add(event['id'])
        if event.get('component') not in COMPONENTS: raise ValueError(f'Unsupported component: {event.get("component")}')
        if 'anchor' in event:
            if not words: raise ValueError('Word anchors need accepted words.json')
            event['start'] = anchor_time(event['anchor'], words)
            event['end'] = event['start'] + float(event['duration'])
        else:
            event['start'], event['end'] = float(event['start']), float(event['end'])
        if not (0 <= event['start'] < event['end'] <= duration + .001):
            raise ValueError(f'Event outside final audio timeline: {event["id"]}')
        if event['end'] - event['start'] < .6: raise ValueError('Readable graphics need at least 0.6 seconds')
        if event.get('position', 'top') not in ('top', 'center', 'full'): raise ValueError('position must be top, center or full')
        if event.get('position')=='full' and event['component']!='broll':raise ValueError('Only video B-roll supports a full-frame slot')
        if event.get('presenter', 'full') not in ('full', 'pip'): raise ValueError('presenter must be full or pip')
        if event['component'] == 'steps':
            if not isinstance(event.get('items'), list) or not 1 <= len(event['items']) <= 6:
                raise ValueError('steps needs 1–6 items')
            if any(not str(t).strip() for t in event['items']): raise ValueError('Empty step item')
        elif event['component'] in ('evidence', 'broll'):
            asset = existing(event['asset'], project)
            if event['component']=='evidence' and asset.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp'): raise ValueError('Evidence asset must be an image')
            if event['component']=='broll':
                metadata=probe(asset)
                if not any(s['codec_type']=='video' for s in metadata['streams']):raise ValueError('B-roll needs a video stream')
                if media_duration(metadata)+.1 < event['end']-event['start']:raise ValueError('B-roll is shorter than its assigned slot')
            event['asset'] = str(asset)
        elif event['component'] == 'split-compare':
            if not event.get('left') or not event.get('right'): raise ValueError('Comparison needs both alternatives')
        elif not event.get('text'): raise ValueError('Text component needs nonempty text')
        result.append(event)
    result.sort(key=lambda e: e['start'])
    for left, right in zip(result, result[1:]):
        if left['end'] > right['start'] + .001: raise ValueError(f'Graphics overlap: {left["id"]}, {right["id"]}')
    return result


def make_cues(words, duration):
    groups = []; group = []
    for word in words:
        if group and (len(''.join(w['text'] for w in group)) + len(word['text']) > 18
                      or word['start'] - group[-1]['end'] > .5
                      or word['end'] - group[0]['start'] > 3.2):
            groups.append(group); group = []
        group.append(word)
    if group: groups.append(group)
    return [{'text': ''.join(w['text'] for w in g).strip(), 'start': g[0]['start'],
             'end': min(duration, g[-1]['end'] + .12, groups[i+1][0]['start'] if i+1 < len(groups) else duration)}
            for i, g in enumerate(groups)]


def validate_cues(cues, duration):
    previous_end = 0
    for cue in cues:
        cue['start'], cue['end'] = float(cue['start']), float(cue['end'])
        if not cue.get('text') or not (previous_end <= cue['start'] < cue['end'] <= duration + .001):
            raise ValueError('Caption cues must be ordered, non-overlapping and within duration')
        previous_end = cue['end']
    return cues


def srt_time(seconds):
    value = round(seconds * 1000); hours, value = divmod(value, 3600000)
    minutes, value = divmod(value, 60000); seconds, ms = divmod(value, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'


def fingerprint(project):
    h = hashlib.sha256()
    for p in sorted((project/'public').rglob('*')):
        if p.is_file() and not any(s.startswith('.') or s == 'snapshots' for s in p.relative_to(project/'public').parts):
            h.update(str(p.relative_to(project/'public')).encode()); h.update(digest(p).encode())
    canvas = read(project/'project.json')['canvas']; h.update(json.dumps(canvas, sort_keys=True).encode())
    return h.hexdigest()


def input_fingerprint(project):
    """Reject stale renders when plans, narration or the skill change after build."""
    config = read(project/'project.json')
    contract = {k: config.get(k) for k in ('source','canvas','duration','style','label','composition_template','component_code')}
    h = hashlib.sha256(json.dumps(contract,sort_keys=True,ensure_ascii=False).encode())
    for name in ('shotbook.json','words.json','caption-cues.json'):
        p=project/name;h.update(name.encode());h.update(digest(p).encode() if p.exists() else b'missing')
    for name in ('composition.html','components.js'):
        h.update(digest(SKILL/'assets'/name).encode())
    for name in ('composition_template', 'component_code'):
        if config.get(name): h.update(digest(existing(config[name],project)).encode())
    h.update(digest(Path(__file__)).encode())
    for value in (config.get('source') or {}).values():
        if value:h.update(digest(existing(value,project)).encode())
    for event in read(project/'shotbook.json').get('events',[]):
        if event.get('asset'):h.update(digest(existing(event['asset'],project)).encode())
    return h.hexdigest()


def renderer_signature():
    return digest(Path(__file__))


def doctor(args):
    output = {'skill': str(SKILL), 'ffmpeg': shutil.which('ffmpeg'), 'ffprobe': shutil.which('ffprobe'),
              'node': shutil.which('node'), 'hyperframes_installed': CLI.exists()}
    import importlib.util
    output['faster_whisper_installed'] = importlib.util.find_spec('faster_whisper') is not None
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if not all(output[k] for k in ['ffmpeg', 'ffprobe', 'node', 'hyperframes_installed']): raise ValueError('Required runtime missing')


def initialize(args):
    project = Path(args.project).expanduser().resolve(); project.mkdir(parents=True, exist_ok=True)
    if (project/'project.json').exists(): raise ValueError('Project already exists; edit its manifest instead of resetting it')
    if args.video and args.audio: raise ValueError('Use an accepted A/V master, not independent replacement audio')
    source = {'video': str(existing(args.video)) if args.video else None,
              'audio': str(existing(args.audio)) if args.audio else None}
    selected = source['video'] or source['audio']; metadata = probe(selected) if selected else None
    duration = media_duration(metadata) if metadata else args.duration
    if not duration or duration <= 0: raise ValueError('Supply media or a positive motion-only duration')
    fps = args.fps
    if not fps and metadata:
        video = next((s for s in metadata['streams'] if s['codec_type'] == 'video'), None)
        fps = fps_value(video['avg_frame_rate']) if video and video.get('avg_frame_rate') not in ('0/0', '0') else None
    fps = fps or 24
    if args.width < 240 or args.height < 240 or args.width % 2 or args.height % 2 or not 1 <= fps <= 120:
        raise ValueError('Canvas must be even-sized, at least 240px; fps between 1 and 120')
    config = {'schema_version': 1, 'name': project.name, 'source': source,
              'canvas': {'width': args.width, 'height': args.height, 'fps': fps}, 'duration': duration,
              'style': {'background': '#191916', 'foreground': '#F6F2E7', 'accent': '#D1E984'},
              'review_limit': 3, 'status': 'initialized', 'mode': 'media' if selected else 'motion-only'}
    write(project/'project.json', config); write(project/'shotbook.json', {'events': []})
    if metadata: write(project/'source-probe.json', metadata)
    print(project)


def analyze(args):
    from PIL import Image, ImageDraw
    source = existing(args.video); out = Path(args.out).expanduser().resolve(); out.mkdir(parents=True, exist_ok=True)
    metadata = probe(source); duration = media_duration(metadata); end = min(args.end or duration, duration)
    if not 0 <= args.start < end or args.every <= 0: raise ValueError('Invalid analysis window or interval')
    count = math.ceil((end-args.start)/args.every)
    if count > 1000: raise ValueError('Limit dense analysis to a <=1000-frame window')
    frames = out/'frames'; frames.mkdir(exist_ok=True)
    for p in frames.glob('frame-*.jpg'): p.unlink()
    run(['ffmpeg', '-v', 'error', '-y', '-ss', args.start, '-i', source, '-t', end-args.start,
         '-vf', f'fps=1/{args.every},scale=480:-2', '-q:v', '3', frames/'frame-%05d.jpg'])
    paths = sorted(frames.glob('frame-*.jpg')); manifest = []
    for i, p in enumerate(paths): manifest.append({'file':str(p),'approx_time':args.start+i*args.every})
    sheets = []; tile_w, tile_h = 260, 190
    for base in range(0,len(paths),20):
        batch = paths[base:base+20]; sheet=Image.new('RGB',(tile_w*4,tile_h*math.ceil(len(batch)/4)), '#151A20'); draw=ImageDraw.Draw(sheet)
        for j,p in enumerate(batch):
            image=Image.open(p);image.thumbnail((250,160));x=(j%4)*tile_w+5;y=(j//4)*tile_h+4;sheet.paste(image,(x,y))
            draw.text((x,y+163),f'~{manifest[base+j]["approx_time"]:.2f}s',fill='white')
        filename=out/f'contact-{base//20+1:02}.jpg';sheet.save(filename,quality=90);sheets.append(str(filename))
    cuts = subprocess.run(['ffmpeg','-hide_banner','-ss',str(args.start),'-i',str(source),'-t',str(end-args.start),
                           '-vf', "scale=320:-2,select='gt(scene,0.25)',showinfo",'-an','-f','null','-'],capture_output=True,text=True)
    if cuts.returncode: raise RuntimeError(cuts.stderr[-1200:])
    candidates=[args.start+float(t) for t in re.findall(r'pts_time:([0-9.]+)',cuts.stderr)]
    write(out/'analysis.json',{'source':str(source),'sha256':digest(source),'metadata':metadata,
          'window':{'start':args.start,'end':end,'every':args.every},'frames':manifest,'contact_sheets':sheets,
          'cut_candidates':candidates,'sampling_note':'Approximate sample labels; inspect native consecutive frames for precise effect boundaries.'})
    print(json.dumps({'analysis':str(out/'analysis.json'),'frames':len(paths),'sheets':sheets,'cut_candidates':candidates},ensure_ascii=False))


def transcribe(args):
    from faster_whisper import WhisperModel
    project=Path(args.project).expanduser().resolve();config=read(project/'project.json')
    selected=config['source']['video'] or config['source']['audio']
    if not selected: raise ValueError('No narration to transcribe')
    source=existing(selected,project);audio=project/'analysis/narration-16k.wav';audio.parent.mkdir(exist_ok=True)
    run(['ffmpeg','-v','error','-y','-i',source,'-vn','-ar','16000','-ac','1',audio])
    model=WhisperModel(args.model,device='cpu',compute_type='int8',cpu_threads=4)
    prompt=existing(args.prompt_file,project).read_text() if args.prompt_file else None
    segments,info=model.transcribe(str(audio),language=args.language,word_timestamps=True,vad_filter=True,beam_size=5,initial_prompt=prompt)
    words=[];sentences=[]
    for segment in segments:
        sentences.append({'start':segment.start,'end':segment.end,'text':segment.text})
        for word in segment.words or []:
            if word.end>word.start and word.word.strip():words.append({'text':word.word,'start':word.start,'end':word.end,'probability':word.probability})
    if not words: raise ValueError('ASR returned no timed words')
    validate_words(words,config['duration'])
    report={'model':args.model,'language':info.language,'source_sha256':digest(source),'segments':sentences,'text_review_required':True}
    if args.expected_script:
        expected=canonical(existing(args.expected_script,project).read_text());observed=canonical(''.join(w['text'] for w in words))
        agreement=difflib.SequenceMatcher(None,expected,observed,autojunk=False).ratio();report['script_agreement']=agreement
        if agreement<.75:
            write(project/'analysis/transcription-rejected.json',report)
            raise ValueError('ASR disagrees with the approved script; prior accepted words were preserved. Use a better model or review the actual audio.')
    write(project/'words.json',words);write(project/'analysis/transcription.json',report)
    state(project,status='transcribed_needs_text_review'); print(json.dumps({'words':len(words),'language':info.language,'text_review_required':True},ensure_ascii=False))


def text(value): return html.escape(str(value),quote=True)


def event_markup(event):
    kind=event['component']; kicker=f'<div class="kicker">{text(event.get("kicker",""))}</div>'
    if kind=='kinetic-title': inner=kicker+f'<div class="title-mask"><h1 class="hero-text">{text(event["text"])}</h1></div>'
    elif kind=='quote': inner=kicker+f'<div class="quote-mark">“</div><h2 class="quote-text">{text(event["text"])}</h2>'
    elif kind=='steps':
        inner=f'<h2 class="section-title">{text(event.get("title",""))}</h2><div class="step-list">'+''.join(f'<div class="step"><span class="step-number">{i+1:02}</span><span>{text(item)}</span></div>' for i,item in enumerate(event['items']))+'</div>'
    elif kind=='split-compare': inner=f'<h2 class="section-title">{text(event.get("title",""))}</h2><div class="comparison"><div class="alternative">{text(event["left"])}</div><div class="alternative highlighted">{text(event["right"])}</div></div>'
    elif kind=='evidence': inner=f'<h2 class="section-title">{text(event.get("title",""))}</h2><div class="image-mask"><img class="evidence-image" src="{text(event["staged_asset"])}" /></div><p class="evidence-caption">{text(event.get("caption",""))}</p>'
    else:
        if event.get('position')=='full':
            inner=f'<video id="{event["id"]}-video" class="clip broll-video" src="{text(event["staged_asset"])}" playsinline muted data-has-audio="false" data-start="{event["start"]}" data-duration="{event["end"]-event["start"]}" data-track-index="2"></video>'
            return f'<section id="{event["id"]}" class="graphic full"><div class="graphic-inner broll">{inner}</div></section>'
        inner=f'<h2 class="section-title">{text(event.get("title",""))}</h2><div class="image-mask"><video id="{event["id"]}-video" class="clip broll-video" src="{text(event["staged_asset"])}" playsinline muted data-has-audio="false" data-start="{event["start"]}" data-duration="{event["end"]-event["start"]}" data-track-index="2"></video></div>'
        # Media owns its explicit timing; its plain ancestors must be untimed.
        return f'<section id="{event["id"]}" class="graphic {event.get("position","top")}"><div class="graphic-inner broll">{inner}</div></section>'
    return f'<section id="{event["id"]}" class="clip graphic {event.get("position","top")}" data-start="{event["start"]}" data-duration="{event["end"]-event["start"]}" data-track-index="2"><div class="graphic-inner {kind}">{inner}</div></section>'


def build(args):
    project=Path(args.project).expanduser().resolve();config=read(project/'project.json');duration=float(config['duration']);canvas=config['canvas']
    words=validate_words(read(project/'words.json'),duration) if (project/'words.json').exists() else []
    cues=validate_cues(read(project/'caption-cues.json'),duration) if (project/'caption-cues.json').exists() else make_cues(words,duration)
    events=resolve_events(read(project/'shotbook.json')['events'],words,duration,project)
    if any(e.get('presenter')=='pip' for e in events) and not config['source'].get('video'):
        raise ValueError('Presenter PiP needs accepted video footage')
    public=project/'public';public.mkdir(exist_ok=True);assets=public/'assets';assets.mkdir(exist_ok=True);vendor=public/'vendor';vendor.mkdir(exist_ok=True)
    gsap=RUNTIME/'node_modules/gsap/dist/gsap.min.js'
    if not gsap.is_file(): raise ValueError('Run npm install in assets/runtime first')
    shutil.copy2(gsap,vendor/'gsap.min.js');shutil.copy2(SKILL/'assets/components.js',public/'components.js')
    selected=config['source']['video'] or config['source']['audio'];media='';has_audio=False
    if config['source'].get('video') and config['source'].get('audio'): raise ValueError('Independent replacement audio is ambiguous; supply accepted master')
    if selected:
        source=existing(selected,project);meta=probe(source);has_audio=any(s['codec_type']=='audio' for s in meta['streams'])
        sig=digest(source)+':'+str(canvas['fps'])+':'+str(duration);old=read(project/'staged-source.json') if (project/'staged-source.json').exists() else {}
        if config['source']['video']:
            staged=assets/'source.mp4'
            if old.get('signature')!=sig or not staged.exists():
                run(['ffmpeg','-v','error','-y','-i',source,'-t',duration,'-vf',f'fps={canvas["fps"]},scale=trunc(iw/2)*2:trunc(ih/2)*2',
                     '-c:v','libx264','-crf','18','-preset','fast','-g',round(canvas['fps']),'-keyint_min',round(canvas['fps']),
                     '-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',staged])
            media=f'<div class="presenter-wrap"><video id="presenter" src="assets/source.mp4" playsinline data-start="0" data-duration="{duration}" data-track-index="0" data-has-audio="{str(has_audio).lower()}"></video></div>'
        else:
            if not has_audio: raise ValueError('Audio input has no audio stream')
            staged=assets/'narration.wav'
            if old.get('signature')!=sig or not staged.exists():run(['ffmpeg','-v','error','-y','-i',source,'-t',duration,'-vn','-ar','48000',staged])
            media=f'<audio id="narration" src="assets/narration.wav" data-start="0" data-duration="{duration}" data-track-index="0" data-volume="1"></audio>'
        write(project/'staged-source.json',{'signature':sig,'path':str(staged),'has_audio':has_audio})
    for event in events:
        if event['component'] in ('evidence','broll'):
            source=Path(event['asset']);asset_sig=digest(source)
            if event['component']=='broll':asset_sig=hashlib.sha256((asset_sig+str(canvas['fps'])+str(event['end']-event['start'])).encode()).hexdigest()
            filename=f'{event["id"]}-{asset_sig[:12]}{source.suffix.lower() if event["component"]=="evidence" else ".mp4"}'
            if event['component']=='evidence':shutil.copy2(source,assets/filename)
            elif not (assets/filename).exists():
                run(['ffmpeg','-v','error','-y','-i',source,'-t',event['end']-event['start'],'-an','-vf',f'fps={canvas["fps"]}',
                     '-c:v','libx264','-crf','18','-g',round(canvas['fps']),'-keyint_min',round(canvas['fps']),'-pix_fmt','yuv420p','-movflags','+faststart',assets/filename])
            event['staged_asset']='assets/'+filename
    captions=''.join(f'<div id="caption-{i}" class="clip caption" data-start="{c["start"]}" data-duration="{c["end"]-c["start"]}" data-track-index="3"><div class="caption-inner">{text(c["text"])}</div></div>' for i,c in enumerate(cues))
    styles=config.get('style',{})
    for key in ('background','foreground','accent'):
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}',styles.get(key,'')): raise ValueError('Style colors must be six-digit hex')
    payload={'events':events,'cues':cues,'duration':duration,'canvas':canvas,'has_presenter':bool(config['source'].get('video'))}
    data=json.dumps(payload,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template=(existing(config['composition_template'],project) if config.get('composition_template') else SKILL/'assets/composition.html').read_text()
    mapping={'ROOT':f'class="{"" if payload["has_presenter"] else "audio-only"}" data-composition-id="talking-head" data-start="0" data-duration="{duration}" data-width="{canvas["width"]}" data-height="{canvas["height"]}" data-fps="{canvas["fps"]}"',
             'MEDIA':media,'EVENTS':''.join(event_markup(e) for e in events),'CAPTIONS':captions,'PAYLOAD':data,
             'BACKGROUND':styles['background'],'FOREGROUND':styles['foreground'],'ACCENT':styles['accent'],
             'LABEL':f'<div class="footer">{text(config["label"])}</div>' if config.get('label') else '',
             'COMPONENT_CODE':(existing(config['component_code'],project) if config.get('component_code') else SKILL/'assets/components.js').read_text().replace('</script','<\\/script')}
    for key,value in mapping.items():template=template.replace('__'+key+'__',value)
    (public/'index.html').write_text(template)
    (project/'subtitles.srt').write_text('\n\n'.join(f'{i+1}\n{srt_time(c["start"])} --> {srt_time(c["end"])}\n{c["text"]}' for i,c in enumerate(cues))+'\n')
    write(project/'resolved-shotbook.json',payload)
    state(project,status='built',expected_audio=has_audio,build_fingerprint=fingerprint(project),build_input_fingerprint=input_fingerprint(project))
    print(json.dumps({'project':str(project),'events':len(events),'cues':len(cues),'duration':duration},ensure_ascii=False))


def render(args):
    project=Path(args.project).expanduser().resolve();config=read(project/'project.json');fp=fingerprint(project)
    if fp!=config.get('build_fingerprint') or input_fingerprint(project)!=config.get('build_input_fingerprint'):
        raise ValueError('Inputs or composition changed after build; rebuild before rendering')
    output=project/'output.mp4';record=read(project/'render.json') if (project/'render.json').exists() else {}
    if not args.force and record.get('fingerprint')==fp and record.get('renderer_signature')==renderer_signature() and output.exists() and record.get('output_sha256')==digest(output):
        print(json.dumps({'reused':str(output)}));return
    if not CLI.exists():raise ValueError('Missing HyperFrames runtime')
    fps=str(Fraction(config['canvas']['fps']).limit_denominator(1001))
    commands=[['node',CLI,'check',project/'public','--at-transitions'],['node',CLI,'render',project/'public','--output',output,'--fps',fps,'--workers','1','--browser-gpu']]
    log=project/'render.log';log.write_text('')
    for command in commands:
        with log.open('a') as f:
            f.write(json.dumps([str(c) for c in command])+'\n');f.flush()
            result=subprocess.run([str(c) for c in command],stdout=f,stderr=subprocess.STDOUT)
        if result.returncode:
            state(project,status='render_failed');raise RuntimeError(log.read_text()[-3500:])
    # B-roll is silent: preserve the accepted native narration and channel layout,
    # rather than letting a renderer's mono-to-stereo mixer alter its level.
    selected=config['source'].get('video') or config['source'].get('audio')
    if config.get('expected_audio') and selected:
        source=existing(selected,project);muxed=project/'output-audio-fixed.mp4'
        run(['ffmpeg','-v','error','-y','-i',output,'-i',source,'-map','0:v:0','-map','1:a:0',
             '-c:v','copy','-c:a','aac','-b:a','192k','-t',config['duration'],'-movflags','+faststart',muxed])
        muxed.replace(output)
    write(project/'render.json',{'fingerprint':fp,'output_sha256':digest(output),'output':str(output),
          'renderer':'hyperframes 0.8.145','renderer_signature':renderer_signature(),
          'audio_policy':'accepted-native-track' if config.get('expected_audio') else 'silent'})
    state(project,status='rendered_needs_checks');print(output)


def check(args):
    project=Path(args.project).expanduser().resolve();config=read(project/'project.json');output=existing(project/'output.mp4');record=read(project/'render.json')
    fp=fingerprint(project);failures=[]
    if fp!=record['fingerprint'] or digest(output)!=record['output_sha256'] or input_fingerprint(project)!=config.get('build_input_fingerprint'):
        failures.append('Render no longer matches source/output fingerprint')
    metadata=probe(output);video=next((s for s in metadata['streams'] if s['codec_type']=='video'),None);audio=next((s for s in metadata['streams'] if s['codec_type']=='audio'),None)
    if not video:failures.append('No video stream')
    else:
        canvas=config['canvas'];tolerance=max(.1,2/canvas['fps'])
        if (video['width'],video['height'])!=(canvas['width'],canvas['height']):failures.append('Wrong dimensions')
        if abs(fps_value(video['avg_frame_rate'])-canvas['fps'])>.01:failures.append('Wrong fps')
        if abs(float(video.get('duration',media_duration(metadata)))-config['duration'])>tolerance:failures.append('Wrong duration')
        if video.get('nb_frames') and abs(int(video['nb_frames'])-round(config['duration']*canvas['fps']))>2:failures.append('Wrong frame count')
        if audio and abs(float(audio.get('duration',media_duration(metadata)))-float(video.get('duration',media_duration(metadata))))>tolerance:failures.append('A/V duration mismatch')
    if config.get('expected_audio') and not audio:failures.append('Expected narration missing')
    try:run(['ffmpeg','-v','error','-xerror','-i',output,'-f','null','-'])
    except RuntimeError as error:failures.append(str(error))
    times={.0,max(.0,config['duration']-.15)}
    for event in read(project/'resolved-shotbook.json')['events']:
        times.update([event['start']+.15,(event['start']+event['end'])/2,max(event['start'],event['end']-.15)])
    samples=project/'review-frames';samples.mkdir(exist_ok=True);frame_paths=[]
    for i,time in enumerate(sorted(times)):
        if time>=config['duration']:continue
        target=samples/f'{i:02}-{time:.3f}s.jpg';run(['ffmpeg','-v','error','-y','-ss',time,'-i',output,'-frames:v','1','-vf','scale=540:-2',target]);frame_paths.append(str(target))
    report={'fingerprint':fp,'output_sha256':digest(output),'mechanical_pass':not failures,'visual_pass':None,'failures':failures,'metadata':metadata,'samples':frame_paths}
    write(project/'mechanical-review.json',report);state(project,status='rendered_needs_visual_review' if not failures else 'checks_failed')
    print(json.dumps({'mechanical_pass':not failures,'failures':failures,'samples':len(frame_paths)},ensure_ascii=False))
    if failures:raise ValueError('Mechanical checks failed')


def accept(args):
    project=Path(args.project).expanduser().resolve();review=read(project/'mechanical-review.json');output=existing(project/'output.mp4')
    config=read(project/'project.json')
    if not review['mechanical_pass'] or review['fingerprint']!=fingerprint(project) or review['output_sha256']!=digest(output) or input_fingerprint(project)!=config.get('build_input_fingerprint'):
        raise ValueError('Run passing checks for the current export before accepting')
    if not args.note.strip():raise ValueError('Record actual observed review evidence')
    review['visual_pass']=True;review['review_note']=args.note;write(project/'accepted-review.json',review);state(project,status='accepted')
    print(output)


def parser():
    p=argparse.ArgumentParser(description=__doc__);subs=p.add_subparsers(dest='command',required=True)
    d=subs.add_parser('doctor');d.set_defaults(func=doctor)
    i=subs.add_parser('init');i.add_argument('project');i.add_argument('--video');i.add_argument('--audio');i.add_argument('--duration',type=float)
    i.add_argument('--width',type=int,default=1080);i.add_argument('--height',type=int,default=1920);i.add_argument('--fps',type=float);i.set_defaults(func=initialize)
    a=subs.add_parser('analyze');a.add_argument('video');a.add_argument('--out',required=True);a.add_argument('--every',type=float,default=.5);a.add_argument('--start',type=float,default=0);a.add_argument('--end',type=float);a.set_defaults(func=analyze)
    t=subs.add_parser('transcribe');t.add_argument('project');t.add_argument('--model',default='small');t.add_argument('--language',default='zh');t.add_argument('--prompt-file');t.add_argument('--expected-script');t.set_defaults(func=transcribe)
    for name,func in [('build',build),('render',render),('check',check),('accept',accept)]:
        q=subs.add_parser(name);q.add_argument('project');q.set_defaults(func=func)
        if name=='render':q.add_argument('--force',action='store_true')
        if name=='accept':q.add_argument('--note',required=True)
    return p


if __name__=='__main__':
    try:
        arguments=parser().parse_args();arguments.func(arguments)
    except (ValueError,RuntimeError,FileNotFoundError) as error:
        print(f'ERROR: {error}',file=sys.stderr);sys.exit(1)
