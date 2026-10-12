// Topic-scene integration for coarse pixel worlds. MIT.
// Requires the scene's c/wc, STYLE, flushPixel(), fixed(), font() helpers.
// Flush the lower pixel layer first; preserve transform/opacity for native text.
function txt(g,s,x,y,size=46,col=P.ink,align='left') {
 fixed(()=>{
  let target=g;
  if(STYLE.pixelWorld&&g===wc){
   flushPixel();target=c;target.save();
   target.setTransform(g.getTransform());target.globalAlpha=g.globalAlpha;
  }else target.save();
  font(target,size);target.fillStyle=col;
  target.textAlign=align;target.textBaseline='middle';
  target.fillText(s,x,y);target.restore();
 });
}
// Keep semantic labels, burned subtitles and real presenter photos readable.
// Pixelation belongs to topic props; later foreground objects may still occlude
// text intentionally, so check semantic anchors in the actual encoded film.
