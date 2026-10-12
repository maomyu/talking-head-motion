/* Painterly topic adaptations of huashu-art-motion (MIT).
 * No author figures, demo frames, character photographs, or private services.
 * All stochastic marks are seeded and cached; live motion is local to props/light.
 */
(() => {
  'use strict';
  const F = window.KOUBO_STYLE_FACTORIES ||= {};
  const W = 1080, H = 1920, TAU = Math.PI * 2;
  const clamp = (v,a=0,b=1) => Math.max(a,Math.min(b,v));
  const age = (t,s) => Math.max(0,t-(s?.start||0));
  function rng(seed) { let n=seed>>>0; return () => {n=(Math.imul(n,1664525)+1013904223)>>>0; return n/4294967296;}; }
  function rgb(c) {
    if (c[0]==='#') {let h=c.slice(1); if(h.length===3)h=h.split('').map(x=>x+x).join(''); return [0,2,4].map(i=>parseInt(h.slice(i,i+2),16));}
    const a=c.match(/[\d.]+/g); return a ? a.slice(0,3).map(Number) : [128,128,128];
  }
  function shade(c,d) { return 'rgb('+rgb(c).map(x=>Math.round(clamp(x+d,0,255))).join(',')+')'; }
  function alpha(c,a) { return 'rgba('+rgb(c).join(',')+','+a+')'; }
  function mix(a,b,q) { const x=rgb(a),y=rgb(b);return 'rgb('+x.map((v,i)=>Math.round(v+(y[i]-v)*q)).join(',')+')'; }
  function polygon(g,p,col) {g.beginPath();p.forEach((q,i)=>i?g.lineTo(...q):g.moveTo(...q));g.closePath();if(col){g.fillStyle=col;g.fill();}}
  function stroke(g,p,col,w=2) {if(!p.length)return;g.beginPath();p.forEach((q,i)=>i?g.lineTo(...q):g.moveTo(...q));g.strokeStyle=col;g.lineWidth=w;g.lineJoin='round';g.lineCap='round';g.stroke();}
  function ellipse(g,x,y,rx,ry,col,rot=0) {g.beginPath();g.ellipse(x,y,Math.max(.1,rx),Math.max(.1,ry),rot,0,TAU);g.fillStyle=col;g.fill();}
  function rect(g,x,y,w,h,col) {g.fillStyle=col;g.fillRect(x,y,w,h);}
  function gradient(g,x0,y0,x1,y1,stops) {const q=g.createLinearGradient(x0,y0,x1,y1);stops.forEach(([p,c])=>q.addColorStop(p,c));return q;}
  function glow(g,x,y,r,col,a=.2) {const q=g.createRadialGradient(x,y,0,x,y,r);q.addColorStop(0,alpha(col,a));q.addColorStop(1,alpha(col,0));g.fillStyle=q;g.fillRect(x-r,y-r,r*2,r*2);}
  function cacheFactory(id) {
    const m=new Map();
    return (key,w,h,fn) => {
      const k=id+':'+key+':'+w+'x'+h;
      if(!m.has(k)) { const c=document.createElement('canvas');c.width=Math.max(1,Math.ceil(w));c.height=Math.max(1,Math.ceil(h));const q=c.getContext('2d');fn(q,c.width,c.height);m.set(k,c); }
      return m.get(k);
    };
  }
  function tilePattern(g,cache,key,col,paint) {return g.createPattern(cache(key+':'+col,256,256,(q)=>paint(q,256,256,col)),'repeat');}
  function paperFiber(g,w,h,seed=1,strength=.06) {
    const r=rng(seed);g.save();g.lineWidth=.7;
    for(let i=0;i<Math.ceil(w*h/220);i++) {const x=r()*w,y=r()*h;g.strokeStyle=i%3?alpha('#685843',strength):alpha('#ffffff',strength*2);g.beginPath();g.moveTo(x,y);g.lineTo(x+(r()-.5)*13,y+r()*3);g.stroke();} g.restore();
  }
  function shortDabs(g,w,h,pal,seed,cell=16,dir=0) {
    const r=rng(seed);g.save();g.lineCap='round';
    for(let y=-cell;y<h+cell;y+=cell) for(let x=-cell;x<w+cell;x+=cell) {
      const px=x+(r()-.5)*cell,py=y+(r()-.5)*cell,c=pal[Math.floor(r()*pal.length)],a=dir+(r()-.5)*.7,len=cell*(.6+r()*.95);
      g.strokeStyle=c;g.lineWidth=cell*(.26+r()*.25);g.beginPath();g.moveTo(px,py);g.quadraticCurveTo(px+Math.cos(a)*len*.45,py+Math.sin(a)*len*.45+1,px+Math.cos(a)*len,py+Math.sin(a)*len);g.stroke();
    }g.restore();
  }
  function flowing(g,w,h,pal,seed,cell=30,field=(x,y)=>0,len=90,lw=8,opacity=.65,bristle=false) {
    const r=rng(seed);g.save();g.globalAlpha=opacity;g.lineCap='round';
    for(let y=-len*.3;y<h+len*.3;y+=cell) for(let x=-len*.3;x<w+len*.3;x+=cell) {
      let px=x+(r()-.5)*cell,py=y+(r()-.5)*cell;const pts=[[px,py]],l=len*(.65+r()*.65),n=Math.max(5,Math.ceil(l/11));
      for(let j=0;j<n;j++){const a=field(px,py);px+=Math.cos(a)*l/n;py+=Math.sin(a)*l/n;pts.push([px,py]);}
      const col=pal[Math.floor(r()*pal.length)];stroke(g,pts,col,lw*(.55+r()*.7));
      if(bristle){stroke(g,pts.map(p=>[p[0]+1.4,p[1]-1.4]),shade(col,30),Math.max(1,lw*.18));}
    }g.restore();
  }
  function clipRect(g,w,h,fn){g.save();g.beginPath();g.rect(0,0,w,h);g.clip();fn();g.restore();}
  function tileFill(g,w,h,pat){g.fillStyle=pat;g.fillRect(0,0,w,h);}
  function dryEdge(g,w,h,col,seed=19,lw=2) {
    const r=rng(seed);for(let k=0;k<4;k++){const p=k===0?[[0,0],[w,0]]:k===1?[[w,0],[w,h]]:k===2?[[w,h],[0,h]]:[[0,h],[0,0]];
      const len=Math.hypot(p[1][0]-p[0][0],p[1][1]-p[0][1]),n=Math.max(2,Math.ceil(len/12)),pts=[];
      for(let j=0;j<=n;j++){const f=j/n;pts.push([p[0][0]+(p[1][0]-p[0][0])*f+(r()-.5)*lw,p[0][1]+(p[1][1]-p[0][1])*f+(r()-.5)*lw]);}stroke(g,pts,col,lw);
    }
  }
  function film(g,x,y,w,h,col,perforation,rot=0) {
    g.save();g.translate(x,y);g.rotate(rot);rect(g,0,0,w,h,col);
    const s=Math.max(8,Math.min(16,h*.18));for(let xx=7;xx<w-4;xx+=s*1.55){rect(g,xx,5,s*.7,s*.45,perforation);rect(g,xx,h-5-s*.45,s*.7,s*.45,perforation);}
    g.restore();
  }
  function reel(g,x,y,r,col,edge,t) {
    g.save();g.translate(x,y);g.rotate(t);ellipse(g,0,0,r,r,col);for(let k=0;k<5;k++){const a=k*TAU/5;ellipse(g,Math.cos(a)*r*.57,Math.sin(a)*r*.57,r*.19,r*.24,edge,a);}ellipse(g,0,0,r*.12,r*.12,edge);g.restore();
  }
  function breezeStrip(g,x,y,w,h,t,col,edge) {
    g.beginPath();g.moveTo(x,y);for(let i=0;i<=20;i++){const f=i/20;g.lineTo(x+w*f,y+Math.sin(f*TAU-t*1.8)*h*.21*f);}for(let i=20;i>=0;i--){const f=i/20;g.lineTo(x+w*f,y+h+Math.sin(f*TAU-t*1.8)*h*.21*f);}g.closePath();g.fillStyle=col;g.fill();g.strokeStyle=edge;g.lineWidth=1.5;g.stroke();
  }
  function simpleLine(g,pts,col,lw) {stroke(g,pts,col,lw);}
  function cornerLight(g,col,alphaMax=.1) {g.save();const gr=g.createLinearGradient(0,0,220,0);gr.addColorStop(0,alpha(col,alphaMax));gr.addColorStop(1,alpha(col,0));g.fillStyle=gr;g.fillRect(0,0,220,1520);g.restore();}

  F['08_impressionism']=() => {
    const id='08_impressionism',cache=cacheFactory(id),P={paper:'#f8efd7',ink:'#5e6174',red:'#cf7180',olive:'#83a795',gold:'#e5c47b',white:'#fffcf0'};
    const material=(q,w,h,c)=>{rect(q,0,0,w,h,c);shortDabs(q,w,h,[shade(c,-13),shade(c,13),mix(c,'#b9b5dc',.17),mix(c,'#e6c296',.2)],93,10,-.12);};
    const pat=(g,c)=>tilePattern(g,cache,'dabs',c,material);
    return {id,name:'印象派 · 光斑短笔触',palette:P,pattern:pat,
      background(g,t){g.drawImage(cache('desk',W,H,q=>{
        rect(q,0,0,W,H,P.paper);q.save();q.beginPath();q.rect(0,0,W,700);q.clip();shortDabs(q,W,700,['#d9dbec','#efdcdf','#c8d4df','#f5e8ce','#d6cfdb'],100,24,-.3);q.restore();
        polygon(q,[[0,610],[W,730],[W,H],[0,H]],'#d7aeb0');q.save();q.beginPath();q.rect(0,700,W,H-700);q.clip();shortDabs(q,W,H,['#dab9b1','#c6a5bb','#f0d5b8','#bfafb5','#d3b6c8'],103,28,.1);q.restore();
        for(let k=0;k<5;k++){const x=40+k*220;stroke(q,[[x,1560],[x+160,730]],'#bea6b7',3);}q.save();q.translate(50,760);q.rotate(-.18);material(q,125,220,'#f4e7d3');q.restore();
        film(q,795,525,205,78,'#938894','#e7d8ce',.12);reel(q,970,1360,86,'#a4aaa0','#cfd6b7',0);
        q.save();q.globalAlpha=.35;shortDabs(q,200,680,['#92ab8b','#a5bc94','#c7c69e'],111,22,-1.1);q.restore();
      }),0,0);
        g.save();g.globalCompositeOperation='screen';for(let i=0;i<15;i++){const x=80+(i*181)%950+Math.sin(t*.4+i)*20,y=170+(i*317)%1290;ellipse(g,x,y,23+Math.sin(t*.8+i)*7,10,'rgba(255,239,170,.2)',-.3);}g.restore();
      },
      plate(g,w,h,c,seed){tileFill(g,w,h,pat(g,c));dryEdge(g,w,h,shade(c,-20),seed,1.5);},
      line(g,pts,c,lw){stroke(g,pts,c,lw*.9);if(pts.length<30)stroke(g,pts.map(p=>[p[0]+1,p[1]-1]),shade(c,25),Math.max(1,lw*.25));},
      motifs(g,t,s){breezeStrip(g,825,1180,180,40,t,P.paper,alpha(P.ink,.25));for(let k=0;k<4;k++)ellipse(g,30+k*20,950+Math.sin(t*.9+k)*12,12,5,['#e6c7a5','#b4c8ac','#b6adce','#c88d9c'][k],-.5);},
      metadata:{mechanism:'固定位置的细碎短笔触与分区冷暖色，局部日光光斑漂移；道具另用更细短笔触。',topic_adaptation:'口播文稿、底片与磁带置于户外采光的剪辑工作台，纸边以断续颜料处理。',motifs:'光斑沿桌面缓移，边缘纸带受风起伏。',limitations:'真实人物保持照片；不是逐帧生成油画肖像。'}};
  };

  F['09_postimp']=() => {
    const id='09_postimp',cache=cacheFactory(id),P={paper:'#ead394',ink:'#19385d',red:'#ca6738',olive:'#708657',gold:'#edb94c',white:'#f8e6b7'};
    const material=(q,w,h,c)=>{rect(q,0,0,w,h,c);flowing(q,w,h,[shade(c,-22),shade(c,19),mix(c,P.gold,.22),mix(c,'#6085a6',.2)],131,15,(x,y)=>.1+.35*Math.sin(y*.033)+.2*Math.cos(x*.021),32,5,.8,true);};
    const pat=(g,c)=>tilePattern(g,cache,'impasto',c,material);
    return {id,name:'梵高 · 流场厚涂',palette:P,pattern:pat,
      background(g,t){g.drawImage(cache('desk',W,H,q=>{
        rect(q,0,0,W,H,'#274e78');q.save();q.beginPath();q.rect(0,0,W,690);q.clip();flowing(q,W,700,['#183454','#356b96','#5b86a3','#78978e','#d6ac49','#52746d'],137,26,(x,y)=>Math.atan2(y-210,x-890)+Math.PI/2,75,10,.88,true);q.restore();
        polygon(q,[[0,760],[W,670],[W,H],[0,H]],'#916245');q.save();q.beginPath();q.rect(0,710,W,H);q.clip();flowing(q,W,H,['#a98443','#c7a451','#806f49','#66806c','#bd6739','#56656f'],147,30,(x,y)=>Math.atan2(y-600,(x-500)*.32),63,10,.75,true);q.restore();
        stroke(q,[[0,757],[1080,672]],P.ink,9);reel(q,85,1250,95,'#d7b34f','#224b71',0);film(q,770,580,280,86,'#cc9c3e','#28496e',-.17);
        q.save();q.translate(735,1190);q.rotate(.3);material(q,280,160,'#96a776');q.restore();
      }),0,0);
        g.save();g.translate(878,220);g.rotate(t*.17);for(let k=0;k<7;k++){g.beginPath();for(let j=0;j<=70;j++){const a=j*.115+k*.25,r=18+j*.95;const x=Math.cos(a)*r,y=Math.sin(a)*r*.78;j?g.lineTo(x,y):g.moveTo(x,y);}g.strokeStyle=['#efb944','#e5d49b','#436a89','#71957e'][k%4];g.lineWidth=4+(k%3);g.stroke();}g.restore();
      },plate(g,w,h,c,seed){tileFill(g,w,h,pat(g,c));dryEdge(g,w,h,P.ink,seed,Math.min(4,Math.min(w,h)*.08));},
      line(g,pts,c,lw){stroke(g,pts,P.ink,lw+2);stroke(g,pts,c,lw);if(pts.length<25)stroke(g,pts.map(p=>[p[0]+1,p[1]-1]),shade(c,30),1);},
      motifs(g,t,s){reel(g,85,1280,66,P.gold,P.ink,age(t,s)*.38);g.save();g.lineCap='round';for(let i=0;i<4;i++){g.beginPath();g.ellipse(88,1280,79+i*9,70+i*6,0,t*.2,t*.2+Math.PI*.65);g.strokeStyle=i%2?P.olive:P.red;g.lineWidth=4;g.stroke();}g.restore();},
      metadata:{mechanism:'曲线流场驱动长厚涂笔触，笔脊高光与普鲁士蓝轮廓；夜空和桌面各有方向场。',topic_adaptation:'磁带盘的圆周流场、底片和文稿的细油彩，剪辑桌成为黄蓝互补色画面。',motifs:'磁带盘旋转、顶部线圈状颜料缓转，跟随镜头局部时间。',limitations:'保留摄影人脸；是绘画材料和物体改编，不冒充梵高原创作品。'}};
  };

  function inkRibbon(g,pts,c,lw,seed=112) {
    if(pts.length>100){stroke(g,pts,c,lw);return;}
    const sample=[];for(let k=0;k<pts.length-1;k++){const a=pts[k],b=pts[k+1],n=Math.max(1,Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1])/4));for(let j=0;j<n;j++){const u=j/n;sample.push([a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u]);}}sample.push(pts[pts.length-1]);
    if(sample.length<2)return;const left=[],right=[],r=rng(seed);
    for(let i=0;i<sample.length;i++){const p=sample[i],a=sample[Math.max(0,i-1)],b=sample[Math.min(sample.length-1,i+1)],ang=Math.atan2(b[1]-a[1],b[0]-a[0])+Math.PI/2,u=i/(sample.length-1),pressure=.14+.86*Math.pow(Math.sin(Math.PI*clamp(u*.93+.02)),.55),ww=lw*.5*pressure*(.92+r()*.14);left.push([p[0]+Math.cos(ang)*ww,p[1]+Math.sin(ang)*ww]);right.push([p[0]-Math.cos(ang)*ww,p[1]-Math.sin(ang)*ww]);}
    g.save();g.globalAlpha=.13;stroke(g,sample,c,lw*1.55);g.restore();polygon(g,[...left,...right.reverse()],c);
    if(lw>3){g.save();g.globalAlpha=.25;for(let j=0;j<4;j++)stroke(g,sample.slice(Math.floor(j*sample.length*.045),Math.floor(sample.length*(.8+j*.04))).map(p=>[p[0]+(j-1.5)*lw*.12,p[1]+(j-1.5)*lw*.09]),'#faf5e9',Math.max(.5,lw*.075));g.restore();}
  }
  F['17_ink']=() => {
    const id='17_ink',cache=cacheFactory(id),P={paper:'#f4efdf',ink:'#25251f',red:'#a83c2d',olive:'#7d8c80',gold:'#b19b64',white:'#faf8ee'};
    const material=(q,w,h,c)=>{rect(q,0,0,w,h,c);paperFiber(q,w,h,170,.07);const r=rng(171);q.save();q.globalAlpha=.038;for(let i=0;i<16;i++){ellipse(q,r()*w,r()*h,20+r()*80,5+r()*25,'#877d66',r()*TAU);}q.restore();};
    const pat=(g,c)=>tilePattern(g,cache,'fiber',c,material);
    return {id,name:'水墨 · 宣纸与枯笔',palette:P,pattern:pat,
      background(g,t){g.drawImage(cache('paper',W,H,q=>{material(q,W,H,P.paper);
        q.save();q.globalAlpha=.08;polygon(q,[[0,540],[80,370],[240,470],[320,320],[500,570],[770,420],[1080,560],[1080,840],[0,810]],P.ink);q.restore();
        q.save();q.globalAlpha=.15;inkRibbon(q,[[0,802],[180,746],[420,788],[680,716],[1080,790]],P.ink,50);q.restore();
        inkRibbon(q,[[38,400],[52,1210],[65,1470]],P.ink,12);inkRibbon(q,[[965,660],[982,1180],[978,1430]],P.ink,6);
        for(let k=0;k<6;k++)inkRibbon(q,[[56,750+k*75],[100,720+k*75],[160,712+k*75]],'#78796a',6+k%2*3,175+k);
        q.save();q.translate(830,330);q.rotate(.1);rect(q,0,0,110,165,'#faf8ef');dryEdge(q,110,165,alpha(P.ink,.35),177,2);for(let i=0;i<4;i++)inkRibbon(q,[[18,28+i*22],[85,25+i*22]],alpha(P.ink,.3),3,178+i);q.restore();
        rect(q,965,1460,43,43,P.red);rect(q,972,1467,29,29,P.paper);rect(q,979,1474,15,15,P.red);
      }),0,0);g.save();g.globalAlpha=.035+.02*(1-Math.exp(-age(t,{start:0})));inkRibbon(g,[[40,900],[115,870],[174,925],[228,892]],P.ink,25);g.restore();},
      plate(g,w,h,c,seed){const base=rgb(c).reduce((a,b)=>a+b,0)>420?mix(c,P.paper,.55):c;tileFill(g,w,h,pat(g,base));if(Math.min(w,h)>30){g.save();g.globalAlpha=.12;inkRibbon(g,[[0,h*.08],[w*.5,h*.035],[w,h*.08]],P.ink,Math.min(12,h*.08),seed);g.restore();}dryEdge(g,w,h,alpha(P.ink,.45),seed,1.3);},
      line(g,pts,c,lw){inkRibbon(g,pts,c,lw,179);},
      motifs(g,t,s){g.save();g.globalAlpha=.3;const wave=Math.sin(age(t,s)*1.1)*10;inkRibbon(g,[[938,900],[964+wave,995],[943,1080],[987-wave,1160]],P.ink,7);g.restore();breezeStrip(g,30,1250,145,26,t,P.paper,alpha(P.ink,.26));},
      metadata:{mechanism:'固定宣纸纤维、留白淡墨山形；压力变化的连续墨带、湿墨晕圈与连续干刷缝。',topic_adaptation:'编辑文稿如手卷，纸带和底片边沿用枯笔，不以油画纹理覆盖白纸。',motifs:'墨色磁带线局部摇摆，纸带微起伏，朱红印章只是几何印记。',limitations:'未模拟真实流体扩散；高密度波形用轻线维持性能，照片人物保持摄影。'}};
  };

  F['19_munch']=() => {
    const id='19_munch',cache=cacheFactory(id),P={paper:'#e7c48c',ink:'#25273e',red:'#c95032',olive:'#687c77',gold:'#e1a34b',white:'#f4d9a4'};
    const mat=(q,w,h,c)=>{rect(q,0,0,w,h,c);flowing(q,w,h,[shade(c,-30),shade(c,18),mix(c,P.red,.16)],192,30,(x,y)=>.45*Math.sin(x*.018)+.5*Math.cos(y*.01),155,11,.38,false);};
    const pat=(g,c)=>tilePattern(g,cache,'long-bands',c,mat);
    return {id,name:'蒙克 · 流动表现主义',palette:P,pattern:pat,
      background(g,t){g.drawImage(cache('desk',W,H,q=>{
        rect(q,0,0,W,H,'#303b4a');q.save();q.beginPath();q.rect(0,0,W,660);q.clip();flowing(q,W,780,['#dc6337','#bb4337','#edaa58','#ecd29a','#9f4337'],191,29,(x,y)=>.45*Math.sin(x*.006)+.28*Math.cos(y*.008),260,14,.65,false);q.restore();
        polygon(q,[[0,670],[W,940],[W,H],[0,H]],'#6e655d');q.save();q.beginPath();q.rect(0,650,W,H);q.clip();flowing(q,W,H,['#323749','#667773','#977c5e','#4d5368','#a47855'],194,36,(x,y)=>.31+.16*Math.sin(y*.006),240,12,.5,false);q.restore();
        for(let k=0;k<5;k++)stroke(q,[[0,720+k*20],[1080,980+k*60]],['#b68861','#704c39','#d0a171','#6c4936','#b79265'][k],11);
      }),0,0);g.save();g.globalAlpha=.27;for(let k=0;k<8;k++){const p=[];for(let j=0;j<30;j++){const x=j*40;p.push([x,90+k*49+Math.sin(j*.23-t*.7+k*.4)*18]);}stroke(g,p,['#f1b665','#f4d9a3','#9e3a3a'][k%3],7+k%2*3);}g.restore();},
      plate(g,w,h,c,seed,t){tileFill(g,w,h,pat(g,c));g.save();g.beginPath();g.rect(0,0,w,h);g.clip();g.globalAlpha=.12;const p=[];for(let i=0;i<=24;i++)p.push([w*i/24,h*.4+Math.sin(i*.3-t*.9)*h*.06]);stroke(g,p,shade(c,-60),Math.min(12,h*.12));g.restore();},
      line(g,pts,c,lw,t){if(pts.length>100){stroke(g,pts,c,lw);return;}stroke(g,pts.map((p,i)=>[p[0]+Math.sin(i*.8+t)*2,p[1]+Math.sin(i*.7-t)*2]),c,lw);},
      motifs(g,t,s){g.save();g.translate(55,1020);g.rotate(-.2);const p=[];for(let j=0;j<25;j++)p.push([Math.sin(j*.27-age(t,s)*1.6)*21,j*14]);stroke(g,p,P.red,17);stroke(g,p.map(p=>[p[0]+3,p[1]]),P.gold,3);g.restore();breezeStrip(g,850,1320,160,50,t,P.paper,alpha(P.ink,.4));},
      metadata:{mechanism:'长而透明的连续色带及红橙天空，区别于梵高短厚笔脊；流线局部随时间波动。',topic_adaptation:'高压剪辑劳动转成弯曲的轨道栏杆与扭动磁带，主题物体保留可读结构。',motifs:'胶带带身起伏、红橙天空长线缓动，按镜头局部时间增强。',limitations:'仅绘画层与少量物体局部形变，人物脸和字幕不会全画面扭曲；不是原画重制。'}};
  };

  F['23_dali']=() => {
    const id='23_dali',cache=cacheFactory(id),P={paper:'#ecd9a6',ink:'#443725',red:'#aa6541',olive:'#7f9291',gold:'#c5964d',white:'#faf2d7'};
    const pat=(g,c)=>tilePattern(g,cache,'volume',c,(q,w,h)=>{rect(q,0,0,w,h,c);q.fillStyle=gradient(q,0,0,w,h,[[0,alpha('#ffffff',.15)],[.6,alpha('#ffffff',0)],[1,alpha('#432510',.24)]]);q.fillRect(0,0,w,h);paperFiber(q,w,h,233,.025);});
    const soft=(g,x,y,r,angle,t)=>{
      const sag=.45+.35*(.5+.5*Math.sin(t*.8)),fold=-r*.12;
      const m=(u,v)=>{if(v<=fold)return[x+u,y+v*.38];const d=v-fold,q=clamp(d/(r-fold)),hang=sag*r*.52*Math.exp(-Math.pow((u+r*.15)/(r*.61),2))*q*q;return[x+u*(1+.12*q),y+fold*.38+d*(.62+.3*sag)+hang];};
      const rim=[],inside=[];for(let i=0;i<100;i++){const a=i*TAU/100;rim.push(m(Math.cos(a)*r,Math.sin(a)*r));inside.push(m(Math.cos(a)*r*.89,Math.sin(a)*r*.89));}
      g.save();g.shadowColor='rgba(47,29,12,.23)';g.shadowBlur=14;g.shadowOffsetX=12;g.shadowOffsetY=24;polygon(g,rim,P.gold);g.restore();polygon(g,inside,gradient(g,x-r,y-r*.4,x+r,y+r,[[0,P.white],[.65,P.paper],[1,'#b49762']]));
      stroke(g,[...rim,rim[0]],'#976d39',1.6);
      for(let k=0;k<12;k++){const a=k*TAU/12;stroke(g,[m(Math.cos(a)*r*.71,Math.sin(a)*r*.71),m(Math.cos(a)*r*.83,Math.sin(a)*r*.83)],P.ink,k%3?1.7:3);}
      const hand=(a,len,lw)=>{const p=[];for(let i=0;i<=16;i++)p.push(m(Math.cos(a)*len*i/16,Math.sin(a)*len*i/16));stroke(g,p,P.ink,lw);};
      hand(angle,r*.69,3.5);hand(angle/12+.8,r*.47,5);const ctr=m(0,0);ellipse(g,ctr[0],ctr[1],4,4,P.ink);
      const p=[];for(let j=0;j<=25;j++)p.push(m(-r*.85+r*1.7*j/25,fold));stroke(g,p,alpha(P.white,.6),2.5);
    };
    return {id,name:'达利 · 悬垂软钟',palette:P,pattern:pat,
      background(g,t){g.drawImage(cache('desert',W,H,q=>{
        q.fillStyle=gradient(q,0,0,0,770,[[0,'#386986'],[.58,'#a6c4c9'],[1,'#e9d9b0']]);q.fillRect(0,0,W,H);q.fillStyle=gradient(q,0,700,0,H,[[0,'#bca078'],[1,'#e0bd86']]);q.fillRect(0,700,W,H-700);
        polygon(q,[[0,707],[150,660],[185,540],[240,558],[255,711]],'#756b5c');polygon(q,[[895,708],[900,550],[955,530],[970,640],[1080,620],[1080,710]],'#8a795f');
        q.save();q.globalAlpha=.18;polygon(q,[[815,805],[950,795],[750,1340],[440,1440]],'#3b2c23');polygon(q,[[0,940],[165,955],[610,1520],[345,1460]],'#3b2c23');q.restore();
        polygon(q,[[0,805],[235,870],[170,1040],[0,995]],'#b08c58');polygon(q,[[0,995],[170,1040],[170,1145],[0,1090]],'#7b6040');polygon(q,[[825,800],[1015,755],[1080,795],[915,870]],'#c3ab77');polygon(q,[[825,800],[915,870],[915,1060],[825,1010]],'#8d7853');
        for(let k=0;k<9;k++)stroke(q,[[0,750+k*k*9],[400,748+k*k*9],[1080,752+k*k*9]],alpha('#79604a',.14),1.2);
      }),0,0);soft(g,930,890,65,t*.6,t);},
      plate(g,w,h,c,seed,t){tileFill(g,w,h,pat(g,c));g.fillStyle=gradient(g,0,0,w,0,[[0,alpha('#fff9df',.2)],[.7,alpha('#ffffff',0)],[1,alpha('#593b22',.25)]]);g.fillRect(0,0,w,h);stroke(g,[[1,1],[w-1,1],[w-1,h-1]],alpha(P.white,.6),1.5);},
      line:simpleLine,
      clock(g,x,y,r,hand,t){const a=typeof hand==='number'?hand:(hand?.angle??t*4.8);soft(g,x,y,r,a,t);return true;},
      motifs(g,t,s){breezeStrip(g,25,1110,160,42,t*.35,P.paper,'#796644');g.save();g.translate(914,1190);g.rotate(.03*Math.sin(t));g.beginPath();g.moveTo(-20,-35);g.bezierCurveTo(-18,8,32,28,17,88+Math.sin(t*.8)*9);g.strokeStyle=P.ink;g.lineWidth=8;g.stroke();g.restore();},
      metadata:{mechanism:'荒漠地平线、体积渐变与独立长投影；钟面、刻度、指针共同走同一悬垂映射，下缘向外舒展。',topic_adaptation:'剪辑时间成为软钟，工作台与纸带孤立在空旷荒漠中，磁带柔软下垂。',motifs:'钟体缓慢变软，两根指针保持可辨认；悬挂胶带轻摆。',limitations:'超现实主题物体改编；没有原场景少女、猫或拟人脸，投影为独立几何影层。'}};
  };

  F['24_hopper']=() => {
    const id='24_hopper',cache=cacheFactory(id),P={paper:'#ecd9ae',ink:'#304b46',red:'#b75540',olive:'#628574',gold:'#dcaa61',white:'#faf0d3'};
    const pat=(g,c)=>tilePattern(g,cache,'paintdrag',c,(q,w,h)=>{rect(q,0,0,w,h,c);const r=rng(242);q.save();q.globalAlpha=.09;for(let k=0;k<100;k++){const x=r()*w;stroke(q,[[x,r()*h],[x+(r()-.5)*3,h]],k%2?shade(c,25):shade(c,-35),1+r()*3);}q.restore();});
    const desk=(q,lit)=>{const wall=lit?'#dac793':'#50776e',floor=lit?'#c39462':'#716d53';rect(q,0,0,W,H,wall);polygon(q,[[0,740],[1080,690],[1080,H],[0,H]],floor);rect(q,60,320,110,430,lit?'#997647':'#344d49');rect(q,900,390,145,280,lit?'#c6ab72':'#3b5b54');for(let k=0;k<7;k++)stroke(q,[[0,780+k*120],[1080,735+k*175]],lit?'#a87748':'#545c4a',2);film(q,30,1340,210,80,lit?'#b46b47':'#5c5247',lit?'#f3dca3':'#81988b',-.18);rect(q,840,1190,180,130,lit?'#a34832':'#693f34');q.save();q.globalAlpha=.14;const r=rng(244);for(let k=0;k<350;k++){const x=r()*W,y=r()*H;stroke(q,[[x,y],[x+2,y+15]],lit?'#f7d49e':'#7ba08b',1);}q.restore();};
    return {id,name:'霍普 · 硬边光切',palette:P,pattern:pat,
      background(g,t,s){g.drawImage(cache('dark',W,H,q=>desk(q,false)),0,0);const shift=Math.sin(age(t,s)*.75)*95;g.save();polygon(g,[[385+shift,0],[750+shift,0],[1080,1450],[720,1470],[200,450]],null);g.clip();g.drawImage(cache('lit',W,H,q=>desk(q,true)),0,0);g.restore();
        for(let k=0;k<4;k++){const y=260+k*110;polygon(g,[[250+shift,y],[650+shift,y],[710+shift,y+28],[265+shift,y+25]],'rgba(32,63,53,.18)');}
      },plate(g,w,h,c,seed,t){tileFill(g,w,h,pat(g,mix(c,'#50756a',.13)));polygon(g,[[w*.52,0],[w,0],[w,h],[w*.7,h]],alpha('#fff1bd',.22));stroke(g,[[0,h],[w,h],[w,0]],shade(c,-38),Math.min(2,h*.08));},
      line(g,pts,c,lw){stroke(g,pts,c,lw);},
      motifs(g,t,s){const x=85+Math.sin(age(t,s)*.7)*24;film(g,x,840,130,52,P.ink,P.paper,-.3);g.save();g.globalAlpha=.5;for(let i=0;i<18;i++){const y=180+(i*83+t*9)%940,xx=380+(i*17)%180;if(xx<650)ellipse(g,xx,y,1.4,1.4,P.white);}g.restore();},
      metadata:{mechanism:'同一工作台分别画冷绿暗面和暖黄明面，通过移动硬边多边形切出光照，细薄油彩拖痕。',topic_adaptation:'片场剪辑桌、底片与案卷置于建筑式切光中，明暗面共享物体几何。',motifs:'硬边日光横移，底片投影与少量光束尘粒跟随运动。',limitations:'几何油画背景，真实人物不重画、不添加强光遮脸；不是大量粒子或柔光滤镜。'}};
  };

  function watercolor(q,w,h,c,seed,layers=5) {
    rect(q,0,0,w,h,c);const r=rng(seed);q.save();
    for(let k=0;k<layers;k++){const p=[],n=10;for(let j=0;j<=n;j++)p.push([w*j/n,(r()-.5)*8]);for(let j=1;j<=n;j++)p.push([w+(r()-.5)*8,h*j/n]);for(let j=n-1;j>=0;j--)p.push([w*j/n,h+(r()-.5)*8]);for(let j=n-1;j>0;j--)p.push([(r()-.5)*8,h*j/n]);q.globalAlpha=.12;q.globalCompositeOperation='multiply';polygon(q,p,k%2?shade(c,-12):shade(c,8));}
    // Pigment pools have translucent fringes, unlike opaque circular speckles.
    q.globalCompositeOperation='multiply';q.globalAlpha=.085;
    for(let i=0;i<14;i++){const x=r()*w,y=r()*h,rr=Math.min(w,h)*(.10+r()*.20),gr=q.createRadialGradient(x,y,0,x,y,rr);gr.addColorStop(0,alpha(shade(c,-22),.5));gr.addColorStop(.68,alpha(shade(c,-10),.24));gr.addColorStop(1,alpha(c,0));ellipse(q,x,y,rr,rr*(.7+r()*.5),gr,r()*TAU);}
    q.globalCompositeOperation='source-over';q.globalAlpha=.045;for(let i=0;i<16;i++)ellipse(q,r()*w,r()*h,15+r()*55,10+r()*60,'#faf9e7',r()*TAU);q.restore();paperFiber(q,w,h,seed+2,.045);
    q.save();q.globalAlpha=.21;dryEdge(q,w,h,shade(c,-42),seed,1.6);q.restore();
  }
  F['25_ghibli']=() => {
    const id='25_ghibli',cache=cacheFactory(id),P={paper:'#f3eed8',ink:'#665641',red:'#bb7255',olive:'#88a365',gold:'#d9b974',white:'#fcf9e9'};
    const pat=(g,c)=>tilePattern(g,cache,'watercolor',c,(q,w,h)=>watercolor(q,w,h,c,253));
    return {id,name:'吉卜力 · 水彩与赛璐璐',palette:P,pattern:pat,
      background(g,t){g.drawImage(cache('workbench',W,H,q=>{
        watercolor(q,W,H,'#e7ecd3',250);q.save();q.beginPath();q.rect(0,0,W,650);q.clip();watercolor(q,W,650,'#b5d4df',251);q.restore();
        polygon(q,[[0,500],[190,430],[420,540],[720,415],[1080,510],[1080,830],[0,830]],'#9bb778');q.save();q.globalAlpha=.12;for(let i=0;i<55;i++){ellipse(q,(i*167)%W,540+(i*67)%220,75,25,'#416546');}q.restore();
        polygon(q,[[0,765],[1080,730],[1080,H],[0,H]],'#c6a174');for(let k=0;k<7;k++)stroke(q,[[0,780+k*160],[1080,745+k*175]],'#a98965',2);
        q.save();q.translate(0,1270);q.rotate(-.06);watercolor(q,235,290,'#e8eddc',256);q.restore();film(q,870,755,200,63,'#809973','#ebefd9',.13);
        for(let i=0;i<90;i++){const x=(i*193)%W,y=640+(i*73)%150;stroke(q,[[x,y+25],[x+3,y]],i%2?'#79955f':'#a8bd7c',1.5);}
      }),0,0);
        const clouds=cache('clouds',700,260,q=>{q.save();q.globalAlpha=.88;[[30,180,110],[160,140,120],[280,172,120],[420,145,95],[570,187,140]].forEach(([x,y,r])=>ellipse(q,x,y,r,r*.5,'#f6f5e8'));q.restore();});g.drawImage(clouds,-150+(t*6)%700,130);
      },plate(g,w,h,c,seed){tileFill(g,w,h,pat(g,c));polygon(g,[[w*.75,0],[w,0],[w,h],[w*.9,h]],alpha('#554632',.12));dryEdge(g,w,h,'#7e6b50',seed,Math.max(.7,Math.min(1.6,h*.035)));},
      line(g,pts,c,lw){stroke(g,pts,c,lw);if(pts.length<25)stroke(g,pts.map(p=>[p[0]+.7,p[1]+.7]),alpha(P.ink,.18),.7);},
      motifs(g,t,s){breezeStrip(g,828,1205,190,65,age(t,s)*1.2,P.paper,alpha(P.ink,.45));for(let i=0;i<7;i++){const x=55+i*12,wind=Math.sin(t*1.8-i*.4)*7;stroke(g,[[x,1450],[x+wind,1390]],P.olive,2);ellipse(g,x+wind,1390,7,16,'#b4c388',wind*.025);}ellipse(g,943,1204,5,5,P.white);},
      metadata:{mechanism:'固定种子的多层半透明水彩积色、淡色水渍、纸纹与湿边；道具用克制赛璐璐月牙阴影。',topic_adaptation:'户外剪辑木桌上的文稿、底片、纸带与案卷，主题材料呈手绘水彩。',motifs:'云层平移，纸带与桌边草叶受同一阵风错相摆动。',limitations:'借鉴背景绘画语法，不生成原作角色；照片人物保持真实，没有把照片卡通化。'}};
  };

  F['28_monet']=() => {
    const id='28_monet',cache=cacheFactory(id),P={paper:'#e0e7d2',ink:'#465e6d',red:'#c891a5',olive:'#86ad92',gold:'#c8c39b',white:'#f1efdc'};
    const water=(q,w,h,c,seed)=>{rect(q,0,0,w,h,c);shortDabs(q,w,h,[shade(c,-17),shade(c,12),mix(c,'#90a7c5',.35),mix(c,'#b792b0',.18),mix(c,'#c4d4b0',.23)],seed,8,0);q.save();q.globalAlpha=.3;const r=rng(seed+1);for(let i=0;i<w*h/280;i++){const x=r()*w,y=r()*h;stroke(q,[[x,y],[x+8+r()*24,y+.7]],i%3?'#bbc6d0':'#d4ccbe',1.6);}q.restore();};
    const pat=(g,c)=>tilePattern(g,cache,'reflection',c,(q,w,h)=>water(q,w,h,c,283));
    return {id,name:'莫奈 · 断色水面反光',palette:P,pattern:pat,
      background(g,t){g.drawImage(cache('reflecting-workbench',W,H,q=>{
        water(q,W,H,'#849dad',280);q.save();q.globalAlpha=.38;for(let k=0;k<9;k++){const x=35+k*128;flowing(q,100,H,['#869c8c','#627f88','#b7bab0'],281+k,40,(xx,y)=>Math.PI*.5+.08*Math.sin(y*.015),90,8,.22);q.translate(125,0);}q.restore();
        polygon(q,[[0,735],[1080,760],[1080,940],[0,885]],'#a8b3ab');q.save();q.globalAlpha=.4;for(let k=0;k<9;k++)stroke(q,[[0,748+k*15],[1080,767+k*17]],['#c7c3b2','#8da7ab','#bfaca9'][k%3],5);q.restore();
        q.save();q.translate(25,1340);q.rotate(-.13);water(q,180,200,'#c5ccae',295);q.restore();film(q,825,520,245,70,'#9ea5a8','#d0d7c7',.06);
        [[90,1040,65],[1030,970,65],[100,1490,90],[970,1420,76]].forEach(([x,y,r])=>{ellipse(q,x,y,r,r*.32,'#739c89');stroke(q,[[x-r*.5,y],[x+r*.5,y]],'#b3c5a0',3);});
      }),0,0);
        g.save();g.globalAlpha=.18;for(let i=0;i<25;i++){const x=(i*109)%W,y=200+(i*107)%1300;stroke(g,[[x,y],[x+28+Math.sin(t*.7+i)*12,y]],i%2?'#e7d8d0':'#d3e1d7',2+Math.sin(t+i));}g.restore();
      },plate(g,w,h,c,seed){tileFill(g,w,h,pat(g,c));g.save();g.globalAlpha=.23;for(let y=8;y<h;y+=17)stroke(g,[[0,y],[w,y+Math.sin(y)*2]],shade(c,30),1);g.restore();},
      line(g,pts,c,lw){stroke(g,pts,c,lw*.8);if(pts.length<30)stroke(g,pts.map(p=>[p[0],p[1]+1]),shade(c,20),1);},
      motifs(g,t,s){[[92,1060,0],[975,1420,1.4]].forEach(([x,y,p])=>{const a=(age(t,s)*.32+p)%1;g.save();g.globalAlpha=(1-a)*.45;g.strokeStyle='#c8d5c6';g.lineWidth=1.8;g.beginPath();g.ellipse(x,y,20+a*80,4.4+a*17.6,0,0,TAU);g.stroke();g.restore();});breezeStrip(g,835,1220,180,32,t*.5,P.paper,alpha(P.ink,.2));},
      metadata:{mechanism:'水平断色短笔、水面冷暖反射与少量固定位置闪光；留白纸面也使用细水平断色。',topic_adaptation:'编辑桌被改编成反光水面平台，照片、文稿与底片像浮起的纸岛。',motifs:'纸岛旁椭圆波纹扩张并消退，水面反光局部脉动。',limitations:'反光为绘画式水平色层，不做真实光线追踪；字幕和人脸不受水面变形。'}};
  };

  const DOT_PAL=['#1a2058','#2a3a9a','#3f6fd0','#6aaee6','#1f6a52','#2f9a5a','#a8c83a','#f2cf3a','#f08a2a','#e0432a','#c0306a','#7a4aa8','#f8f4e8','#e8b48a','#f6e49a','#f6c48a','#cfe08a','#b0cff0','#f2b8c8','#c99a4a','#9a7ac8'];
  const DOT_RGB=DOT_PAL.map(rgb);
  function pointPair(c){const z=rgb(c);let best={error:Infinity,a:12,b:17,q:.5};for(let i=0;i<DOT_RGB.length;i++)for(let j=i+1;j<DOT_RGB.length;j++){const a=DOT_RGB[i],b=DOT_RGB[j],d=b.map((v,k)=>v-a[k]),den=d.reduce((s,v)=>s+v*v,0),q=clamp(z.reduce((s,v,k)=>s+(v-a[k])*d[k],0)/den,.18,.82),error=z.reduce((s,v,k)=>s+(v-a[k]-d[k]*q)**2,0)+.004*den;if(error<best.error)best={error,a:i,b:j,q};}return best;}
  function dots(q,w,h,target,seed,pitch=9){const r=rng(seed),pair=pointPair(target),groups=DOT_PAL.map(()=>new Path2D());rect(q,0,0,w,h,target);for(let iy=0,y=0;y<h+pitch;iy++,y+=pitch*.866){for(let x=(iy%2)*pitch*.5;x<w+pitch;x+=pitch){const xx=x+(r()-.5)*1.1,yy=y+(r()-.5)*1.1,choice=r(),ix=choice<.07?Math.floor(r()*DOT_PAL.length):(r()<pair.q?pair.b:pair.a),p=groups[ix];p.moveTo(xx+pitch*.435,yy);p.arc(xx,yy,pitch*.435,0,TAU);}}groups.forEach((p,i)=>{q.fillStyle=DOT_PAL[i];q.fill(p);});}
  F['29_seurat']=() => {
    const id='29_seurat',cache=cacheFactory(id),P={paper:'#e4deb5',ink:'#3b4964',red:'#ba6d74',olive:'#90a56d',gold:'#d7b675',white:'#f3edcd'};
    const pat=(g,c)=>tilePattern(g,cache,'optical-dots',c,(q,w,h)=>dots(q,w,h,c,293,8));
    return {id,name:'修拉 · 光学混色点彩',palette:P,pattern:pat,
      background(g,t){g.drawImage(cache('point-workbench',W,H,q=>{
        dots(q,W,H,'#9aae9b',290,10);q.save();q.beginPath();q.rect(0,0,W,680);q.clip();dots(q,W,680,'#b6c5d4',291,10);q.restore();
        q.save();polygon(q,[[0,720],[1080,660],[1080,H],[0,H]],null);q.clip();dots(q,W,H,'#bcb282',292,10);q.restore();
        q.save();q.translate(20,1060);q.rotate(-.14);dots(q,165,245,P.paper,294,8);q.restore();film(q,845,620,235,67,'#5b6570','#b4c5ba',.18);
        q.save();q.translate(955,1390);q.beginPath();q.arc(0,0,85,0,TAU);q.clip();q.translate(-90,-90);dots(q,180,180,'#668379',295,7);q.restore();
      }),0,0);g.save();for(let i=0;i<70;i++){const x=24+(i*197)%1030,y=120+(i*139)%1360;g.globalAlpha=.06+.08*Math.max(0,Math.sin(t*.8+i));ellipse(g,x,y,3.5,3.5,i%3?'#f8f4e8':'#cfe08a');}g.restore();},
      plate(g,w,h,c,seed){tileFill(g,w,h,pat(g,c));},line(g,pts,c,lw){stroke(g,pts,c,lw*.72);if(pts.length<50){for(let k=0;k<pts.length;k+=2)ellipse(g,pts[k][0],pts[k][1],Math.max(1.1,lw*.4),Math.max(1.1,lw*.4),shade(c,10));}},
      motifs(g,t,s){reel(g,950,1380,48,P.olive,P.paper,age(t,s)*.25);g.save();g.globalAlpha=.45;for(let k=0;k<7;k++)ellipse(g,44+k*10,680+Math.sin(t*.9+k)*12,3.5,3.5,DOT_PAL[14+k]);g.restore();},
      metadata:{mechanism:'固定六角点阵、等尺度色点，以调色板双色投影求混色比例并加入少量补色；Path2D 按色批次一次缓存。',topic_adaptation:'印刷件、案卷与工作台都用光学点彩材料，文字与摄影层维持可读。',motifs:'局部稀疏高光点微脉动，磁带盘按镜头局部时间转动。',limitations:'色点混合为 RGB 近似，非真实颜料光谱；所有大面积点阵仅初始化一次。'}};
  };

  F['32_rembrandt']=() => {
    const id='32_rembrandt',cache=cacheFactory(id),P={paper:'#cbb886',ink:'#291e15',red:'#8d4e31',olive:'#777343',gold:'#c9a15c',white:'#ead6a1'};
    const mat=(q,w,h,c)=>{rect(q,0,0,w,h,mix(c,'#62452b',.12));flowing(q,w,h,[shade(c,-30),shade(c,18),mix(c,'#b28c55',.18)],323,36,(x,y)=>.08+.12*Math.sin(y*.018),105,12,.2,false);const r=rng(324);q.save();q.globalAlpha=.18;for(let k=0;k<16;k++){const y=r()*h;stroke(q,[[0,y],[w*.35+r()*w*.4,y+(r()-.5)*3]],'#efe0b4',.5+r()*1.2);}q.restore();};
    const pat=(g,c)=>tilePattern(g,cache,'chiaroscuro-bristle',c,mat);
    return {id,name:'伦勃朗 · 明暗与笔脊',palette:P,pattern:pat,
      background(g,t){g.drawImage(cache('dark-desk',W,H,q=>{
        rect(q,0,0,W,H,'#211a14');flowing(q,W,H,['#3d2b1a','#4d3824','#282319','#5d452a','#2b241a'],320,67,(x,y)=>.5+Math.sin(y*.003)*.3,185,36,.28,false);
        polygon(q,[[0,800],[1080,745],[1080,H],[0,H]],'#392d21');for(let k=0;k<6;k++)stroke(q,[[0,830+k*185],[1080,770+k*195]],'#453526',3);
        glow(q,290,660,690,'#c7a063',.47);polygon(q,[[145,200],[310,200],[790,1400],[0,1150]],'rgba(187,144,77,.07)');
        rect(q,68,220,152,34,'#745431');polygon(q,[[52,254],[236,254],[190,295],[95,295]],'#a58046');stroke(q,[[145,222],[110,150],[145,50]],'#5c4731',11);
        q.save();q.translate(865,1230);q.rotate(.18);mat(q,195,220,'#82774f');q.restore();film(q,18,1310,180,77,'#56432b','#b49a65',-.08);paperFiber(q,W,H,327,.014);
      }),0,0);glow(g,175,305,220,P.gold,.08+.025*Math.sin(t*6.2)+.015*Math.sin(t*10));},
      plate(g,w,h,c,seed){tileFill(g,w,h,pat(g,c));g.fillStyle=gradient(g,0,0,w,h,[[0,alpha('#fff0b3',.18)],[.42,alpha('#fff0b3',0)],[1,alpha('#1c1108',.37)]]);g.fillRect(0,0,w,h);const r=rng(seed+321);for(let k=0;k<8;k++){const x=r()*w*.7,len=w*(.15+r()*.27);stroke(g,[[x,2+k*.9],[Math.min(w,x+len),2+k*.9]],alpha('#e8d19b',.2+r()*.25),.7+r()*.7);}dryEdge(g,w,h,alpha('#281a0f',.65),seed,2);},
      line(g,pts,c,lw){stroke(g,pts,mix(c,P.ink,.18),lw);if(pts.length<40)stroke(g,pts.map(p=>[p[0]-.8,p[1]-1.1]),alpha(P.white,.35),Math.max(.7,lw*.15));},
      motifs(g,t,s){g.save();for(let i=0;i<45;i++){const x=120+(i*73)%280,y=350+(i*47+t*(6+i%4))%980;if(x<120+(y-230)*.45){g.globalAlpha=.07+.14*Math.max(0,Math.sin(i+t*.6));ellipse(g,x,y,.8+i%3*.3,.8+i%3*.3,P.white);}}g.restore();const p=[];for(let i=0;i<16;i++)p.push([72+Math.sin(i*.25-t*.55)*8,1130+i*12]);stroke(g,p,'#79623a',3);},
      after(g){cornerLight(g,'#d0a36b',.065);},
      metadata:{mechanism:'棕金调的明暗聚光、暗部失去边沿，亮部平行细笔脊长短随机，暗桌上保留宽干刷方向。',topic_adaptation:'台灯照亮同一文稿、磁带与冲印件，案卷和底片呈暖色油画材料。',motifs:'台灯光池轻微闪动，光束内少量尘粒飘移，磁带尾端缓摆。',limitations:'经典油画材料近似，不生成伦勃朗级别的人物肖像；摄影人脸保留，叠加只在边缘。'}};
  };

  F['35_shinkai']=() => {
    const id='35_shinkai',cache=cacheFactory(id),P={paper:'#f1e9d2',ink:'#2e415b',red:'#c6746e',olive:'#73949a',gold:'#e2b66c',white:'#fff6df'};
    const pat=(g,c)=>tilePattern(g,cache,'cel',c,(q,w,h)=>{rect(q,0,0,w,h,c);polygon(q,[[w*.55,0],[w,0],[w,h],[w*.82,h]],mix(c,'#293e69',.24));stroke(q,[[1,1],[w-1,1]],alpha('#fff5d9',.7),2);paperFiber(q,w,h,357,.01);});
    const clouds=()=>cache('cumulus',1050,430,q=>{
      const r=rng(351),blobs=[];for(let k=0;k<30;k++)blobs.push([70+r()*940,175+r()*120,40+r()*100]);q.save();q.beginPath();blobs.forEach(([x,y,r])=>{q.moveTo(x+r,y);q.arc(x,y,r,0,TAU);});q.fillStyle='#a4b7d3';q.fill();q.clip();blobs.forEach(([x,y,r])=>{const gr=q.createRadialGradient(x+r*.19,y-r*.29,r*.1,x,y,r);gr.addColorStop(0,'#fff3d8');gr.addColorStop(.58,'#f1eee3');gr.addColorStop(.86,'rgba(230,233,233,.5)');gr.addColorStop(1,'rgba(230,233,233,0)');ellipse(q,x+r*.17,y-r*.28,r*.85,r*.82,gr);});q.restore();
    });
    return {id,name:'新海诚 · 积云逆光',palette:P,pattern:pat,
      background(g,t){g.drawImage(cache('twilight-workbench',W,H,q=>{
        q.fillStyle=gradient(q,0,0,0,840,[[0,'#4174ad'],[.38,'#83b8d2'],[.78,'#d7d5cf'],[1,'#f4d8ad']]);q.fillRect(0,0,W,H);
        polygon(q,[[0,716],[1080,690],[1080,H],[0,H]],'#a17b63');for(let k=0;k<6;k++)stroke(q,[[0,750+k*182],[1080,724+k*200]],'#775d54',2);
        for(let i=0;i<12;i++){const x=i*95,ht=35+(i*47)%150;rect(q,x,690-ht,65,ht,'#657f95');rect(q,x+5,700-ht,6,ht*.5,'#b9c2c2');}
        stroke(q,[[52,0],[60,680]],'#33465b',5);stroke(q,[[986,0],[992,700]],'#42516c',4);
        for(let k=0;k<3;k++){q.beginPath();q.moveTo(0,330+k*22);q.quadraticCurveTo(490,395+k*23,1080,300+k*29);q.strokeStyle='#526b87';q.lineWidth=1.5;q.stroke();}
        film(q,18,1115,210,73,'#637985','#f4e9d1',-.17);rect(q,908,1290,170,170,'#776871');polygon(q,[[908,1290],[1078,1290],[1078,1312],[919,1304]],'#eadcbf');
      }),0,0);
        g.save();g.globalAlpha=.82;g.drawImage(cache('cumulus-soft',1050,430,q=>{q.filter='blur(3px)';q.drawImage(clouds(),0,0);q.filter='none';q.globalAlpha=.55;q.drawImage(clouds(),0,0);q.globalAlpha=1;}),-100+(t*3.5)%150,80);g.restore();
        g.drawImage(cache('rays',W,1500,q=>{q.save();q.filter='blur(15px)';for(let k=0;k<3;k++)polygon(q,[[865,208],[905,228],[520+k*120,1320],[345+k*85,1180]],['rgba(255,242,200,.085)','rgba(255,242,210,.09)','rgba(255,246,218,.05)'][k]);q.restore();}),0,0);
        glow(g,879,228,105,'#fff0c2',.2+.03*Math.sin(t*.7));
      },plate(g,w,h,c,seed){tileFill(g,w,h,pat(g,c));dryEdge(g,w,h,P.ink,seed,Math.max(.8,Math.min(2.2,h*.05)));stroke(g,[[1,1],[w-1,1],[w-1,h*.55]],alpha(P.white,.8),2.3);},
      line(g,pts,c,lw){stroke(g,pts,P.ink,lw+1.4);stroke(g,pts,c,lw);},
      motifs(g,t,s){g.save();g.globalCompositeOperation='screen';for(let k=0;k<4;k++){const x=862-k*40,y=230+k*36;polygon(g,Array.from({length:6},(_,j)=>[x+Math.cos(j*TAU/6)*9,y+Math.sin(j*TAU/6)*9]),alpha(k%2?'#ffd8a3':'#aadbec',.1));}g.restore();for(let k=0;k<15;k++)ellipse(g,855+(k*29)%190,360+(k*113+t*5)%1080,1,1,alpha(P.white,.34));g.save();g.strokeStyle=alpha('#b6d8eb',.6);g.lineWidth=1.2;for(let k=0;k<3;k++){const x=39+k*18,y=780+k*140+Math.sin(t+k)*5;g.beginPath();g.arc(x,y,5,0,Math.PI);g.stroke();ellipse(g,x-1.5,y-2,1,1,'#ffffff');}g.restore();},
      after(g){cornerLight(g,'#ffe4ad',.035);},
      metadata:{mechanism:'积云先统一冷灰轮廓再绘暖白高光，不逐泡勾线；暖冷天空、赛璐璐道具阴影、逆光边缘与缓存丁达尔光束。',topic_adaptation:'城市天际线下的剪辑工作台，电缆和底片同构，文稿与胶片保留硬边逆光。',motifs:'云层缓移、局部六角镜头光斑、玻璃小水滴高光与稀疏逆光尘粒。',limitations:'风格化背景和道具，不把真实口播人物动漫化；光束只在背景，脸部没有强曝光遮盖。'}};
  };

  F['36_picasso_blue']=() => {
    const id='36_picasso_blue',cache=cacheFactory(id),P={paper:'#b6c8d8',ink:'#132240',red:'#315c85',olive:'#3b6878',gold:'#6b8fb6',white:'#d3dde4'};
    const blue=c=>{const r=rgb(c),v=(r[0]+r[1]+r[2])/3;return mix('#1d3866','#b6c8d8',clamp((v-15)/235));};
    const material=(q,w,h,c)=>{const b=blue(c);rect(q,0,0,w,h,b);flowing(q,w,h,[shade(b,-9),shade(b,8),mix(b,'#3b6878',.12)],363,33,(x,y)=>Math.PI*.49+.08*Math.sin(x*.023),190,12,.24,false);};
    const pat=(g,c)=>tilePattern(g,cache,'long-blue-brush',c,material);
    return {id,name:'毕加索蓝色时期 · 长干刷',palette:P,pattern:pat,
      background(g,t){g.drawImage(cache('blue-editor-desk',W,H,q=>{
        rect(q,0,0,W,H,'#284d77');flowing(q,W,H,['#2d5a94','#34577f','#234269','#3b6878','#42688c'],360,46,(x,y)=>1.57+.06*Math.cos(x*.01),260,25,.4,false);
        polygon(q,[[0,795],[1080,720],[1080,H],[0,H]],'#315171');q.save();q.globalAlpha=.24;flowing(q,W,H,['#51769a','#183d60','#4b6e8f'],361,63,(x,y)=>.2,210,19,.25,false);q.restore();
        q.save();q.translate(42,295);q.rotate(-.055);material(q,100,480,'#acbed1');dryEdge(q,100,480,P.ink,364,4);q.restore();q.save();q.translate(929,500);q.rotate(.05);material(q,114,470,'#638aac');dryEdge(q,114,470,P.ink,365,3);q.restore();
        film(q,20,1250,180,92,'#204770','#91aec2',-.27);reel(q,985,1410,78,'#486e8d','#17314f',0);stroke(q,[[0,795],[1080,720]],P.ink,5);
      }),0,0);g.save();g.globalAlpha=.13;const p=[];for(let j=0;j<=26;j++)p.push([15+j*40,330+Math.sin(j*.13-t*.16)*18]);stroke(g,p,P.white,1.2);g.restore();},
      plate(g,w,h,c,seed){tileFill(g,w,h,pat(g,c));dryEdge(g,w,h,P.ink,seed,Math.max(1.2,Math.min(3,h*.04)));},
      line(g,pts,c,lw){stroke(g,pts,blue(c),lw);if(pts.length<35)stroke(g,pts.map(p=>[p[0]+.5,p[1]+.5]),alpha(P.ink,.2),.8);},
      motifs(g,t,s){const p=[];for(let i=0;i<=30;i++)p.push([955+Math.sin(i*.22-t*.45)*12,880+i*15]);stroke(g,p,'#193753',7);stroke(g,p.map(p=>[p[0]-2,p[1]]),'#7494b1',1.2);reel(g,85,1370,49,'#6b8fb6','#1d3866',age(t,s)*.14);},
      metadata:{mechanism:'严格蓝调的低对比长干刷、延长纸张轮廓与稳定普鲁士蓝外缘，避免变成短色点印象派。',topic_adaptation:'拉长的文稿、狭窄案卷和深蓝磁带构成忧郁剪辑桌，所有绘制材料归入蓝色域。',motifs:'磁带尾端缓慢波动，线盘低速旋转，细月光横线缓移。',limitations:'蓝调约束仅作用绘画物体，真实人物保留摄影颜色与脸；无代码生成的拉长人像。'}};
  };
})();
