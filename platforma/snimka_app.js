// СНИМКА · app.js на AERO_КЛИЕНТ · 2026-10-06T17:35 UTC · sha256 4cc1aee6f8f9ef0e
// СНИМКА · дословни извадки, НЕ СЕ ПИШАТ НА РЪКА: node platforma/proba_karti.mjs snimka <AERO_КЛИЕНТ>
const PIP = 0.1;                 // 1 пипс = 0.10 $ на унция
  const BR_CELI = 3;
  const CELI_K = ['tp1', 'tp2', 'tp3'];
  const STOP_P = 130;                                   // стоп · 130 пипса от входа
  const CEL2_P = (dir) => (dir > 0 ? 130 : 100);        // старата последна цел (до 06.10) · само за запис без нива
  function zakonTp123(o) {
    try { const Z = window.AERO_MOD && window.AERO_MOD.zakoni; if (Z && typeof Z.tp123 === 'function') return Z.tp123(o); } catch (e) { /* правилото отдолу */ }
    const z = o || {};
    const kind = String(z.kind || '').toLowerCase();
    if (z.mode === 'tp123' && Number.isFinite(z.pips)) {
      const b = Math.max(0, Math.min(3, Math.round(+z.best || 0)));
      return { best: b, pips: z.pips, k: b ? 'cel' + b : kind === 'sl' ? (z.pips < 0 ? 'stop' : 'vhod') : 'drugo' };
    }
    const m = Number.isFinite(z.m) ? z.m : 0;
    const b = m >= 129.95 ? 3 : m >= 99.95 ? 2 : m >= 49.95 ? 1 : 0;
    if (b) return { best: b, pips: [50, 100, 130][b - 1], k: 'cel' + b };
    if (kind === 'sl') return z.naVh ? { best: 0, pips: 0, k: 'vhod' } : { best: 0, pips: -STOP_P, k: 'stop' };
    if (!Number.isFinite(z.hod)) return { best: 0, pips: null, k: 'drugo' };
    let p = Math.round(z.hod * 10) / 10;
    if (z.naVh && p < 0) p = 0;
    return { best: 0, pips: Math.max(p, -STOP_P), k: 'drugo' };
  }
  function naiDaleche(tp, nv, dir, vidIzh, hodIzh) {
    let m = 0;
    (tp || []).forEach((x, i) => { if ((x.vzeta || i < nv) && Number.isFinite(x.pips)) m = Math.max(m, x.pips); });
    if (!(tp || []).length && nv) m = nv >= 2 ? CEL2_P(dir) : 50;
    if (/^tp\d$/.test(String(vidIzh || '')) && Number.isFinite(hodIzh)) m = Math.max(m, hodIzh);
    return m;
  }
  function ednaPoz(ch, nv, vid, dir, naVh) {
    const dv = (h, kind) => ({ sbor: (h[0] + h[1]) / 2, halves: h, kind });
    const v = vid === 'tp3' ? 'tp2' : String(vid || '');
    if (nv >= 2 || v === 'tp2') return dv([50, CEL2_P(dir)], 'tp2');
    if (v === 'sl') return dv(nv >= 1 ? [50, 0] : naVh ? [0, 0] : [-STOP_P, -STOP_P], 'sl');
    const h0 = ch.length === 1 ? ch[0] : ch[Math.min(1, ch.length - 1)];
    const x = Number.isFinite(h0) ? Math.round(h0 * 10) / 10 : 0;
    const h2 = nv >= 1 || naVh ? Math.max(0, x) : x;
    return dv([nv >= 1 ? 50 : h2, h2], v);
  }
  const hodP = (vhod, izhod, dir) => Math.round(Number((((izhod - vhod) * dir) / PIP).toFixed(6)) * 10) / 10;
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
      /* 06.10 · ЗАКОНЪТ ТП 1·2·3 · записът по новия закон ("mode":"tp123") има истинска цел 3 (затваря); старият
         «tp3» е остатъкът от трите позиции до 15.09 → сделката е затворена на цел 2, както досега */
      const e123 = x.mode === 'tp123';
      const vid0 = String(x.exit_kind || (e123 ? '' : x.vid) || '').toLowerCase();
      const vid = vid0 === 'tp3' && !e123 ? 'tp2' : vid0;
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
      /* 29.09 · ЗАКОНЪТ НА ПОЛОВИНИТЕ за цялата история. Записът на половини ("mode":"polovin" · бот v18.95 и
         сглобеното от сървъра) носи числото на СДЕЛКАТА — sum_pips (средното на половините: +90/+75/+25/0/−130…).
         Всеки друг запис (старият дневник на бота) дава само КОЙ е изходът (hit · exit_kind · стоп = вход);
         числото му е по стария закон и не се взима → ednaPoz (законът на половините). */
      /* 06.10 · ЗАКОНЪТ ТП 1·2·3 за ЦЯЛАТА история (zakonTp123 → mod/core.js · tp123): записът на бота по новия закон
         ("mode":"tp123") носи сам числото и целта (sum_pips · best · vid); всеки друг запис (половините от 29.09, старият
         дневник, сглобеното от картите) дава само доказателството — кои цели са взети (hit · exit_kind), нивата им, изхода
         и стопа на входа — а числото е най-високата стигната цел (+50 · +100 · +130) или −130 · 0 · ходът. */
      const izPx = vid0 === 'tp3' && !e123 ? null : num(x.exit_px);
      const hodIzh = entry !== null && izPx !== null ? hodP(entry, izPx, dir) : null;
      const h0 = ch.length === 1 ? ch[0] : ch[Math.min(1, ch.length - 1)];
      const Z = zakonTp123({ mode: x.mode, best: num(x.best), pips: e123 ? num(x.sum_pips) : null, vid: x.vid,
        m: naiDaleche(tp, nv, dir, vid, hodIzh), kind: vid, naVh, hod: hodIzh !== null ? hodIzh : h0 });
      const P = { sbor: Z.pips === null ? 0 : Z.pips, best: Z.best, k: Z.k };
      const sbor = P.sbor;
      out.push({
        dir, entry, d: utcDate(x.opened || x.otvoreno || x.vhod_utc || x.opened_utc),
        zatvD, chasti: [sbor], sbor,
        tp, vzeti: nv, sl: slL, vid, izhodPx: izPx,
        be40: naVh && nv < 1,
        /* zakon: 'star' · сделка отпреди 15.09, 14:12 (тогава с три позиции) · преброена по сегашния */
        starZakon: x.zakon === 'star', otKarti: x.izvor_zapis === 'karti',
        prichina: (x.prichina || x.reason) ? bezZhargon(String(x.prichina || x.reason)) : prichinaLedger(vid, nv, tp.length, naVh),
      });
      /* 29.09 · ВСЯКА сделка носи режима, половините и вида до mod/core.js · krai (видът: «Цел 2» · «Цел 1 + вход» ·
         «На входа» · «Стоп» · «Друг изход») — старите вече са преброени на половини */
      { const o = out[out.length - 1]; o.mode = 'tp123'; o.best = P.best; o.zakonVid = P.k; o.exit_kind = vid; }   // 06.10 · ТП 1·2·3 · видът за mod/core.js · krai
    });
    return out.length ? out.sort((p, q) => p.zatvD - q.zatvD) : null;
  }
  function prichinaLedger(vid, k, n, naVh) {
    const ime = (kk) => 'ТП' + Math.min(3, kk) + ' — най-високата стигната';
    if (k >= 3) return 'ТП3 — сделката е затворена';
    if (vid === 'sl') return k ? ime(k) + ', после СЛ на входа' : naVh ? 'СЛ на входа след +40' : 'СЛ преди +40';
    const pred = k ? ime(k) + ', после ' : naVh ? 'СЛ на входа след +40, после ' : '';
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
    /* 06.10 · КАРТИТЕ В TELEGRAM (законът: «ВХОД · ТП1 · ТП2 · ТП3 · СЛ») · новата карта ВХОД:
       «🟢 ВХОД · КУПИ ЗЛАТО · 4,130.38» · «СЛ 4,117.38 · −130 пипса» · «ТП1 4,135.38 · +50   ТП2 … · +100   ТП3 … · +130».
       Първо записът `d` на бота (mode tp123, ev signal: входът и нивата), после думите; старите карти — дословно както досега.
       ПЪТ НАЗАД: plan_rezervi/2026-10-06_tp123_karti_plat/app.js */
    const vx = g.match(/ВХОД\s*·\s*(?:КУПИ|ПРОДАЙ)\s+ЗЛАТО\s*·\s*([\d,]+\.\d+)/);
    const dv = k.dan && k.dan.mode === 'tp123' && k.dan.ev === 'signal' && k.dan.levels && typeof k.dan.levels === 'object' ? k.dan : null;
    const e = vx || g.match(/вход\s+([\d,]+\.\d+)/);
    const entry = dv && num(dv.entry) !== null ? num(dv.entry) : e ? num(e[1]) : null;
    if (entry === null) return null;
    const s = vx ? g.match(/(?:^|\n)\s*СЛ\s+([\d,]+\.\d+)(?:\s*·\s*[−–-]?(\d+)\s*пипса)?/) : g.match(/стоп\s+([\d,]+\.\d+)(?:\s*·\s*(\d+)\s*пипса)?/);
    const sl = dv && num(dv.levels.sl) !== null ? num(dv.levels.sl) : s ? num(s[1]) : null;
    const slPips = (s && s[2]) ? +s[2] : (sl !== null ? Math.round(Math.abs(sl - entry) / PIP) : 130);
    const tp = [];
    let x;
    if (dv) CELI_K.forEach((c) => { const p = num(dv.levels[c]); if (p !== null) tp.push({ px: p, pips: Math.round(Math.abs(p - entry) / PIP) }); });
    if (!tp.length && vx) { const re = /ТП([123])\s+([\d,]+\.\d+)\s*·\s*\+(\d+)/g; while ((x = re.exec(g)) !== null) tp.push({ px: num(x[2]), pips: +x[3] }); }
    RE_CEL.lastIndex = 0;
    if (!tp.length) while ((x = RE_CEL.exec(g)) !== null) tp.push({ px: num(x[2]), pips: +x[3] });
    if (!tp.length) {
      const red = g.split('\n').find((l) => /цели\s/.test(l));
      if (red) { RE_CEL_NOV.lastIndex = 0; while ((x = RE_CEL_NOV.exec(red)) !== null) tp.push({ px: num(x[1]), pips: +x[2] }); }
    }
    if (!tp.length) return null;
    /* 06.10 · ЗАКОНЪТ ТП 1·2·3 · новата ВЛЕЗ носи три цели (+50 · +100 · +130) и цел 3 затваря; старата (до 15.09) имаше
       трета на +200 — тя беше остатък, сделката се затваряше на цел 2 → там целите остават две */
    const nov123 = (k.dan && k.dan.mode === 'tp123') || (tp.length >= 3 && tp[2].pips <= 130);
    tp.splice(nov123 ? 3 : 2);
    const v = { d: k.d, dir, entry, sl, slPips, tp, maxCel: 0, zatv: null, mMax: 0, tp123: nov123 };
    /* 29.09 · бот v18.95 · ВЛЕЗ на сделка на две половини: «1 сделка · 2 половини × лот 0.10» */
    if (/2\s+половини/.test(g)) v.polovin = true;
    return v;
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
      /* «✅ … стопът беше на входа» · стопът е ударен на входа → 0 (както сървърът · data.mjs) · 06.10 · и «🛑 СЛ на входа» */
      naVhoda: vid === 'sl' && (/^✅/.test(g.trim()) || /стопът беше на входа/.test(g) || /СЛ на входа/.test(g)),
      /* 06.10 · КАРТИТЕ В TELEGRAM · картата по закона казва сама: «СЛ на входа · 0 пипса» (без цел) ·
         «сделката: ТПn +N пипса» (стигнатата цел) — броят се само за сделка по закона ТП 1·2·3 (chastiZatvorena) */
      nula: /(?:СЛ на входа|стопът беше на входа)\s*·\s*0\s*пипса/.test(g),
      tpN: +((g.match(/сделката:\s*ТП([123])\s*\+/) || [])[1] || 0),
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
        /* 06.10 · КАРТИТЕ В TELEGRAM · и новата карта «ВХОД · КУПИ|ПРОДАЙ ЗЛАТО · N» */
        if (k.text.indexOf('ВЛЕЗ') >= 0 || /ВХОД\s*·/.test(k.text)) { const v = vhodOt(k); if (v) vhodove.push(v); }
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
      /* 06.10 · ЗАКОНЪТ ТП 1·2·3 · ходът на ЦЕЛ-картата (цената вдясно на стрелката, и при гап) е доказателство за целта */
      if (n && Number.isFinite(x.to)) t.mMax = Math.max(t.mMax || 0, hodP(t.entry, x.to, t.dir));
      const dn = k.dan && k.dan.mode === 'tp123' ? k.dan : null;
      if (dn) t.tp123 = true;
      /* 29.09 · бот v18.95 · сделка на ДВЕ ПОЛОВИНИ (ВЛЕЗ «2 половини» или думите на изхода): числото на
         СДЕЛКАТА е «сделката донесе N пипса» на затварящата карта (средното на половините, и с .5) */
      const gx = gol(k.text);
      /* 06.10 · по закона ТП 1·2·3 цел 1 и цел 2 НЕ затварят (затварят цел 3, стопът, обратът, времето) */
      const zatvaria = dn && typeof dn.closes === 'boolean' ? dn.closes : (x.zatvarya && !(t.tp123 && /^tp[12]$/.test(x.vid)));
      if (zatvaria) {
        t.zatv = { d: x.d, vid: x.vid, to: x.to, parts: x.parts, naVhoda: x.naVhoda, nula: x.nula, tpN: x.tpN };
        /* 06.10 · картата по закона ТП 1·2·3 носи числото и целта на СДЕЛКАТА (`d`: pips · best) */
        if (dn && Number.isFinite(+dn.pips)) { t.zatv.sbor = +dn.pips; t.zatv.best = +dn.best || 0; }
      }
    });
    return { vhodove, bezVhod };
  }
  function chastiZatvorena(v) {
    const z = v.zatv;
    const k = Math.min(v.maxCel, v.tp.length);
    const vid = z.vid === 'tp3' && !v.tp123 ? 'tp2' : z.vid;   // 06.10 · старото «tp3» = остатък · по ТП 1·2·3 цел 3 затваря
    /* 06.10 · ЗАКОНЪТ ТП 1·2·3 · картата на бота по новия закон носи числото и целта на сделката */
    if (Number.isFinite(z.sbor) && v.tp123) {
      const Zb = zakonTp123({ mode: 'tp123', best: z.best || 0, pips: z.sbor, kind: vid });
      return { ch: [Zb.pips], otBota: false, best: Zb.best, k: Zb.k, kind: vid, nv: Math.max(k, Zb.best) };
    }
    /* цел 1 = картата ЦЕЛ 1 или ✅ «стопът беше на входа» без карта «стопът на входа» при +40 (както сървърът · data.mjs) ·
       числото = най-високата стигната цел (нивата на взетите цели и ходът на ЦЕЛ-картите) · иначе −130 · 0 · ходът */
    /* 06.10 · КАРТИТЕ В TELEGRAM · сделка по закона ТП 1·2·3: «СЛ на входа · 0 пипса» = без цел (не става цел 1) ·
       «сделката: ТПn +N» = стигнатата цел n по думите на самата карта */
    const nv0 = vid === 'sl' && z.naVhoda && !v.be40 && !(v.tp123 && z.nula) ? Math.max(1, k) : k;
    const nv = v.tp123 && z.tpN ? Math.max(nv0, Math.min(z.tpN, v.tp.length || z.tpN)) : nv0;
    const hodIzh = Number.isFinite(z.to) ? hodP(v.entry, z.to, v.dir) : null;
    const h0 = hodIzh !== null ? hodIzh : (z.parts && z.parts.length ? z.parts[Math.min(1, z.parts.length - 1)] : 0);
    const m = Math.max(naiDaleche(v.tp, nv, v.dir, vid, hodIzh), v.mMax || 0);
    const Z = zakonTp123({ m, kind: vid, naVh: !!(v.be40 || z.naVhoda) && nv < 1, hod: h0 });
    return { ch: [Z.pips === null ? 0 : Z.pips], otBota: false, best: Z.best, k: Z.k, kind: vid, nv };
  }
  function imeCeli(k) { return 'ТП' + Math.min(3, k) + ' — най-високата стигната'; }   // 06.10 · G1-02 (в)
  function prichinaZatv(v) {
    const z = v.zatv;
    const k0 = Math.min(v.maxCel, v.tp.length);
    /* 29.09 · ✅ «стопът беше на входа» без карта «+40» = цел 1 е взета (както chastiZatvorena и сървърът) ·
       06.10 · по закона ТП 1·2·3 «СЛ на входа · 0 пипса» е без цел, «сделката: ТПn» е цел n (като chastiZatvorena) */
    const k1 = z.vid === 'sl' && z.naVhoda && !v.be40 && !(v.tp123 && z.nula) ? Math.max(1, k0) : k0;
    const k = v.tp123 && z.tpN ? Math.max(k1, Math.min(z.tpN, v.tp.length || z.tpN)) : k1;
    const naVh = !!(v.be40 || z.naVhoda);
    if (k >= 3) return 'ТП3 — сделката е затворена';   // 06.10 · G1-02 (в) · беше «всички цели взети» при k ≥ броя нива
    if (z.vid === 'sl') return k ? imeCeli(k) + ', после СЛ на входа' : naVh ? 'СЛ на входа след +40' : 'СЛ преди +40';
    const pred = k ? imeCeli(k) + ', после ' : naVh ? 'СЛ на входа след +40, после ' : '';
    if (z.vid === 'flip') return pred + 'затворена · посоката се обърна';
    if (z.vid === 'time') return pred + 'затворена по време';
    return pred + 'затворена';
  }
