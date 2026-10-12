/* V4: one real overscanned scenic canvas, one crop, no mirror/repeat/feather.
 * MIT. The existing camera events, narration, semantic actions and gate stay.
 * Project canvas 1080x1920; far-field range is intentionally bounded so the
 * composition stays recognizable through the long labor/assembly world pans.
 */
(() => {
'use strict';
window.createWorldBackplate = function(style, options={}) {
  const W=options.width||1080,H=options.height||1920;
  const depth=options.depth??.32,zoomDepth=options.zoomDepth??.42;
  const maxX=options.maxX??160,maxY=options.maxY??70;
  const anchorX=W/2,anchorY=options.anchorY??230;
  // Current 24-shot track minimum is >.96 after z^zoomDepth. Use .95 plus
  // raster guard; this is constant across all shots, not an added zoom event.
  const zoomFloor=options.zoomFloor??.95,guard=options.guard??4;
  if(anchorY<=0||anchorY>=H)throw Error('V4 background anchor must lie inside the canvas');
  const overscan=Math.max(1,
    1/zoomFloor+(maxX+guard)/anchorX,
    1/zoomFloor+(maxX+guard)/(W-anchorX),
    1/zoomFloor+(maxY+guard)/anchorY,
    1/zoomFloor+(maxY+guard)/(H-anchorY));
  const field=document.createElement('canvas');
  field.width=Math.ceil(W*overscan);field.height=Math.ceil(H*overscan);
  const fc=field.getContext('2d');let last=null;
  const p=style.palette;
  function line(g,pts,col,lw=2){g.beginPath();pts.forEach((v,i)=>i?g.lineTo(...v):g.moveTo(...v));g.strokeStyle=col;g.lineWidth=lw;g.stroke();}
  function arch(x,y,w,h){const a=new Path2D();a.moveTo(x,y+h);a.lineTo(x,y+h*.37);a.quadraticCurveTo(x,y+h*.12,x+w/2,y);a.quadraticCurveTo(x+w,y+h*.12,x+w,y+h*.37);a.lineTo(x+w,y+h);a.closePath();return a;}
  // These are actual ornamental shapes on a nearer page/frame layer. No strips
  // copied from an opaque background: there is no hidden rectangular splice.
  function rim(g,t,shot){
    if(typeof style.rim==='function'){style.rim(g,t,shot);return;}
    if(style.id==='02_egypt'){
      const colors=[p.red,'#2a58a8',p.gold,p.olive];
      const band=(x,y,w,h)=>{g.fillStyle=p.white;g.fillRect(x,y,w,h);const vertical=h>w,L=vertical?h:w;
        for(let u=0,k=0;u<L;u+=42,k++){g.fillStyle=colors[k%4];if(vertical)g.fillRect(x+3,y+u+3,w-6,Math.max(0,Math.min(36,L-u-3)));else g.fillRect(x+u+3,y+3,Math.max(0,Math.min(36,L-u-3)),h-6);}
        g.strokeStyle=p.ink;g.lineWidth=1.8;g.strokeRect(x,y,w,h);};
      band(14,12,1052,30);band(15,42,28,1500);band(1037,42,28,1500);band(14,1500,1052,32);
    }else if(style.id==='05_gothic'){
      for(const x of [28,998]){const a=arch(x,295,54,780);g.save();g.clip(a);
        for(let y=295,k=0;y<1080;y+=36,k++){g.fillStyle=k%2?p.red:p.olive;g.fillRect(x,y,54,36);line(g,[[x,y],[x+54,y+36]],p.gold,2);g.beginPath();g.arc(x+27,y+18,3,0,Math.PI*2);g.fillStyle=p.white;g.fill();}
        g.restore();g.strokeStyle=p.ink;g.lineWidth=3;g.stroke(a);}
      for(let x=30,k=0;x<W;x+=48,k++){g.fillStyle=k%2?p.red:p.olive;g.fillRect(x,1472,44,28);g.beginPath();g.arc(x+22,1486,3,0,Math.PI*2);g.fillStyle=p.white;g.fill();}
    }else if(style.id==='10_nouveau'){
      g.strokeStyle=p.gold;g.lineWidth=6;g.strokeRect(36,55,1008,1465);
      g.strokeStyle=p.ink;g.lineWidth=1.8;g.strokeRect(30,49,1020,1477);g.strokeRect(44,63,992,1449);
    }
  }
  function paint(g,absoluteTime,shot,base,tracked){
    const dx=maxX*Math.tanh(((tracked.x-(base.x??W/2))*depth)/maxX);
    const dy=maxY*Math.tanh(((tracked.y-(base.y??H/2))*depth)/maxY);
    const z=Math.pow(Math.max(.01,tracked.z/(base.z??1)),zoomDepth);
    if(z<zoomFloor-1e-8)throw Error(`V4 background zoom ${z} below certified floor ${zoomFloor}; recompute overscan for this camera track`);
    if(Math.abs((tracked.r||0)-(base.r||0))>1e-8)throw Error('V4 finite track compositor has no camera roll; compute a rotated coverage envelope before adding roll');
    fc.reset();fc.imageSmoothingEnabled=!style.pixelWorld;fc.scale(overscan,overscan);
    style.background(fc,absoluteTime,shot);
    if(style.motifs){fc.save();style.motifs(fc,absoluteTime,shot);fc.restore();}
    g.save();g.imageSmoothingEnabled=!style.pixelWorld;
    g.translate(anchorX,anchorY);g.scale(z,z);g.translate(-dx,-dy);
    // Exactly one source image. Its native frame is painted at higher canvas
    // resolution; cached materials retain their original sampling resolution.
    g.drawImage(field,-anchorX*overscan,-anchorY*overscan);g.restore();
    g.save();rim(g,absoluteTime,shot);g.restore();
    const bounds={left:anchorX-z*(anchorX*overscan+dx),top:anchorY-z*(anchorY*overscan+dy),
      right:anchorX+z*(field.width-anchorX*overscan-dx),bottom:anchorY+z*(field.height-anchorY*overscan-dy)};
    last={time:absoluteTime,shot:shot?.id,dx,dy,z,overscan,bounds,
      covered:bounds.left<=0&&bounds.top<=0&&bounds.right>=W&&bounds.bottom>=H};
    if(!last.covered)throw Error('V4 scenic canvas does not cover the output: '+JSON.stringify(last));
    if(options.onFrame)options.onFrame(last);
  }
  return {paint,coverage:()=>last,options:{width:W,height:H,depth,zoomDepth,maxX,maxY,anchorX,anchorY,zoomFloor,overscan,
    sourceWidth:field.width,sourceHeight:field.height,mode:'single overscanned scenic field crop; optional vector ornamental rim'}};
};
})();

/* Integration: replace engine/lib/world_backplate.js with this file's content
 * only after project validation; the current cam() call signature is unchanged.
 * Root retains smooth currentT for CAM and stepped prop/sprite clocks.
 *
 * Real limits:
 * - The fixed interface supplies a flattened background, so this is a single
 *   scenic plane, not a reconstructed multi-plane 3D world.
 * - Uniform overscan is approximately 1.3744x. Some extreme side decorations
 *   are cropped; high-value page ornament is re-drawn as genuine vector rim
 *   for Egyptian/Gothic/Nouveau worlds. No opaque rectangular restoration.
 * - Existing cached raster material tiles/backgrounds are resampled up to
 *   overscan times actual far-camera zoom. This does not add source detail.
 * - Far-field motion is bounded at 160/70 native pixels; foreground CAM events
 *   are unchanged. Motion stops with those events; there is no added drift.
 * - Source background motifs are part of that plane. The separate rim keeps
 *   actual outline shapes, but is not a full author-scene layer decomposition.
 * - The certified track is unrolled and z^zoomDepth >=.95. New tracks below
 *   that floor or with roll fail rather than silently produce empty edges.
 * - Mechanical coverage and determinism cannot replace encoded visual review
 *   or establish improved film-gate results. Root will run real MP4 gates.
 */
