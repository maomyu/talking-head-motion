/* Frame-addressed layer reconstruction. Reference video playback is not a layer. */
'use strict';
const spec=window.REFERENCE_SPEC,canvas=document.querySelector('#film'),ctx=canvas.getContext('2d',{alpha:false});
const assets=new Map(),cache=new Map();let prepared=new Map();
const clamp=n=>Math.max(0,Math.min(1,n));
function value(track,frame,fallback){
  if(track===undefined)return fallback;
  if(typeof track!=='object'||track===null)return track;
  if(Array.isArray(track))return track[Math.max(0,Math.min(track.length-1,frame))];
  const keys=track.keys;if(!keys?.length)throw Error('Empty animation track');
  if(frame<=keys[0][0])return keys[0][1];
  for(let i=1;i<keys.length;i++)if(frame<=keys[i][0]){
    let p=clamp((frame-keys[i-1][0])/(keys[i][0]-keys[i-1][0]));
    const easing=track.easing||'linear';
    if(easing==='hold')p=frame<keys[i][0]?0:1;
    if(easing==='outCubic')p=1-(1-p)**3;
    if(easing==='inOutCubic')p=p<.5?4*p**3:1-(-2*p+2)**3/2;
    return keys[i-1][1]+(keys[i][1]-keys[i-1][1])*p;
  }
  return keys.at(-1)[1];
}
async function load(url){
  if(cache.has(url))return cache.get(url);
  const image=new Image();image.src=url;await image.decode();cache.set(url,image);
  if(cache.size>36)cache.delete(cache.keys().next().value);return image;
}
function active(layer,f){return f>=(layer.start_frame??0)&&f<(layer.end_frame??spec.frames);}
function pathRect(x,y,w,h,r){ctx.beginPath();ctx.roundRect(x,y,w,h,Math.min(r,w/2,h/2));}
function draw(layer,f){
  if(!active(layer,f))return;
  const v=(key,def)=>value(layer[key],f,def);
  ctx.save();ctx.globalAlpha=clamp(v('opacity',1));ctx.globalCompositeOperation=layer.blend_mode||'source-over';
  if(ctx.globalAlpha===0){ctx.restore();return;}
  if(layer.matrix)ctx.transform(...layer.matrix[f]);
  if(layer.screen_clip){const c=layer.screen_clip;pathRect(c.x,c.y,c.width,c.height,c.radius??0);ctx.clip();}
  const x=v('x',0),y=v('y',0),w=v('width',spec.width),h=v('height',spec.height);
  ctx.translate(x+w/2,y+h/2);ctx.rotate(v('rotation',0)*Math.PI/180);ctx.transform(1,0,v('skew',0),1,0,0);
  ctx.translate(-w/2,-h/2);
  if(layer.clip){const c=layer.clip;pathRect(v('clip_x',c.x??0),v('clip_y',c.y??0),v('clip_width',c.width??w),v('clip_height',c.height??h),v('radius',c.radius??0));ctx.clip();}
  if(v('blur',0)>0)ctx.filter=`blur(${v('blur',0)}px)`;
  const im=prepared.get(layer.id);
  if(layer.kind==='image'||layer.kind==='sequence'){
    if(!im)throw Error('Unprepared image '+layer.id);
    if(layer.outline){
      const o=layer.outline,mask=document.createElement('canvas');mask.width=im.width;mask.height=im.height;
      const mx=mask.getContext('2d');mx.drawImage(im,0,0);mx.globalCompositeOperation='source-in';mx.fillStyle=o.color;mx.fillRect(0,0,mask.width,mask.height);
      const r=v('outline_width',o.width??5);for(let i=0;i<16;i++){const a=i*Math.PI/8;ctx.drawImage(mask,Math.cos(a)*r,Math.sin(a)*r,w,h);}
    }
    if(layer.crop){const c=layer.crop;ctx.drawImage(im,c.x,c.y,c.width,c.height,0,0,w,h);}else ctx.drawImage(im,0,0,w,h);
  }else if(layer.kind==='rect'){
    pathRect(0,0,w,h,v('radius',0));if(!layer.no_fill){ctx.fillStyle=layer.color;ctx.fill();}
    if(layer.stroke){ctx.strokeStyle=layer.stroke.color;ctx.lineWidth=layer.stroke.width;ctx.stroke();}
  }else if(layer.kind==='text'){
    ctx.font=`${layer.weight||800} ${v('font_size',60)}px ReferenceSans`;ctx.textAlign=layer.align||'left';ctx.textBaseline=layer.baseline||'top';
    if(layer.shadow){ctx.shadowColor=layer.shadow.color;ctx.shadowBlur=layer.shadow.blur||0;ctx.shadowOffsetX=layer.shadow.x||0;ctx.shadowOffsetY=layer.shadow.y||0;}
    const reveal=Math.floor(v('reveal',Array.from(layer.text).length)),text=Array.from(layer.text).slice(0,reveal).join('');
    if(layer.stroke){ctx.strokeStyle=layer.stroke.color;ctx.lineWidth=layer.stroke.width;ctx.lineJoin='round';ctx.strokeText(text,0,0);}
    ctx.fillStyle=layer.color;ctx.fillText(text,0,0);
  }else if(layer.kind==='gradient'){
    const g=ctx.createLinearGradient(0,0,0,h);for(const [p,color] of layer.stops)g.addColorStop(p,color);ctx.fillStyle=g;ctx.fillRect(0,0,w,h);
  }else throw Error('Unsupported layer kind '+layer.kind);
  ctx.restore();
}
async function boot(){
  if(!spec?.layers?.length)throw Error('Missing frame composition');canvas.width=spec.width;canvas.height=spec.height;
  for(const [key,asset] of Object.entries(spec.assets))assets.set(key,asset);
  await document.fonts.load('800 64px ReferenceSans');await document.fonts.ready;
  window.prepare=async frame=>{
    if(!Number.isInteger(frame)||frame<0||frame>=spec.frames)throw Error('Frame outside composition');
    prepared=new Map();await Promise.all(spec.layers.filter(layer=>active(layer,frame)&&['image','sequence'].includes(layer.kind)).map(async layer=>{
      const a=assets.get(layer.asset);if(!a)throw Error('Missing asset '+layer.asset);
      let url=a.path;
      if(layer.kind==='sequence'){
        const t=spec.times[frame]-(layer.time_origin??0)+(layer.media_start??0);
        let index=0;while(index+1<a.times.length&&a.times[index+1]<=t+1e-7)index++;
        if(t<0||t>a.times.at(-1)+(a.last_duration??1/a.fps))throw Error('Sequence window outside real footage: '+layer.id);
        url=a.paths[index];
      }
      prepared.set(layer.id,await load(url));
    }));
  };
  window.renderFrame=frame=>{ctx.fillStyle=spec.background||'#000';ctx.fillRect(0,0,spec.width,spec.height);for(const layer of spec.layers)draw(layer,frame);};
  await prepare(0);renderFrame(0);window.__canvas=canvas;window.__ready=true;
}
boot().catch(error=>{window.__bootFailed=String(error);console.error(error);});
