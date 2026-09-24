// СНИМКА · profil2.js на AERO_КЛИЕНТ · 2026-09-24T16:51 UTC · sha256 173b08d909bc41b9
// СНИМКА · дословни извадки, НЕ СЕ ПИШАТ НА РЪКА: node platforma/proba_karti.mjs snimka <AERO_КЛИЕНТ>
const PIP = 0.1;
  const BR_CELI = 2;
  const STOP_P = 130;
  const CEL2_P = (dir) => (dir > 0 ? 130 : 100);
  function ednaPoz(ch, nv, vid, dir, naVh) {
    /* naVh · 22.09 · бот v18.85: стопът е отишъл на входа при +40 (картата exit-be), преди цел 1 → 0, не −130 */
    if (nv >= 2 || vid === 'tp2' || vid === 'tp3') return CEL2_P(dir);
    if (vid === 'sl') return nv >= 1 || naVh ? 0 : -STOP_P;
    /* обрат / по време: при старите две — ВТОРАТА (тя е стояла до изхода) · след цел 1 не под нулата */
    const h = Math.round(ch.length === 1 ? ch[0] : ch[Math.min(1, ch.length - 1)]);
    return nv >= 1 || naVh ? Math.max(0, h) : h;
  }
  const hodP = (vhod, izhod, dir) => Math.round(Number((((izhod - vhod) * dir) / PIP).toFixed(6)));
  function num(v) {
    if (v === null || v === undefined || v === '') return null;
    if (typeof v === 'number') return Number.isFinite(v) ? v : null;
    const x = parseFloat(String(v).replace(/[\s\u00a0\u2009\u202f,]/g, '').replace(/[\u2212\u2013]/g, '-'));
    return Number.isFinite(x) ? x : null;
  }
  const ENT = { '&lt;': '<', '&gt;': '>', '&amp;': '&', '&quot;': '"', '&#39;': "'", '&nbsp;': ' ' };
  const razEnt = (t) => String(t).replace(/&(lt|gt|amp|quot|#39|nbsp);/g, (m) => ENT[m]);
  const gol = (html) => razEnt(String(html || '').replace(/<[^>]*>/g, ''));
  const RE_CEL = /([123])\uFE0F?\u20E3\s*([\d,]+\.\d+)\s*\((\d+)\s*п\)/g;
  function vhodOt(k) {
    const g = gol(k.text);
    const m = g.match(/(КУПИ|ПРОДАЙ)\s+(ЗЛАТО|СРЕБРО)/);
    if (!m || m[2] !== 'ЗЛАТО') return null;
    const dir = m[1] === 'КУПИ' ? 1 : -1;
    const e = g.match(/вход\s+([\d,]+\.\d+)/);
    const entry = e ? num(e[1]) : null;
    if (entry === null) return null;
    const s = g.match(/стоп\s+([\d,]+\.\d+)(?:\s*·\s*(\d+)\s*пипса)?/);
    const sl = s ? num(s[1]) : null;
    const slPips = (s && s[2]) ? +s[2] : (sl !== null ? Math.round(Math.abs(sl - entry) / PIP) : 130);
    const tp = [];
    let x;
    RE_CEL.lastIndex = 0;
    while ((x = RE_CEL.exec(g)) !== null) tp.push({ px: num(x[2]), pips: +x[3] });
    if (!tp.length) {
      const red = g.split('\n').find((l) => /цели\s/.test(l));
      if (red) { const re = /([\d,]+\.\d+)\s*\+(\d+)/g; while ((x = re.exec(red)) !== null) tp.push({ px: num(x[1]), pips: +x[2] }); }
    }
    if (!tp.length) return null;
    const tri = tp.length > BR_CELI;                  // старата карта с три цели
    tp.splice(BR_CELI);
    return { d: k.d, dir, entry, sl, slPips, tp, maxCel: 0, zatv: null, tri };
  }
  function izhodOt(k) {
    const g = gol(k.text);
    const m = g.match(/ЗЛАТО\s+(покупка|продажба)/);
    if (!m) return null;
    const f = g.match(/([\d,]+\.\d+)\s*(?:\(\d{1,2}:\d{2}\))?\s*→\s*([\d,]+\.\d+)/);
    if (!f) return null;
    const vid = ((k.tag.split(':')[1]) || '').split('#')[0];
    const pz = g.match(/по позиции:\s*([^\n]*?)\s*пипса/);
    const parts = pz ? pz[1].split('·').map((s) => num(s)) : null;
    return {
      d: k.d, dir: m[1] === 'покупка' ? 1 : -1, from: num(f[1]), to: num(f[2]), vid,
      parts: parts && parts.every((v) => v !== null) ? parts : null,
      zatvarya: /СДЕЛКАТА ДОНЕСЕ/i.test(g) || /^(tp2|tp3|sl|flip|time|eod)$/.test(vid),
      /* «✅ … стопът беше на входа» · стопът е ударен на входа → 0 (както сървърът · data.mjs) */
      naVhoda: vid === 'sl' && (/^✅/.test(g.trim()) || /стопът беше на входа/.test(g)),
    };
  }
  function beOt(k) {
    const g = gol(k.text);
    const m = g.match(/ЗЛАТО\s+(покупка|продажба)/);
    const s = g.match(/стопа\s+на\s+([\d,]+\.\d+)/);
    const c = g.match(/1️?⃣\s*([\d,]+\.\d+)/);
    if (!m || (!s && !c)) return null;
    return { d: k.d, dir: m[1] === 'покупка' ? 1 : -1, from: s ? num(s[1]) : null, to: null, cel1: c ? num(c[1]) : null, vid: 'be40', zatvarya: false };
  }
  function sglobiSdelki(karti) {
    const vhodove = [];
    karti.forEach((k) => {
      if (k.tag === 'signal') {
        if (k.text.indexOf('ВЛЕЗ') >= 0) { const v = vhodOt(k); if (v) vhodove.push(v); }
        return;
      }
      if (/^exit-be\b/.test(k.tag)) {
        /* не е изход · само отбелязва входа: стопът е на входа (be40) */
        const b = beOt(k);
        if (!b) return;
        for (let i = vhodove.length - 1; i >= 0; i--) {
          const v = vhodove[i];
          if (v.zatv || v.dir !== b.dir || +v.d > +b.d) continue;
          if ((b.from !== null && Math.abs(v.entry - b.from) <= 0.006) || (b.cel1 !== null && v.tp[0] && Math.abs(v.tp[0].px - b.cel1) <= 0.006)) { v.be40 = true; break; }
        }
        return;
      }
      const gl = k.tag.split(':')[0];
      if (gl !== 'exit' && gl !== 'exit2') return;
      const x = izhodOt(k);
      if (!x || x.from === null) return;
      let t = null;
      for (let i = vhodove.length - 1; i >= 0; i--) {
        const v = vhodove[i];
        if (v.zatv || v.dir !== x.dir || +v.d > +x.d) continue;
        if (Math.abs(v.entry - x.from) <= 0.006) { t = v; break; }
      }
      if (!t) return;
      const n = /^tp(\d)$/.exec(x.vid);
      if (n) t.maxCel = Math.max(t.maxCel, +n[1]);
      if (x.zatvarya) t.zatv = { d: x.d, vid: x.vid, to: x.to, parts: x.parts, naVhoda: x.naVhoda };
    });
    return { vhodove };
  }
  function chastiZatvorena(v) {
    const z = v.zatv;
    const k = Math.min(v.maxCel, v.tp.length);
    const vid = z.vid === 'tp3' ? 'tp2' : z.vid;
    const hod = Number.isFinite(z.to) ? [hodP(v.entry, z.to, v.dir)] : (z.parts && z.parts.length ? z.parts : [0]);
    return { ch: [ednaPoz(hod, k, vid, v.dir, !!(v.be40 || z.naVhoda))], otBota: false };
  }
  const imeCeli = (k) => (k === 1 ? 'цел 1' : k === 2 ? 'цел 1 и цел 2' : 'целите');
  function prichinaZatv(v) {
    const z = v.zatv;
    const k = Math.min(v.maxCel, v.tp.length);
    const naVh = !!(v.be40 || z.naVhoda);
    if (k >= v.tp.length) return 'всички цели взети';
    if (z.vid === 'sl') return k ? imeCeli(k) + ', после стоп на входа' : naVh ? 'стоп на входа след +40' : 'стоп преди цел 1';
    const pred = k ? imeCeli(k) + ', после ' : naVh ? 'стоп на входа след +40, после ' : '';
    if (z.vid === 'flip') return pred + 'затворена · посоката се обърна';
    if (z.vid === 'time') return pred + 'затворена по време';
    return pred + 'затворена';
  }
