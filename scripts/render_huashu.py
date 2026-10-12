#!/usr/bin/env python3
"""Render a parameterized, word-anchored Huashu B-roll segment locally."""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote
from motion import SKILL, anchor_time, digest, existing, probe, read, write


def resolve_spec_assets(spec, base):
    """Keep asset paths valid if the resolved spec lives in a different folder."""
    media=[]
    for cue in spec.get('cues',[]):
        media.append(cue.get('image'));frames=cue.get('frames')
        media.extend(frames if isinstance(frames,list) else [frames])
    data=spec.get('data') or {};media.append(data.get('image'));character=data.get('character')
    if isinstance(character,str):media.append(character)
    elif isinstance(character,dict):
        frames=character.get('frames');media.extend(frames.values() if isinstance(frames,dict) else [frames])
    if any(isinstance(v,str) and v.startswith(('http://','https://')) for v in media):
        raise ValueError('Stage media locally with provenance before deterministic rendering')
    module_spec=importlib.util.spec_from_file_location('huashu_spec_assets',SKILL/'assets/huashu-engine/spec_assets.py')
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    allowed=set();module.localize(spec,base,allowed)
    def convert(value):
        if isinstance(value,dict):return {k:convert(v) for k,v in value.items()}
        if isinstance(value,list):return [convert(v) for v in value]
        if isinstance(value,str) and value.startswith('/__file__/'):return unquote(value[len('/__file__/'):])
        return value
    return convert(spec),{p:digest(p) for p in sorted(allowed)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('project');p.add_argument('--spec',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    project=Path(a.project).expanduser().resolve();source=existing(a.spec,project);spec=read(source);out=Path(a.out).expanduser()
    if not out.is_absolute():out=project/out
    out=out.resolve();out.parent.mkdir(parents=True,exist_ok=True)
    if not 0<float(spec['duration'])<=8:raise ValueError('Split this B-roll into segments of up to 8 seconds')
    grammars={'y1_kurzgesagt','y2_vox','y3_whiteboard','y4_storytime','y5_kinetic_type','t1_3b1b','t2_keynote_ui','t3_finance_chart'}
    if spec.get('grammar') not in grammars:raise ValueError('Use a bundled grammar')
    words=read(project/'words.json') if (project/'words.json').exists() else []
    offset=float(spec.pop('timeline_start',0));uses_anchors=False
    for cue in spec.get('cues',[]):
        if 'anchor' in cue:
            uses_anchors=True
            if not words:raise ValueError('Word cues require accepted final words.json')
            cue['at']=anchor_time(cue.pop('anchor'),words)-offset
        if not 0<=float(cue['at'])<float(spec['duration']):raise ValueError('Cue is outside its B-roll segment')
    if any(c['at']>n['at'] for c,n in zip(spec.get('cues',[]),spec.get('cues',[])[1:])):raise ValueError('Cues must be ordered')
    spec,asset_hashes=resolve_spec_assets(spec,source.parent)
    resolved=out.with_suffix('.spec.json');write(resolved,spec)
    engine=SKILL/'assets/huashu-engine';log=out.with_suffix('.render.log');command=[sys.executable,str(engine/'render.py'),'--spec',str(resolved),'--out',str(out)]
    with log.open('w') as f:
        f.write(json.dumps(command)+'\n');f.flush();r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError(log.read_text()[-2600:])
    metadata=probe(out);v=next(s for s in metadata['streams'] if s['codec_type']=='video')
    expected=round(float(spec['duration'])*int(spec.get('fps',30)))
    if int(v.get('nb_frames',0))!=expected:raise ValueError('Huashu B-roll frame count mismatch')
    write(out.with_suffix('.manifest.json'),{'engine':read(engine/'upstream.json'),'source_spec_sha256':digest(source),
          'resolved_spec_sha256':digest(resolved),'words_sha256':digest(project/'words.json') if uses_anchors else None,
          'asset_hashes':asset_hashes,'output_sha256':digest(out),'frames':expected,'width':v['width'],'height':v['height']})
    print(out)


if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,FileNotFoundError) as e:print(f'ERROR: {e}',file=sys.stderr);sys.exit(1)
