/* STAGING ONLY. Load after V4 world_backplate.js and before edit_story.js.
 * Changes only 02_egypt. The V4 single overscanned background remains intact;
 * its fixed Egyptian rim is replaced by the same physical ornament attached
 * to the existing relative foreground camera. No new CAM event or time clock.
 */
(() => {
  'use strict';
  const createV4 = window.createWorldBackplate;
  if (typeof createV4 !== 'function') throw Error('Egypt rim patch requires V4 world_backplate.js first');

  window.createWorldBackplate = function createEgyptRimCoflow(style, options = {}) {
    // All other style objects and options reach the frozen V4 function intact.
    if (style.id !== '02_egypt') return createV4(style, options);
    const W = options.width || 1080, H = options.height || 1920;
    const anchorX = W / 2, anchorY = H / 2;
    const p = style.palette, colors = [p.red, '#2a58a8', p.gold, p.olive];
    const contextMaterials = new WeakMap();
    function paintMaterial(g, col, t) {
      let materials = contextMaterials.get(g);
      if (!materials) { materials = new Map(); contextMaterials.set(g, materials); }
      if (!materials.has(col)) materials.set(col, style.pattern ? style.pattern(g, col, t) : col);
      return materials.get(col);
    }
    function band(g, x, y, w, h, t) {
      // A narrow physical painted strip. No copied opaque background rectangle.
      g.fillStyle = paintMaterial(g, p.white, t); g.fillRect(x, y, w, h);
      const vertical = h > w, L = vertical ? h : w;
      for (let u = 0, k = 0; u < L; u += 42, k++) {
        g.fillStyle = paintMaterial(g, colors[k % colors.length], t);
        if (vertical) g.fillRect(x + 3, y + u + 3, w - 6, Math.max(0, Math.min(36, L - u - 3)));
        else g.fillRect(x + u + 3, y + 3, Math.max(0, Math.min(36, L - u - 3)), h - 6);
      }
      g.strokeStyle = p.ink; g.lineWidth = 1.8; g.strokeRect(x, y, w, h);
    }
    function scenicRim(g, t) {
      // V4's original Egyptian strip positions; now actual scene coordinates.
      band(g, 14, 12, 1052, 30, t); band(g, 15, 42, 28, 1500, t);
      band(g, 1037, 42, 28, 1500, t); band(g, 14, 1500, 1052, 32, t);
    }
    // The core still paints the original plaster, registers, glyphs and scarab
    // on its continuous overscanned field. Only its viewport-fixed restore is
    // disabled. A private copy prevents mutation of the original factory.
    const rimless = Object.assign({}, style, { rim() {} });
    const background = createV4(rimless, options);
    if (style.metadata) {
      style.metadata.world_camera = 'V5仅埃及：灰泥/分栏/圣甲虫仍用V4连续单幅overscan；四色实体饰带跟随已有相机的完整相对平移/倍率，不再固定于输出视口。没有新增CAM事件、时间漂移或镜像拼缝。';
      style.metadata.egypt_rim_fix = '固定恢复边框移入近景饰带层；语义物体、人物照片、文稿和中文字幕由原场景绘制。';
    }
    let last = null;
    return {
      paint(g, absoluteTime, shot, base, tracked) {
        background.paint(g, absoluteTime, shot, base, tracked);
        const dx = tracked.x - (base.x ?? W / 2);
        const dy = tracked.y - (base.y ?? H / 2);
        const z = tracked.z / (base.z ?? 1);
        const roll = (tracked.r || 0) - (base.r || 0);
        if (!(Number.isFinite(dx) && Number.isFinite(dy) && Number.isFinite(z) && z > 0)) {
          throw Error('Egypt rim requires a finite existing relative camera');
        }
        // Near-plane co-motion follows only the already-authored camera input.
        // A strip may leave the view during a real pan. The original certified
        // V4 scenic field beneath it continues to cover every output pixel.
        g.save(); g.translate(anchorX, anchorY); g.scale(z, z);
        if (roll) g.rotate(roll);
        g.translate(-anchorX - dx, -anchorY - dy);
        scenicRim(g, absoluteTime); g.restore();
        last = Object.assign({}, background.coverage(), {
          egyptRim: { mode: 'existing full relative camera; no viewport restore', dx, dy, z, roll },
          foregroundCameraEventsChanged: false
        });
        if (options.onEgyptRimFrame) options.onEgyptRimFrame(last);
      },
      coverage: () => last || background.coverage(),
      options: Object.assign({}, background.options, {
        egyptRim: 'near ornament layer follows existing full relative CAM',
        scope: '02_egypt only; unchanged V4 continuous background coverage'
      })
    };
  };
})();
