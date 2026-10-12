#!/usr/bin/env python3
"""Full Huashu scene workflow. No voice/provider calls; all rendering is local.

huashu_full.py catalog
huashu_full.py init PROJECT_ENGINE [--width 1920 --height 1080]
huashu_full.py render PROJECT_ENGINE --solo my_scene --from 0 --to 3 --fps 24 --no-counter --out shot.mp4
huashu_full.py render bundled --film gallery --solo 09_postimp --from 0 --to 3 --fps 24 --no-counter --out preview.mp4
huashu_full.py qa PROJECT_ENGINE --ids my_scene --out qa/
huashu_full.py lint storyboard.md --script narration.txt
huashu_full.py breakdown --video reference.mp4 --out analysis/
huashu_full.py deliver final.mp4 --root PROJECT --qa qa/ --out output/

The 35 bundled scenes are original horizontal capability examples. New films
must redesign scene objects/composition. y6 is a production method, not a spec.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path

SKILL=Path(__file__).resolve().parents[1]
FULL=SKILL/'assets/huashu-full'
ENGINE=FULL/'scripts/engine'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def selected(path):
 value=ENGINE if path=='bundled' else Path(path).expanduser().resolve()
 for name in ['index.html','engine.js','render.py','scenes/index.js']:
  if not (value/name).is_file():raise ValueError(f'Incomplete scene project: {value/name}')
 return value

def run(command,log):
 log=Path(log);log.parent.mkdir(parents=True,exist_ok=True)
 with log.open('w') as out:
  out.write(json.dumps(command,ensure_ascii=False)+'\n');out.flush()
  result=subprocess.run(command,stdout=out,stderr=subprocess.STDOUT)
 if result.returncode:
  print(log.read_text()[-6000:],file=sys.stderr)
  raise RuntimeError(f'Command exited {result.returncode}; log: {log}')
 print(f'log: {log}')
 return log

def argument(args,key,default=None):return args[args.index(key)+1] if key in args else default

def render(engine,args):
 if args[:1]==['--']:args=args[1:]
 output=argument(args,'--out')
 if output is None:raise ValueError('render requires --out')
 out=Path(output).expanduser().resolve()
 log=out.parent/(out.name+'.render.log')
 command=[sys.executable,str(engine/'render.py'),*args]
 run(command,log)
 manifest={'schema_version':1,'scope':'local scene render, not a complete new-topic film acceptance','engine':str(engine),
  'upstream_commit':json.loads((FULL/'upstream.json').read_text())['commit'],'command':command,'log':str(log),
  'engine_files':{str(p.relative_to(engine)):sha(p) for p in sorted(engine.rglob('*')) if p.is_file() and '__pycache__' not in str(p) and p.suffix in ['.js','.py','.html']},
  'render_input_files':{str(p.relative_to(engine)):sha(p) for p in sorted(engine.rglob('*')) if p.is_file() and '__pycache__' not in str(p) and p.suffix.lower() in ['.js','.py','.html','.json','.woff','.woff2','.ttf','.otf','.png','.jpg','.jpeg','.webp','.svg'] and p.name not in [out.name,out.with_suffix('.full-engine-manifest.json').name]},
  'visual_review':False,'independent_review':False,'audio_review':False}
 if '--stills' in args:
  manifest['stills']=[{'path':str(p),'sha256':sha(p)} for p in sorted(out.glob('*.png'))]
  if not manifest['stills']:raise RuntimeError('Renderer returned no stills')
  write(out/'render-manifest.json',manifest)
 else:
  if not out.is_file():raise RuntimeError('Renderer returned no media')
  probe=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out)],capture_output=True,text=True,check=True)
  metadata=json.loads(probe.stdout);v=next((x for x in metadata['streams'] if x['codec_type']=='video'),None)
  if not v or int(v.get('nb_frames',0))<1:raise RuntimeError('No usable video stream/frames')
  decode=subprocess.run(['ffmpeg','-v','error','-i',str(out),'-map','0:v:0','-f','null','-'],capture_output=True,text=True)
  if decode.returncode or decode.stderr.strip():raise RuntimeError(f'Full decode failed: {decode.stderr[-1500:]}')
  manifest.update({'output':str(out),'sha256':sha(out),'bytes':out.stat().st_size,'probe':metadata,'full_video_decode':True})
  write(out.with_suffix('.full-engine-manifest.json'),manifest)
 print(out)

def init_project(dest,width,height):
 dest=Path(dest).expanduser().resolve()
 if dest.exists():raise ValueError('Use a new project directory; init never overwrites existing work')
 if width<=0 or height<=0 or width%2 or height%2:raise ValueError('Use positive even output dimensions')
 shutil.copytree(ENGINE,dest,ignore=shutil.ignore_patterns('__pycache__','*.render.log'))
 shutil.copy2(FULL/'LICENSE',dest/'LICENSE')
 (dest/'eras.js').write_text(f'window.FILM_SIZE = [{width},{height}];\nwindow.ERAS = [{{id:"project_intro",dur:3}}];\n')
 # This concrete object/event is a working smoke-test, not an automatic finished film.
 (dest/'scenes/project_intro.js').write_text('''// Project-owned starter: three paper footage strips fall into a laptop timeline.
window.SCENES = window.SCENES || {};
SCENES.project_intro = {draw(c,lt){
 const {W,H}=window.STAGE,u=Math.min(W/1920,H/1080),cx=W*.5,cy=H*.54;
 c.fillStyle='#eee7d7';c.fillRect(0,0,W,H);c.save();c.translate(cx,cy);c.scale(u,u);
 c.fillStyle='#242424';c.beginPath();c.roundRect(-610,-300,1220,660,32);c.fill();
 c.fillStyle='#f7f0df';c.fillRect(-568,-258,1136,528);
 c.strokeStyle='#cfc4aa';c.lineWidth=3;for(let i=0;i<5;i++){c.beginPath();c.moveTo(-500,-160+i*90);c.lineTo(500,-160+i*90);c.stroke();}
 const cols=['#bd563c','#648571','#cc9c45'];
 for(let i=0;i<3;i++){const p=Math.max(0,Math.min(1,(lt-.3-i*.3)/.22)),dy=(1-p)*-480;
 c.save();c.translate(-460+i*230,-190+i*90+dy);c.fillStyle=cols[i];c.fillRect(0,0,320,64);
 c.fillStyle='#fff3d5';for(let j=0;j<6;j++){c.fillRect(12+j*47,12,38,40);}c.restore();}
 c.fillStyle='#bd563c';c.fillRect(-460+Math.max(0,lt-1.35)*160,-228,6,460);
 c.fillStyle='#242424';c.beginPath();c.moveTo(-700,364);c.lineTo(700,364);c.lineTo(780,405);c.lineTo(-780,405);c.closePath();c.fill();c.restore();
}};
''')
 write(dest/'project-provenance.json',{'source':'talking-head-motion/assets/huashu-full','upstream_commit':json.loads((FULL/'upstream.json').read_text())['commit'],
  'starter_scope':'working paper/laptop scene only; replace eras.js and create topic-specific scenes','width':width,'height':height,'accepted':False})
 print(dest)

def main():
 parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
 sub=parser.add_subparsers(dest='action',required=True)
 sub.add_parser('catalog')
 ip=sub.add_parser('init');ip.add_argument('engine');ip.add_argument('--width',type=int,default=1920);ip.add_argument('--height',type=int,default=1080)
 for name in ['render','qa']:
  sp=sub.add_parser(name,add_help=False);sp.add_argument('engine');sp.add_argument('args',nargs=argparse.REMAINDER)
 for name in ['lint','deliver']:
  sp=sub.add_parser(name,add_help=False);sp.add_argument('args',nargs=argparse.REMAINDER)
 bp=sub.add_parser('breakdown');bp.add_argument('--video',required=True);bp.add_argument('--out',required=True);bp.add_argument('--thresh',type=float,default=5);bp.add_argument('--debounce',type=int,default=12)
 a=parser.parse_args()
 if a.action=='catalog':
  data=json.loads((FULL/'upstream.json').read_text());print(json.dumps({'commit':data['commit'],'scenes':[p.stem for p in sorted((ENGINE/'scenes').glob('[0-9]*.js'))],
    'grammar_cards':[p.stem for p in sorted((FULL/'references/动画语法').glob('*.md'))],'parameterized_grammars':[p.stem for p in sorted((ENGINE/'clips').glob('*.js'))],
    'y6_presenter_explainer':'scene-production method; requires authorized project sprite frames, not a --spec renderer'},ensure_ascii=False,indent=2))
 elif a.action=='init':init_project(a.engine,a.width,a.height)
 elif a.action=='render':render(selected(a.engine),a.args)
 elif a.action=='breakdown':
  subprocess.run([sys.executable,str(FULL/'scripts/analyze/breakdown.py'),'--video',a.video,'--out',a.out,'--thresh',str(a.thresh),'--debounce',str(a.debounce)],check=True)
 else:
  args=a.args[1:] if a.args[:1]==['--'] else a.args
  source={'qa':'qa.py','lint':'storyboard_lint.py','deliver':'deliver.py','breakdown':'analyze/breakdown.py'}[a.action]
  if a.action=='qa':args=['--project',str(selected(a.engine)),*args]
  subprocess.run([sys.executable,str(FULL/'scripts'/source),*args],check=True)

if __name__=='__main__':
 try:main()
 except (ValueError,RuntimeError,FileNotFoundError,subprocess.CalledProcessError) as e:
  print(f'ERROR: {e}',file=sys.stderr);sys.exit(1)
