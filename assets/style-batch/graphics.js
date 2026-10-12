/* Eleven topic-specific graphic/digital art worlds. No author room/character. */
(() => {
'use strict';
const K=KS,R=window.KOUBO_STYLE_FACTORIES,W=1080,H=1920;
const P=(paper,ink,red,olive,gold,white)=>({paper,ink,red,olive,gold,white});
const palettes={
11:P('#b8a58a','#30241a','#8f482e','#7f8270','#a88c58','#e5d4b1'),
12:P('#eee5d2','#171614','#c72c26','#285aa0','#edbe25','#faf7eb'),
13:P('#f7e3a8','#151313','#d62632','#306bb8','#f4ce24','#fff9ef'),
14:P('#adc4a9','#172722','#b54037','#438561','#bd9b4c','#e8efcc'),
15:P('#568e89','#182e34','#b7534e','#438d85','#d5a953','#ecf6e7'),
16:P('#f4dfc8','#363932','#df6650','#628d75','#d9ae56','#fff7e6'),
22:P('#e8dbc0','#191715','#c93022','#606663','#9a8062','#f8efdc'),
26:P('#180a29','#17202b','#f960b2','#51d1ce','#eabb50','#eaffed'),
27:P('#ead5a9','#111316','#b93b38','#39727d','#eebd32','#fff8da'),
31:P('#f2bd26','#131511','#e24431','#16815f','#ee803a','#fff3bf'),
33:P('#e9dec2','#242321','#6f6559','#827b6c','#afa28b','#f8efdb')};
function base(p){return {palette:p,background(g,t,s){g.fillStyle=p.paper;g.fillRect(0,0,W,H);},plate(g,w,h,col){g.fillStyle=col;g.fillRect(0,0,w,h);}};}
function line(g,pts,col,lw){K.path(g,pts,false);g.strokeStyle=col;g.lineWidth=lw;g.lineCap='round';g.lineJoin='round';g.stroke();}
function poly(g,pts,col){K.path(g,pts);g.fillStyle=col;g.fill();}
function circle(g,x,y,r,col){g.beginPath();g.arc(x,y,r,0,Math.PI*2);g.fillStyle=col;g.fill();}
function tile(g,id,col,fn,size=96){return K.pattern(g,id+':'+col,size,size,q=>{q.fillStyle=col;q.fillRect(0,0,size,size);fn(q,size);});}
function dots(q,n,pitch,col,r){q.fillStyle=col;q.beginPath();for(let y=-pitch;y<n+pitch;y+=pitch/2)for(let x=-pitch;x<n+pitch;x+=pitch){q.moveTo(x+((Math.round(y/(pitch/2))%2)*pitch/2)+r,y);q.arc(x+((Math.round(y/(pitch/2))%2)*pitch/2),y,r,0,Math.PI*2);}q.fill();}
function rays(g,x,y,t,col,count=12,range=130,lw=6){g.save();for(let i=0;i<count;i++){let a=i/count*Math.PI*2+.025*Math.floor(t*8)%1;line(g,[[x+Math.cos(a)*range,y+Math.sin(a)*range],[x+Math.cos(a)*(range+22+9*Math.sin(t*7+i)),y+Math.sin(a)*(range+22+9*Math.sin(t*7+i))]],col,lw);}g.restore();}
function frameMotif(g,p,x,y,t,kind=0){g.save();g.translate(x,y);g.rotate(Math.sin(t*2+kind)*.09);g.strokeStyle=p.ink;g.lineWidth=5;g.strokeRect(-58,-43,116,86);for(let i=0;i<4;i++){g.fillStyle=p.gold;g.fillRect(-48+i*25,-35,11,8);g.fillRect(-48+i*25,27,11,8);}g.restore();}
function panelDots(g,id,p,col,w,h){g.save();g.fillStyle=tile(g,id,col,(q,n)=>dots(q,n,16,K.alpha(p.ink,.17),2.7));g.fillRect(0,0,w,h);g.restore();}
function register(id,name,style,meta){style.id=id;style.name=name;style.metadata=meta;R[id]=()=>style;}
{
let p=palettes[11],s=base(p);
s.background=(g,t,shot)=>{g.fillStyle=p.paper;g.fillRect(0,0,W,H);let r=K.rng(711);for(let i=0;i<34;i++){let x=r()*W,y=r()*1550,w=160+r()*390,h=170+r()*400,dx=Math.sin(t*.7+i)*7;let pts=[[x+dx,y],[x+w,y+70],[x+w*.78,y+h],[x-45,y+h*.7]];let gr=g.createLinearGradient(x,y,x+w,y+h);gr.addColorStop(0,K.alpha(p.white,.33));gr.addColorStop(1,K.alpha(i%3?p.ink:p.gold,.28));K.path(g,pts);g.fillStyle=gr;g.fill();g.strokeStyle=K.alpha(p.ink,.4);g.lineWidth=2;g.stroke();}g.drawImage(K.cached('cub:bggrain',W,1550,q=>K.grain(q,W,1550,15000,15,.15)),0,0);};
s.pattern=(g,col)=>tile(g,'cub',col,(q,n)=>{let r=K.rng(col);for(let i=0;i<10;i++){poly(q,[[r()*n,r()*n],[r()*n,r()*n],[r()*n,r()*n]],K.alpha(i%2?p.ink:p.white,.16));}K.hatch(q,n,n,K.alpha(p.ink,.16),15,-.5,1.5);},160);
s.plate=(g,w,h,col,seed,t)=>{let pts=[[0,6],[w*.96,-7],[w,h*.85],[w*.91,h],[2,h*.98]];K.path(g,pts);g.fillStyle=s.pattern(g,col);g.fill();g.strokeStyle=p.ink;g.lineWidth=4;g.stroke();g.save();g.clip();let rr=K.rng(seed);for(let i=0;i<5;i++)poly(g,[[w*rr(),0],[w*rr(),h],[w*rr(),h*.46]],K.alpha(i%2?p.gold:p.ink,.13));g.restore();};
s.line=(g,pts,col,lw)=>{line(g,pts,col,lw);if(pts.length<20){g.save();g.translate(7,-4);line(g,pts,K.alpha(col,.3),Math.max(1,lw*.3));g.restore();}};
s.motifs=(g,t,shot)=>{for(let i=0;i<3;i++){g.save();g.translate(70+i*465,180+i%2*100);g.rotate(.15+i*.22);frameMotif(g,p,Math.sin(t*4+i)*8,0,t,i);g.restore();}};
register('11_cubism','分析立体主义',s,{mechanism:'半透明渐变切面、深褐大面、木纹与排线；对象多视角错线',topic_adaptation:'文稿与剪辑板成为分裂后重新拼合的平面，真实人物保留照片',motifs:'底片的不同视角缓错位、空间切面轻移',limitations:'二维平面重建，不改变真实人物五官形体'});
}
{
let p=palettes[12],s=base(p);
s.background=(g,t,shot)=>{g.fillStyle=p.paper;g.fillRect(0,0,W,H);poly(g,[[0,1320],[1080,940],[1080,1570],[0,1570]],p.gold);circle(g,870,280,182,p.red);g.save();g.translate(140,320);g.rotate(-.65+.22*Math.sin(t*.9));g.fillStyle=p.ink;g.fillRect(-16,-210,32,540);circle(g,0,0,43,p.olive);circle(g,0,0,13,p.white);g.restore();g.fillStyle=K.alpha(p.olive,.35);g.fillRect(0,0,62,1560);for(let i=0;i<5;i++){g.strokeStyle=p.ink;g.lineWidth=3;g.beginPath();g.arc(900,280,205+i*24,Math.PI*.3,Math.PI*.9+Math.sin(t*.8)*.06);g.stroke();}g.drawImage(K.cached('bau:grain',W,H,q=>K.grain(q,W,H,9000,16,.065)),0,0);};
s.plate=(g,w,h,col)=>{g.fillStyle=col;g.fillRect(0,0,w,h);g.strokeStyle=p.ink;g.lineWidth=6;g.strokeRect(0,0,w,h);g.fillStyle=p.red;g.fillRect(0,0,Math.min(14,w*.1),h);};
s.clock=(g,x,y,r,hand,t)=>{g.save();g.translate(x,y);circle(g,0,0,r,p.gold);circle(g,0,0,r*.8,p.paper);for(let i=0;i<12;i++){let a=i*Math.PI/6;circle(g,Math.sin(a)*r*.65,-Math.cos(a)*r*.65,5,p.ink);}line(g,[[Math.sin(hand)*r*.15,Math.cos(hand)*r*.15],[-Math.sin(hand)*r*.56,-Math.cos(hand)*r*.56]],p.ink,12);line(g,[[0,0],[Math.sin(hand*2)*r*.7,-Math.cos(hand*2)*r*.7]],p.red,8);circle(g,0,0,15,p.olive);g.restore();return true;};
s.motifs=(g,t,shot)=>{let lt=t-shot.start;g.save();g.translate(918,1470);g.rotate(Math.min(.5,lt)*.6);poly(g,[[-40,25],[40,25],[0,-43]],p.red);g.restore();};
register('12_bauhaus','包豪斯几何',s,{mechanism:'原色圆方三角、等粗杆和关节盘、石版颗粒',topic_adaptation:'编辑流程与时钟重塑为有精确比例的机械几何',motifs:'转轴杆、同心弧、三角卡点',limitations:'保留口播照片，人物没有转成人偶'});
}
{
let p=palettes[13],s=base(p);
s.background=(g,t,shot)=>{g.fillStyle=tile(g,'pop:bg',p.white,(q,n)=>dots(q,n,24,K.alpha(p.olive,.55),4.5));g.fillRect(0,0,W,H);poly(g,[[0,1380],[W,1180],[W,1570],[0,1570]],p.gold);let a=22+Math.sin(t*8)*7;poly(g,[[920,80],[840,330],[920,320],[830,550],[1030,275],[955,292],[1040,80]],p.red);g.strokeStyle=p.ink;g.lineWidth=10;g.stroke();};
s.pattern=(g,col)=>tile(g,'pop',col,(q,n)=>dots(q,n,16,K.alpha(p.ink,.25),3));
s.plate=(g,w,h,col)=>{g.fillStyle=s.pattern(g,col);g.fillRect(0,0,w,h);g.strokeStyle=p.ink;g.lineWidth=8;g.strokeRect(0,0,w,h);line(g,[[15,15],[w*.3,15]],p.white,7);};
s.line=(g,pts,col,lw)=>line(g,pts,col,Math.max(4,lw*1.25));
s.motifs=(g,t,shot)=>{if(shot.presenter==='main')return;for(let i=0;i<3;i++){let b=(Math.floor(t*12)-2*i)%12;circle(g,82+i*30,200-(b<4?8:0),b<4?11:7,p.ink);}rays(g,990,1400,t,p.ink,8,43,5);};
register('13_pop','波普漫画',s,{mechanism:'本戴点印刷纹、粗黑轮廓、平涂与白高光',topic_adaptation:'剪辑物件变成漫画道具，关键事件配短动作线',motifs:'闪电、轮流跳起的点、爆发动作线',limitations:'不添加拟声大字遮挡内容'});
}
{
let p=palettes[14],s=base(p);s.pixelWorld=true;s.timeQuant=12;
s.background=(g,t,shot)=>{g.fillStyle=p.paper;g.fillRect(0,0,W,H);g.fillStyle=p.olive;for(let y=0;y<1550;y+=96)for(let x=(y/96)%2?48:0;x<W;x+=96){g.fillRect(x,y,8,24);g.fillRect(x-8,y+8,24,8);}g.fillStyle=p.ink;g.fillRect(0,1400,W,160);for(let i=0;i<14;i++){g.fillStyle=i%2?p.gold:p.olive;g.fillRect(i*80,1440,72,96);}let phase=Math.floor(t*12)%4;for(let k=0;k<6;k++){g.fillStyle=p.white;g.fillRect(120+k*156+phase*8,118,32,16);} };
s.plate=(g,w,h,col)=>{let n=8;g.fillStyle=p.ink;g.fillRect(-n,-n,w+n*2,h+n*2);g.fillStyle=col;g.fillRect(0,0,w,h);g.fillStyle=p.white;g.fillRect(n,n,w-n*2,n);g.fillStyle=K.shade(col,-.22);g.fillRect(n,h-n*2,w-n*2,n);};
s.line=(g,pts,col,lw)=>{line(g,pts.map(([x,y])=>[Math.round(x/8)*8,Math.round(y/8)*8]),col,Math.max(8,Math.round(lw/8)*8));};
s.motifs=(g,t,shot)=>{for(let k=0;k<3;k++){let y=260-k*36-Math.floor(t*12)%4*8;g.fillStyle=k===Math.floor(t*2)%3?p.red:p.gold;g.fillRect(36,y,16,16);} };
register('14_8bit','8-bit像素游戏',s,{mechanism:'图形世界135×240低分辨率放大，像素轮廓与12fps对象步进',topic_adaptation:'文稿、轨道、剪刀、胶卷成为像素道具；人物采用清晰实拍插入',motifs:'像素状态点与块状云移动',limitations:'保护真实照片、关键中文标签和字幕清晰；道具仍保持像素轮廓与步进'});
}
{
let p=palettes[15],s=base(p);
s.background=(g,t,shot)=>{let gr=g.createRadialGradient(280,330,60,580,730,1400);gr.addColorStop(0,'#a6c5a8');gr.addColorStop(1,p.paper);g.fillStyle=gr;g.fillRect(0,0,W,H);let horizon=1050;g.save();g.beginPath();g.rect(0,horizon,W,510);g.clip();for(let j=0;j<10;j++){let a=1/(j+1),b=1/(j+2),y=horizon+a*850,y2=horizon+b*850;for(let i=-6;i<7;i++){poly(g,[[540+i*a*550,y],[540+(i+1)*a*550,y],[540+(i+1)*b*550,y2],[540+i*b*550,y2]],(i+j)%2?p.ink:p.white);}}g.restore();let x=920,y=270,r=110;gr=g.createRadialGradient(x-38,y-45,2,x,y,r);gr.addColorStop(0,p.white);gr.addColorStop(.28,'#8da7a2');gr.addColorStop(.49,'#172a31');gr.addColorStop(.54,'#e3d5ab');gr.addColorStop(.79,'#627879');gr.addColorStop(1,p.ink);g.fillStyle=gr;g.beginPath();g.arc(x,y,r,0,Math.PI*2);g.fill();line(g,[[x-r*.68,y+8*Math.sin(t*2)],[x+r*.67,y+8*Math.sin(t*2)]],K.alpha(p.white,.5),6);};
s.pattern=(g,col)=>tile(g,'ray',col,(q,n)=>{let gr=q.createLinearGradient(0,0,n,n);gr.addColorStop(0,K.shade(col,-.3));gr.addColorStop(.23,K.mix(col,p.white,.68));gr.addColorStop(.42,col);gr.addColorStop(1,K.shade(col,-.35));q.fillStyle=gr;q.fillRect(0,0,n,n);q.fillStyle='rgba(255,255,255,.3)';q.beginPath();q.ellipse(24,18,14,6,-.4,0,Math.PI*2);q.fill();},160);
s.plate=(g,w,h,col)=>{let gr=g.createLinearGradient(0,0,w,h);gr.addColorStop(0,K.shade(col,-.2));gr.addColorStop(.2,K.mix(col,p.white,.7));gr.addColorStop(.5,col);gr.addColorStop(1,K.shade(col,-.32));g.fillStyle=gr;g.beginPath();g.roundRect(0,0,w,h,Math.min(24,w*.04,h*.04));g.fill();line(g,[[15,h*.12],[w*.84,h*.07]],K.alpha(p.white,.6),5);};
s.motifs=(g,t,shot)=>{g.save();g.translate(120,270);g.rotate(t*.4);g.strokeStyle=p.gold;g.lineWidth=5;g.beginPath();g.ellipse(0,0,85,25,0,0,Math.PI*2);g.stroke();g.restore();};
register('15_raytrace','早期光追CGI',s,{mechanism:'塑料Phong约定的高光暗边、镜面铬球、透视棋盘',topic_adaptation:'编辑设备与文稿托板改为带体积的塑料模块',motifs:'环旋转、环境反射高光滑动',limitations:'Canvas二维着色模拟，不是物理光追'});
}
{
let p=palettes[16],s=base(p);
s.background=(g,t,shot)=>{g.fillStyle=p.paper;g.fillRect(0,0,W,H);let lt=t-shot.start,damp=Math.sin(lt*13)*Math.exp(-lt*2.8);g.save();g.translate(900,220);g.rotate(.12+damp*.08);poly(g,[[-160,-160],[190,-115],[175,245],[-155,215]],p.gold);g.restore();poly(g,[[0,1260],[W,1410],[W,1570],[0,1570]],K.mix(p.olive,p.paper,.5));g.drawImage(K.cached('flat:grain',W,H,q=>K.grain(q,W,H,35000,80,.055)),0,0);};
s.pattern=(g,col)=>tile(g,'flat',col,(q,n)=>K.grain(q,n,n,900,82,.12),160);
s.plate=(g,w,h,col)=>{g.fillStyle=s.pattern(g,col);g.beginPath();g.roundRect(0,0,w,h,Math.min(22,w*.07,h*.07));g.fill();};
s.line=(g,pts,col,lw)=>line(g,pts,col,Math.max(2,lw*.65));
s.motifs=(g,t,shot)=>{let lt=t-shot.start,k=Math.sin(lt*13)*Math.exp(-lt*3);for(let i=0;i<3;i++){g.save();g.translate(70+i*464,260+(i%2)*70);g.rotate(.2+k*.16);poly(g,[[-15,-24],[25,-7],[10,25],[-25,7]],i%2?p.red:p.olive);g.restore();}};
register('16_2026','当代颗粒扁平插画',s,{mechanism:'无重轮廓块面、密度颗粒与阻尼跟随动作',topic_adaptation:'文稿和工具变成柔和编辑物件，镜头撞击后道具轻回弹',motifs:'事件后的阻尼纸片与灯形色块',limitations:'照片保留自然画面，图形仅有限颗粒'});
}
{
let p=palettes[22],s=base(p);
s.background=(g,t,shot)=>{g.fillStyle=p.paper;g.fillRect(0,0,W,H);circle(g,900,300,210,p.ink);let q=.5-.5*Math.cos(t*2.2);poly(g,[[650+q*60,60],[1040,470],[880,480]],p.red);poly(g,[[0,1110],[1080,1440],[1080,1570],[0,1570]],p.red);line(g,[[0,1070],[1080,1410]],p.ink,11);g.save();g.translate(34,290);g.rotate(-.3);g.fillStyle=p.ink;g.fillRect(0,0,60,1000);g.restore();g.drawImage(K.cached('con:grain',W,H,q=>K.grain(q,W,H,16000,72,.09)),0,0);g.save();g.translate(900,300);g.setLineDash([35,18]);g.lineDashOffset=-t*160;g.strokeStyle=p.red;g.lineWidth=6;g.beginPath();g.arc(0,0,236,0,Math.PI*2);g.stroke();g.restore();};
s.photoFilter='grayscale(1)';s.pattern=(g,col)=>tile(g,'con',col,(q,n)=>dots(q,n,14,K.alpha(p.ink,.19),2.4));
s.plate=(g,w,h,col)=>{g.fillStyle=s.pattern(g,col);g.fillRect(0,0,w,h);poly(g,[[0,0],[w*.12,0],[0,h*.18]],p.red);g.strokeStyle=p.ink;g.lineWidth=3;g.strokeRect(0,0,w,h);};
s.line=(g,pts,col,lw)=>line(g,pts,col,lw*1.12);
s.motifs=(g,t,shot)=>{if(shot.presenter==='main')return;for(let k=0;k<3;k++){let r=28+((t*.5+k/3)%1)*140;g.strokeStyle=K.alpha(p.red,1-r/185);g.lineWidth=5;g.beginPath();g.arc(40,1280,r,-.5,.5);g.stroke();}};
register('22_constructivism','俄国构成主义',s,{mechanism:'灰度真实照片拼贴、印刷网点、红楔黑圆、斜构图',topic_adaptation:'将剪辑材料变成工程宣传拼贴，红楔指向流程事件',motifs:'红楔刺入、虚线滚动、声音传播弧',limitations:'没有复用作者人物或原海报文字'});
}
{
let p=palettes[26],s=base(p);
s.background=(g,t,shot)=>{let gr=g.createLinearGradient(0,0,0,1550);gr.addColorStop(0,p.paper);gr.addColorStop(1,'#3f1640');g.fillStyle=gr;g.fillRect(0,0,W,H);g.save();g.translate(875,300);gr=g.createLinearGradient(0,-160,0,160);gr.addColorStop(0,p.gold);gr.addColorStop(.5,p.red);gr.addColorStop(1,'#823355');g.beginPath();g.arc(0,0,166,0,Math.PI*2);g.clip();g.fillStyle=gr;g.fillRect(-166,-166,332,332);g.fillStyle=p.paper;for(let i=0;i<8;i++){let y=-20+i*30-(t*9%30);g.fillRect(-180,y,360,4+i*1.2);}g.restore();g.strokeStyle=K.alpha(p.olive,.5);g.lineWidth=3;g.beginPath();for(let i=-6;i<7;i++){g.moveTo(540,1060);g.lineTo(540+i*190,1560);}for(let i=0;i<8;i++){let y=1060+520/(i+1-(t*.7%1));g.moveTo(0,y);g.lineTo(W,y);}g.stroke();};
s.pattern=(g,col)=>tile(g,'vapor',col,(q,n)=>{let gr=q.createLinearGradient(0,0,n,n);gr.addColorStop(0,K.shade(col,-.25));gr.addColorStop(1,col);q.fillStyle=gr;q.fillRect(0,0,n,n);q.fillStyle='rgba(0,0,0,.08)';for(let y=0;y<n;y+=4)q.fillRect(0,y,n,1);});
s.plate=(g,w,h,col)=>{g.fillStyle=K.mix(col,p.paper,.22);g.fillRect(0,0,w,h);g.strokeStyle=p.olive;g.lineWidth=3;g.strokeRect(0,0,w,h);g.strokeStyle=p.red;g.strokeRect(4,3,w,h);line(g,[[12,12],[w-12,12]],K.alpha(p.white,.45),2);};
s.line=(g,pts,col,lw)=>{g.save();g.shadowColor=col;g.shadowBlur=5;line(g,pts,col,lw);g.shadowBlur=0;line(g,pts,K.mix(col,p.white,.45),Math.max(1,lw*.25));g.restore();};
s.after=(g,t,shot)=>{g.save();g.beginPath();g.rect(0,0,W,1560);g.clip();g.fillStyle=tile(g,'vhsScan','rgba(0,0,0,0)',(q,n)=>{q.fillStyle='rgba(0,0,0,.07)';for(let y=0;y<n;y+=4)q.fillRect(0,y,n,1);},32);g.fillRect(0,0,W,1560);let y=(t*80)%1540;g.fillStyle='rgba(238,255,255,.055)';g.fillRect(0,y,W,10);g.restore();};
s.motifs=(g,t,shot)=>{let x=70,y=220+(t*30%150);line(g,[[x,y],[x+45,y]],p.olive,3);line(g,[[x+55,y+10],[x+85,y+10]],p.red,3);};
register('26_vaporwave','蒸汽波霓虹',s,{mechanism:'落日切条、滚动透视网格、双灯管轮廓与VHS扫描纹',topic_adaptation:'剪辑设备成为复古电子桌面，保护真实照片和字幕',motifs:'落日条上滚、网格前滚、轻跟踪线',limitations:'用户明确请求35画风包含蓝紫，按原门禁记录例外；未全屏严重色差'});
}
{
let p=palettes[27],s=base(p);
s.background=(g,t,shot)=>{g.fillStyle=p.paper;g.fillRect(0,0,W,H);let center=[860,270];for(let i=0;i<26;i++){let a=i/26*Math.PI*2,da=.018;poly(g,[[center[0]+Math.cos(a)*130,center[1]+Math.sin(a)*130],[center[0]+Math.cos(a-da)*1350,center[1]+Math.sin(a-da)*1350],[center[0]+Math.cos(a+da)*1350,center[1]+Math.sin(a+da)*1350]],i%2?K.alpha(p.ink,.38):K.alpha(p.red,.24));}g.fillStyle=tile(g,'kirby:bg',p.gold,(q,n)=>dots(q,n,18,K.alpha(p.red,.22),3.5));g.fillRect(0,1310,W,250);};
s.pattern=(g,col)=>tile(g,'kirby',col,(q,n)=>{q.save();q.translate(4,3);dots(q,n,14,K.alpha(p.red,.24),2.4);q.restore();K.hatch(q,n,n,K.alpha(p.ink,.17),20,-1,2);});
s.plate=(g,w,h,col)=>{g.save();g.translate(4,3);g.fillStyle=s.pattern(g,col);g.fillRect(0,0,w,h);g.restore();g.strokeStyle=p.ink;g.lineWidth=7;g.strokeRect(0,0,w,h);g.save();g.beginPath();g.rect(0,0,w,h);g.clip();poly(g,[[w,0],[w,h],[w*.78,h],[w*.91,h*.2]],p.ink);K.hatch(g,w,h,K.alpha(p.ink,.26),20,-1,2);g.restore();};
s.line=(g,pts,col,lw)=>line(g,pts,col,Math.max(4,lw*1.4));
s.motifs=(g,t,shot)=>{if(shot.presenter==='main')return;let rr=K.rng(12);for(let k=0;k<3;k++){let x=45+(k%2)*975,y=430+k*400;for(let i=0;i<17;i++){let a=rr()*Math.PI*2,d=rr()*60;circle(g,x+Math.cos(a)*d,y+Math.sin(a)*d,5+(1-d/65)*11*(1+.09*Math.sin(Math.floor(t*12)/12*13+i)),p.ink);}}};
register('27_kirby','Kirby银河漫画',s,{mechanism:'四色印刷错位、黑块阴影与羽化排线、夸张放射透视',topic_adaptation:'剪辑板和文稿成为立体积木块，强调剪切和落轨事件',motifs:'Kirby krackle能量簇、透视速度线',limitations:'道具漫画化，保留真人照片；未模拟超级英雄人物'});
}
{
let p=palettes[31],s=base(p);s.timeQuant=8;
s.background=(g,t,shot)=>{g.fillStyle=p.paper;g.fillRect(0,0,W,H);g.fillStyle=p.olive;g.fillRect(0,1340,W,220);line(g,[[0,1340],[W,1340]],p.ink,13);for(let k=0;k<4;k++){let x=80+(k%2)*930,y=200+Math.floor(k/2)*920;let q=Math.floor(t*8)%4;rays(g,x,y,q*.11,p.ink,6,38,8);}};
s.plate=(g,w,h,col)=>{g.fillStyle=col;g.beginPath();g.roundRect(0,0,w,h,Math.min(25,h*.1,w*.1));g.fill();g.strokeStyle=p.ink;g.lineWidth=11;g.stroke();};
s.line=(g,pts,col,lw)=>line(g,pts,col,Math.max(8,Math.min(13,lw*1.5)));
s.motifs=(g,t,shot)=>{let q=Math.floor(t*8)/8;for(let k=0;k<2;k++){let y=300+k*920,b=Math.abs(Math.sin(q*128/60*Math.PI+k));frameMotif(g,p,65+k*950,y-22*b,q,k);rays(g,65+k*950,y-22*b,q,p.ink,6,80,7);}};
register('31_haring','哈林街头线描',s,{mechanism:'等粗圆头黑线、饱和平涂、8fps硬切动作',topic_adaptation:'电影底片和剪刀成为街头动作符号，不代码画新小人',motifs:'放射动作线与卡拍跃动底片',limitations:'不采用原样跳舞人，仅把动作语言移到编辑道具'});
}
{
let p=palettes[33],s=base(p);s.timeQuant=12;s.elastic=true;s.photoFilter='grayscale(1)';
s.background=(g,t,shot)=>{g.fillStyle=p.paper;g.fillRect(0,0,W,H);g.fillStyle=K.alpha(p.ink,.06);for(let x=0;x<W;x+=84)g.fillRect(x,0,16,1540);let gr=g.createRadialGradient(540,720,220,540,720,1050);gr.addColorStop(0,'rgba(0,0,0,0)');gr.addColorStop(1,K.alpha(p.ink,.25));g.fillStyle=gr;g.fillRect(0,0,W,1570);g.strokeStyle=K.alpha(p.ink,.2);g.lineWidth=3;g.strokeRect(25,35,W-50,1500);};
s.plate=(g,w,h,col)=>{g.fillStyle=col;g.beginPath();g.roundRect(0,0,w,h,Math.min(w*.1,h*.1,28));g.fill();g.strokeStyle=p.ink;g.lineWidth=6;g.stroke();};
s.line=(g,pts,col,lw)=>{if(pts.length<8&&pts.length>2){g.beginPath();g.moveTo(...pts[0]);for(let i=1;i<pts.length-1;i++){let a=pts[i],b=pts[i+1];g.quadraticCurveTo(a[0],a[1],(a[0]+b[0])/2,(a[1]+b[1])/2);}g.lineTo(...pts.at(-1));g.strokeStyle=col;g.lineWidth=Math.max(5,lw);g.lineCap='round';g.stroke();}else line(g,pts,col,lw);};
s.motifs=(g,t,shot)=>{let q=Math.floor(t*12)/12,b=Math.abs(Math.sin(q*128/60*Math.PI));for(let k=0;k<2;k++){g.save();g.translate(75+k*930,340+850*k);g.scale(1+.08*(1-b),1-.09*(1-b));frameMotif(g,p,0,-30*b,q,k);g.restore();}};
s.after=(g,t,shot)=>{g.save();g.beginPath();g.rect(0,0,W,1560);g.clip();let rr=K.rng(10+Math.floor(t*6));g.strokeStyle=K.alpha(p.ink,.16);g.lineWidth=1;for(let i=0;i<3;i++){let x=rr()*W;g.beginPath();g.moveTo(x,0);g.lineTo(x+2,1560);g.stroke();}g.fillStyle=K.alpha(p.white,.015+.012*Math.sin(t*24));g.fillRect(0,0,W,1560);g.restore();};
register('33_rubberhose','1930橡皮管卡通',s,{mechanism:'单色老胶片、12fps步进、道具绕落地点挤压拉伸',topic_adaptation:'手机、底片、剪辑工具成为弹性卡通道具；保留灰度真人',motifs:'错拍弹跳、弯线、细划痕',limitations:'不画派切眼或白手套人物，运动来自实际道具而非噪声'});
}
})();
