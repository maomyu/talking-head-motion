#!/usr/bin/env python3
"""Create a read-only, native-frame comparison page from local review cases.

Selection and feedback remain in the conversation. Sources and private artwork
are registered with the existing loopback review server's explicit allowlist.
"""
import argparse
import html
import json
from fractions import Fraction
from pathlib import Path
from reference_render import sha

PAGE=r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>真人逐帧动画对照</title><style>
*{box-sizing:border-box}body{margin:0;background:#0d1218;color:#edf2f8;font:15px/1.65 system-ui,-apple-system,sans-serif}main{max-width:1180px;margin:auto;padding:36px 24px 80px}h1{font-size:32px;margin:8px 0}h2{font-size:24px;margin:0}h3{font-size:16px}p{color:#b4c0cf;margin:10px 0}a{color:#80cfff}header,.case{margin-bottom:30px}.case{background:#161e28;border:1px solid #334154;border-radius:18px;padding:24px;scroll-margin-top:16px}.tag{display:inline-block;color:#ffd48b;background:#493820;padding:3px 10px;border-radius:8px;font-size:13px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:20px}.player{background:#080b0f;border-radius:12px;padding:12px;text-align:center}.player video{width:100%;height:min(62vh,670px);object-fit:contain;display:block}.label{margin-bottom:8px;color:#c9d4e1}.controls,.events{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}button{font:inherit;background:#283849;color:#fff;border:1px solid #465e76;border-radius:9px;padding:8px 14px;cursor:pointer}button:hover{background:#3b536b}.clock{font-variant-numeric:tabular-nums;color:#80cfff}.facts{display:grid;grid-template-columns:1fr 1fr;gap:16px}.facts div{background:#101821;padding:16px;border-radius:10px}.facts ul{padding-left:20px;margin:8px 0;color:#b4c0cf}details{margin:16px 0}summary{cursor:pointer;color:#80cfff}.full{width:100%;height:65vh;background:#000;margin-top:12px}table{border-collapse:collapse;width:100%;font-size:13px;margin:14px 0}td,th{text-align:left;padding:10px;border-bottom:1px solid #334154}.status{padding:12px 16px;background:#222e3c;border-radius:10px}nav a{display:inline-block;margin:10px 16px 0 0}.error{color:#ffb3a6}img{max-width:100%}@media(max-width:650px){main{padding:24px 12px}.case{padding:14px}.cols,.facts{gap:8px}.player{padding:5px}.player video{height:42vh}.label{font-size:12px}h1{font-size:25px}.facts{grid-template-columns:1fr}}
</style><main><header><span class="tag">实际拍摄 · 原生时间轴 · 对话审核</span><h1>真人逐帧动画对照</h1><p>左侧直接读取完整原片，右侧播放按图层重建的实际 MP4。人物来自移动实拍视频；这些片段用于核验动画，未进行口型同步。</p><p>逐帧处理、人工审片、精细重建分别记录。未通过逐项核验的片段不会标成“百分百复刻”。修改意见直接在对话中告诉 Agent。</p><nav>__NAV__<a href="index.html">查看此前30条机制样片</a><a href="#inventory">30条完整原片的处理记录</a></nav></header>__CASES__<section class="case" id="inventory"><h2>完整原片与逐帧记录</h2><p>下表由实际解码报告生成。机器遍历每个原生 RGB 帧和 PTS；这不等于 Agent 已逐帧理解所有动画，也不等于每条已精细复刻。</p><div id="inventory-state" class="status">正在读取处理记录…</div><div id="inventory-table"></div></section></main><script>
const CASES=__DATA__;
function loaded(v){return v.readyState?Promise.resolve():new Promise((r,j)=>{v.addEventListener('loadedmetadata',r,{once:true});v.addEventListener('error',j,{once:true})})}
async function seek(v,t){await loaded(v);if(Math.abs(v.currentTime-t)<.0005)return;await new Promise((r,j)=>{v.addEventListener('seeked',r,{once:true});v.addEventListener('error',j,{once:true});v.currentTime=t})}
for(const c of CASES){const root=document.getElementById(c.id),a=root.querySelector('.original'),b=root.querySelector('.replica'),clock=root.querySelector('.clock');let frame=0,playing=false,busy=false;
 const label=()=>{clock.textContent=`原片 F${c.first_frame+frame} · ${((c.first_frame+frame)/c.fps).toFixed(3)}s ｜ 重建 F${frame}/${c.frames-1} · ${(frame/c.fps).toFixed(3)}s ｜ ${c.fps} fps`};
 function pause(){playing=false;a.pause();b.pause();root.querySelector('[data-act="play"]').textContent='同步原速播放'}
 async function go(f){pause();frame=Math.max(0,Math.min(c.frames-1,f));await Promise.all([seek(a,(c.first_frame+frame+.15)/c.fps),seek(b,(frame+.15)/c.fps)]);label()}
 async function play(){if(playing){pause();return}if(frame>=c.frames-1)await go(0);await Promise.all([seek(a,(c.first_frame+frame+.15)/c.fps),seek(b,(frame+.15)/c.fps)]);playing=true;root.querySelector('[data-act="play"]').textContent='暂停对照';try{await Promise.all([a.play(),b.play()])}catch(e){pause();clock.textContent='播放失败，请点击重新播放：'+e.message}}
 root.querySelectorAll('[data-act]').forEach(btn=>btn.onclick=()=>{const action=btn.dataset.act;if(action==='play')play();else if(action==='prev')go(frame-1);else if(action==='next')go(frame+1);else go(0)});
 root.querySelectorAll('[data-frame]').forEach(btn=>btn.onclick=()=>go(Number(btn.dataset.frame)));
 function tick(_,meta){if(playing){frame=Math.max(0,Math.min(c.frames-1,Math.floor(meta.mediaTime*c.fps+.01)));label();const af=Math.floor(a.currentTime*c.fps+.01)-c.first_frame;if(frame===c.frames-1){go(c.frames-1)}else if(Math.abs(af-frame)>1&&!busy){busy=true;seek(a,(c.first_frame+frame+.15)/c.fps).finally(()=>busy=false)}}b.requestVideoFrameCallback(tick)}
 if(b.requestVideoFrameCallback)b.requestVideoFrameCallback(tick);else b.addEventListener('timeupdate',()=>{if(playing){frame=Math.min(c.frames-1,Math.floor(b.currentTime*c.fps));label();if(frame===c.frames-1)go(c.frames-1)}});
 b.addEventListener('ended',()=>go(c.frames-1));Promise.all([loaded(a),loaded(b)]).then(()=>go(0)).catch(()=>clock.textContent='视频读取失败');label();
}
function esc(v){const d=document.createElement('span');d.textContent=String(v);return d.innerHTML}
async function inventory(){try{const r=await fetch('precision-inventory.json',{cache:'no-store'});if(!r.ok)throw Error(r.status);const d=await r.json();document.getElementById('inventory-state').textContent=d.summary;document.getElementById('inventory-table').innerHTML='<table><thead><tr><th>来源</th><th>完整下载</th><th>原生帧／处理帧</th><th>人工审片范围</th><th>精细重建</th></tr></thead><tbody>'+d.rows.map(x=>'<tr>'+[x.rank,x.download,x.frames,x.visual_scope,x.reconstruction].map(v=>'<td>'+esc(v)+'</td>').join('')+'</tr>').join('')+'</tbody></table>'}catch(e){document.getElementById('inventory-state').textContent='暂未读取到完整解码记录；不据此声明处理完成。'}}inventory();
</script></html>'''

def make(cases_path,out):
    data=json.loads(Path(cases_path).read_text());out=Path(out);out.mkdir(parents=True,exist_ok=True)
    media_path=out/'media-map.json';media=json.loads(media_path.read_text()) if media_path.exists() else {}
    sections=[];nav=[];clients=[]
    for case in data:
        c=dict(case);cid=c['id'];source=Path(c['source']).resolve();replica=Path(c['replica']).resolve()
        if not source.is_file() or not replica.is_file():raise ValueError('Source or encoded reconstruction missing: '+cid)
        if source==replica:raise ValueError('Reference replay is not a reconstruction')
        manifest=replica.with_suffix('.manifest.json')
        if not manifest.is_file():raise ValueError('Encoded reconstruction manifest missing: '+cid)
        proof=json.loads(manifest.read_text())
        if proof.get('output_sha256')!=sha(replica) or proof.get('reference',{}).get('sha256')!=sha(source):raise ValueError('Displayed media identity failed: '+cid)
        if proof.get('frames')!=c['frames'] or Fraction(proof.get('fps','0'))!=Fraction(str(c['fps'])) or proof['reference'].get('first_frame')!=c['first_frame']:raise ValueError('Displayed native window differs from the actual render: '+cid)
        for key,file in [('source',source),('replica',replica)]:media[f'{cid}-{key}.mp4']=str(file)
        e=html.escape;li=lambda values:''.join('<li>'+e(str(v))+'</li>' for v in values)
        events=''.join(f'<button data-frame="{int(v["frame"])}">{e(v["name"])} · F{c["first_frame"]+int(v["frame"])}</button>' for v in c.get('events',[]))
        links=''
        for i,item in enumerate(c.get('evidence',[])):
            p=Path(item['path']).resolve()
            if not p.is_file():raise ValueError('Evidence missing: '+str(p))
            name=f'{cid}-evidence-{i}{p.suffix}';media[name]=str(p);links+=f'<a href="media/{name}" target="_blank">{e(item["name"])}</a>　'
        sections.append(f'''<section class="case" id="{e(cid)}"><span class="tag">{e(c['status'])}</span><h2>{e(c['name'])}</h2><p>{e(c['description'])}</p><div class="cols"><div class="player"><div class="label">完整原片 · 对齐选定窗口</div><video class="original" muted playsinline preload="metadata" src="media/{cid}-source.mp4"></video></div><div class="player"><div class="label">移动实拍 · 图层重建</div><video class="replica" muted playsinline preload="metadata" src="media/{cid}-replica.mp4"></video></div></div><div class="controls"><button data-act="play">同步原速播放</button><button data-act="prev">前一帧</button><button data-act="next">后一帧</button><button data-act="start">回到窗口开头</button><a href="media/{cid}-replica.mp4" download>下载实际 MP4</a></div><div class="clock"></div><div class="events">{events}</div><div class="facts"><div><strong>已测量／实际验证</strong><ul>{li(c.get('verified',[]))}</ul></div><div><strong>还存在的差异</strong><ul>{li(c.get('unresolved',[]))}</ul></div></div><p>{links}</p><details><summary>播放完整原片（含原声）</summary><video class="full" controls preload="none" src="media/{cid}-source.mp4"></video></details></section>''')
        nav.append(f'<a href="#{e(cid)}">{e(c["name"])}</a>');clients.append({**{k:c[k] for k in ('id','first_frame','frames')},'fps':float(Fraction(str(c['fps'])))})
    page=PAGE.replace('__NAV__',''.join(nav)).replace('__CASES__',''.join(sections)).replace('__DATA__',json.dumps(clients,ensure_ascii=False).replace('<','\\u003c'))
    media_path.write_text(json.dumps(media,ensure_ascii=False,indent=2)+'\n');(out/'precision.html').write_text(page)
    return out/'precision.html'

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cases',required=True,type=Path);p.add_argument('--dir',required=True,type=Path);a=p.parse_args();print(make(a.cases,a.dir))
