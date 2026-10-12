/* Topic-specific material factories. Sources: huashu-full style cards and scenes
 * 01/02/03/04/05/06/10/18/20/21/30/34. No source-room/character rendering is used.
 * All raster textures, tile layouts and ornamental paths have stable seeds.
 */
(() => {
  'use strict';
  const F = window.KOUBO_STYLE_FACTORIES = window.KOUBO_STYLE_FACTORIES || {};
  const W = 1080, H = 1920, CH = 1540, TAU = Math.PI * 2;
  const K = () => window.KS, P = () => window.PAINT;
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const mod = (x, n) => ((x % n) + n) % n;
  const palette = (paper, ink, red, olive, gold, white) => ({ paper, ink, red, olive, gold, white });
  const line = (g, pts, col, lw = 3) => {
    if (!pts || pts.length < 2) return;
    g.beginPath(); pts.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]));
    g.strokeStyle = col; g.lineWidth = lw; g.stroke();
  };
  const circle = (g, x, y, r, col, edge = null, lw = 2) => {
    g.beginPath(); g.arc(x, y, Math.max(.01, r), 0, TAU);
    if (col) { g.fillStyle = col; g.fill(); }
    if (edge) { g.strokeStyle = edge; g.lineWidth = lw; g.stroke(); }
  };
  const poly = pts => { const p = new Path2D(); pts.forEach((q, i) => i ? p.lineTo(q[0], q[1]) : p.moveTo(q[0], q[1])); p.closePath(); return p; };
  const clipped = (g, fn) => { g.save(); g.beginPath(); g.rect(0, 0, W, CH); g.clip(); fn(); g.restore(); };
  const rectClip = (g, w, h) => { g.beginPath(); g.rect(0, 0, w, h); g.clip(); };
  const points = (seed, count, w = W, h = CH) => {
    const r = K().rng(seed); return Array.from({ length: count }, () => [r() * w, r() * h, r(), r() * TAU]);
  };
  const semantic = shot => {
    const s = `${shot && shot.action || ''} ${shot && shot.object || ''} ${shot && shot.id || ''}`;
    if (/clock|time|second|minute|hour|时间|分钟|时钟|秒/.test(s)) return 'clock';
    if (/cut|trim|edit|剪|切/.test(s)) return 'cut';
    if (/voice|audio|wave|配音|波形|声音/.test(s)) return 'wave';
    if (/folder|archive|file|稿|文件|归档/.test(s)) return 'folder';
    if (/photo|image|照片|图/.test(s)) return 'photo';
    return 'film';
  };

  // Low-resolution physical material map, baked once per style/color. The
  // relief/foil/mineral recipes retain source mechanisms without full-frame
  // readback or frame-by-frame random brush work.
  function material(g, id, kind, col, size = 256) {
    return K().pattern(g, `${id}/material/${kind}/${col}/${size}`, size, size, q => {
      const p = P(), b = p.hex(col), r = K().rng(431 + id.charCodeAt(0) * 17 + kind.length * 29);
      const im = q.createImageData(size, size), d = im.data;
      const height = (x, y) => p.fbm(x * .022 + 7, y * .022, 4) + .14 * p.fbm(x * .085, y * .085 + 2, 3);
      for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
        const n = p.fbm(x * .035 + 13, y * .035, 4), gr = (r() - .5) * 12;
        let v = n * 25 + gr, a = 255, rr = b[0], gg = b[1], bb = b[2];
        if (kind === 'rock') {
          const h = height(x, y), dx = (height(x + 1, y) - h) * 9, dy = (height(x, y + 1) - h) * 9;
          const shade = (-dx * -.55 - dy * -.62 + .56) / Math.hypot(dx, dy, 1);
          v = (shade - .45) * 42 + n * 20 + gr;
        } else if (kind === 'clay') {
          v = n * 29 + p.noise(x * .006, y * .9) * 12 + gr * .5;
        } else if (kind === 'foil') {
          v = n * 48 + p.noise(x * .008, y * .19) * 30 + gr * .9;
          rr += v; gg += v * .8; bb += v * .45; v = 0;
        } else if (kind === 'mineral') {
          const chip = p.fbm(x * .026 + 11, y * .026 + 4, 5);
          if (chip > .28) { rr = 216; gg = 198; bb = 162; v = gr; }
          else if (chip > .245) { v -= 34; }
          else v = n * 32 + gr * 1.25;
        } else if (kind === 'oil') {
          v = n * 17 + gr * .4 + ((x % 4 === 0) ? 3 : 0) - ((y % 4 === 0) ? 3 : 0);
        } else if (kind === 'litho') v = n * 11 + gr * .7;
        else if (kind === 'gouache') v = p.noise(x * .007, y * .22) * 16 + n * 12 + gr * .35;
        else if (kind === 'charcoal') { a = r() < .07 || n > .24 ? 45 : 210 + r() * 45; v = gr; }
        else if (kind === 'leather') v = n * 16 + gr * .75;
        else v = n * 20 + gr;
        const i = (y * size + x) * 4; d[i] = rr + v; d[i + 1] = gg + v * .86; d[i + 2] = bb + v * .7; d[i + 3] = a;
      }
      q.putImageData(im, 0, 0);
      if (kind === 'foil') {
        q.strokeStyle = 'rgba(80,45,8,.18)'; q.lineWidth = 1;
        for (let y = 0; y < size; y += 64) for (let x = (y / 64 % 2) * 32; x < size; x += 64) q.strokeRect(x + .5, y + .5, 64, 64);
      }
      if (kind === 'oil' || kind === 'gouache') {
        q.lineCap = 'round';
        for (let i = 0; i < 160; i++) {
          const x = r() * size, y = r() * size, a = kind === 'oil' ? r() * Math.PI : -.25 + (r() - .5) * .3;
          const len = kind === 'oil' ? 10 + r() * 18 : 45 + r() * 90;
          line(q, [[x, y], [x + Math.cos(a) * len, y + Math.sin(a) * len]], r() < .5 ? 'rgba(255,245,220,.045)' : 'rgba(20,10,0,.035)', kind === 'oil' ? 3 : 7);
        }
      }
    });
  }
  function field(g, id, kind, col) {
    g.drawImage(K().cached(`${id}/background/${kind}`, W, H, q => { q.fillStyle = material(q, id, kind, col); q.fillRect(0, 0, W, H); }), 0, 0);
  }
  function plateBase(g, id, kind, col, w, h) { g.fillStyle = material(g, id, kind, col); g.fillRect(0, 0, w, h); }
  function border(g, w, h, col, inset = 7, lw = 2) {
    g.strokeStyle = col; g.lineWidth = lw; g.strokeRect(inset, inset, Math.max(0, w - inset * 2), Math.max(0, h - inset * 2));
  }
  function cracks(g, w, h, seed, count, dark, light = null) {
    const r = K().rng(seed);
    for (let k = 0; k < count; k++) {
      let x = r() * w, y = r() * h, a = r() * TAU; const pts = [[x, y]];
      for (let j = 0; j < 10; j++) { a += (r() - .5) * .85; x += Math.cos(a) * (7 + r() * 17); y += Math.sin(a) * (7 + r() * 17); pts.push([x, y]); }
      if (light) line(g, pts.map(([x, y]) => [x + 1.4, y + 1.4]), light, 2.2);
      line(g, pts, dark, 1.2);
    }
  }
  function spiral(g, x, y, r, angle, col, lw = 2, turns = 2.4) {
    const pts = []; for (let k = 0; k <= 44; k++) { const u = k / 44, a = angle + u * TAU * turns, rr = r * (1 - .88 * u); pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]); } line(g, pts, col, lw);
  }
  function leaf(g, x, y, len, width, a, col, edge = null) {
    g.save(); g.translate(x, y); g.rotate(a); g.beginPath(); g.moveTo(0, 0);
    g.quadraticCurveTo(-width, -len * .48, 0, -len); g.quadraticCurveTo(width, -len * .48, 0, 0); g.fillStyle = col; g.fill();
    if (edge) { g.strokeStyle = edge; g.lineWidth = 1.5; g.stroke(); } g.restore();
  }
  function rosette(g, x, y, r, rot, colors, edge = null, n = 8) {
    g.save(); g.translate(x, y); g.rotate(rot);
    for (let i = 0; i < n; i++) { g.save(); g.rotate(i / n * TAU); g.fillStyle = colors[i % colors.length]; g.beginPath(); g.ellipse(r * .57, 0, r * .45, r * .24, 0, 0, TAU); g.fill(); if (edge) { g.strokeStyle = edge; g.lineWidth = 1.5; g.stroke(); } g.restore(); }
    circle(g, 0, 0, r * .22, colors[colors.length - 1], edge); g.restore();
  }
  // Small editing symbols live on the margin/ornament layer. Primary semantic
  // phone/photo/scissors/film/cassette/clock geometry stays in the shared scene.
  function glyph(g, kind, x, y, s, ink, fill = null, phase = 0) {
    g.save(); g.translate(x, y); g.scale(s, s); g.strokeStyle = ink; g.fillStyle = fill || ink; g.lineWidth = 3; g.lineCap = 'round'; g.lineJoin = 'round';
    if (kind === 'cut') {
      circle(g, -15, 14, 9, null, ink, 3); circle(g, 15, 14, 9, null, ink, 3);
      const a = .2 + .2 * phase; line(g, [[-10, 7], [23 + a * 12, -28]], ink, 4); line(g, [[10, 7], [-23 - a * 12, -28]], ink, 4); circle(g, 0, -4, 3, ink);
    } else if (kind === 'clock') {
      circle(g, 0, 0, 24, fill, ink, 3); line(g, [[-1, -17], [0, 0], [14 * Math.cos(phase), 14 * Math.sin(phase)]], ink, 3);
      for (let k = 0; k < 4; k++) circle(g, Math.cos(k * Math.PI / 2) * 19, Math.sin(k * Math.PI / 2) * 19, 1.5, ink);
    } else if (kind === 'wave') {
      const pts = []; for (let i = 0; i <= 28; i++) pts.push([-28 + i * 2, Math.sin(i * .58 - phase) * (4 + 13 * Math.sin(i / 28 * Math.PI))]); line(g, pts, ink, 3);
    } else if (kind === 'folder') {
      const p = poly([[-27, -20], [-8, -20], [-2, -13], [28, -13], [25, 22], [-27, 22]]); if (fill) g.fill(p); g.stroke(p); line(g, [[-23, -8], [24, -8]], ink, 2);
    } else if (kind === 'photo') {
      if (fill) g.fillRect(-27, -23, 54, 46); g.strokeRect(-27, -23, 54, 46);
      line(g, [[-23, 16], [-9, -4], [2, 9], [12, -10], [23, 16]], ink, 2); circle(g, -13, -12, 3.5, ink);
    } else {
      if (fill) g.fillRect(-30, -22, 60, 44); g.strokeRect(-30, -22, 60, 44);
      for (let x = -24; x <= 24; x += 12) { g.fillStyle = ink; g.fillRect(x - 2, -18, 4, 5); g.fillRect(x - 2, 13, 4, 5); }
      line(g, [[-28, -10], [28, -10]], ink, 2); line(g, [[-28, 10], [28, 10]], ink, 2); line(g, [[0, -9], [0, 9]], ink, 2);
    }
    g.restore();
  }
  const metadata = (mechanism, topic_adaptation, motifs, limitations) => ({ mechanism, topic_adaptation, motifs, limitations });

  F['01_cave'] = () => {
    const id = '01_cave', p = palette('#ba7b45', '#21150d', '#9c3520', '#744527', '#cf8f2c', '#f0dfbf');
    const embers = points(1401, 22), pats = new WeakMap();
    const carbon = (g, col, t) => {
      const pat = material(g, id, 'charcoal', col, 128);
      // Grains step at 9fps while the actual contour stays fixed.
      if (pat.setTransform) { const r = K().rng(73 + Math.floor(t * 9) * 13); pat.setTransform(new DOMMatrix().translate(r() * 128, r() * 128)); }
      pats.set(g, pat); return pat;
    };
    return {
      id, name: '洞穴岩画', palette: p,
      background(g, t, shot) {
        field(g, id, 'rock', p.paper);
        g.drawImage(K().cached(`${id}/rock_cracks`, W, H, q => {
          cracks(q, W, H, 401, 20, 'rgba(40,22,10,.6)', 'rgba(255,226,180,.22)');
          q.strokeStyle = material(q, id, 'charcoal', p.red); q.lineWidth = 9;
          for (const x of [70, 1010]) { q.beginPath(); q.moveTo(x, 185); q.lineTo(x - 16, 460); q.lineTo(x + 8, 740); q.lineTo(x - 10, 1110); q.lineTo(x, 1475); q.stroke(); }
          for (let k = 0; k < 6; k++) glyph(q, ['film','cut','wave','folder','clock','photo'][k], k % 2 ? 1005 : 73, 310 + Math.floor(k / 2) * 420, .86, p.ink, null, .5);
        }), 0, 0);
        clipped(g, () => { g.globalAlpha = .18; glyph(g, semantic(shot), 540, 1230, 3.2, p.red, null, Math.floor(t * 8) % 2); });
        const v = g.createRadialGradient(540, 680, 360, 540, 680, 1300); v.addColorStop(0, 'rgba(24,10,2,0)'); v.addColorStop(1, 'rgba(24,10,2,.6)'); g.fillStyle = v; g.fillRect(0, 0, W, H);
      },
      pattern(g, col, t) { return material(g, id, 'rock', col); },
      plate(g, w, h, col, seed, t) {
        g.save(); rectClip(g, w, h); plateBase(g, id, 'rock', col, w, h);
        border(g, w, h, carbon(g, p.ink, t), 4, 5);
        const count = Math.min(9, Math.max(2, Math.floor(w / 45))); g.fillStyle = carbon(g, p.red, t);
        for (let i = 0; i < count; i++) circle(g, (i + .5) / count * w, h - 9, Math.min(3.5, h * .05), g.fillStyle);
        g.restore();
      },
      line(g, pts, col, lw, t) { g.save(); g.lineCap = 'round'; g.lineJoin = 'round'; line(g, pts, K().alpha(col, .18), lw + 5); line(g, pts, carbon(g, col, t), lw); g.restore(); },
      motifs(g, t) { clipped(g, () => {
        embers.forEach(([x, y, s, ph], i) => { const xx = i % 2 ? 990 + Math.sin(t + ph) * 38 : 75 + Math.sin(t + ph) * 30, yy = mod(y - t * (45 + s * 35), 1480);
          const a = .25 + .5 * Math.abs(Math.sin(t * 6 + ph)); circle(g, xx, yy, 1.5 + s * 2.5, K().alpha('#ffe082', a)); });
        const n = Math.floor(mod(t * 3, 8)); for (let i = 0; i <= n; i++) line(g, [[190 + i * 32, 1490], [200 + i * 32, 1458]], carbon(g, p.red, t), 5);
      }); },
      after(g, t) { clipped(g, () => { const glow = g.createRadialGradient(940 + Math.sin(t * 3.1) * 28, 1200, 12, 940, 1200, 680); glow.addColorStop(0, 'rgba(255,180,75,.085)'); glow.addColorStop(1, 'rgba(255,160,65,0)'); g.globalCompositeOperation = 'overlay'; g.fillStyle = glow; g.fillRect(0, 0, W, CH); }); },
      metadata: metadata('法线受光岩面、裂缝亮边、带孔炭线9fps颗粒错位、赭石标记', '手机、稿件和托板带岩面凹凸；剪切、底片、归档符号作为岩刻落在边栏', '两姿态剪刀岩刻、计时刻痕依次写出、侧边余烬与微弱火光', '没有重建上游少女/猫/野牛；岩面静态缓存，火光不重新计算法线。真实照片不做岩刻化')
    };
  };

  F['02_egypt'] = () => {
    const id = '02_egypt', p = palette('#eadcb8', '#2a1810', '#b8322a', '#2e8a55', '#e0ab38', '#f6f2e8');
    const colors = [p.red, '#2a58a8', p.gold, p.olive];
    const blockBand = (g, x, y, w, h) => {
      g.fillStyle = p.white; g.fillRect(x, y, w, h);
      const vertical = h > w, L = vertical ? h : w, step = 42;
      for (let u = 0, i = 0; u < L; u += step, i++) { g.fillStyle = colors[i % 4]; if (vertical) g.fillRect(x + 3, y + u + 3, w - 6, Math.min(step - 6, L - u - 3)); else g.fillRect(x + u + 3, y + 3, Math.min(step - 6, L - u - 3), h - 6); }
      g.strokeStyle = p.ink; g.lineWidth = 1.8; g.strokeRect(x, y, w, h);
    };
    return {
      id, name: '埃及墓室壁画', palette: p,
      background(g) { field(g, id, 'plaster', p.paper);
        g.drawImage(K().cached(`${id}/registers`, W, H, q => {
          blockBand(q, 14, 12, 1052, 30); blockBand(q, 15, 42, 28, 1500); blockBand(q, 1037, 42, 28, 1500);
          blockBand(q, 14, 1500, 1052, 32); q.fillStyle = '#1c2236'; q.fillRect(0, 1540, W, H - 1540);
          for (const x of [54, 138, 943, 1026]) line(q, [[x, 145], [x, 1465]], '#9a2b22', 2.3);
          for (const y of [480, 945, 1465]) line(q, [[46, y], [1030, y]], 'rgba(154,43,34,.24)', 1.5);
          cracks(q, W, 1500, 205, 9, 'rgba(90,70,50,.3)');
        }), 0, 0);
      },
      pattern(g, col) { return material(g, id, 'plaster', col); },
      plate(g, w, h, col) { g.save(); rectClip(g, w, h); plateBase(g, id, 'plaster', col, w, h); border(g, w, h, p.ink, 3, 2.5);
        if (w > 70 && h > 38) { blockBand(g, 5, 5, w - 10, Math.min(12, h * .15)); line(g, [[7, h - 8], [w - 7, h - 8]], p.red, 2); } g.restore(); },
      line(g, pts, col, lw) { g.save(); g.lineCap = 'round'; g.lineJoin = 'round'; line(g, pts, col, lw); g.restore(); },
      motifs(g, t, shot) { clipped(g, () => {
        const kinds = ['film', 'folder', 'photo', 'clock', 'wave', 'cut'];
        for (let i = 0; i < 18; i++) { const x = i % 2 ? 985 : 95, y = 220 + Math.floor(i / 2) * 142;
          const phase = mod(t * 1.8 - i * .24, 3.1), reveal = clamp(phase / .35);
          g.save(); g.setLineDash([Math.max(.1, reveal * 130), 900]); glyph(g, kinds[(i + (semantic(shot) === 'clock' ? 3 : 0)) % 6], x, y, .77, phase < .35 ? p.gold : colors[i % 4], null, Math.floor(t * 12) % 4); g.restore();
        }
        // Scarab carries the edited media disc along the upper register.
        const x = 170 + mod(t * 65, 740), y = 137, pose = Math.floor(t * 12) % 2;
        circle(g, x + 38, y, 22, p.red, p.ink, 2); glyph(g, 'film', x + 38, y, .28, p.gold);
        g.fillStyle = '#2c56b0'; g.beginPath(); g.ellipse(x - 7, y, 21, 14, 0, 0, TAU); g.fill(); g.strokeStyle = p.ink; g.lineWidth = 2; g.stroke();
        line(g, [[x - 24, y], [x + 8, y]], '#3fa6a0', 3);
        for (let k = -1; k <= 1; k++) for (const s of [-1, 1]) line(g, [[x + k * 11, y], [x + k * 11 - 4, y + s * 19], [x + k * 11 + (pose ? 8 : -8), y + s * 25]], p.ink, 2);
      }); },
      metadata: metadata('灰泥平涂、四色带、红色分栏、清晰等宽轮廓、逐笔铭文', '剪刀/底片/波形/文件夹改成分栏编辑符号；稿件和手机材料沿用灰泥彩绘、四色边框', '12fps水纹/波形步进、铭文描写、圣甲虫推动媒体日盘', '符号是主题改编的装饰，未声称为可翻译古埃及文字；不画原人物，真实图库保持照片')
    };
  };

  F['03_greek'] = () => {
    const id = '03_greek', p = palette('#dc6a2f', '#1b120d', '#8a2a37', '#54341e', '#e8904c', '#f6ead6');
    const meander = g => { g.fillStyle = p.paper; g.fillRect(0, 0, 96, 58); line(g, [[4,51],[4,7],[80,7],[80,40],[26,40],[26,22],[60,22],[60,30]], p.ink, 7); };
    const strip = () => K().cached(`${id}/meander`, W + 192, 58, q => { for (let x = 0; x < W + 192; x += 96) { q.save(); q.translate(x,0); meander(q); q.restore(); } });
    return {
      id, name: '希腊黑绘陶器', palette: p,
      background(g) { field(g, id, 'clay', p.paper);
        g.drawImage(K().cached(`${id}/vessel`, W, H, q => {
          // A broad vase banding system surrounds the edit field, with no room.
          q.fillStyle = p.ink; q.fillRect(0, 0, W, 38); q.fillRect(0, 1470, W, 38); q.fillRect(0, 1530, W, H - 1530);
          for (const x of [64, 1016]) { q.strokeStyle = p.ink; q.lineWidth = 13; q.beginPath(); q.moveTo(x, 210); q.bezierCurveTo(x - 38, 430, x + 35, 1140, x, 1410); q.stroke(); }
          for (let y = 260, k = 0; y < 1460; y += 102, k++) for (const x of [64, 1016]) rosette(q, x, y, 22, k * .4, [p.ink, p.ink, p.red], p.gold, 8);
          cracks(q, W, 1460, 306, 7, 'rgba(52,18,6,.35)', 'rgba(255,190,140,.15)');
        }), 0, 0);
      },
      pattern(g, col) { return material(g, id, 'clay', col); },
      plate(g, w, h, col) { g.save(); rectClip(g, w, h); plateBase(g, id, 'clay', col, w, h);
        const band = Math.min(17, h * .16); g.fillStyle = p.ink; g.fillRect(0,0,w,band); g.fillRect(0,h-band,w,band);
        g.fillStyle = p.red; g.fillRect(0,h-band,w,Math.min(5,band * .35));
        for (let x = 10; x < w; x += 19) circle(g, x, Math.max(3, band / 2), Math.min(2, band / 4), p.white);
        border(g,w,h,p.ink,3,3); border(g,w,h,p.gold,Math.min(7,h*.2),1.3); g.restore(); },
      line(g, pts, col, lw) { g.save(); g.lineJoin='round'; g.lineCap='round'; line(g,pts,p.ink,Math.max(3,lw+2)); line(g,pts,col===p.ink?p.gold:col,Math.max(1.5,lw*.45)); g.restore(); },
      motifs(g,t,shot) { clipped(g,()=>{
        g.drawImage(strip(), -mod(t * 48,96), 42); g.save(); g.translate(W,1468); g.scale(-1,-1); g.drawImage(strip(), -mod(t*30,96),0); g.restore();
        for (const [x,y,k] of [[79,595,0],[1001,1040,1]]) { g.save();g.translate(x,y);g.rotate(.12*Math.sin(t*4+k)); glyph(g,semantic(shot),0,0,.95,p.gold,p.ink,t*2);g.restore(); }
        for(let i=0;i<5;i++) { const x=260+i*135,y=1432+Math.sin(t*3.5+i)*4; rosette(g,x,y,16,t*.9*(i%2?1:-1),[p.ink,p.red,p.ink],p.gold); }
      }); },
      metadata: metadata('陶土水平拉坯纹、黑釉边带、陶土刻线、紫红附加色与白点', '文件夹/文稿采用黑釉纹带；工具轮廓先黑剪影再刻亮线，编辑母题嵌在陶瓶饰带', '上下反向滚动回纹、悬挂工具摆动、玫瑰纹缓慢转动', '主体彩色面积为可读性保留，未把真实照片量化为黑绘；没有原酒神/少女/猫')
    };
  };

  F['04_roman'] = () => {
    const id='04_roman',p=palette('#e4ddcd','#46322a','#a8322a','#6f9341','#d0a23c','#f5f1e8');
    const tilePattern=(g,col) => K().pattern(g,`${id}/tessera/${col}`,192,192,q=>{
      const r=K().rng(407),s=16;q.fillStyle='#70675c';q.fillRect(0,0,192,192);
      for(let row=0;row<13;row++) for(let i=-1;i<13;i++) { const x=i*s+(row%2)*8,y=row*s,w=13+r()*2,h=13+r()*2,a=(r()-.5)*.11;
        q.save();q.translate(x+8,y+8);q.rotate(a);q.fillStyle=K().shade(col,(r()-.5)*.12);q.fillRect(-w/2,-h/2,w,h);q.fillStyle='rgba(255,255,255,.16)';q.fillRect(-w/2,-h/2,w,1.6);q.fillStyle='rgba(0,0,0,.15)';q.fillRect(w/2-1.6,-h/2,1.6,h);q.restore();
      }
    });
    const ornamental=()=>K().cached(`${id}/stone_border`,W+144,70,q=>{
      q.fillStyle=tilePattern(q,p.white);q.fillRect(0,0,W+144,70);
      // Fixed stone positions, sampled black/white at centres of a spiral band.
      for(let y=0;y<70;y+=10) for(let x=0;x<W+144;x+=10) { const u=mod(x,72),dx=u-36,dy=y-34,rad=Math.hypot(dx,dy),angle=Math.atan2(dy,dx);const z=mod(angle+rad*.14,TAU); if(z<1.38 || y>58) {q.fillStyle='#2b2520';q.fillRect(x+1,y+1,8,8);q.fillStyle='rgba(255,255,255,.12)';q.fillRect(x+1,y+1,8,1);} }
    });
    return {
      id,name:'庞贝马赛克',palette:p,
      background(g) { g.fillStyle=tilePattern(g,p.paper);g.fillRect(0,0,W,H);g.drawImage(K().cached(`${id}/archive_mosaic`,W,H,q=>{
        q.fillStyle=tilePattern(q,p.red);q.fillRect(82,154,14,1240);q.fillRect(984,154,14,1240);q.fillRect(96,1450,888,18);
        for(let i=0;i<14;i++) {const x=i%2?1030:50,y=230+Math.floor(i/2)*180;q.fillStyle=tilePattern(q,i%3?p.gold:p.red);q.fillRect(x-15,y-15,30,30);q.fillStyle=tilePattern(q,p.ink);q.fillRect(x-5,y-5,10,10);}
        q.fillStyle=tilePattern(q,p.red);q.fillRect(0,1540,W,H-1540);
      }),0,0); },
      pattern:tilePattern,
      plate(g,w,h,col) {g.save();rectClip(g,w,h);g.fillStyle=tilePattern(g,col);g.fillRect(0,0,w,h);border(g,w,h,p.ink,3,3);border(g,w,h,p.white,9,3);if(w>120&&h>80){g.fillStyle=tilePattern(g,p.red);g.fillRect(12,h-22,w-24,9);}g.restore();},
      line(g,pts,col,lw) {g.save();g.lineJoin='round';g.lineCap='square';line(g,pts,p.white,lw+7);line(g,pts,tilePattern(g,col),lw+1);g.restore();},
      motifs(g,t,shot) {clipped(g,()=>{g.drawImage(ornamental(),-mod(t*38,72),48);g.save();g.translate(W,1534);g.scale(-1,-1);g.drawImage(ornamental(),-mod(t*38,72),0);g.restore();
        for(let i=0;i<5;i++){const x=185+i*175,y=1430;circle(g,x,y,12,p.ink);const k=mod(Math.floor(t*5)-i,5);circle(g,x,y,8,k===0?p.gold:p.red);}
        const k=Math.floor(t*6)%6;g.save();g.translate(1028,780);g.rotate(k*TAU/6);glyph(g,semantic(shot),0,0,.63,p.ink,p.white,k);g.restore();
      });},
      metadata:metadata('固定错缝tessera布局、灰浆间隙、石块倒角明暗、白色石圈边缘','手机/稿件/波形/文件夹都用镶嵌石表面，实体轮廓加白石晕圈','周期石块卷涡带平移、归档格子的颜色逐格传播、边栏媒体图腾分步旋转','主题重建采用缓存平移边带和规则错缝石块；未复制原scene昂贵的距离场/Voronoi轮廓布局，不把真人照片碎石化')
    };
  };

  F['05_gothic'] = () => {
    const id='05_gothic',p=palette('#ecdfc0','#2b1a12','#c3262e','#24449e','#d9a63a','#f8f2e2');
    const arch=(x,y,w,h)=>{const a=new Path2D();a.moveTo(x,y+h);a.lineTo(x,y+h*.37);a.quadraticCurveTo(x,y+h*.12,x+w/2,y);a.quadraticCurveTo(x+w,y+h*.12,x+w,y+h*.37);a.lineTo(x+w,y+h);a.closePath();return a;};
    const illuminated=(g,col)=>K().pattern(g,`${id}/illuminated/${col}`,160,160,q=>{
      q.fillStyle=material(q,id,'foil',col);q.fillRect(0,0,160,160);
      for(let y=-20;y<180;y+=40)for(let x=-20;x<180;x+=40){line(q,[[x,y+20],[x+20,y],[x+40,y+20],[x+20,y+40],[x,y+20]],'rgba(85,50,14,.25)',1.3);circle(q,x+20,y+20,2,'rgba(255,240,180,.65)');}
    });
    return {
      id,name:'哥特泥金手抄本',palette:p,
      background(g){field(g,id,'plaster',p.paper);g.drawImage(K().cached(`${id}/scriptorium`,W,H,q=>{
        q.fillStyle=illuminated(q,p.gold);q.fill(arch(122,164,836,1260));q.strokeStyle=p.ink;q.lineWidth=4;q.stroke(arch(122,164,836,1260));
        for(const x of [28,998]) {q.fillStyle=p.olive;q.fill(arch(x,295,54,780));q.save();q.clip(arch(x,295,54,780));for(let y=295,k=0;y<1080;y+=36,k++){q.fillStyle=k%2?p.red:p.olive;q.fillRect(x,y,54,36);line(q,[[x,y],[x+54,y+36]],p.gold,2);circle(q,x+27,y+18,3,p.white);}q.restore();q.strokeStyle=p.ink;q.lineWidth=3;q.stroke(arch(x,295,54,780));}
        for(let x=30,k=0;x<W;x+=48,k++){q.fillStyle=k%2?p.red:p.olive;q.fillRect(x,1472,44,28);circle(q,x+22,1486,3,p.white);}
        q.fillStyle=material(q,id,'plaster',p.paper);q.fillRect(0,1540,W,H-1540);
      }),0,0);},
      pattern:illuminated,
      plate(g,w,h,col,seed,t){g.save();rectClip(g,w,h);plateBase(g,id,'plaster',col,w,h);border(g,w,h,p.ink,3,3);border(g,w,h,p.gold,8,3);const s=Math.min(16,h*.15);if(w>70&&h>45){for(let x=12,k=0;x<w-12;x+=22,k++) circle(g,x,Math.max(10,h-12),Math.min(2.3,s*.2),k%2?p.olive:p.red);g.fillStyle=illuminated(g,p.gold);g.fillRect(6,6,s,s);const sx=mod(t*48,w+60)-30;const gl=g.createLinearGradient(sx-20,0,sx+20,0);gl.addColorStop(0,'rgba(255,248,210,0)');gl.addColorStop(.5,'rgba(255,248,210,.4)');gl.addColorStop(1,'rgba(255,248,210,0)');g.fillStyle=gl;g.fillRect(6,6,s,s);}g.restore();},
      line(g,pts,col,lw){g.save();g.lineJoin='round';line(g,pts,p.ink,lw+2);line(g,pts,col,lw);g.restore();},
      motifs(g,t,shot){clipped(g,()=>{
        for(const sd of [-1,1]) {const x=sd<0?90:990,pts=[];for(let i=0;i<46;i++){const y=160+i*28;pts.push([x+Math.sin(y*.011+t*1.6+sd)*13,y]);}line(g,pts,p.ink,2.8);
          for(let i=3;i<44;i+=3){const [px,py]=pts[i];leaf(g,px,py,24,10,sd*.8+Math.sin(t*3+i)*.28,[p.olive,p.red,p.gold][i%3],p.ink);}
        }
        for(const [x,y,rot]of [[72,1180,0],[1009,1380,1]]) {g.save();g.translate(x,y);g.rotate(Math.sin(t*2.5+rot)*.12);glyph(g,semantic(shot),0,0,.73,p.ink,p.gold,t);g.restore();}
        const a=.5+.5*Math.sin(t*5);for(const x of [55,1025]){g.globalAlpha=.18*a;circle(g,x,530,24,p.white);g.globalAlpha=1;}
      });},
      metadata:metadata('羊皮纸、带细拉丝的泥金、菱格压花、尖拱、红蓝彩玻璃、粗墨外轮廓','编辑现场改为手抄本画页；文稿/文件夹为泥金边手稿，手机/轨道填压花彩绘','页边藤蔓与叶片摇摆、金色工具摆动、彩窗光点和小金块局部扫光','泥金亮带限定于小金块与背景，不覆盖真人脸；装饰不含上游骑士/人脸猫')
    };
  };

  F['06_renaissance'] = () => {
    const id='06_renaissance',p=palette('#bba987','#332519','#8e3329','#65785d','#c4a45e','#eee2c6');
    const dust=points(607,28),oil=(g,col)=>material(g,id,'oil',col);
    return {
      id,name:'文艺复兴油画',palette:p,
      background(g){field(g,id,'oil','#493c2a');g.drawImage(K().cached(`${id}/perspective_edit`,W,H,q=>{
        const sky=q.createLinearGradient(0,120,0,820);sky.addColorStop(0,'#829ba1');sky.addColorStop(.52,'#d3d8cc');sky.addColorStop(1,'#6e7c61');q.fillStyle=sky;q.fillRect(115,150,850,730);
        for(let j=0;j<4;j++){const pts=[[115,880]];for(let x=115;x<=965;x+=8){const y=480+j*82-Math.abs(P().fbm(x*.009,7+j,4))*130;pts.push([x,y]);}pts.push([965,880]);q.fillStyle=['#b2c0b9','#91a4a0','#7c9188','#667956'][j];q.fill(poly(pts));}
        const river=[];for(let i=0;i<=28;i++){const u=i/28;river.push([520+Math.sin(u*7)*75*u,600+u*310]);}for(let i=0;i<river.length-1;i++)line(q,[river[i],river[i+1]],'#d2d8ca',3+i*.35);
        q.strokeStyle='#66513a';q.lineWidth=12;q.strokeRect(108,144,864,744);
        // Perspective archive plane. Receding folio tiles, not the source room.
        const horizon=820;for(let row=0;row<6;row++){const a=row/6,b=(row+1)/6,y0=horizon+a*a*720,y1=horizon+b*b*720;for(let col=-5;col<5;col++){const x0=540+col*135*(.2+a*1.3),x1=540+(col+1)*135*(.2+a*1.3),x2=540+(col+1)*135*(.2+b*1.3),x3=540+col*135*(.2+b*1.3);q.fillStyle=(row+col)%2?'#756345':'#4c3828';q.fill(poly([[x0,y0],[x1,y0],[x2,y1],[x3,y1]]));}}
        q.fillStyle=oil(q,'#332519');q.fillRect(0,1540,W,H-1540);
        cracks(q,W,H,619,38,'rgba(32,20,9,.13)','rgba(255,230,190,.07)');
      }),0,0);const shade=g.createRadialGradient(460,650,180,540,700,1050);shade.addColorStop(0,'rgba(15,8,3,0)');shade.addColorStop(1,'rgba(15,8,3,.48)');g.fillStyle=shade;g.fillRect(0,0,W,H);},
      pattern:oil,
      plate(g,w,h,col){g.save();rectClip(g,w,h);plateBase(g,id,'oil',col,w,h);const volume=g.createLinearGradient(0,0,w,h);volume.addColorStop(0,'rgba(255,240,205,.28)');volume.addColorStop(.35,'rgba(255,240,205,.05)');volume.addColorStop(1,'rgba(25,10,3,.27)');g.fillStyle=volume;g.fillRect(0,0,w,h);border(g,w,h,'rgba(60,40,20,.4)',2,2);g.restore();},
      line(g,pts,col,lw){g.save();g.lineJoin='round';g.lineCap='round';line(g,pts,K().alpha(p.ink,.18),lw+3);line(g,pts,col,lw);g.restore();},
      motifs(g,t,shot){clipped(g,()=>{
        dust.forEach(([x,y,s,ph],i)=>{const xx=i%2?990+Math.sin(t*.6+ph)*30:80+Math.sin(t*.6+ph)*25,yy=mod(y-t*(8+s*13),CH);circle(g,xx,yy,.8+s*1.6,K().alpha('#f4e1b5',.18+.18*Math.sin(t*2+ph)));});
        // A flying folio uses articulated paper leaves, recalling mechanical
        // studies without drawing the source ornithopter's pilot.
        const x=80+mod(t*42,100),y=300+Math.sin(t*2.3)*16,flap=.3+.7*(.5+.5*Math.sin(t*8));g.save();g.translate(x,y);g.rotate(-.16);g.fillStyle=oil(g,p.white);g.fill(poly([[-5,0],[-62,-44*flap],[-72,22],[-6,15]]));g.fill(poly([[5,0],[62,-44*flap],[72,22],[6,15]]));line(g,[[-66,8],[0,12],[66,8]],p.ink,1.5);g.restore();
        glyph(g,semantic(shot),1008,1350,.7,p.gold,null,t*.6);
      });},
      metadata:metadata('空气透视蓝灰远山、真实投影档案台、油彩经纬与细刷痕、软明暗体积','编辑工具/稿纸/波形托板带油彩肌理与左上受光；整理时间以透视档案格和飞页表达','机械折页扑动、光中浮尘、边栏工具缓转','保持照片清晰，未对照片施加sfumato模糊；没有原房间、少女、猫或扑翼机驾驶者')
    };
  };

  F['10_nouveau'] = () => {
    const id='10_nouveau',p=palette('#e5ddbd','#4e3320','#d9706a','#6f9a80','#c9a24a','#f6eedb');
    const litho=(g,col)=>K().pattern(g,`${id}/litho_ornament/${col}`,192,192,q=>{q.fillStyle=material(q,id,'litho',col);q.fillRect(0,0,192,192);for(let y=24,row=0;y<210;y+=48,row++)for(let x=24+(row%2)*24;x<210;x+=48){circle(q,x,y,9,null,'rgba(90,104,64,.22)',1.3);circle(q,x,y,2,'rgba(90,104,64,.2)');}});
    const whip=(g,pts,w,col,edge=p.ink)=>{const path=window.KIT.ribbon(pts,q=>1+(w-1)*Math.sin(Math.PI*q));g.fillStyle=col;g.fill(path);if(edge){g.strokeStyle=edge;g.lineWidth=1.5;g.stroke(path);}};
    return {
      id,name:'新艺术慕夏海报',palette:p,
      background(g){field(g,id,'litho',p.paper);g.drawImage(K().cached(`${id}/poster_edit`,W,H,q=>{
        const gr=q.createLinearGradient(0,55,0,1500);gr.addColorStop(0,'#b9cba0');gr.addColorStop(.55,'#cfd3a6');gr.addColorStop(1,'#ecc9a2');q.fillStyle=gr;q.fillRect(36,55,1008,1465);q.globalAlpha=.28;q.fillStyle=litho(q,p.paper);q.fillRect(36,55,1008,1465);q.globalAlpha=1;
        q.strokeStyle=p.gold;q.lineWidth=6;q.strokeRect(36,55,1008,1465);q.strokeStyle=p.ink;q.lineWidth=1.8;q.strokeRect(30,49,1020,1477);q.strokeRect(44,63,992,1449);
        circle(q,540,330,245,'#ddbf80',p.ink,2.5);circle(q,540,330,218,'#ebb8b2',p.ink,2);circle(q,540,330,192,'#cad4b0',p.ink,2);
        for(let i=0;i<30;i++){const a=i/30*TAU;leaf(q,540+Math.cos(a)*205,330+Math.sin(a)*205,20,6,a+Math.PI/2,p.gold,p.ink);}
        q.fillStyle='#6f8f63';q.fillRect(36,1470,1008,50);
      }),0,0);},
      pattern:litho,
      plate(g,w,h,col,seed,t){g.save();rectClip(g,w,h);g.fillStyle=litho(g,col);g.fillRect(0,0,w,h);border(g,w,h,p.ink,2,4);border(g,w,h,p.gold,7,1.5);
        if(w>150&&h>65){const pts=[];for(let i=0;i<=24;i++){const u=i/24;pts.push([12+u*(w-24),h-13+Math.sin(u*TAU*2-t*2)*3]);}whip(g,pts,5,p.gold);for(const x of [14,w-14])spiral(g,x,h-14,7,t*.1,p.ink,1,1.1);}g.restore();},
      line(g,pts,col,lw){g.save();if(pts.length>100)line(g,pts,col,lw);else{const dense=pts.length<20?window.KIT.densify(pts,4):pts;whip(g,dense,lw*1.4,col,null);}g.restore();},
      motifs(g,t,shot){clipped(g,()=>{
        for(const side of [-1,1]){const base=side<0?77:1003,pts=[];for(let i=0;i<=42;i++){const u=i/42;pts.push([base+Math.sin(u*8-t*2+side)*27*u,1435-u*1030]);}whip(g,pts,10,p.olive);for(let k=5;k<40;k+=6){const [x,y]=pts[k];leaf(g,x,y,40,12,side*.9+Math.sin(t*2+k)*.15,p.olive,p.ink);}rosette(g,pts[40][0],pts[40][1],32,Math.sin(t*2.5+side)*.12,[side<0?p.red:p.white,p.white,p.gold],p.ink,side<0?5:6);}
        g.save();g.translate(540,330);g.rotate(t*.12);for(let k=0;k<18;k++){const a=k/18*TAU;circle(g,Math.cos(a)*234,Math.sin(a)*234,4,p.white,p.ink,1);}g.restore();
        const sy=1025+Math.sin(t*1.7)*11;glyph(g,semantic(shot),1000,sy,.7,p.ink,p.gold,t);
      });},
      metadata:metadata('石版纸斑驳、粗外轮廓/细内线、可变宽鞭线、螺旋收尾、圆形装饰框','卷草变为编辑连线与波形；稿件、手机、底片是带植物纹样的海报印刷面','边栏长茎/花头摇摆、磁带式卷草行波、圆钉光环转动','只用工具与植物母题，没有慕夏人物；高采样波形用轻量线条保留声音可读性')
    };
  };

  F['18_klimt'] = () => {
    const id='18_klimt',p=palette('#c49434','#1d140c','#a8322b','#3e7556','#e8c46b','#f4efe2');
    const flakes=points(1807,18);
    const ornament=(g,col)=>K().pattern(g,`${id}/gold_weave/${col}`,240,240,q=>{
      q.fillStyle=material(q,id,'foil',col);q.fillRect(0,0,240,240);const r=K().rng(1819);
      for(let i=0;i<25;i++){const x=r()*240,y=r()*240,s=7+r()*9;if(i%3===0){q.fillStyle=i%2?p.white:p.ink;q.fillRect(x,y,s,s*2.3);q.strokeStyle=p.gold;q.lineWidth=1;q.strokeRect(x,y,s,s*2.3);}else if(i%3===1){circle(q,x,y,s,p.red);circle(q,x,y,s*.64,p.white);circle(q,x,y,s*.3,'#2a4a9a');}else{circle(q,x,y,s,p.ink);spiral(q,x,y,s*.86,0,p.gold,1.2);}}
    });
    return {
      id,name:'克里姆特金色时期',palette:p,
      background(g){field(g,id,'foil','#9d742c');g.drawImage(K().cached(`${id}/gold_archive`,W,H,q=>{
        q.fillStyle=ornament(q,'#b38b39');q.fillRect(0,80,W,1430);
        for(let y=90;y<1510;y+=18)for(const x of [30,1032]){q.fillStyle=Math.floor(y/18)%2?p.ink:p.white;q.fillRect(x,y,16,16);}
        for(const x of [86,994]) {line(q,[[x,1460],[x,330]],p.ink,9);for(let i=0;i<7;i++)spiral(q,x,450+i*140,46,i%2?Math.PI:0,p.gold,6,1.8);}
        q.fillStyle=material(q,id,'foil','#9d742c');q.fillRect(0,1540,W,H-1540);
      }),0,0);},
      pattern:ornament,
      plate(g,w,h,col,seed,t){g.save();rectClip(g,w,h);g.fillStyle=material(g,id,'foil',col);g.fillRect(0,0,w,h);border(g,w,h,p.ink,3,3);border(g,w,h,p.gold,7,1.5);
        if(w>95&&h>60){for(let i=0;i<Math.min(5,Math.floor(w/70));i++){const x=28+i*70,y=h-20;circle(g,x,y,12,p.ink);spiral(g,x,y,10,t*(i%2?2:-2),p.gold,1.8);}
          const sx=mod(t*90,w+240)-120,gl=g.createLinearGradient(sx-90,0,sx+90,0);gl.addColorStop(0,'rgba(255,245,186,0)');gl.addColorStop(.5,'rgba(255,245,186,.17)');gl.addColorStop(1,'rgba(255,245,186,0)');g.fillStyle=gl;g.fillRect(0,0,w,h);}g.restore();},
      line(g,pts,col,lw){g.save();g.lineJoin='round';line(g,pts,p.ink,lw+2);line(g,pts,col,lw);g.restore();},
      motifs(g,t,shot){clipped(g,()=>{flakes.forEach(([x,y,s,ph],i)=>{const xx=i%2?1000+Math.sin(t+ph)*35:77+Math.sin(t+ph)*28,yy=mod(y+t*(32+s*44),1490);g.save();g.translate(xx,yy);g.rotate(t*.8+ph);g.scale(Math.cos(t*3+ph),1);g.fillStyle=p.gold;g.fillRect(-5-s*4,-5-s*4,10+s*8,10+s*8);g.strokeStyle=p.ink;g.lineWidth=1;g.strokeRect(-5-s*4,-5-s*4,10+s*8,10+s*8);g.restore();});
        for(const [x,y,i] of [[78,260,0],[1000,1130,1]]){circle(g,x,y,31,p.ink,p.gold,2);spiral(g,x,y,27,t*(i?1.6:-1.6),p.gold,3);glyph(g,semantic(shot),x,y,.42,p.white,null,t);}
      });},
      metadata:metadata('金箔拉丝/拼接、褐金背景、同心圆/黑白长方块、深底金螺旋','手机、档案、稿件和磁带由金箔平面装饰构成，真实人像与平面装饰形成反差','对象上金螺旋反向转动、限定托板的金箔流光、侧边金屑翻面下落','装饰只附着工具和托板，真人脸保留原照片；未复用原金袍人物、猫和房间')
    };
  };

  F['20_dunhuang'] = () => {
    const id='20_dunhuang',p=palette('#a5452f','#5a2414','#a5452f','#3f8f6e','#d8b05a','#ecdfc4');
    const pet=points(2007,14),mineral=(g,col)=>material(g,id,'mineral',col,320);
    const ribbon=(g,pts,w,col)=>{const path=window.KIT.ribbon(pts,q=>w*(.8+.2*Math.sin(q*9))*(1-q*.2));g.fillStyle=mineral(g,col);g.fill(path);g.strokeStyle=p.ink;g.lineWidth=2.4;g.stroke(path);line(g,pts,p.white,1.5);};
    return {
      id,name:'敦煌矿物壁画',palette:p,
      background(g){field(g,id,'mineral',p.paper);g.drawImage(K().cached(`${id}/cave_edit`,W,H,q=>{
        q.fillStyle='#7a3020';q.fillRect(0,0,W,34);for(let x=0,k=0;x<W;x+=60,k++){q.fillStyle=[p.olive,'#2f5f8f',p.white,p.red][k%4];q.fill(poly([[x,34],[x+60,34],[x+30,84]]));circle(q,x+30,91,4,p.gold,p.ink,1.5);}
        q.fillStyle=mineral(q,'#2f5f8f');q.fillRect(122,150,836,1270);q.strokeStyle=p.olive;q.lineWidth=19;q.strokeRect(122,150,836,1270);q.strokeStyle=p.ink;q.lineWidth=3;q.strokeRect(111,140,858,1290);
        for(const x of [96,984])for(let y=240;y<1500;y+=150)rosette(q,x,y,29,y*.01,[p.olive,p.white,'#5a86b0',p.gold],p.ink,8);
        q.fillStyle=mineral(q,p.paper);q.fillRect(0,1540,W,H-1540);cracks(q,W,CH,2013,34,'rgba(50,25,15,.22)');
      }),0,0);},
      pattern:mineral,
      plate(g,w,h,col){g.save();rectClip(g,w,h);g.fillStyle=mineral(g,col);g.fillRect(0,0,w,h);border(g,w,h,p.ink,3,2.6);border(g,w,h,p.olive,7,2);if(w>100&&h>50)for(const x of [15,w-15])rosette(g,x,h-15,9,0,[p.white,p.olive,p.gold],p.ink,4);g.restore();},
      line(g,pts,col,lw){g.save();g.lineCap='round';g.lineJoin='round';line(g,pts,col,lw);g.restore();},
      motifs(g,t,shot){clipped(g,()=>{
        // Flying film ribbons carry the apsara movement language without a
        // new human figure: broad arch, S-tail, mineral paint and perforations.
        for(const side of [-1,1]){const pts=[];for(let i=0;i<=35;i++){const u=i/35;pts.push([side<0?72+Math.sin(u*5.8-t*3.4)*45:1008-Math.sin(u*5.8-t*3.4+1.3)*45,240+u*1140-u*u*100]);}ribbon(g,pts,24,side<0?p.olive:'#5a86b0');g.fillStyle=p.gold;for(let i=2;i<pts.length;i+=4)circle(g,pts[i][0],pts[i][1],2.5,p.gold);}
        pet.forEach(([x,y,s,ph],i)=>{const xx=i%2?1000+Math.sin(t*1.5+ph)*35:70+Math.sin(t*1.5+ph)*35,yy=mod(y+t*(32+s*20),1490);g.save();g.translate(xx,yy);g.scale(1,.25+.75*Math.abs(Math.cos(t*3+ph)));rosette(g,0,0,8+s*5,t*.5,[p.white,p.olive,p.red,p.gold],p.ink,4);g.restore();});
        glyph(g,semantic(shot),82,1430,.64,p.ink,p.gold,t);
      });},
      metadata:metadata('土红地仗、石青/石绿矿物色、铁线描、低频块状剥落、卷草垂幔与莲花','底片和磁带转为飞天披帛式宽飘带；稿件/波形/文件夹带露白灰地仗的矿物彩绘','沿侧边飘带的大弧/S尾行波、四瓣天花翻面落下','不绘制新飞天人物；剥落只存在背景/对象表面，未让裂纹或烟熏跨过真实照片')
    };
  };

  F['21_kusama'] = () => {
    const id='21_kusama',p=palette('#d8181e','#141210','#d8181e','#f6d02a','#f6d02a','#fbf6ee');
    const grids=new Map(),pats=new WeakMap();
    const grid=(w,h,sp,seed)=>{const key=`${w}/${h}/${sp}/${seed}`;if(!grids.has(key)){const r=K().rng(seed),o=[];for(let y=-sp,j=0;y<h+sp;y+=sp*.87,j++)for(let x=-sp+(j%2)*sp*.5;x<w+sp;x+=sp)o.push([x+(r()-.5)*sp*.18,y+(r()-.5)*sp*.18,.78+r()*.4,r()*TAU]);grids.set(key,o);}return grids.get(key);};
    const dotfield=(g,w,h,col,t,seed,sp=56)=>{g.fillStyle=col;g.fillRect(0,0,w,h);const dc=col===p.olive||col===p.gold?p.ink:(col===p.white?K().alpha(p.red,.14):p.white);grid(w,h,sp,seed).forEach(([x,y,s,rot])=>{const a=.85+.22*Math.sin(Math.hypot(x-w*.43,y-h*.52)*.025-t*5);g.fillStyle=dc;g.beginPath();g.ellipse(x,y,sp*.21*s*a,sp*.19*s*a,rot,0,TAU);g.fill();});};
    const pattern=(g,col,t)=>{const pat=K().pattern(g,`${id}/dots/${col}`,112,96,q=>{dotfield(q,112,96,col,0,2121,56);});if(pat.setTransform)pat.setTransform(new DOMMatrix().translate(0,mod(t*19,96)));pats.set(g,pat);return pat;};
    return {
      id,name:'草间弥生无限波点',palette:p,
      background(g,t){g.fillStyle=p.red;g.fillRect(0,0,W,H);clipped(g,()=>{
        grid(W,CH,112,2107).forEach(([x,y,s,rot])=>{const rad=24*s*(.85+.25*Math.sin(Math.hypot(x-540,y-820)*.012-t*6));g.fillStyle=p.white;g.beginPath();g.ellipse(x,y,rad,rad*.93,rot,0,TAU);g.fill();circle(g,x+43,y+46,7*s*(.85+.2*Math.sin(t*4+rot)),p.white);});
        // Recursive media aperture: regular light grid gives a true repeated
        // mirror-space cue rather than arbitrary bokeh.
        g.fillStyle='rgba(5,4,10,.2)';g.fillRect(125,250,830,1020);g.strokeStyle=p.gold;g.lineWidth=9;g.strokeRect(125,250,830,1020);
        for(let z=0;z<4;z++){const depth=mod(z/4-t*.085,1),s=.22+.7*depth;g.strokeStyle=K().alpha(p.white,.11+.1*depth);g.lineWidth=2;g.strokeRect(540-380*s,730-440*s,760*s,880*s);for(let k=0;k<9;k++){const x=540+(k-4)*86*s;circle(g,x,730-425*s,2+2*depth,[p.gold,p.white,'#ff7ad0','#3aa8ff'][k%4]);}}
      });},
      pattern,
      plate(g,w,h,col,seed,t){g.save();rectClip(g,w,h);dotfield(g,w,h,col,t,2101+(seed||0),clamp(Math.min(w,h)*.22,24,58));border(g,w,h,p.ink,2,4.5);g.restore();},
      line(g,pts,col,lw){g.save();g.lineJoin='round';g.lineCap='round';line(g,pts,p.ink,lw+3);line(g,pts,col,lw);g.restore();},
      motifs(g,t,shot){clipped(g,()=>{
        for(const [x,y,k]of [[76,390,0],[1000,1320,1]]){circle(g,x,y,43,p.gold,p.ink,4);for(let i=0;i<8;i++){const a=i/8*TAU+t*.6;circle(g,x+Math.cos(a)*29,y+Math.sin(a)*29,5*(.9+.22*Math.sin(t*5+i)),p.ink);}glyph(g,semantic(shot),x,y,.55,p.ink,null,t);}
      });},
      metadata:metadata('大小双层六角波点、从媒体中心传播的半径行波、对象波点下移、规则递归镜格','手机/照片框/稿件/波形/文件夹全成为带边缘分界的波点实体','波点连续胀缩、点沿对象流下、媒体镜格纵深循环','半径设上限防止吞成纯白；主体有4.5px黑边保留可读性，真实人物照片没有脸部波点')
    };
  };

  F['30_matisse'] = () => {
    const id='30_matisse',p=palette('#1d4fb8','#141414','#e2322a','#1f9a5a','#f7d21e','#f7f3e8');
    const shapes=new Map(),cut=(pts,seed)=>P().cut(pts,seed,18,2.3);
    const capsule=(A,th,L,w)=>{const d=[Math.sin(th),-Math.cos(th)],n=[-d[1],d[0]],tip=[A[0]+d[0]*(L-w/2),A[1]+d[1]*(L-w/2)],o=[[A[0]+n[0]*w*.4,A[1]+n[1]*w*.4]];for(let k=0;k<=7;k++){const a=Math.atan2(n[1],n[0])-k/7*Math.PI;o.push([tip[0]+Math.cos(a)*w/2,tip[1]+Math.sin(a)*w/2]);}o.push([A[0]-n[0]*w*.4,A[1]-n[1]*w*.4]);return o;};
    const algae=(key,len,width)=>{if(!shapes.has(key)){const path=new Path2D();path.addPath(cut(capsule([0,0],0,len,width*.24),3001+key));for(let i=0;i<7;i++){const u=.15+i*.105;path.addPath(cut(capsule([Math.sin(u*1.6)*len*.1,-u*len],(i%2?1:-1)*(1.05-.55*u),width*(1-.45*u),width*(.34-.12*u)),3009+key+i));}shapes.set(key,path);}return shapes.get(key);};
    const gouache=(g,col)=>material(g,id,'gouache',col);
    const shadow=(g,fn)=>{g.save();g.shadowColor='rgba(10,20,40,.28)';g.shadowOffsetX=5;g.shadowOffsetY=6;g.shadowBlur=4;fn();g.restore();};
    return {
      id,name:'马蒂斯爵士剪纸',palette:p,
      background(g){g.drawImage(K().cached(`${id}/polynesia_edit`,W,H,q=>{
        q.fillStyle=p.white;q.fillRect(0,0,W,H);for(let j=0;j<7;j++)for(let i=0;i<5;i++){const x=i*216,y=j*220;q.fillStyle=gouache(q,(i+j)%2?p.paper:'#4f95dc');q.fill(cut([[x-2,y-2],[x+218,y],[x+216,y+222],[x-2,y+220]],3019+i+j*7));}
        q.fillStyle=gouache(q,p.olive);q.fill(cut([[0,1450],[W,1442],[W,H],[0,H]],3031));q.fillStyle=p.ink;q.fill(cut([[0,1440],[W,1433],[W,1460],[0,1470]],3028));
      }),0,0);},
      pattern:gouache,
      plate(g,w,h,col,seed,t){const key=`${id}/cutplate/${w}/${h}/${seed||0}`,path=shapes.get(key)||cut([[2,2],[w-2,0],[w,h-2],[0,h]],3079+(seed||0));shapes.set(key,path);g.save();shadow(g,()=>{g.fillStyle=gouache(g,col);g.fill(path);});if(w>100&&h>55){g.fillStyle=p.gold;g.fill(cut([[w-21,7],[w-8,4],[w-5,21],[w-19,24]],301));}g.restore();},
      line(g,pts,col,lw){g.save();g.lineCap='butt';g.lineJoin='miter';if(pts.length>100)line(g,pts,col,lw);else{const pp=pts.map(([x,y],i)=>[x+Math.sin(i*2.71)*1.2,y+Math.cos(i*1.31)*1.2]);line(g,pp,K().alpha(p.ink,.15),lw+3);line(g,pp,col,lw);}g.restore();},
      motifs(g,t,shot){clipped(g,()=>{
        for(const [x,y,len,wd,key,ph,col]of [[75,1340,570,82,1,0,p.white],[1010,1080,680,90,2,1.4,p.white],[65,700,330,65,3,2.2,p.gold],[1014,1470,300,60,4,3.3,'#ef6f9a']]){g.save();g.translate(x,y);g.rotate(Math.sin(t*2.8+ph)*.12);g.scale(.94+.06*Math.sin(t*3.6+ph),1);shadow(g,()=>{g.fillStyle=gouache(g,col);g.fill(algae(key,len,wd));});g.restore();}
        for(let i=0;i<7;i++){const x=i%2?1000:75,y=240+i*162,rr=11+6*(.8+.2*Math.sin(t*6+i));g.save();g.translate(x,y);g.rotate(t*(i%2?.4:-.4));g.fillStyle=p.gold;g.fill(cut(Array.from({length:10},(_,k)=>{const a=k/10*TAU,r=k%2?rr*.42:rr;return[Math.cos(a)*r,Math.sin(a)*r];}),3100+i));g.restore();}
        g.save();g.translate(82,130+mod(t*42,1300));g.rotate(t*.6);g.scale(Math.cos(t*4),1);glyph(g,semantic(shot),0,0,.65,p.ink,p.white,t);g.restore();
      });},
      metadata:metadata('稳定种子的剪刀折线、水粉长条刷痕、纸片投影、双蓝棋盘、胶囊手指形海藻','文件夹/手机/稿件有手剪外缘和纸张厚度；剪切事件与飞动碎纸形成同一语言','海藻绕根摆动/卷边、黄星旋转、媒体纸片翻面落下','无伊卡洛斯/新人物；共享场景主几何由材质和描线适配，未做全层像素位移；纸片不跨真人脸')
    };
  };

  F['34_shadowpuppet'] = () => {
    const id='34_shadowpuppet',p=palette('#f2d7a0','#3a160a','#c0352a','#2f7d4c','#d99a2e','#fff6d6');
    const cutPatches=new Map(),leather=(g,col)=>K().pattern(g,`${id}/leather/${col}`,96,96,q=>{
      q.fillStyle=material(q,id,'leather',col);q.fillRect(0,0,96,96);q.globalCompositeOperation='destination-out';P().carve.dots(q,8,8,94,94,20,3);q.globalCompositeOperation='source-over';
    });
    const rivet=(g,x,y,r=5)=>{circle(g,x,y,r,p.ink);circle(g,x-1,y-1,r*.42,p.gold);};
    const screenWeave=()=>K().cached(`${id}/woven_screen`,W,H,q=>{q.strokeStyle='rgba(110,74,28,.08)';q.lineWidth=1;for(let x=0;x<W;x+=3)line(q,[[x,0],[x,H]],q.strokeStyle,1);for(let y=0;y<H;y+=3)line(q,[[0,y],[W,y]],q.strokeStyle,1);});
    const piecePlate=(w,h,col,seed)=>K().cached(`${id}/plate/${w}/${h}/${col}/${seed||0}`,Math.ceil(w),Math.ceil(h),q=>{
      const path=new Path2D();path.rect(2,2,w-4,h-4);P().piece(q,path,col,k=>{
        // Carve only the perimeter so document words/waveforms remain legible.
        if(w>60&&h>35){P().carve.dots(k,8,8,w-8,20,18,2.8);P().carve.dots(k,8,h-19,w-8,h-7,18,2.8);P().carve.dots(k,8,20,20,h-20,18,2.5);P().carve.dots(k,w-20,20,w-7,h-20,18,2.5);}
      },{edge:5,line:p.ink,lw:2.6});
    });
    return {
      id,name:'中国透光皮影',palette:p,
      background(g,t){const ts=Math.floor(t*15)/15,fl=.5*P().noise(ts*3,1)+.3*P().noise(ts*9,4),cx=540+fl*25,cy=740+P().noise(ts*2,7)*18;const gr=g.createRadialGradient(cx,cy,50,cx,cy,1300);gr.addColorStop(0,p.white);gr.addColorStop(.38,p.paper);gr.addColorStop(.76,'#cf9a58');gr.addColorStop(1,'#7a4a20');g.fillStyle=gr;g.fillRect(0,0,W,H);g.drawImage(screenWeave(),0,0);
        g.drawImage(K().cached(`${id}/wood_frame`,W,H,q=>{q.fillStyle='#5e3419';q.fillRect(0,0,W,35);q.fillRect(0,35,25,1505);q.fillRect(W-25,35,25,1505);q.fillRect(0,1515,W,30);q.fillStyle='#a46730';q.fillRect(27,37,W-54,7);q.fillRect(27,1505,W-54,7);for(const x of [41,1039])for(let y=64;y<1490;y+=26){q.fillStyle=y%52?p.red:p.olive;q.fillRect(x-6,y-6,12,12);}}),0,0);
      },
      pattern:leather,
      plate(g,w,h,col,seed,t){const layer=piecePlate(w,h,col,seed);P().stamp(g,layer,{dx:4+Math.sin(Math.floor(t*10)/10*3)*.5,dy:3,shadow:.2,blur:3});if(w>80&&h>55){rivet(g,12,12,3.5);rivet(g,w-12,h-12,3.5);}},
      line(g,pts,col,lw,t){g.save();g.globalCompositeOperation='multiply';g.lineCap='round';g.lineJoin='round';line(g,pts,K().alpha(p.ink,.2),lw+2);line(g,pts,col,lw);g.restore();},
      motifs(g,t,shot){clipped(g,()=>{
        const ts=Math.floor(t*10)/10;
        // A jointed editing-tool puppet: each blade is a rigid leather piece,
        // and the control rods stay outside the shared centre/presenter area.
        for(const sd of [-1,1]){const x=sd<0?83:998,y=sd<0?590:1240,a=.35*Math.sin(ts*5+(sd>0?1.5:0)),end=[x+sd*22,y+160];
          line(g,[[x,y],end,[sd<0?40:1040,1510]],'rgba(60,30,12,.5)',3);
          for(const blade of [-1,1]){g.save();g.translate(x,y);g.rotate(blade*(.23+a*.45));const key=`blade/${blade}`,layer=cutPatches.get(key)||K().cached(`${id}/${key}`,62,123,q=>{const path=poly([[22,111],[8,100],[23,16],[39,4],[41,81],[32,111]]);P().piece(q,path,blade>0?p.red:p.olive,k=>P().carve.dots(k,17,19,40,104,15,2.6),{edge:4,line:p.ink,lw:2});});cutPatches.set(key,layer);g.translate(-26,-103);P().stamp(g,layer,{dx:3,dy:2,shadow:.16,blur:2});g.restore();}rivet(g,x,y,6);
          glyph(g,semantic(shot),x,y+170,.64,p.ink,p.gold,ts);
        }
      });},
      metadata:metadata('幕后暖灯/3px织布、彩色皮件镂孔、保留皮边、偏移软影+multiply透光、铆钉与杆操','手机/稿件/波形/文件夹是刻花皮件，剪刀以两块刚体皮片围绕同一铆钉运动','灯光15fps轻微漂移，剪刀10fps分节开合，边侧操纵杆跟随铆钉','透光multiply可能压暗深色对象，雕花仅留在边缘保障文稿可读；无旦角/新人物，不处理真人照片')
    };
  };

  // The time-cost shots share their position and hand choreography, but the
  // actual timer body is rebuilt with each material's shape/mechanism.
  const clockLanguage = {
    '01_cave':'岩刻计时盘与赭石刻痕', '02_egypt':'放射日盘计时器',
    '03_greek':'黑釉圆盘与亮陶土刻线指针', '04_roman':'白石轮廓和错缝镶嵌计时盘',
    '05_gothic':'尖拱泥金计时器', '06_renaissance':'油彩明暗圆盘',
    '10_nouveau':'百合花瓣计时盘', '18_klimt':'黑白方格金箔方形计时器',
    '20_dunhuang':'石青石绿莲花计时盘', '21_kusama':'波点南瓜形计时器',
    '30_matisse':'剪纸星形计时盘', '34_shadowpuppet':'带铆钉的透光皮件计时器'
  };
  for (const id of Object.keys(clockLanguage)) {
    const create = F[id];
    F[id] = () => {
      const style = create(), p = style.palette;
      style.metadata.topic_adaptation += `；${clockLanguage[id]}保留可读时分针`;
      style.clock = (g,x,y,r,hand,t) => {
        g.save(); g.translate(x,y); g.rotate(-.08);
        const face = new Path2D(); face.arc(0,0,r*.77,0,TAU);
        if (id === '05_gothic') {
          const shell = new Path2D(); shell.moveTo(-r*.92,r*.87);shell.lineTo(-r*.92,-r*.2);shell.quadraticCurveTo(-r*.86,-r*.83,0,-r*1.24);shell.quadraticCurveTo(r*.86,-r*.83,r*.92,-r*.2);shell.lineTo(r*.92,r*.87);shell.closePath();
          g.fillStyle=material(g,id,'foil',p.gold);g.fill(shell);g.strokeStyle=p.ink;g.lineWidth=5;g.stroke(shell);
        } else if (id === '18_klimt') {
          g.fillStyle=material(g,id,'foil',p.gold);g.fillRect(-r,-r,r*2,r*2);g.strokeStyle=p.ink;g.lineWidth=4;g.strokeRect(-r,-r,r*2,r*2);
          const s=r*.22;for(let i=0;i<9;i++){g.fillStyle=i%2?p.ink:p.white;g.fillRect(-r+i*s,-r,s,s*.7);g.fillRect(-r+i*s,r-s*.7,s,s*.7);}
          for(const dx of [-r*.86,r*.86])for(let i=0;i<3;i++)spiral(g,dx,(i-1)*r*.5,r*.09,t*.7,p.ink,1.8);
        } else if (id === '21_kusama') {
          for(const k of [0,4,1,3,2]) {const dx=(k-2)*r*.29,rx=r*(k===2?.56:.48),ry=r*(k===2?1:.89);g.beginPath();g.ellipse(dx,0,rx,ry,0,0,TAU);g.fillStyle=p.gold;g.fill();g.strokeStyle=p.ink;g.lineWidth=4;g.stroke();g.save();g.clip();for(let row=-4;row<=4;row++)for(let col=-2;col<=2;col++)circle(g,dx+col*rx*.29,row*ry*.21,r*.045*(1-.1*Math.abs(col))*(.85+.2*Math.sin(t*5+k+row)),p.ink);g.restore();}
          leaf(g,0,-r*.86,r*.31,r*.1,.1,'#2a3a14',p.ink);
        } else if (id === '30_matisse') {
          const pts=Array.from({length:18},(_,i)=>{const a=i/18*TAU,rr=i%2?r*.9:r*1.08;return[Math.cos(a)*rr,Math.sin(a)*rr];});g.shadowColor='rgba(10,20,40,.28)';g.shadowOffsetX=5;g.shadowOffsetY=6;g.shadowBlur=4;g.fillStyle=material(g,id,'gouache',p.gold);g.fill(P().cut(pts,3041,18,2.3));g.shadowColor='transparent';
        } else if (id === '10_nouveau' || id === '20_dunhuang') {
          for(let i=0;i<12;i++){const a=i/12*TAU,dx=Math.cos(a)*r*.72,dy=Math.sin(a)*r*.72;leaf(g,dx,dy,r*.39,r*.14,a+Math.PI/2,id==='20_dunhuang'?(i%2?p.olive:p.white):p.gold,p.ink);}circle(g,0,0,r*.86,null,p.ink,3);
        } else if (id === '02_egypt') {
          circle(g,0,0,r*.95,p.red,p.ink,4);for(let i=0;i<16;i++){const a=i/16*TAU;line(g,[[Math.cos(a)*r*.77,Math.sin(a)*r*.77],[Math.cos(a)*r*.96,Math.sin(a)*r*.96]],p.gold,3);}circle(g,0,0,r*.83,null,p.gold,3);
        } else if (id === '03_greek') {
          circle(g,0,0,r,p.ink);circle(g,0,0,r*.88,p.red);circle(g,0,0,r*.85,p.ink);for(let i=0;i<24;i++){const a=i/24*TAU;circle(g,Math.cos(a)*r*.935,Math.sin(a)*r*.935,r*.012,p.white);}
        } else if (id === '34_shadowpuppet') {
          const layer=K().cached(`${id}/clock/${r}`,Math.ceil(r*2+10),Math.ceil(r*2+10),q=>{const ring=new Path2D();ring.arc(r+5,r+5,r,0,TAU);P().piece(q,ring,p.gold,k=>{k.beginPath();k.arc(r+5,r+5,r*.79,0,TAU);k.fill();for(let i=0;i<20;i++){const a=i/20*TAU;circle(k,r+5+Math.cos(a)*r*.91,r+5+Math.sin(a)*r*.91,r*.025,'#000000');}},{edge:4,line:p.ink,lw:3});});g.save();g.translate(-r-5,-r-5);P().stamp(g,layer,{dx:4,dy:3,shadow:.2,blur:3});g.restore();
        } else {
          g.fillStyle=style.pattern(g,p.ink,t);g.beginPath();g.arc(0,0,r,0,TAU);g.fill();circle(g,0,0,r*.91,null,p.gold,4);
        }
        if (id === '03_greek') g.fillStyle=material(g,id,'clay',p.ink);
        else if (id === '06_renaissance') {const vol=g.createRadialGradient(-r*.25,-r*.3,r*.05,0,0,r*.95);vol.addColorStop(0,p.white);vol.addColorStop(.7,p.paper);vol.addColorStop(1,'#6c573c');g.fillStyle=vol;}
        else g.fillStyle=material(g,id,id==='01_cave'?'rock':id==='20_dunhuang'?'mineral':id==='30_matisse'?'gouache':'plaster',p.white);
        g.fill(face);g.strokeStyle=id==='03_greek'?p.gold:p.ink;g.lineWidth=2.8;g.stroke(face);
        const ink=id==='03_greek'?p.gold:p.ink;
        for(let i=0;i<12;i++){const a=i/12*TAU;line(g,[[Math.sin(a)*r*.68,-Math.cos(a)*r*.68],[Math.sin(a)*r*.57,-Math.cos(a)*r*.57]],ink,i%3?2:4);}
        const angle=id==='34_shadowpuppet'?Math.floor(hand*10)/10:hand;
        const arm=(a,len,col,width)=>{g.save();g.rotate(a);if(id==='34_shadowpuppet'){g.globalCompositeOperation='multiply';g.fillStyle=col;const armPath=poly([[-width*.5,8],[-width*.42,-len],[0,-len-9],[width*.42,-len],[width*.5,8]]);g.fill(armPath);g.strokeStyle=p.ink;g.lineWidth=1.6;g.stroke(armPath);}else line(g,[[0,0],[0,-len]],col,width);g.restore();};
        arm(angle*.65,r*.41,ink,Math.max(5,r*.06));arm(angle*2.3,r*.61,id==='03_greek'?p.white:p.red,Math.max(4,r*.04));circle(g,0,0,r*.045,id==='34_shadowpuppet'?p.ink:p.red);if(id==='34_shadowpuppet')circle(g,-1,-1,r*.021,p.gold);
        g.restore();return true;
      };
      return style;
    };
  }
})();
