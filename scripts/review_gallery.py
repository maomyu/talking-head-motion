#!/usr/bin/env python3
"""Export actual encoded shots and build a local video review gallery."""
import argparse, concurrent.futures, hashlib, json, subprocess
from pathlib import Path

ROOT=None
STYLE=None

def run(args): subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp(t):
    ms=round(t*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'

def main():
    global ROOT,STYLE
    ap=argparse.ArgumentParser();ap.add_argument('--film',required=True,type=Path);ap.add_argument('--project',required=True,type=Path);ap.add_argument('--styles',type=Path);ap.add_argument('--presenter-note',default='人物及声音沿用当前母片。素材身份、授权与同步情况见项目审片记录。');ap.add_argument('--reuse',action='store_true',help='Reuse only hash-verified clips of the identical film');a=ap.parse_args();ROOT=a.project.resolve();STYLE=a.styles
    film=a.film.resolve();f=json.loads((ROOT/'storyboard.json').read_text());fps=f['fps']
    out=ROOT/'审核页面';out.mkdir(exist_ok=True);clips=ROOT/'renders/clips';clips.mkdir(exist_ok=True)
    total=round(float(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=duration','-of','default=nw=1:nk=1',str(film)]))*fps)
    existing_path=ROOT/'renders/24分镜审核manifest.json'
    existing=json.loads(existing_path.read_text()) if a.reuse and existing_path.is_file() else {}
    reuse={s['key']:s for s in existing.get('shots',[])} if existing.get('source_sha256')==sha(film) else {}
    def export(pair):
        i,s=pair;lo=round(s['start']*fps);hi=round(s['end']*fps) if i<len(f['shots'])-1 else total
        vid=clips/f'{i+1:02d}_{s["id"]}.mp4';poster=clips/f'{i+1:02d}_{s["id"]}.jpg';t=lo/fps;d=(hi-lo)/fps
        prior=reuse.get(s['id']);expected=prior and prior.get('start')==t and prior.get('end')==t+d
        if expected and vid.is_file() and poster.is_file() and vid.with_suffix('.srt').is_file() and sha(vid)==prior.get('sha256'):
            return prior
        run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',str(film),'-t',str(d),'-map','0:v:0','-map','0:a:0','-c:v','libx264','-crf','18','-preset','fast','-c:a','aac','-b:a','192k','-movflags','+faststart',str(vid)])
        run(['ffmpeg','-v','error','-xerror','-i',str(vid),'-f','null','-'])
        run(['ffmpeg','-y','-v','error','-ss',str(min(.8,d/2)),'-i',str(vid),'-frames:v','1','-q:v','3',str(poster)])
        cues=[dict(c,text=c['text'],start=max(c['start']-t,0),end=min(c['end']-t,d)) for c in f['captions'] if c['end']>t and c['start']<t+d]
        vid.with_suffix('.srt').write_text('\n\n'.join(f'{j+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for j,c in enumerate(cues))+'\n')
        print(f'clip {i+1:02d}/{len(f["shots"])} {s["id"]}',flush=True)
        return {'key':s['id'],'index':i+1,'title':s['object'],'action':s['action'],'camera':s['camera'],'presenter':s['presenter'],'start':t,'end':t+d,'original_boundary':[s['start'],s['end']],'duration':d,'video':str(vid),'poster':str(poster),'sha256':sha(vid),'full_decode':True}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: shots=list(pool.map(export,enumerate(f['shots'])))
    styles=json.loads(STYLE.read_text())['previews'] if STYLE else []
    media={'film.mp4':str(film)}
    def register(items,kind):
        for s in items:
            key=s.get('key',s.get('id'));rev=s.get('sha256',s.get('video_sha256'))[:12];s['video_url']=f'/media/{kind}_{key}.mp4?v={rev}';s['poster_url']=f'/media/{kind}_{key}.jpg?v={rev}'
            media[f'{kind}_{key}.mp4']=s['video'];media[f'{kind}_{key}.jpg']=s['poster']
    register(shots,'shot');register(styles,'style')
    run(['ffmpeg','-y','-v','error','-ss','27','-i',str(film),'-frames:v','1','-q:v','3',str(out/'film.jpg')])
    data={'film':'/media/film.mp4?v='+sha(film)[:12],'film_sha256':sha(film),'duration':total/fps,'shots':shots,'styles':styles,'scope':f'{len(shots)} 段实际分镜；{len(styles)} 条原库画风预览；'+a.presenter_note}
    (out/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));(out/'media-map.json').write_text(json.dumps(media,ensure_ascii=False,indent=2))
    (ROOT/'renders/24分镜审核manifest.json').write_text(json.dumps({'source_film':str(film),'source_sha256':sha(film),'fps':fps,'shots':shots,'boundary_policy':'nearest frame, contiguous; final shot includes the final encoded frame','audio':'对应母片原音；碎片可能从句中进入，结合完整稿审核'},ensure_ascii=False,indent=2))
    page=HTML.replace('24 段',str(len(shots))+' 段').replace('35 种',str(len(styles))+' 种').replace('本题24镜','本题'+str(len(shots))+'镜')
    page=page.replace('75 秒，1080×1920，24fps。沿用已生成的完整 Fish 配音。',f'{total/fps:.2f} 秒，{f.get("width",1080)}×{f.get("height",1920)}，{fps}fps。声音采用当前定稿母片。')
    page=page.replace('同一素材贯穿手机、剪辑时间轴、冲印照片、磁带、累计白板和合卷收尾。人物在开场、目标、关键结论与提问中反复出现。','人物与内容相关的动效按镜头表展开。逐镜动作、相机与全片时间码见分镜页。')
    page=page.replace('当前人物是获准使用的图库实拍示意，未对口型。正式剪你的自拍视频时，采用你的原画面和原声。',a.presenter_note.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'))
    page=page.replace('纸本讲解口播 · 完整稿','完整口播稿')
    (out/'index.html').write_text(page)
    print('gallery ->',out,flush=True)

HTML='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>花叔风格 · 口播与逐镜审核</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f4efe4;color:#282722;font:16px/1.6 system-ui,-apple-system,sans-serif}header,main{max-width:1400px;margin:auto;padding:28px}header{border-bottom:1px solid #c9bfaa}h1{font-size:30px;margin:0 0 10px}h2{font-size:21px;margin:10px 0}p{margin:8px 0;color:#5e584b}.pill{background:#e8ddc7;padding:4px 9px;border-radius:3px;font-size:13px}nav{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}button,select{border:1px solid #bcb19b;background:#fbf7eb;color:#282722;border-radius:6px;padding:10px 16px;cursor:pointer;font:inherit}button.active{background:#282722;color:#fbf7eb}a{color:#97433c}section[hidden]{display:none}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:20px}.card{border:1px solid #c9bfaa;background:#fbf7eb;border-radius:10px;padding:16px;overflow:hidden}.card h2{font-size:18px}video{display:block;width:100%;background:#ded5c5;border-radius:5px}.shot video{height:390px;object-fit:contain}.art video{aspect-ratio:16/9}.film{display:grid;grid-template-columns:minmax(250px,470px) 1fr;gap:32px}.film video{max-height:76vh}.small{font-size:13px;color:#706754}.tools{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}.empty{padding:50px}.time{font-variant-numeric:tabular-nums}@media(max-width:700px){header,main{padding:18px}.film{display:block}.film video{max-height:65vh}.grid{grid-template-columns:1fr}.shot video{height:420px}}</style>
<header><span class="pill">本机视频审核 · 不自动发布</span><h1>花叔风格 · 口播与逐镜审核</h1><p>完整口播、24 段实际分镜、35 种原生画风，均可播放。这里用于播放和浏览；喜欢的画风、修改要求和确认，直接在对话里告诉我。</p><nav><button class="active" data-tab="film">完整稿</button><button data-tab="shots">24 段分镜</button><button data-tab="styles">35 种画风</button></nav></header>
<main><section id="film"><div class="film"><video id="full" controls playsinline preload="metadata" poster="film.jpg"></video><div><h2>纸本讲解口播 · 完整稿</h2><p>75 秒，1080×1920，24fps。沿用已生成的完整 Fish 配音。</p><p>同一素材贯穿手机、剪辑时间轴、冲印照片、磁带、累计白板和合卷收尾。人物在开场、目标、关键结论与提问中反复出现。</p><p>当前人物是获准使用的图库实拍示意，未对口型。正式剪你的自拍视频时，采用你的原画面和原声。</p><p><a id="downloadFilm" download="花叔纸本口播.mp4">下载完整 MP4</a> · <a href="data.json" download>分镜资料</a></p><p class="small">你可以在对话里逐条指出节奏、动作、字与人物位置的问题；技术检查不能替代你的风格判断。35 种画风的星级与短板来自原配方卡。</p></div></div></section>
<section id="shots" hidden><h2>24 段分镜 · 对应配音</h2><p>这些片段从同一完整稿按实际帧界导出，显示全片时间码。连续表达被拆开时，请结合完整稿判断句意与衔接。</p><div class="tools"><select id="shotFilter"><option value="all">全部分镜</option><option value="main">人物为主</option><option value="animation">动效为主</option></select><span id="shotCount"></span></div><div class="grid" id="shotGrid"></div></section>
<section id="styles" hidden><h2>35 种画风 · 原库能力预览</h2><p>每条都是 3 秒横屏动画，保留原场景的材料、笔触与动势。这里用于挑画风；选定后需按你的题材重写构图，不会把 35 种画风混到一条口播里。</p><div class="tools"><select id="artFilter"><option value="all">全部画风</option></select><span id="artCount"></span></div><div class="grid" id="artGrid"></div></section></main>
<script>
let data;
function el(tag,text,cls){const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n}
function time(t){return Math.floor(t/60)+':'+(t%60).toFixed(2).padStart(5,'0')}
function card(s,kind){const key=kind+'_'+(s.key||s.id),n=el('article',null,'card '+(kind==='shot'?'shot':'art'));n.dataset.group=kind==='shot'?(s.presenter==='main'||s.presenter==='large_print'?'main':'animation'):s.group;n.append(el('h2',kind==='shot'?String(s.index).padStart(2,'0')+' · '+s.title:s.name));const v=el('video');v.controls=true;v.playsInline=true;v.preload='none';v.src=s.video_url;v.poster=s.poster_url;v.setAttribute('aria-label',kind==='shot'?'分镜 '+s.index:s.name+'画风');n.append(v);if(kind==='shot'){n.append(el('p',time(s.start)+' — '+time(s.end)+' · '+s.duration.toFixed(2)+' 秒','small time'),el('p',s.action),el('p','镜头：'+s.camera,'small'))}else{n.append(el('p',s.quality+' · '+s.group,'small'),el('p',s.technique),el('p','动态：'+s.motion),el('p','原配方短板：'+s.weakness,'small'))}const a=el('a','下载视频');a.href=s.video_url;a.download=(s.key||s.id)+'.mp4';n.append(a);return n}
document.addEventListener('play',e=>{if(e.target.tagName==='VIDEO')document.querySelectorAll('video').forEach(v=>{if(v!==e.target)v.pause()})},true);
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{document.querySelectorAll('video').forEach(v=>v.pause());document.querySelectorAll('main>section').forEach(s=>s.hidden=s.id!==b.dataset.tab);document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x===b))});
function filter(grid,value){let count=0;grid.querySelectorAll('.card').forEach(c=>{c.hidden=value!=='all'&&c.dataset.group!==value;if(!c.hidden)count++});return count}
fetch('data.json').then(r=>r.json()).then(d=>{data=d;document.getElementById('full').src=d.film;document.getElementById('downloadFilm').href=d.film;d.shots.forEach(s=>shotGrid.append(card(s,'shot')));d.styles.forEach(s=>artGrid.append(card(s,'style')));for(const group of new Set(d.styles.map(s=>s.group))){const o=el('option',group);o.value=group;artFilter.append(o)}shotCount.textContent=d.shots.length+' 段';artCount.textContent=d.styles.length+' 条';shotFilter.onchange=()=>shotCount.textContent=filter(shotGrid,shotFilter.value)+' 段';artFilter.onchange=()=>artCount.textContent=filter(artGrid,artFilter.value)+' 条'}).catch(e=>document.body.append(el('p','资料加载失败：'+e)));
</script></html>'''
if __name__=='__main__':main()
