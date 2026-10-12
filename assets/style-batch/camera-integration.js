// Within the theme scene closure, after STYLE/W/H and time helpers exist:
const worldBackplate=createWorldBackplate(STYLE,{width:W,height:H});
function cam(g,base,events,t,fn){
 const s=liveShot||shotAt(currentT);
 const sceneClock=STYLE.timeQuant?Math.max(s.start,Math.floor(currentT*STYLE.timeQuant)/STYLE.timeQuant):currentT;
 const tracked=CAM.track(base,events,t+(currentT-sceneClock));
 styled(()=>worldBackplate.paint(g,currentT,s,base,tracked));
 // Topic object camera below matches the accepted portrait scene convention.
 g.save();g.translate(W/2,0);g.scale(.9,.9);g.translate(-W/2,0);
 CAM.with(g,tracked,fn);g.restore();
}
// Place ornamental motifs behind semantic props/labels.
// Do not quantize a smooth camera with a stepped 8-bit sprite clock.
