#!/usr/bin/env python3
"""Make clearly labelled, non-personal Chinese development narration on macOS."""
import argparse
import json
import subprocess
from pathlib import Path
from motion import media_duration, probe, write

p=argparse.ArgumentParser(description=__doc__);p.add_argument('out');p.add_argument('--rate',type=int,default=180);a=p.parse_args()
out=Path(a.out).expanduser().resolve();out.mkdir(parents=True,exist_ok=True)
lines=['做口播，最费时间的，往往不是说话，而是剪辑。',
       '先拆参考视频，找出重点文字、画面变化和转场规律。',
       '再把动效做成组件，跟着新口播的关键词出现。',
       '最后检查字幕、声音和画面，在本地导出完整视频。']
cues=[];position=0
for i,line in enumerate(lines):
    raw=out/f'{i}.aiff';wav=out/f'{i}.wav'
    subprocess.run(['say','-v','Tingting','-r',str(a.rate),'-o',str(raw),line],check=True)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-ar','48000','-ac','1',str(wav)],check=True)
    duration=media_duration(probe(wav));cues.append({'text':line,'start':position,'end':position+duration});position+=duration
concat=out/'concat.txt';concat.write_text(''.join(f"file '{i}.wav'\n" for i in range(len(lines))))
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(concat),str(out/'narration.wav')],check=True)
write(out/'cues.json',cues);(out/'script.txt').write_text('\n'.join(lines))
write(out/'provenance.json',{'mode':'development example','voice':'macOS Tingting','rate':a.rate,'identity':'not the user','caption_timing':'exact generated sentence file boundaries; not word alignment'})
print(json.dumps({'audio':str(out/'narration.wav'),'duration':position},ensure_ascii=False))
