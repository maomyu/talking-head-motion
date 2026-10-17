/* Independently authored, deterministic component choreography. */
(async () => {
  if (window.__captionFontsReady) await window.__captionFontsReady;
  await document.fonts.ready;
  const plan = window.motionPlan;
  document.getElementById('stage').style.setProperty('--stage-height', `${plan.canvas.height}px`);
  const tl = gsap.timeline({paused: true});
  // The stage uses pixels from the composition contract; scale typographic tokens
  // once during setup, before any tween, for a genuinely different canvas size.
  const ratio = plan.canvas.width / 1080;
  const fontSizes = [...document.querySelectorAll('.graphic-inner,.graphic-inner *,.caption-inner')]
    .map(el => [el, parseFloat(getComputedStyle(el).fontSize)]);
  fontSizes.forEach(([el, size]) => { el.style.fontSize = `${size * ratio}px`; });
  function fit(el, maxHeight) {
    if (!el) return;
    let size = parseFloat(getComputedStyle(el).fontSize);
    while ((el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > maxHeight) && size > 20 * ratio) {
      size *= .94; el.style.fontSize = `${size}px`;
    }
    if (el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > maxHeight + 2) {
      throw new Error(`Text does not fit: ${el.textContent.slice(0, 30)}`);
    }
  }
  for (const e of plan.events) {
    const host = document.getElementById(e.id), child = host.querySelector('.graphic-inner');
    const length = e.end - e.start, enter = Math.min(.5, length / 3), exit = Math.min(.25, length / 4);
    fit(child.querySelector('.hero-text'), plan.canvas.height * .24);
    fit(child.querySelector('.quote-text'), plan.canvas.height * .28);
    const maximumBottom = plan.canvas.height * .76;
    if (host.offsetTop + host.offsetHeight > maximumBottom) throw new Error(`Graphic enters caption safety region: ${e.id}`);
    tl.fromTo(child, {y: 30 * ratio, opacity: 0}, {y: 0, opacity: 1, duration: enter, ease: 'power3.out'}, e.start);
    const presenter = document.querySelector('.presenter-wrap');
    if (presenter && e.presenter === 'pip') {
      tl.to(presenter, {scale: .28, x: plan.canvas.width * .32, y: plan.canvas.height * .12, duration: .32, ease: 'power3.inOut'}, e.start);
      tl.to(presenter, {scale: 1, x: 0, y: 0, duration: exit, ease: 'power3.inOut'}, e.end - exit);
    }
    if (e.component === 'kinetic-title') {
      const title = child.querySelector('.hero-text');
      // This title intentionally enters through its clipping mask. The annotation
      // is restricted to this element; all other text retains layout auditing.
      title.setAttribute('data-layout-allow-overflow', 'masked-entry');
      title.setAttribute('data-layout-allow-occlusion', 'masked-entry');
      tl.fromTo(title, {yPercent: 105, scale: .96}, {yPercent: 0, scale: 1, duration: enter, ease: 'power3.out'}, e.start);
    } else if (e.component === 'steps') {
      const items = [...child.querySelectorAll('.step')];
      const stagger = Math.min(.18, Math.max(0, length - enter - exit) / Math.max(items.length * 2, 1));
      if (Array.isArray(e.item_times) && e.item_times.length === items.length) {
        items.forEach((item, i) => tl.fromTo(item, {x: 48 * ratio, opacity: 0}, {x: 0, opacity: 1, duration: Math.min(.32,e.end-e.item_times[i]), ease: 'power3.out'}, e.item_times[i]));
      } else { tl.fromTo(items, {x: 48 * ratio, opacity: 0}, {x: 0, opacity: 1, duration: enter, stagger, ease: 'power3.out'}, e.start); }
    } else if (e.component === 'split-compare') {
      tl.fromTo(child.querySelectorAll('.alternative'), {y: 24 * ratio, opacity: 0}, {y: 0, opacity: 1, duration: enter, stagger: Math.min(.16, length / 6), ease: 'power3.out'}, e.start);
    } else if (e.component === 'evidence') {
      tl.fromTo(child.querySelector('.evidence-image'), {scale: 1.06}, {scale: 1, duration: length, ease: 'power1.out'}, e.start);
    }
    tl.to(child, {y: -14 * ratio, opacity: 0, duration: exit, ease: 'power2.in'}, e.end - exit);
  }
  plan.cues.forEach((cue, i) => {
    const child = document.getElementById('caption-' + i).querySelector('.caption-inner');
    fit(child, plan.canvas.height * .12);
    tl.fromTo(child, {y: 8 * ratio, opacity: 0}, {y: 0, opacity: 1, duration: Math.min(.12, (cue.end - cue.start) / 3), ease: 'power2.out'}, cue.start);
  });
  tl.fromTo('.edit-rail',{scaleX:0},{scaleX:1,duration:.65,ease:'power3.out'},0);
  tl.fromTo('.background-bars i',{y:0},{y:-24*ratio,duration:4,ease:'sine.inOut',stagger:.15,repeat:Math.ceil(plan.duration/8),yoyo:true},0);
  window.__timelines = window.__timelines || {};
  window.__timelines['talking-head'] = tl;
})();
