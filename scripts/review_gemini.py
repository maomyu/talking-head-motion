#!/usr/bin/env python3
"""Optional, explicit remote review of the actual local export."""
import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from motion import digest, existing, fingerprint, read, run, write


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('project');parser.add_argument('--model',required=True)
    parser.add_argument('--allow-remote',action='store_true');args=parser.parse_args()
    if not args.allow_remote:raise ValueError('This command uploads video; use --allow-remote within authorized work')
    key=os.environ.get('GEMINI_API_KEY')
    if not key:raise ValueError('Set GEMINI_API_KEY; no request was sent')
    if not re.fullmatch(r'[A-Za-z0-9._-]+',args.model):raise ValueError('Invalid model name')
    project=Path(args.project).expanduser().resolve();output=existing(project/'output.mp4');config=read(project/'project.json')
    current=fingerprint(project);review=read(project/'mechanical-review.json');sha=digest(output)
    if not review['mechanical_pass'] or review['fingerprint']!=current or review['output_sha256']!=sha:raise ValueError('Run current mechanical checks first')
    folder=project/'model-review';folder.mkdir(exist_ok=True);ledger_file=folder/'ledger.json'
    ledger=read(ledger_file) if ledger_file.exists() else []
    cache=folder/f'{sha[:16]}-{args.model}.json'
    if cache.exists():print(cache);return
    if len(ledger)>=int(config.get('review_limit',3)):raise ValueError('Review limit reached; inspect unresolved issues before another request')
    proxy=folder/'review-proxy.mp4'
    run(['ffmpeg','-v','error','-y','-i',output,'-vf','scale=512:-2,fps=12','-c:v','libx264','-crf','29','-c:a','aac','-b:a','64k','-movflags','+faststart',proxy])
    if proxy.stat().st_size>12_000_000:raise ValueError('Review proxy exceeds safe inline size; use targeted windows or implement Files API')
    prompt=('Review the actual attached talking-head/motion video. Return JSON with pass (boolean), '
            'issues (array of objects: start_seconds, end_seconds, severity, problem, suggested_fix), '
            'and limitations (array of strings). Check text readability, timing against speech, '
            'unintended black/frozen frames, overlay overlap and evidence consistency. Do not pretend '
            'to have verified every native frame or exact lip sync. Plan: '+json.dumps(read(project/'resolved-shotbook.json'),ensure_ascii=False))
    payload={'contents':[{'parts':[{'text':prompt},{'inlineData':{'mimeType':'video/mp4','data':base64.b64encode(proxy.read_bytes()).decode()}}]}],
             'generationConfig':{'responseMimeType':'application/json'}}
    request=urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{args.model}:generateContent',
             data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','x-goog-api-key':key},method='POST')
    entry={'output_sha256':sha,'fingerprint':current,'model':args.model,'status':'request_started'};ledger.append(entry);write(ledger_file,ledger)
    try:
        with urllib.request.urlopen(request,timeout=180) as response:raw=json.load(response)
        content=''.join(p.get('text','') for p in raw['candidates'][0]['content']['parts']);result=json.loads(content)
        if not isinstance(result.get('pass'),bool) or not isinstance(result.get('issues'),list):raise ValueError('Model returned an invalid review schema')
        write(cache,{'output_sha256':sha,'fingerprint':current,'model':args.model,'review':result,'usage':raw.get('usageMetadata'),
                     'sampling_limit':'Default static processing may miss fast effects; inspect encoded dense frames separately.'})
        entry['status']='received';write(ledger_file,ledger);print(cache)
    except Exception:
        entry['status']='failed_or_unknown';write(ledger_file,ledger)
        raise RuntimeError('Model review failed or has unknown outcome; inspect the ledger before retrying. No success was recorded.')


if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,FileNotFoundError) as e:print(f'ERROR: {e}',file=sys.stderr);sys.exit(1)
