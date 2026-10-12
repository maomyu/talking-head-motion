#!/usr/bin/env python3
"""Apply an authored keep EDL to original picture and voice, without overwriting sources."""
import argparse
import hashlib
import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path


def probe(p):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))


def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''): h.update(chunk)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('video',type=Path); ap.add_argument('--edl',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path); ap.add_argument('--fps',type=float)
    a=ap.parse_args(); src=a.video.resolve(); dst=a.out.resolve()
    report=dst.with_suffix('.edit.json')
    if not src.is_file(): ap.error('原片不存在')
    if dst==src or dst.exists() or report.exists(): ap.error('拒绝覆盖原片、成片或剪辑记录；请使用新输出路径')
    if dst.suffix.lower()!='.mp4': ap.error('输出须为 MP4')
    info=probe(src); videos=[s for s in info['streams'] if s['codec_type']=='video']; audios=[s for s in info['streams'] if s['codec_type']=='audio']
    if not videos or not audios: ap.error('原片须有画面与原生音轨；不能把无声片称为原声口播')
    v=videos[0]; duration=float(info['format']['duration'])
    fps=a.fps or float(Fraction(v.get('avg_frame_rate','0/1')))
    if not math.isfinite(fps) or not 1<=fps<=120: ap.error('帧率不可用；请显式 --fps')
    edl=json.loads(a.edl.read_text()); keep=edl.get('keep')
    if not isinstance(keep,list) or not keep: ap.error('keep 必须为非空区间数组')
    mapping=[]; filters=[]; prev=0; output_t=0
    for i,seg in enumerate(keep):
        start,end=float(seg['start']),float(seg['end'])
        if not all(math.isfinite(x) for x in (start,end)) or not 0<=start<end<=duration+1e-6 or start<prev: ap.error('区间须有限、递增、不重叠，且在原片内')
        # Apply the same frame boundaries to both picture and native sound.
        lo=round(start*fps)/fps; hi=min(math.floor(duration*fps)/fps,round(end*fps)/fps)
        if hi<=lo or (mapping and lo<mapping[-1]['source_end']): ap.error('量化后区间为空或重叠；调整句界')
        filters += [f'[0:v:0]trim=start={lo:.9f}:end={hi:.9f},setpts=PTS-STARTPTS,fps={fps:.9f},format=yuv420p[v{i}]',f'[0:a:0]atrim=start={lo:.9f}:end={hi:.9f},asetpts=PTS-STARTPTS[a{i}]']
        mapping.append({'source_start':lo,'source_end':hi,'output_start':output_t,'output_end':output_t+hi-lo,'requested_start':start,'requested_end':end,'reason':seg.get('reason','')})
        prev=end; output_t+=hi-lo
    filters.append(''.join(f'[v{i}][a{i}]' for i in range(len(keep)))+f'concat=n={len(keep)}:v=1:a=1[v][a]')
    dst.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['ffmpeg','-n','-v','error','-i',str(src),'-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-c:v','libx264','-crf','18','-preset','fast','-c:a','aac','-b:a','256k','-movflags','+faststart',str(dst)],check=True)
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(dst),'-f','null','-'],check=True)
    record={'source':str(src),'source_sha256':digest(src),'edl':str(a.edl.resolve()),'edl_sha256':digest(a.edl),'output':str(dst),'output_sha256':digest(dst),'fps':fps,'planned_duration':output_t,'mapping':mapping,'output_probe':probe(dst),'verification':{'full_decode':True,'semantic_edit':'requires actual sentence review','voice':'native source, no TTS or voice processing; AAC re-encoding'}}
    report.write_text(json.dumps(record,ensure_ascii=False,indent=2))
    print(json.dumps({'output':str(dst),'report':str(report),'duration':output_t,'kept_segments':len(keep)},ensure_ascii=False))


if __name__=='__main__': main()
