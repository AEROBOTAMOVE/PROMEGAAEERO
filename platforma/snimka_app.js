// СНИМКА · app.js на AERO_КЛИЕНТ · 2026-09-24T16:51 UTC · sha256 3e67c7cbebf0c30c
// СНИМКА · дословни извадки, НЕ СЕ ПИШАТ НА РЪКА: node platforma/proba_karti.mjs snimka <AERO_КЛИЕНТ>
const PIP = 0.1;                 // 1 пипс = 0.10 $ на унция
  const BR_CELI = 2;
  const CELI_K = ['tp1', 'tp2'];
  const STOP_P = 130;                                   // стоп преди цел 1 · разстояние 13 $
  const CEL2_P = (dir) => (dir > 0 ? 130 : 100);        // цел 2 · 13 $ покупка / 10 $ продажба
  function ednaPoz(ch, nv, vid, dir, naVh) {
    /* naVh · 22.09 · бот v18.85: стопът е отишъл на входа при +40 (картата exit-be), преди цел 1 →
       стоп след това е 0, не −130 (сметката е същата като след цел 1) */
    if (nv >= 2 || vid === 'tp2' || vid === 'tp3') return CEL2_P(dir);
    if (vid === 'sl') return nv >= 1 || naVh ? 0 : -STOP_P;
    /* обрат / по време: при една позиция — самата тя; при старите две — ВТОРАТА, защото тя е
       стояла до изхода (първата е излизала на цел 1). След цел 1 стопът е на входа → не под нулата. */
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
  function utcDate(s) {
    if (!s) return null;
    if (s instanceof Date) return isNaN(+s) ? null : s;
    let t = String(s).trim().replace(' ', 'T');
    if (/^\d{4}-\d\d-\d\dT\d\d:\d\d$/.test(t)) t += ':00';
    if (!/(Z|[+\-]\d\d:?\d\d)$/i.test(t)) t += 'Z';
    const d = new Date(t);
    return isNaN(+d) ? null : d;
  }
  const ENT = { '&lt;': '<', '&gt;': '>', '&amp;': '&', '&quot;': '"', '&#39;': "'", '&nbsp;': ' ' };
  const razEnt = (t) => String(t).replace(/&(lt|gt|amp|quot|#39|nbsp);/g, (m) => ENT[m]);
  const gol = (html) => razEnt(String(html || '').replace(/<[^>]*>/g, ''));
  const ZHARGON = [
    [/\bshort\s+сделка/gi, 'продажба'],
    [/\blong\s+сделка/gi, 'покупка'],
    [/\bshort\b/gi, 'продажба'],
    [/\blong\b/gi, 'покупка'],
    [/\bTP\s?([123])\b/gi, 'цел $1'],
    [/\bSL\b/gi, 'стоп'],
    [/\s*\(по бар\)/g, ''],
  ];
  const bezZhargon = (t) => ZHARGON.reduce((s, z) => s.replace(z[0], z[1]), String(t));
  function ledgerOt(j) {
    const a = Array.isArray(j) ? j
      : (j && Array.isArray(j.sdelki)) ? j.sdelki
        : (j && Array.isArray(j.trades)) ? j.trades : null;
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
      /* 22.09 · записът може да е по новия закон (една част) или по стария (две части от 15.09,
         три отпреди) — и в трите случая сделката е ЕДНО число по закона (ednaPoz по-долу).
         sum_pips на стария запис е сборът на двете позиции → не се взима. */
      const entry = num(x.entry || x.vhod);
      const Lv = x.levels || {};
      const hit = x.hit || {};
      const kl = CELI_K.filter((k) => num(Lv[k]) !== null);
      let nv = 0;
      kl.forEach((k, i) => { if (hit[k]) nv = i + 1; });
      const vid0 = String(x.exit_kind || x.vid || '').toLowerCase();
      const vid = vid0 === 'tp3' ? 'tp2' : vid0;   // цел 3 няма → сделката се затваря на цел 2
      const mv = /^tp(\d)$/.exec(vid);
      if (mv) nv = Math.max(nv, Math.min(+mv[1], kl.length || BR_CELI));
      const tp = entry !== null ? kl.map((k, i) => ({ px: num(Lv[k]), pips: Math.round(Math.abs(num(Lv[k]) - entry) / PIP), vzeta: i < nv })) : [];
      /* т. 10 (собственикът) · след взета цел 1 стопът е на входа → никога минус (прескок/спред → 0).
         Минус има само при стоп преди цел 1, и тогава е точно −130 (стопът е разстояние).
         22.09 · бот v18.85: стопът отива на входа още при +40 (картата exit-be). Записът го казва с
         hit.be (сървърът · data.mjs), stop_at_entry или стоп, равен на входа (ботът пише стопа, където е
         накрая · мерено 22.09 в live/sdelki.json: 64 от 64 записа — стоп = вход ⇔ стопът е бил преместен). */
      const slL = num(Lv.sl);
      const naVh = !!(hit.be || hit.be40 || x.stop_at_entry === true || (entry !== null && slL !== null && Math.abs(slL - entry) < 0.01));
      const sbor = ednaPoz(ch, nv, vid, dir, naVh);
      out.push({
        dir, entry, d: utcDate(x.opened || x.otvoreno || x.vhod_utc || x.opened_utc),
        zatvD, chasti: [sbor], sbor,
        tp, vzeti: nv, sl: slL, vid, izhodPx: vid0 === 'tp3' ? null : num(x.exit_px),
        be40: naVh && nv < 1,
        /* zakon: 'star' · сделка отпреди 15.09, 14:12 (тогава с три позиции) · преброена по сегашния */
        starZakon: x.zakon === 'star', otKarti: x.izvor_zapis === 'karti',
        prichina: (x.prichina || x.reason) ? bezZhargon(String(x.prichina || x.reason)) : prichinaLedger(vid, nv, tp.length, naVh),
      });
    });
    return out.length ? out.sort((p, q) => p.zatvD - q.zatvD) : null;
  }
  function prichinaLedger(vid, k, n, naVh) {
    const ime = (kk) => (kk === 1 ? 'цел 1' : kk === 2 ? 'цел 1 и цел 2' : 'целите');
    if (n && k >= n) return 'всички цели взети';
    if (vid === 'sl') return k ? ime(k) + ', после стоп на входа' : naVh ? 'стоп на входа след +40' : 'стоп преди цел 1';
    const pred = k ? ime(k) + ', после ' : naVh ? 'стоп на входа след +40, после ' : '';
    if (vid === 'flip') return pred + 'затворена · посоката се обърна';
    if (vid === 'time') return pred + 'затворена по време';
    return pred + 'затворена';
  }
  const RE_CEL = /([123])️?⃣\s*([\d,]+\.\d+)\s*\((\d+)\s*п\)/g;
  const RE_CEL_NOV = /([\d,]+\.\d+)\s*\+(\d+)/g;
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
      if (red) { RE_CEL_NOV.lastIndex = 0; while ((x = RE_CEL_NOV.exec(red)) !== null) tp.push({ px: num(x[1]), pips: +x[2] }); }
    }
    if (!tp.length) return null;
    tp.splice(BR_CELI);                                  // цел 3 няма · двете цели са за ЕДНАТА позиция
    return { d: k.d, dir, entry, sl, slPips, tp, maxCel: 0, zatv: null };
  }
  function izhodOt(k) {
    const g = gol(k.text);
    const m = g.match(/ЗЛАТО\s+(покупка|продажба)/);
    if (!m) return null;
    /* 16.09 · в скобите след цената на входа може да има и ДАТА («4,395.26 (09.09 23:27) → …»),
       не само час — с (\d{1,2}:\d{2}) тези 9 карти не се четяха и сделките им изпадаха */
    const f = g.match(/([\d,]+\.\d+)\s*(?:\([^)]*\))?\s*→\s*([\d,]+\.\d+)/);
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
  function beOt(k, vhodove) {
    const g = gol(k.text);
    const m = g.match(/ЗЛАТО\s+(покупка|продажба)/);
    if (!m) return;
    const dir = m[1] === 'покупка' ? 1 : -1;
    const s = g.match(/стопа\s+на\s+([\d,]+\.\d+)/);
    const c = g.match(/1️?⃣\s*([\d,]+\.\d+)/);
    const stop = s ? num(s[1]) : null;
    const cel1 = c ? num(c[1]) : null;
    for (let i = vhodove.length - 1; i >= 0; i--) {
      const v = vhodove[i];
      if (v.zatv || v.dir !== dir || +v.d > +k.d) continue;
      if ((stop !== null && Math.abs(v.entry - stop) <= 0.006) || (cel1 !== null && v.tp[0] && Math.abs(v.tp[0].px - cel1) <= 0.006)) { v.be40 = true; return; }
    }
  }
  function sglobiSdelki(karti) {
    const vhodove = [];
    let bezVhod = 0;
    karti.forEach((k) => {
      if (k.tag === 'signal') {
        if (k.text.indexOf('ВЛЕЗ') >= 0) { const v = vhodOt(k); if (v) vhodove.push(v); }
        return;
      }
      if (/^exit-be\b/.test(k.tag)) { beOt(k, vhodove); return; }   // не е изход · само стопът на входа
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
      if (!t) { bezVhod++; return; }
      const n = /^tp(\d)$/.exec(x.vid);
      if (n) t.maxCel = Math.max(t.maxCel, +n[1]);
      if (x.zatvarya) t.zatv = { d: x.d, vid: x.vid, to: x.to, parts: x.parts, naVhoda: x.naVhoda };
    });
    return { vhodove, bezVhod };
  }
  function chastiZatvorena(v) {
    const z = v.zatv;
    const k = Math.min(v.maxCel, v.tp.length);
    const vid = z.vid === 'tp3' ? 'tp2' : z.vid;
    const hod = Number.isFinite(z.to) ? [hodP(v.entry, z.to, v.dir)] : (z.parts && z.parts.length ? z.parts : [0]);
    return { ch: [ednaPoz(hod, k, vid, v.dir, !!(v.be40 || z.naVhoda))], otBota: false };
  }
  function imeCeli(k) { return k === 1 ? 'цел 1' : k === 2 ? 'цел 1 и цел 2' : 'целите'; }
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
