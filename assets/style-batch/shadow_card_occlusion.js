/* STAGING V6, 34_shadowpuppet only. Load after styles/heritage.js and before
 * scenes/edit_story.js. V4 scene and CAM stay byte-for-byte unchanged.
 * notes() in the frozen V4 scene identifies its semantic word cards by seed43.
 */
(() => {
  'use strict';
  const factories = window.KOUBO_STYLE_FACTORIES;
  if (!factories || typeof factories['34_shadowpuppet'] !== 'function') {
    throw Error('Shadow card patch requires the V4 heritage factory first');
  }
  const createV4 = factories['34_shadowpuppet'];
  factories['34_shadowpuppet'] = function createBackedShadowCards() {
    const style = createV4(), drawV4Plate = style.plate;
    const contextBackings = new WeakMap(), inset = 23;
    function backing(g) {
      let pattern = contextBackings.get(g);
      if (!pattern) {
        pattern = window.KS.pattern(g, '34_shadowpuppet/v6/opaque-word-card', 128, 128, q => {
          // Complete opaque paper underneath the translucent leather centre.
          // Stable, faint fibres retain a warm physical material without holes.
          q.fillStyle = style.palette.white; q.fillRect(0, 0, 128, 128);
          const random = window.KS.rng(340643);
          q.strokeStyle = 'rgba(100,65,27,.045)'; q.lineWidth = .65;
          for (let i = 0; i < 72; i++) {
            const x = random() * 128, y = random() * 128;
            q.beginPath(); q.moveTo(x, y);
            q.lineTo(x + 3 + random() * 10, y + (random() - .5) * 3); q.stroke();
          }
        });
        contextBackings.set(g, pattern);
      }
      return pattern;
    }
    style.plate = function drawBackedSemanticCard(g, w, h, col, seed, t) {
      if (seed === 43 && w > inset * 2 && h > inset * 2) {
        // V4 text begins at x40; its middle-aligned 66px words and underline
        // fit inside this centre. The carved 8..20px perimeter stays unbacked.
        // Keep inherited globalAlpha: the backing must never bypass a future
        // caller's opacity entrance. Frozen V4 notes use translation, not fade.
        g.save(); g.globalCompositeOperation = 'source-over';
        g.shadowColor = 'rgba(0,0,0,0)'; g.filter = 'none';
        g.fillStyle = backing(g);
        g.fillRect(inset, inset, w - inset * 2, h - inset * 2); g.restore();
      }
      // Retains V4 carved edge, multiply skin, rivets, shadow and stepped clock.
      drawV4Plate.call(style, g, w, h, col, seed, t);
    };
    style.metadata = Object.assign({}, style.metadata, {
      text_card_occlusion: 'V6仅34：seed43语义文字卡中心先铺不透明浅皮纸，原透光皮片/镂孔边缘/铆钉/阴影保留；相机、音轨、文稿内容和节奏沿用V4。'
    });
    return style;
  };
})();
