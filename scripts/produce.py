#!/usr/bin/env python3
"""Resume a reviewed editorial plan through local B-roll, MP4 and QA."""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from motion import SKILL, digest, existing, fingerprint, read, renderer_signature, state, write
from render_huashu import resolve_spec_assets


def call(project, stage, arguments, record):
    record['stage']=stage;record['status']='running';write(project/'production-run.json',record)
    log=project/'logs'/f'{stage}.log';log.parent.mkdir(exist_ok=True)
    with log.open('w') as f:
        result=subprocess.run([str(x) for x in arguments],stdout=f,stderr=subprocess.STDOUT)
    record['steps'].append({'stage':stage,'exit_code':result.returncode,'log':str(log)})
    write(project/'production-run.json',record)
    if result.returncode:raise RuntimeError(f'{stage} failed; inspect {log}\n{log.read_text()[-1200:]}')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project');parser.add_argument('--model',default='small')
    parser.add_argument('--expected-script');parser.add_argument('--prompt-file')
    args=parser.parse_args();project=Path(args.project).expanduser().resolve()
    config=read(project/'project.json');record={'started_at':datetime.now(timezone.utc).isoformat(),'steps':[]}
    helper=SKILL/'scripts/motion.py'
    try:
        if not read(project/'shotbook.json').get('events'):
            raise ValueError('Author a semantic shotbook before producing; an empty plan is not a complete film')
        source=config['source'].get('video') or config['source'].get('audio')
        if source and not (project/'words.json').exists() and not (project/'caption-cues.json').exists():
            command=[sys.executable,helper,'transcribe',project,'--model',args.model]
            if args.expected_script:command+=['--expected-script',existing(args.expected_script,project)]
            if args.prompt_file:command+=['--prompt-file',existing(args.prompt_file,project)]
            call(project,'transcribe',command,record)
        elif source and (project/'analysis/transcription.json').exists():
            transcript=read(project/'analysis/transcription.json')
            if transcript.get('source_sha256')!=digest(existing(source,project)):
                raise ValueError('Narration changed: regenerate and review final timestamps before producing')
        jobs=read(project/'broll-jobs.json') if (project/'broll-jobs.json').exists() else []
        if not isinstance(jobs,list):raise ValueError('broll-jobs.json must be an array')
        cache=read(project/'broll-cache.json') if (project/'broll-cache.json').exists() else {}
        seen=set()
        for i,job in enumerate(jobs):
            spec=existing(job['spec'],project);out=Path(job['out']).expanduser()
            if not out.is_absolute():out=project/out
            out=out.resolve()
            if out in seen:raise ValueError('B-roll jobs must have unique outputs')
            if out==spec or out==project/'output.mp4' or (source and out==existing(source,project)):
                raise ValueError('B-roll output would overwrite an input/master')
            seen.add(out);content=read(spec)
            renderer=job.get('renderer','huashu')
            if renderer not in ('huashu','social'):raise ValueError('Unknown B-roll renderer')
            if renderer=='social':
                paths=[content[k] for k in ('portrait','cutout','presenter_video') if content.get(k)]+content.get('images',[])
                asset_hashes=[digest(existing(value,spec.parent)) for value in paths]
                engine_files=[SKILL/'assets/social-grammars/social.js',SKILL/'assets/social-grammars/index.html',SKILL/'scripts/social_grammar.py']+[SKILL/'assets/huashu-engine/lib/fonts'/f for f in ('NotoSansSC-800.woff','NotoSerifSC-sub.woff')]
                signature=digest(spec)+''.join(digest(p) for p in engine_files)+json.dumps(asset_hashes,sort_keys=True)
            else:
                _,asset_hashes=resolve_spec_assets(content,spec.parent)
                signature=digest(spec)+digest(SKILL/'assets/huashu-engine/upstream.json')+digest(SKILL/'scripts/render_huashu.py')+json.dumps(asset_hashes,sort_keys=True)
            if any('anchor' in c for c in content.get('cues',[])):signature+=digest(existing(project/'words.json'))
            signature=hashlib.sha256(signature.encode()).hexdigest();old=cache.get(str(out),{})
            if old.get('signature')!=signature or not out.exists() or old.get('output_sha256')!=digest(out):
                command=([sys.executable,SKILL/'scripts/social_grammar.py','--spec',spec,'--output',out,'--overwrite'] if renderer=='social' else [sys.executable,SKILL/'scripts/render_huashu.py',project,'--spec',spec,'--out',out])
                call(project,f'broll-{i+1}',command,record)
                cache[str(out)]={'signature':signature,'output_sha256':digest(out)};write(project/'broll-cache.json',cache)
            else:record['steps'].append({'stage':f'broll-{i+1}','reused':str(out)})
        call(project,'build',[sys.executable,helper,'build',project],record)
        fp=fingerprint(project);history=read(project/'render-history.json') if (project/'render-history.json').exists() else []
        existing_render=read(project/'render.json') if (project/'render.json').exists() else {}
        if existing_render.get('fingerprint') and not history:
            history.append({'fingerprint':existing_render['fingerprint'],'imported_existing_render':True})
        unchanged=existing_render.get('fingerprint')==fp and existing_render.get('renderer_signature')==renderer_signature() and (project/'output.mp4').exists() and existing_render.get('output_sha256')==digest(project/'output.mp4')
        if not unchanged:
            if len(history)>=int(config.get('review_limit',3)):
                raise ValueError('Review limit reached. Preserve the last preview and report unresolved issues; increase the project limit only for a justified new scope')
            history.append({'fingerprint':fp,'started_at':datetime.now(timezone.utc).isoformat(),'status':'attempted'})
            write(project/'render-history.json',history)
        call(project,'render',[sys.executable,helper,'render',project],record)
        if not unchanged:
            history[-1]['status']='rendered';history[-1]['output_sha256']=digest(project/'output.mp4');write(project/'render-history.json',history)
        call(project,'check',[sys.executable,helper,'check',project],record)
        record.update(status='needs_editorial_review',output=str(project/'output.mp4'),fingerprint=fp,
                      review_route='current-codex',
                      note='Mechanical checks passed. The current Codex agent should continue reviewing actual encoded frames, transcript, native audio measurements, face crop, evidence and style; report unverified listening/lip-sync limits. Gemini is optional and requires a user request.')
        write(project/'production-run.json',record)
        print(json.dumps(record,ensure_ascii=False,indent=2))
    except (ValueError,RuntimeError,FileNotFoundError,KeyError) as error:
        record.update(status='failed',error=str(error));write(project/'production-run.json',record)
        state(project,status='production_failed');raise


if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,FileNotFoundError,KeyError) as e:print(f'ERROR: {e}',file=sys.stderr);sys.exit(1)
