#!/usr/bin/env python3
"""Build the 35 full-film review page from hash-bound, mechanically verified local outputs."""
from pathlib import Path
import argparse,json,hashlib,csv,shutil
S=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--manifest',required=True);ap.add_argument('--storyboard',required=True);ap.add_argument('--captions',required=True);ap.add_argument('--presenter-note',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 records=json.loads(Path(a.manifest).read_text());story=json.loads(Path(a.storyboard).read_text());d=Path(a.out).resolve();d.mkdir(parents=True,exist_ok=True)
 assert len(records)==35 and len({x['id'] for x in records})==35,'Expected 35 distinct full films'
 films=[];media={}
 for i,x in enumerate(sorted(records,key=lambda x:x['id']),1):
  f=Path(x['path']);p=Path(x['poster']);assert f.is_file() and p.is_file(),'Missing media'
  assert sha(f)==x['video_sha256'] and x['full_av_decode'] and x['audio_packet_identical'],'Output verification missing/stale'
  assert x['gate']['gate_light']!='red' and abs(x['duration']-story['shots'][-1]['end'])<=1/x['fps'],'Incomplete/red film'
  films.append({'number':i,'id':x['id'],'name':x['name'],'metadata':x['metadata'],'ready':True,'duration':x['duration'],'frames':x['frames'],'width':x['width'],'height':x['height'],'fps':x['fps'],'review_status':'未审核','video':f"/media/{x['id']}.mp4",'poster':f"/media/{x['id']}.jpg",'video_sha256':x['video_sha256'],'file':str(f),'gate':x['gate']['gate_light']})
  media[x['id']+'.mp4']=str(f);media[x['id']+'.jpg']=str(p)
 assert len({x['accepted_aac_packet_sha256'] for x in records})==1,'Different narration masters'
 media['captions.srt']=str(Path(a.captions).resolve());assert Path(media['captions.srt']).is_file()
 (d/'data.json').write_text(json.dumps({'films':films,'shots':story['shots'],'presenter_note':a.presenter_note,'comparison_note':'35条分别为完整口播；同一文案、声音、语义镜头与人物回归点，比较材料、造型、光影与母题动作。'},ensure_ascii=False,indent=2))
 (d/'media-map.json').write_text(json.dumps(media,ensure_ascii=False,indent=2));shutil.copy2(S/'assets/style-batch/review.html',d/'index.html')
 with (d/'35画风审核清单.csv').open('w',encoding='utf-8-sig',newline='') as out:
  w=csv.writer(out);w.writerow(['序号','画风','时长秒','实际动画机制','道具迁移','母题动作','制作限制','完整MP4','SHA256','审核'])
  for x in films:w.writerow([x['number'],x['name'],x['duration'],x['metadata']['mechanism'],x['metadata']['topic_adaptation'],x['metadata']['motifs'],x['metadata']['limitations'],x['file'],x['video_sha256'],'待用户审核'])
 print(d)
if __name__=='__main__':main()
