/* Original, deterministic mechanism reconstructions. Source videos are not bundled. */
'use strict';
const C=document.querySelector('#film'),ctx=C.getContext('2d');
const W=1080,H=1920,TAU=Math.PI*2;
let S=window.SOCIAL_SPEC,portrait,cutout,presenterVideo,media=[];
const clamp=(n,a=0,b=1)=>Math.max(a,Math.min(b,n));
const ease=n=>1-Math.pow(1-clamp(n),3);
const lerp=(a,b,p)=>a+(b-a)*p;
const gate=(t,at,d=.5)=>ease((t-at)/d);
const round=(x,y,w,h,r=24)=>{ctx.beginPath();ctx.roundRect(x,y,w,h,r);};
const fill=(color)=>{ctx.fillStyle=color;ctx.fill();};
function background(color='#11141c',grid=false){ctx.fillStyle=color;ctx.fillRect(0,0,W,H);if(grid){ctx.strokeStyle='#ffffff13';ctx.lineWidth=1;for(let x=0;x<W;x+=54){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}for(let y=0;y<H;y+=54){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}}}
function text(value,x,y,size=76,color='#fff',o={}){
  value=String(value);ctx.save();ctx.font=`${o.weight||800} ${size}px ${o.serif?'SocialSerif':'SocialSans'},"PingFang SC",sans-serif`;
  const max=o.maxWidth||920;let actual=size;
  while(ctx.measureText(value).width>max&&actual>24){actual-=2;ctx.font=`800 ${actual}px ${o.serif?'SocialSerif':'SocialSans'},"PingFang SC",sans-serif`;}
  ctx.textAlign=o.align||'center';ctx.textBaseline='middle';
  if(o.shadow){ctx.shadowColor='#0009';ctx.shadowBlur=10;ctx.shadowOffsetY=7;}
  if(o.stroke){ctx.lineWidth=o.strokeWidth||10;ctx.strokeStyle=o.stroke;ctx.lineJoin='round';ctx.strokeText(value,x,y);}
  ctx.fillStyle=color;ctx.fillText(value,x,y);ctx.restore();return actual;
}
function lines(value,x,y,size=60,color='#fff',width=800,leading=1.35){
  ctx.font=`800 ${size}px SocialSans,"PingFang SC",sans-serif`;let row='',rows=[];
  for(const ch of String(value)){if(ch==='\n'||ctx.measureText(row+ch).width>width){rows.push(row);row=ch==='\n'?'':ch;}else row+=ch;}if(row)rows.push(row);
  rows.forEach((r,i)=>text(r,x,y+i*size*leading,size,color,{maxWidth:width}));return rows.length;
}
function image(im,x,y,w,h,o={}){
  ctx.save();if(o.radius){round(x,y,w,h,o.radius);ctx.clip();}if(o.circle){ctx.beginPath();ctx.arc(x+w/2,y+h/2,Math.min(w,h)/2,0,TAU);ctx.clip();}
  if(o.blur)ctx.filter=`blur(${o.blur}px)`;ctx.globalAlpha=o.alpha??1;
  const sw=im.videoWidth||im.width,sh=im.videoHeight||im.height;
  const scale=Math.max(w/sw,h/sh)*(o.zoom||1),iw=sw*scale,ih=sh*scale;
  const ax=o.anchorX??.5,ay=o.anchorY??.4;ctx.drawImage(im,x+(w-iw)*ax,y+(h-ih)*ay,iw,ih);ctx.restore();
}
function speaker(x=0,y=0,w=W,h=H,o={}){image(presenterVideo||portrait,x,y,w,h,o);}
let outlinePoints;
function person(x,y,w,h,o={}){const im=cutout||portrait;ctx.save();ctx.globalAlpha=o.alpha??1;if(o.outline&&!o.dashed){ctx.shadowColor=o.outline;ctx.shadowBlur=2;for(const [dx,dy] of [[-8,0],[8,0],[0,-8],[0,8]])ctx.drawImage(im,x+dx,y+dy,w,h);}ctx.shadowColor='transparent';ctx.drawImage(im,x,y,w,h);if(o.dashed&&outlinePoints){ctx.strokeStyle=o.outline||'#fff';ctx.lineWidth=10;ctx.setLineDash([28,22]);ctx.beginPath();outlinePoints.forEach(([px,py],i)=>{if(i===0)ctx.moveTo(x+px*w,y+py*h);else ctx.lineTo(x+px*w,y+py*h);});ctx.closePath();ctx.stroke();ctx.setLineDash([]);}ctx.restore();}
function frame(x,y,w,h,draw,o={}){ctx.save();ctx.shadowColor='#0008';ctx.shadowBlur=30;ctx.shadowOffsetY=18;round(x,y,w,h,o.radius||30);fill(o.color||'#fff');ctx.shadowColor='transparent';round(x+8,y+8,w-16,h-16,o.radius||24);ctx.clip();draw(x+8,y+8,w-16,h-16);ctx.restore();}
function card(label,x,y,w=400,h=145,color='#ffd734',o={}){ctx.save();ctx.translate(x+w/2,y+h/2);ctx.rotate(o.angle||0);round(-w/2,-h/2,w,h,18);fill(color);text(label,0,0,o.size||68,o.ink||'#101820',{maxWidth:w-36,stroke:o.stroke});ctx.restore();}
function arcText(str,cx,cy,r,center=-Math.PI/2,span=1.7,size=58,color='#fff',o={}){
  const chars=Array.from(str),fitSize=Math.min(size,Math.abs(r*span)/chars.length*.76);chars.forEach((ch,i)=>{let angle=center-span/2+(i+.5)*span/chars.length;ctx.save();ctx.translate(cx+Math.cos(angle)*r,cy+Math.sin(angle)*r);ctx.rotate(angle+(center>0?-Math.PI/2:Math.PI/2));text(ch,0,0,fitSize,color,{maxWidth:100,...o});ctx.restore();});
}
function graphic(x,y,w,h,index=0){
  if(media.length){image(media[index%media.length],x,y,w,h,{radius:20});return;}
  ctx.save();round(x,y,w,h,22);ctx.clip();const palettes=[['#204478','#94c4df'],['#795c45','#f3d4a3'],['#195b4c','#a4dcc0']];let p=palettes[index%3];const g=ctx.createLinearGradient(x,y,x+w,y+h);g.addColorStop(0,p[0]);g.addColorStop(1,p[1]);ctx.fillStyle=g;ctx.fillRect(x,y,w,h);
  // An explicit original infographic stands in for project evidence, never a factual screenshot.
  ctx.fillStyle='#ffffff23';for(let i=0;i<6;i++)ctx.fillRect(x+w*.1+i*w*.13,y+h*(.72-i*.07),w*.09,h*(.2+i*.07));
  ctx.strokeStyle='#fbe47b';ctx.lineWidth=Math.max(4,w*.01);ctx.beginPath();for(let i=0;i<6;i++){let px=x+w*(.12+i*.15),py=y+h*(.7-.06*i-.1*Math.sin(i));if(i===0)ctx.moveTo(px,py);else ctx.lineTo(px,py);}ctx.stroke();text(S.evidence_labels?.[index%S.evidence_labels.length]||['流程','结果','案例'][index%3],x+w/2,y+h*.22,Math.min(58,w*.12),'#fff',{maxWidth:w*.8});ctx.restore();
}
function subtitle(t){if(!S.subtitle)return;card(S.subtitle,110,1640,860,110,'#101722dd',{size:44,ink:'#fff'});}
const animations={};
animations.d01_three_band=t=>{
  background('#151925',true);let a=gate(t,.15),b=gate(t,.8),c=gate(t,1.3);
  graphic(75,lerp(-450,90,a),930,480,0);graphic(75,lerp(1950,580,b),930,700,1);
  graphic(75,lerp(1960,1290,c),930,470,2);
  let d=gate(t,1.7,.45);person(lerp(200,100,d),lerp(1360,770,d),740*d,990*d,{alpha:d});
  if(t>2.2){card(S.title,125,650,830,120,S.accent,{size:70});card(S.detail,100,1550,880,110,'#fff',{size:46});}
};
animations.d02_word_tiles=t=>{
  speaker();const chars=Array.from(S.title);let cell=Math.min(175,850/chars.length),gap=10,x=(W-chars.length*(cell+gap)+gap)/2;
  chars.forEach((ch,i)=>{let p=gate(t,.2+i*.16,.32);if(p<=0)return;ctx.save();ctx.globalAlpha=p;let tx=lerp(540,x+i*(cell+gap)+cell/2,p),ty=lerp(670,1080,p);ctx.translate(tx,ty);ctx.scale(p,p);card(ch,-cell/2+8,-cell/2+12,cell,cell,'#82dc24',{size:Math.min(116,cell*.72),ink:'#82dc24'});card(ch,-cell/2,-cell/2,cell,cell,S.accent||'#1e9b67',{size:Math.min(116,cell*.72),ink:S.ink||'#fff'});ctx.restore();});subtitle(t);
};
animations.d03_evidence_over_speaker=t=>{
  background('#edeae1');let p=gate(t,.1);frame(80,170,920,1490,(x,y,w,h)=>{speaker(x,y,w,h,{blur:18*p});ctx.fillStyle=`rgba(0,0,0,${p*.36})`;ctx.fillRect(x,y,w,h);if(p>0){ctx.globalAlpha=p;graphic(x+25,y+20,w-50,h*.61,Math.floor(t/1.6));frame(x+w*.32,y+h*.68,w*.36,h*.26,(a,b,c,d)=>speaker(a,b,c,d),{color:'#fff'});ctx.globalAlpha=1;}});
  text(S.title,540,110,64,'#242830',{maxWidth:950});card(S.detail,120,1665,840,115,'#1d2838',{size:49,ink:'#fff'});
};
animations.d04_orbit_title=t=>{
  background(S.background||'#4d9990',true);let p=gate(t,.05,.7),r=lerp(740,310,p);
  ctx.save();ctx.beginPath();ctx.arc(540,850,r,0,TAU);ctx.clip();speaker(540-r,850-r,2*r,2*r,{anchorY:.18});ctx.restore();
  ctx.strokeStyle='#f4f5df';ctx.lineWidth=8;ctx.beginPath();ctx.arc(540,850,r,0,TAU);ctx.stroke();
  if(p>.6){arcText(S.title,540,850,r+83,-Math.PI/2,2.2,64,S.accent);if(t>2){const cs=Array.from(S.detail);arcText(cs.slice(0,12).join(''),540,850,r+75,Math.PI/2,-1.8,44,'#fff');if(cs.length>12)arcText(cs.slice(12).join(''),540,850,r+132,Math.PI/2,-1.8,44,'#fff');}}
};
animations.d05_focus_pip=t=>{
  let p=gate(t,.6,.75);speaker(0,0,W,H,{blur:p*24});ctx.fillStyle=`rgba(0,0,0,${p*.5})`;ctx.fillRect(0,0,W,H);
  let w=lerp(W,365,p),h=lerp(H,460,p),x=lerp(0,358,p),y=lerp(0,270,p);frame(x,y,w,h,(a,b,c,d)=>speaker(a,b,c,d),{color:'#f5f1e3'});
  if(t>1.7){let b=gate(t,1.7,.4);ctx.save();ctx.globalAlpha=b;frame(358,950,365,460,(a,c,d,e)=>speaker(a,c,d,e),{color:'#f5f1e3'});ctx.restore();}
  if(p>.5){ctx.globalAlpha=p;text(S.items?.[0]||S.title,540,790,49,S.accent,{maxWidth:900});if(t>1.7)text(S.items?.[1]||S.detail,540,1480,49,'#fff',{maxWidth:900});ctx.globalAlpha=1;}
};
animations.d06_frosted_chapter=t=>{
  let p=gate(t,.2,.55),exit=gate(t,3.2,.5);speaker(0,0,W,H,{blur:20*p*(1-exit)});ctx.save();ctx.globalAlpha=p*(1-exit);ctx.translate(0,exit*1400);
  round(150,400,780,1080,28);fill('#f4f7f7b5');text(S.label||'PART 01',280,510,46,'#323b4b',{align:'left',maxWidth:300});
  text(S.title,540,920,106,'#fff',{maxWidth:700,stroke:'#61666e',strokeWidth:5,shadow:true});text(S.detail,540,1070,49,'#fff',{maxWidth:680,shadow:true});ctx.restore();
};
animations.d07_iris_mask=t=>{
  background('#07080b');let p=gate(t,.2,.85),r=lerp(1130,315,p);ctx.save();ctx.beginPath();ctx.arc(540,860,r,0,TAU);ctx.clip();speaker(lerp(0,225,p),lerp(0,545,p),lerp(W,630,p),lerp(H,630,p),{anchorY:.12});ctx.restore();
  if(p>.8){ctx.strokeStyle='#f8e0b5';ctx.lineWidth=7;ctx.setLineDash([19,18]);ctx.lineDashOffset=0;ctx.beginPath();ctx.arc(540,860,r+15,0,TAU);ctx.stroke();ctx.setLineDash([]);arcText(S.title,540,860,r+92,-Math.PI/2,1.9,60);text(S.detail,540,1410,50,S.accent,{maxWidth:860});}
};
animations.d08_glass_stack=t=>{
  background('#14171c',true);const g=ctx.createLinearGradient(180,300,900,1550);g.addColorStop(0,'#ffffff18');g.addColorStop(.5,'#ffffff04');g.addColorStop(1,'#9bccff23');
  round(120,220,840,1450,70);fill(g);ctx.strokeStyle='#e2e9f189';ctx.lineWidth=4;ctx.stroke();ctx.strokeStyle='#fff';ctx.lineWidth=7;ctx.beginPath();ctx.moveTo(170,310);ctx.lineTo(170,570);ctx.stroke();
  text(S.title,540,390,83,'#fff',{maxWidth:720,shadow:true});(S.items||['整理素材','理解句意','动画编排']).forEach((item,i)=>{let p=gate(t,.35+i*.5,.5);if(!p)return;ctx.save();ctx.globalAlpha=p;frame(230,lerp(1550,620+i*260,p),620,180,(x,y,w,h)=>{const gg=ctx.createLinearGradient(x,y,x,y+h);gg.addColorStop(0,'#555092');gg.addColorStop(1,'#252341');ctx.fillStyle=gg;ctx.fillRect(x,y,w,h);text(item,x+w/2,y+h/2,60,'#fff',{maxWidth:w-50});},{color:'#ece6ff',radius:26});ctx.restore();});
};
animations.d09_editorial_type=t=>{
  speaker();ctx.fillStyle='#122c2060';ctx.fillRect(0,0,W,H);const items=S.items||[S.title,S.detail,'层级'];
  items.forEach((v,i)=>{let p=gate(t,.2+i*.45,.55);ctx.save();ctx.globalAlpha=p;let x=i===0?285:i===1?810:300,y=1070+i*260;text(v,lerp(x+(i%2?-150:150),x,p),y,120-i*20,i===1?S.accent:'#fff',{serif:i!==1,maxWidth:i===1?440:520,shadow:true});if(i===0){ctx.strokeStyle='#dfe9e133';ctx.lineWidth=2;ctx.strokeRect(40,960,490,230);}text(['MAIN POINT','DETAIL','STRUCTURE'][i],x,y+90,28,'#eff4e9',{maxWidth:420});ctx.restore();});
};
animations.d10_sticker_label=t=>{
  speaker();let p=gate(t,.4,.4),x=lerp(1600,540,p);ctx.save();ctx.translate(x,1100);ctx.rotate(-.055+Math.sin(t*2)*.008);round(-430,-95,860,190,8);fill('#4bdf28');round(-450,-120,860,190,8);fill(S.accent||'#14a46f');text(S.title,-20,-24,96,S.ink||'#fff',{maxWidth:800,stroke:'#0d252441',strokeWidth:5});ctx.restore();
  if(t>1.7){text(S.detail,540,1350,58,'#fff',{maxWidth:940,shadow:true});}
};
animations.d11_punch_caption=t=>{
  const p=gate(t,.5,.12),q=gate(t,2.6,.3);speaker(0,0,W,H,{zoom:1+.13*p-.1*q,anchorY:.31});
  ctx.save();let enter=gate(t,.55,.16);ctx.translate(540,1190);ctx.scale(lerp(1.4,1,enter),lerp(1.4,1,enter));ctx.globalAlpha=enter;text(S.title,0,0,117,S.accent,{maxWidth:900,shadow:true,stroke:'#1119',strokeWidth:5});ctx.restore();subtitle(t);
};
animations.d12_type_depth=t=>{
  background('#141514');const items=S.items||['理解句意','重建动作','检查成片'];
  ctx.save();ctx.translate(0,-t*24);for(let row=0;row<9;row++)for(let col=0;col<3;col++){ctx.globalAlpha=.23;text(items[(row+col)%3],col*450-90+(row%2)*100,row*240+120,92,'#e4d386',{maxWidth:440});}ctx.restore();
  items.forEach((v,i)=>{let e=gate(t,.3+i*.4);ctx.save();ctx.globalAlpha=e;let y=450+i*430;round(120,lerp(y+200,y,e),840,310,8);fill('#080b0be8');text('0'+(i+1),255,y+95,112,'#fff',{maxWidth:220});text('STEP',255,y+215,36,'#fff',{maxWidth:200});text(v,660,y+155,88,i===1?S.accent:'#fff',{maxWidth:530});ctx.restore();});
};
animations.d13_cutout_outline=t=>{
  speaker(0,0,W,H,{blur:22});ctx.fillStyle='#0a152680';ctx.fillRect(0,0,W,H);let p=gate(t,.2,.6);
  let q=gate(t,.05,.45);ctx.save();ctx.translate(0,lerp(-900,0,q));round(475,360,500,500,36);fill('#fff4ee');text('制作流程',725,440,50,'#1b2736',{maxWidth:440});text('图片 + 音频',725,555,49,'#53616d',{maxWidth:440});text('数字人口播',725,650,49,'#53616d',{maxWidth:440});text('本地动画编排',725,745,43,'#53616d',{maxWidth:440});ctx.restore();
  person(lerp(-800,30,p),850,700,940,{outline:'#fff',dashed:true});text(S.title,540,240,85,S.accent,{maxWidth:940,shadow:true});
  if(p>.6)arcText(S.question||'重点怎么呈现？',450,1290,450,-Math.PI/2,1.8,71,'#bfe4fa',{stroke:'#142638',strokeWidth:5});
  card(S.detail,85,1740,910,105,'#fff',{size:48});
};
animations.d14_collage_cards=t=>{
  background('#699b74');ctx.strokeStyle='#f9f2d999';ctx.lineWidth=4;ctx.strokeRect(60,260,960,1370);
  const positions=[[250,760,-.045],[540,850,.025],[820,700,.055]];
  positions.forEach(([x,y,a],i)=>{let p=gate(t,.08+i*.15,.5);ctx.save();ctx.translate(x,lerp(-700,y,p));ctx.rotate(a);frame(-155,-385,310,770,(xx,yy,w,h)=>{if(media.length)graphic(xx,yy,w,h,i);else speaker(xx,yy,w,h,{zoom:1+i*.15,anchorX:.3+i*.2});},{color:'#fff7d8',radius:25});ctx.restore();});
  text(S.title,540,1340,96,'#a11956',{maxWidth:890,serif:true});text(S.detail,540,1480,52,'#fff',{maxWidth:910});
};
animations.d15_behind_type=t=>{
  speaker(0,0,W,H,{blur:22});ctx.fillStyle='#14202bcc';ctx.fillRect(0,0,W,H);let p=gate(t,.25,.4);ctx.save();ctx.globalAlpha=p;ctx.translate(540,520);ctx.scale(lerp(.75,1,p),lerp(.75,1,p));text(S.title,0,0,200,S.accent||'#fff',{maxWidth:980,stroke:'#10131b',strokeWidth:10});ctx.restore();
  person(80,450,920,1227,S.outline?{outline:'#fff'}:{});
  card(S.detail,110,1540,860,125,'#101722e0',{size:49,ink:'#fff'});
};
animations.d16_floating_frame=t=>{
  background('#07080c');frame(265,280,550,790,(x,y,w,h)=>speaker(x,y,w,h),{radius:6});
  // The tutorial demonstrates a static frame plus icons, not an observed camera motion.
  for(let i=0;i<3;i++){const x=400+i*140;ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(x,1200,43,0,TAU);ctx.fill();round(x-58,1260,116,93,36);fill('#fff');}
  text(S.title,540,1450,80,S.accent,{maxWidth:930});text(S.detail,540,1570,48,'#fff',{maxWidth:920});
};
animations.d17_mask_reveal=t=>{
  background('#111b2a');speaker();let p=gate(t,.8,1.3);ctx.save();ctx.beginPath();if(S.direction==='left')ctx.rect(0,0,W*p,H);else{let q=p*.88+.12;ctx.rect(W*(1-q)/2,H*(1-q)/2,W*q,H*q);}ctx.clip();graphic(0,0,W,H,0);ctx.restore();
  text(S.title,540,200,86,S.accent,{maxWidth:950});card(S.detail,100,1510,880,130,'#fff',{size:52});
};
animations.d18_radial_orbit=t=>{
  background('#151a31');ctx.save();ctx.translate(540,890);ctx.strokeStyle='#dce8fa99';
  for(let i=0;i<56;i++){let a=i*TAU/56,r=220+(i%7)*40+(t*480%300);ctx.lineWidth=6+(i%4)*8;ctx.shadowColor='#e6fcff';ctx.shadowBlur=14;ctx.beginPath();ctx.moveTo(Math.cos(a)*r,Math.sin(a)*r*1.55);ctx.lineTo(Math.cos(a)*(r+120+(i%5)*45),Math.sin(a)*(r+120+(i%5)*45)*1.55);ctx.stroke();}
  ctx.restore();const z=lerp(.12,1,gate(t,.1,.45));person(540-310*z,1060-520*z,620*z,830*z);
  ctx.save();ctx.translate(540,1160);ctx.rotate(-.2);ctx.strokeStyle='#fff';ctx.lineWidth=7;ctx.beginPath();ctx.ellipse(0,0,480,160,0,0,TAU);ctx.stroke();let a=t*1.6;ctx.fillStyle=S.accent;ctx.beginPath();ctx.arc(Math.cos(a)*480,Math.sin(a)*160,14,0,TAU);ctx.fill();ctx.restore();
  text(S.title,540,350,96,S.accent,{maxWidth:950});text(S.detail,540,1450,52,'#fff',{maxWidth:920});
};
animations.d19_corner_keywords=t=>{
  speaker();const items=S.items||['内容','节奏','画面','声音'];
  [[210,370],[870,370],[210,1380],[870,1380]].forEach(([x,y],i)=>{text(items[i]||S.title,x,y,112,'#dcb567',{maxWidth:350,shadow:true,serif:true,stroke:'#69542a',strokeWidth:4});});
  text(S.detail,540,1630,48,'#fff',{maxWidth:920,shadow:true});
};
animations.d20_mosaic_relay=t=>{
  background('#acb7a0');for(let i=0;i<6;i++){let x=40+(i%3)*340,y=300+Math.floor(i/3)*850;frame(x,y,320,690,(a,b,w,h)=>{if(media.length)graphic(a,b,w,h,i+Math.floor(t/1.4));else speaker(a,b,w,h,{zoom:1+(i%3)*.2,anchorX:.15+(i%2)*.7});},{color:'#f4efdf',radius:10});}
  text(S.title,540,1080,87,S.accent,{maxWidth:950,stroke:'#111',strokeWidth:8});text(S.detail,540,1820,46,'#fff',{maxWidth:950});
};
animations.d21_shatter_type=t=>{
  speaker();text(S.detail,540,1520,52,'#fff',{maxWidth:910,shadow:true});let p=gate(t,1.35,.65);
  if(p===0){text(S.title,540,1070,145,S.accent,{maxWidth:960,stroke:'#172135',strokeWidth:10});return;}
  text(S.title,540,1070,145,S.accent,{maxWidth:960,stroke:'#172135',strokeWidth:10});
  const cw=980,ch=270,nx=8,ny=3;for(let y=0;y<ny;y++)for(let x=0;x<nx;x++){let i=y*nx+x,cx=50+(x+.5)*cw/nx,cy=935+(y+.5)*ch/ny,dx=(cx-540)*p*2.8,dy=(cy-1070)*p*3-p*280;ctx.save();ctx.translate(cx+dx,cy+dy);ctx.rotate((i%2?1:-1)*p*(.25+(i%5)*.18));ctx.globalAlpha=1-p;ctx.beginPath();ctx.moveTo(-cw/nx/2,-ch/ny/2);ctx.lineTo(cw/nx/2,-ch/ny/2+8);ctx.lineTo(cw/nx/2,ch/ny/2);ctx.lineTo(-cw/nx/2,ch/ny/2-8);ctx.clip();text(S.title,540-cx,1070-cy,145,S.accent,{maxWidth:960,stroke:'#172135',strokeWidth:10});ctx.restore();}
};
animations.d22_chart_overlay=t=>{
  speaker();let p=gate(t,.3,.5);ctx.save();ctx.globalAlpha=p;ctx.translate(0,lerp(180,0,p));round(150,960,780,490,20);fill('#130c15ec');text(S.title,540,1040,61,'#fff',{maxWidth:700});let values=S.values||[.75,.65,.55,.3,.18];ctx.strokeStyle=S.accent||'#ee4d45';ctx.shadowColor=ctx.strokeStyle;ctx.shadowBlur=24;ctx.lineWidth=10;ctx.beginPath();let q=clamp((t-.75)/1.4);for(let i=0;i<values.length;i++){let x=220+i*160,y=1400-values[i]*280;if(i===0)ctx.moveTo(x,y);else{let r=clamp(q*(values.length-1)-(i-1));if(r>0){let px=220+(i-1)*160,py=1400-values[i-1]*280;ctx.lineTo(lerp(px,x,r),lerp(py,y,r));}}}ctx.stroke();ctx.restore();text(S.detail,540,1570,48,'#fff',{maxWidth:940,shadow:true});
};
animations.d23_split_crack=t=>{
  speaker();const p=gate(t,.8,.25)*(1-gate(t,2.75,.25)),points=[[600,-20],[410,580],[640,880],[480,1230],[610,1530],[545,1940]];
  ctx.fillStyle='#000';ctx.beginPath();points.forEach(([x,y],i)=>{if(i===0)ctx.moveTo(x-p*170,y);else ctx.lineTo(x-p*170*(1-y/2200),y);});[...points].reverse().forEach(([x,y])=>ctx.lineTo(x+p*170*(1-y/2200),y));ctx.closePath();ctx.fill();
  text(S.title,540,1040,142,S.accent,{maxWidth:930,stroke:'#151b25',strokeWidth:8});text(S.detail,540,1640,51,'#fff',{maxWidth:940,shadow:true});
};
animations.d24_concept_presenter=t=>{
  speaker(0,0,W,H,{blur:30});ctx.fillStyle='#07080de0';ctx.fillRect(0,0,W,H);const light=ctx.createRadialGradient(340,660,10,340,660,400);light.addColorStop(0,'#b78349');light.addColorStop(1,'#0000');ctx.fillStyle=light;ctx.fillRect(0,200,750,1000);ctx.fillStyle='#0e1214';ctx.beginPath();ctx.arc(360,415,118,0,TAU);ctx.fill();ctx.beginPath();ctx.moveTo(245,545);ctx.quadraticCurveTo(155,580,155,790);ctx.lineTo(150,1050);ctx.lineTo(290,1050);ctx.lineTo(310,880);ctx.lineTo(365,880);ctx.lineTo(385,1050);ctx.lineTo(525,1050);ctx.lineTo(530,780);ctx.quadraticCurveTo(530,560,430,545);ctx.closePath();ctx.fill();
  Array.from(S.title).slice(0,8).forEach((ch,i)=>text(ch,760,300+i*95,78,'#d15d2d',{maxWidth:200}));
  person(240,960,660,880,{outline:'#fff'});card(S.detail,70,1720,940,115,'#f5d360',{size:47});
};
animations.d26_film_frame=t=>{
  background('#111');speaker(80,150,920,1590);ctx.fillStyle='#171819';ctx.fillRect(0,0,80,H);ctx.fillRect(1000,0,80,H);ctx.fillStyle='#ece8dc';
  for(let y=55;y<H;y+=105){round(22,y,36,65,5);ctx.fill();round(1022,y,36,65,5);ctx.fill();}
  const chars=Array.from(S.title).slice(0,8);chars.forEach((ch,i)=>text(ch,155,340+i*105,83,S.accent,{maxWidth:120,stroke:'#17191b',strokeWidth:5}));card(S.detail,175,1500,730,140,'#111d',{size:50,ink:'#fff'});
};
function wavy(x,y,w,h,phase=0){ctx.beginPath();const amp=9,step=12;for(let a=0;a<=w;a+=step){let xx=x+a,yy=y+Math.sin(a*.075+phase)*amp;if(a===0)ctx.moveTo(xx,yy);else ctx.lineTo(xx,yy);}for(let a=0;a<=h;a+=step)ctx.lineTo(x+w+Math.sin(a*.075+phase)*amp,y+a);for(let a=w;a>=0;a-=step)ctx.lineTo(x+a,y+h+Math.sin(a*.075+phase)*amp);for(let a=h;a>=0;a-=step)ctx.lineTo(x+Math.sin(a*.075+phase)*amp,y+a);ctx.closePath();}
animations.d27_wavy_frame=t=>{
  background('#07090b');text(S.title,540,190,77,'#fff',{maxWidth:950});let p=gate(t,.2,.6);ctx.save();ctx.translate(540,990);ctx.scale(lerp(1.3,1,p),lerp(1.3,1,p));wavy(-430,-590,860,1180,t*1.2);fill('#fbf8ed');wavy(-422,-582,844,1164,t*1.2);ctx.clip();graphic(-422,-582,844,1164,0);ctx.fillStyle='#0008';ctx.fillRect(-450,-610,900,1220);ctx.restore();text(S.label||'01',540,560,136,'#fff',{maxWidth:400});let q=gate(t,1.25,.4);person(140,lerp(1460,1120,q),330,440,{alpha:q,outline:'#fff'});text(S.detail,540,1650,44,'#fff',{maxWidth:760});
};
animations.d28_marker_sweep=t=>{
  background('#090b0e');text(S.detail,540,680,70,'#fff',{maxWidth:930});const p=gate(t,.3,.65);ctx.save();round(100,905,880*p,190,6);fill(S.accent||'#cfb36b');ctx.restore();text(S.title,540,1000,125,p>.98?'#161811':'#fff',{maxWidth:830});text('把真正的重点标出来',540,1270,44,'#b9bdb9',{maxWidth:920});
};
animations.d30_gallery_focus=t=>{
  background('#e9ece8');let cells=[];for(let i=0;i<9;i++){let x=45+(i%3)*335,y=320+Math.floor(i/3)*450;cells.push([x,y,320,430]);graphic(x,y,320,430,i);}
  let p=gate(t,.35,.35),s=(S.selected??2)+3*Math.min(2,Math.floor(Math.max(0,t-1)/1.05)),[x,y,w,h]=cells[s%9];ctx.save();ctx.beginPath();ctx.rect(0,280,W,1430);ctx.rect(x,y,w,h);ctx.fillStyle=`rgba(12,18,25,${p*.72})`;ctx.fill('evenodd');ctx.strokeStyle='#fff';ctx.lineWidth=4;ctx.strokeRect(x,y,w,h);ctx.restore();text(S.title,540,190,80,'#202933',{maxWidth:960});text(S.detail,540,1790,48,'#202933',{maxWidth:940});
};
async function loadImage(path){if(!path)throw Error('A staged portrait image is required');const im=new Image();im.src=path;await im.decode();return im;}
async function boot(){
  if(!S||!animations[S.grammar])throw Error('Missing spec or unknown social grammar');
  if(!S.title||!S.detail)throw Error('Title and detail are required');C.width=W;C.height=H;window.__canvas=C;
  portrait=await loadImage(S.portrait);if(S.cutout)cutout=await loadImage(S.cutout);if(['d01_three_band','d13_cutout_outline','d15_behind_type','d18_radial_orbit','d24_concept_presenter','d27_wavy_frame'].includes(S.grammar)&&!cutout)throw Error('Transparent cutout required; rectangular fallback rejected');
  if(cutout){const off=document.createElement('canvas');off.width=180;off.height=Math.round(180*cutout.height/cutout.width);const ox=off.getContext('2d');ox.drawImage(cutout,0,0,off.width,off.height);const a=ox.getImageData(0,0,off.width,off.height).data,left=[],right=[];for(let y=0;y<off.height;y+=2){let l=-1,r=-1;for(let x=0;x<180;x++)if(a[(y*180+x)*4+3]>128){if(l===-1)l=x;r=x;}if(l>=0){left.push([Math.max(0,l-2)/180,y/off.height]);right.push([Math.min(180,r+2)/180,y/off.height]);}}outlinePoints=[...left,...right.reverse()];}
  media=await Promise.all((S.images||[]).map(loadImage));await Promise.all([document.fonts.load('800 70px SocialSans'),document.fonts.load('800 70px SocialSerif')]);await document.fonts.ready;
  if(S.presenter_video){presenterVideo=document.createElement('video');presenterVideo.muted=true;presenterVideo.preload='auto';presenterVideo.src=S.presenter_video;await new Promise((resolve,reject)=>{presenterVideo.addEventListener('loadeddata',resolve,{once:true});presenterVideo.addEventListener('error',()=>reject(Error('Presenter video failed to load')),{once:true});});}
  window.__total=S.duration||4;window.prepare=async t=>{if(!presenterVideo)return;const target=Math.min((S.video_start||0)+Math.max(0,t),presenterVideo.duration-.001);if(Math.abs(presenterVideo.currentTime-target)<.0001)return;await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Presenter seek timed out')),10000);presenterVideo.addEventListener('seeked',()=>{clearTimeout(timer);resolve();},{once:true});presenterVideo.currentTime=target;});};
  window.renderFrame=t=>{ctx.save();ctx.clearRect(0,0,W,H);animations[S.grammar](Math.min(t,window.__total));ctx.restore();};
  window.renderFrame(0);window.__ready=true;
}
boot().catch(e=>{window.__bootFailed=String(e);console.error(e);});
