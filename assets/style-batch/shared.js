(() => {
'use strict';
window.KOUBO_STYLE_FACTORIES=window.KOUBO_STYLE_FACTORIES||{};
const cache=new Map();
function rgb(col){if(Array.isArray(col))return col;let s=String(col);if(s.startsWith('#')){s=s.slice(1);if(s.length===3)s=s.split('').map(x=>x+x).join('');return [parseInt(s.slice(0,2),16),parseInt(s.slice(2,4),16),parseInt(s.slice(4,6),16)];}let m=s.match(/[\d.]+/g);return m?m.slice(0,3).map(Number):[0,0,0];}
function mix(a,b,q){a=rgb(a);b=rgb(b);return '#'+a.map((v,i)=>Math.max(0,Math.min(255,Math.round(v+(b[i]-v)*q))).toString(16).padStart(2,'0')).join('');}
function rng(seed){let a=typeof seed==='number'?seed:[...String(seed)].reduce((s,c)=>Math.imul(s^c.charCodeAt(0),16777619),2166136261);return()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
function cached(key,w,h,fn){if(!cache.has(key)){let c=document.createElement('canvas');c.width=Math.max(1,Math.round(w));c.height=Math.max(1,Math.round(h));let g=c.getContext('2d');fn(g,c);cache.set(key,c);}return cache.get(key);}
function path(g,pts,closed=true){g.beginPath();pts.forEach(([x,y],i)=>i?g.lineTo(x,y):g.moveTo(x,y));if(closed)g.closePath();}
window.KS={rgb,rng,mix,shade:(c,d)=>mix(c,d<0?'#000000':'#ffffff',Math.min(1,Math.abs(d))),alpha:(c,a)=>`rgba(${rgb(c).join(',')},${a})`,rgba:(c,a)=>`rgba(${rgb(c).join(',')},${a})`,cached,pattern:(g,k,w,h,fn)=>g.createPattern(cached(k,w,h,fn),'repeat'),path,
 grain(g,w,h,n,seed,alpha=.1){let r=rng(seed);g.save();g.fillStyle=`rgba(0,0,0,${alpha})`;for(let i=0;i<n;i++){let sz=.5+r()*2;g.fillRect(r()*w,r()*h,sz,sz);}g.restore();},
 hatch(g,w,h,col,spacing=20,angle=-.6,lw=2){g.save();g.beginPath();g.rect(0,0,w,h);g.clip();g.strokeStyle=col;g.lineWidth=lw;let dy=Math.tan(angle)*w;g.beginPath();for(let y=-Math.abs(dy);y<h+Math.abs(dy);y+=spacing){g.moveTo(0,y);g.lineTo(w,y+dy);}g.stroke();g.restore();},cache,clear:()=>cache.clear()};
})();
