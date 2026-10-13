#!/usr/bin/env python3
"""Build a read-only fixed-style catalogue backed by verified local MP4s.

All choices and review notes belong in the conversation. No forms, ratings,
recording, localStorage or upload endpoints are created.
"""
import argparse,html,json
from pathlib import Path
from fixed_styles import CATALOG,library
from reference_render import sha
from precision_gallery import frozen_preview

def colours(value,label=''):
    if isinstance(value,dict):
        return [p for k,v in value.items() for p in colours(v,str(k))]
    if isinstance(value,list) and len(value)==3 and all(isinstance(v,(int,float)) and 0<=v<=255 for v in value):
        return [(label,'#'+''.join(f'{round(v):02x}' for v in value))]
    if isinstance(value,str) and value.startswith('#') and len(value) in (4,7):return [(label,value)]
    return []

def make(cases_path,out,catalog=CATALOG):
    cases=json.loads(Path(cases_path).read_text());data=library(catalog);out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    media_path=out/'media-map.json';media=json.loads(media_path.read_text()) if media_path.exists() else {};group={};payload={};sections=[];nav=[];e=html.escape
    for c in cases:
        path=Path(c['replica']).resolve();proof=json.loads(path.with_suffix('.manifest.json').read_text())
        if proof.get('output_sha256')!=sha(path):raise ValueError('Style preview file changed: '+c['id'])
        if proof['frames']!=c['frames'] or proof['reference']['first_frame']!=c['first_frame']:raise ValueError('Style preview native window changed')
        if c.get('bindings',{}).get('output_sha256',proof['output_sha256'])!=proof['output_sha256']:raise ValueError('Style preview and visual review disagree')
        sid=c.get('style_id') or 'TH-DY-'+c['id'].split('-')[1];key=c['id']+'-replica.mp4';media[key]=str(frozen_preview(path,out,proof['output_sha256']))
        group.setdefault(sid,[]).append(c)
        roi=c.get('replica_crop_xywh')
        payload[c['id']]={'src':'media/'+key,'name':c['name'],'description':c['description'],'status':c['status'],'frames':c['frames'],'duration':proof['duration'],'width':proof['width'],'height':proof['height'],'roi':roi,'compare':'precision.html#'+c['id'],'sha':proof['output_sha256'],'unresolved':c.get('unresolved',[])}
    for row in data['styles']:
        sid=row['id'];rank=row['source_rank'];items=group.get(sid,[]);recipe=json.loads((Path(catalog).resolve().parent/row['recipe']).read_text()) if row.get('recipe') else {}
        swatches=''.join(f'<span class="swatch"><i style="background:{e(hex)}"></i>{hex}</span>' for label,hex in colours(recipe.get('palette',{}))[:6])
        variants=''.join(f'<button data-variant="{e(c["id"])}">{e(c.get("variant",c["name"]))}</button>' for c in items)
        notes=''.join(f'<li>{e(str(v))}</li>' for v in recipe.get('uses',[])[:4] if any('\u4e00'<=x<='\u9fff' for x in str(v)))
        state=row['readiness']['scope'];first=items[0]['id'] if items else None
        video=f'<div class="empty">本款的精细动画正在重建；完成编码对照后展示实际视频。<p><a href="mechanisms-legacy.html#case-{rank:02d}">观看已有机制演示</a>（动作有简化，不作为精细复刻验收）</p></div>' if not first else f'<div class="stage"><video controls playsinline muted preload="none" data-first="{e(first)}"></video></div><p class="window"></p><p class="description"></p><p class="status"></p><div class="actions"><a class="compare" href="precision.html#{e(first)}">原片与重建逐帧对照</a><a class="download" download>下载本动画 MP4</a></div><details><summary>本视频的具体差异</summary><ul class="differences"></ul></details>'
        sections.append(f'<section class="style" id="case-{rank:02d}"><div class="title"><span>{e(sid)} · v{e(row["version"])}</span><h2>{e(row["name"])}</h2></div><div class="body"><div class="preview">{video}</div><aside><p class="scope">{e(state)}</p><p class="instruction">今后在对话中说“用 {e(sid)}”或这个名称即可。子版本可按内容安排；指定某个子版本时直接沿用。</p><div class="variants">{variants}</div><div class="palette">{swatches}</div><ul>{notes}</ul></aside></div></section>')
        nav.append(f'<a href="#case-{rank:02d}">{rank:02d} {e(row["name"])}</a>')
    page=PAGE.replace('__COUNT__',str(len(cases))).replace('__NAV__',''.join(nav)).replace('__SECTIONS__',''.join(sections)).replace('__DATA__',json.dumps(payload,ensure_ascii=False).replace('<','\\u003c'))
    media_path.write_text(json.dumps(media,ensure_ascii=False,indent=2)+'\n');(out/'index.html').write_text(page);return out/'index.html'

PAGE='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>30款固定口播风格</title><style>
*{box-sizing:border-box}body{margin:0;background:#0e1219;color:#eef3fa;font:15px/1.65 system-ui,-apple-system,sans-serif}main{max-width:1180px;margin:auto;padding:40px 24px 80px}h1{font-size:36px;line-height:1.25}h2{font-size:25px;margin:4px 0 0}p{color:#b8c4d5}a{color:#8fceff}header{margin-bottom:28px}.badge,.title span{color:#f6cc83;font-size:13px;letter-spacing:.06em}nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:24px}nav a{padding:5px 10px;border:1px solid #334256;border-radius:7px;text-decoration:none;font-size:12px}.style{margin:32px 0;border:1px solid #334256;background:#161e2a;border-radius:16px;overflow:hidden;scroll-margin-top:18px}.title{padding:20px 26px;border-bottom:1px solid #334256}.body{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:28px;padding:24px}.stage{position:relative;width:100%;height:580px;background:#080b10;overflow:hidden;border-radius:12px}.stage video{width:100%;height:100%;object-fit:contain}.stage.crop{height:auto;aspect-ratio:var(--ratio);max-width:430px;margin:auto}.stage.crop video{position:absolute;width:var(--vw);height:var(--vh);left:var(--vx);top:var(--vy);object-fit:fill}.actions,.variants{display:flex;flex-wrap:wrap;gap:12px;margin:18px 0}.variants button{font:inherit;color:#fff;background:#293d55;border:1px solid #526a84;border-radius:7px;padding:7px 10px;cursor:pointer}.variants button.active{border-color:#e8be78;background:#5a472c}.window{font-variant-numeric:tabular-nums;font-size:13px;color:#89caff}.description{font-size:14px}.status{font-size:13px;color:#e1c291}.scope{padding:12px;border-left:3px solid #b79b65;background:#101721}.instruction{font-size:14px}.palette{margin:18px 0}.swatch{display:block;font-size:12px;color:#b9c6d8;margin:6px 0}.swatch i{display:inline-block;width:16px;height:16px;vertical-align:middle;border-radius:4px;margin-right:8px;border:1px solid #7b8696}details{margin:18px 0}summary{cursor:pointer;color:#8fceff}pre{white-space:pre-wrap;font-size:11px;max-height:380px;overflow:auto;color:#bdcadc}li{margin:8px 0;color:#b8c4d5;font-size:13px}.empty{padding:50px 30px;color:#bdcadc;background:#101721;border-radius:10px}@media(max-width:750px){main{padding:24px 12px}h1{font-size:27px}.body{grid-template-columns:1fr;padding:15px}.stage{height:520px}.title{padding:16px}h2{font-size:22px}}
</style><main><header><span class="badge">固定编号 · 对话指定 · 实际视频</span><h1>30款口播剪辑风格</h1><p>现有 __COUNT__ 个实际动画片段，可观看原片与重建的同步逐帧对照。编号与名称用于今后指定风格；同一风格的不同编排列为子版本，完成范围在各款注明。</p><p>喜欢哪款，直接在对话里告诉 Agent。人物为真实拍摄的演示素材，用于看动画效果，尚未做中文口型同步。</p><nav>__NAV__</nav></header>__SECTIONS__</main><script>
const VARIANTS=__DATA__;
for(const card of document.querySelectorAll('.style')){const video=card.querySelector('video');if(!video)continue;let chosen=video.dataset.first;function show(id,load=true){const d=VARIANTS[id];chosen=id;video.pause();const stage=video.parentElement;stage.classList.toggle('crop',!!d.roi);if(d.roi){const [x,y,w,h]=d.roi;stage.style.cssText=`--ratio:${w/h};--vw:${100*d.width/w}%;--vh:${100*d.height/h}%;--vx:${-100*x/w}%;--vy:${-100*y/h}%`}else stage.style.cssText='';if(load){video.src=d.src;video.load()}card.querySelector('.window').textContent=`${d.frames} 原生帧 · ${d.duration.toFixed(3)} 秒 · ${d.width}×${d.height}`;card.querySelector('.description').textContent=d.description;card.querySelector('.status').textContent=d.status;card.querySelector('.compare').href=d.compare;card.querySelector('.download').href=d.src;const list=card.querySelector('.differences');list.replaceChildren(...d.unresolved.map(x=>{const li=document.createElement('li');li.textContent=x;return li}));card.querySelectorAll('[data-variant]').forEach(b=>b.classList.toggle('active',b.dataset.variant===id))}show(chosen,false);card.querySelectorAll('[data-variant]').forEach(b=>b.onclick=()=>show(b.dataset.variant));const observer=new IntersectionObserver(es=>{for(const e of es){if(e.isIntersecting&&!video.getAttribute('src'))show(chosen);if(!e.isIntersecting)video.pause()}},{rootMargin:'120px'});observer.observe(card)}
</script></html>'''
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cases',type=Path,required=True);p.add_argument('--dir',type=Path,required=True);p.add_argument('--catalog',type=Path,default=CATALOG);a=p.parse_args();print(make(a.cases,a.dir,a.catalog))
