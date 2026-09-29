// СНИМКА · profil2.js на AERO_КЛИЕНТ · 2026-09-29T09:36 UTC · sha256 01fb343ab9e6206c
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
    const v = { d: k.d, dir, entry, sl, slPips, tp, maxCel: 0, zatv: null, tri };
    /* 29.09 · бот v18.95 · ВЛЕЗ на сделка на две половини: «1 сделка · 2 половини × лот 0.10» (като app.js) */
    if (/2\s+половини/.test(g)) v.polovin = true;
    return v;
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
      /* 29.09 · бот v18.95 · сделка на ДВЕ ПОЛОВИНИ (като app.js): числото на СДЕЛКАТА е «сделката донесе N
         пипса» на затварящата карта (средното на половините, и с .5) */
      const gx = gol(k.text);
      if (/прибери половината|половина\s+1:|ЦЕЛ 1 беше прибрана/.test(gx)) t.polovin = true;
      if (x.zatvarya) {
        t.zatv = { d: x.d, vid: x.vid, to: x.to, parts: x.parts, naVhoda: x.naVhoda };
        if (t.polovin) {
          const sb = gx.match(/сделката\s+донесе\s*([+−–\-]?[\d.,]+)\s*пипса/i);
          t.zatv.sbor = sb ? num(sb[1]) : null;
        }
      }
    });
    return { vhodove };
  }
  function chastiZatvorena(v) {
    const z = v.zatv;
    /* 29.09 · бот v18.95 · сделка на две половини → числото, което ботът е написал за СДЕЛКАТА */
    if (v.polovin && Number.isFinite(z.sbor)) return { ch: [z.sbor], otBota: false };
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
  const CELI_K = ['tp1', 'tp2'];
  function utcDate(s) {
    if (!s) return null;
    if (s instanceof Date) return isNaN(+s) ? null : s;
    let t = String(s).trim().replace(' ', 'T');
    if (/^\d{4}-\d\d-\d\dT\d\d:\d\d$/.test(t)) t += ':00';
    if (!/(Z|[+\-]\d\d:?\d\d)$/i.test(t)) t += 'Z';
    const d = new Date(t);
    return isNaN(+d) ? null : d;
  }
  const ZHARGON = [
    [/макрото мълчи/gi, 'доларът и лихвите не дават посока'],
    [/\b\d{1,3}(?:,\d{3})+\.\d+\b/g, (m) => cena(num(m))],   // «4,302.87» → «4 302,87»
    [/\bshort\b/gi, 'продажба'], [/\blong\b/gi, 'покупка'], [/\bTP\s?([123])\b/gi, 'цел $1'], [/\bSL\b/gi, 'стоп'], [/\s*\(по бар\)/g, ''],
  ];
  const bezZhargon = (t) => ZHARGON.reduce((s, z) => s.replace(z[0], z[1]), String(t));
  function prichinaLedger(vid, k, n, naVh) {
    if (n && k >= n) return 'всички цели взети';
    if (vid === 'sl') return k ? imeCeli(k) + ', после стоп на входа' : naVh ? 'стоп на входа след +40' : 'стоп преди цел 1';
    const pred = k ? imeCeli(k) + ', после ' : naVh ? 'стоп на входа след +40, после ' : '';
    if (vid === 'flip') return pred + 'затворена · посоката се обърна';
    if (vid === 'time') return pred + 'затворена по време';
    return pred + 'затворена';
  }
  function ledgerOt(j) {
    const a = Array.isArray(j) ? j : (j && Array.isArray(j.sdelki)) ? j.sdelki : (j && Array.isArray(j.trades)) ? j.trades : null;
    if (!a) return null;
    const out = [];
    a.forEach((x) => {
      if (!x || typeof x !== 'object') return;
      const pos = String(x.direction || x.posoka || x.dir || '').toLowerCase();
      const dir = /long|buy|куп|нагоре/.test(pos) ? 1 : /short|sell|прод|надолу/.test(pos) ? -1 : 0;
      const parts = x.parts || x.chasti || x.pozicii || x['части'];
      if (!dir || !Array.isArray(parts) || !parts.length) return;
      const ch = parts.map(num);
      if (ch.some((v) => v === null)) return;
      const zatvD = utcDate(x.closed || x.zatvoreno || x.izhod_utc || x.closed_utc);
      if (!zatvD) return;
      /* 22.09 · една част (новият закон) или две / три (старите) → ЕДНО число по закона */
      const star = ch.length > 2;
      const entry = num(x.entry || x.vhod);
      const Lv = x.levels || {};
      const hit = x.hit || {};
      const kl = CELI_K.filter((k) => num(Lv[k]) !== null);
      let nv = 0;
      kl.forEach((k, i) => { if (hit[k]) nv = i + 1; });
      const vid0 = String(x.exit_kind || x.vid || '').toLowerCase();
      const vid = vid0 === 'tp3' ? 'tp2' : vid0;       // цел 3 няма → затваря се на цел 2
      const mv = /^tp(\d)$/.exec(vid);
      if (mv) nv = Math.max(nv, Math.min(+mv[1], kl.length || BR_CELI));
      const tp = entry !== null ? kl.map((k, i) => ({ px: num(Lv[k]), pips: Math.round(Math.abs(num(Lv[k]) - entry) / PIP), vzeta: i < nv })) : [];
      /* 22.09 · бот v18.85: стопът на входа при +40 → hit.be (data.mjs), stop_at_entry или стоп = вход (като app.js) */
      const slL = num(Lv.sl);
      const naVh = !!(hit.be || hit.be40 || x.stop_at_entry === true || (entry !== null && slL !== null && Math.abs(slL - entry) < 0.01));
      /* 29.09 · бот v18.95 · сделка на ДВЕ ПОЛОВИНИ ("mode":"polovin") → числото на СДЕЛКАТА е sum_pips (като app.js) */
      const sbor = x.mode === 'polovin' && num(x.sum_pips) !== null ? num(x.sum_pips) : ednaPoz(ch, nv, vid, dir, naVh);
      out.push({
        dir, entry, d: utcDate(x.opened || x.otvoreno || x.vhod_utc || x.opened_utc),
        zatvD, chasti: [sbor], sbor,
        tp, vzeti: nv, sl: slL, vid, izhodPx: vid0 === 'tp3' ? null : num(x.exit_px), be40: naVh && nv < 1,
        prichina: (x.prichina || x.reason) ? bezZhargon(String(x.prichina || x.reason)) : prichinaLedger(vid, nv, tp.length, naVh),
        tri: star || num(Lv.tp3) !== null || !!x.prebroeno,
      });
    });
    return out.length ? out.sort((p, q) => p.zatvD - q.zatvD) : null;
  }
