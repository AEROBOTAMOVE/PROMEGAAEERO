// СНИМКА · netlify/functions/_lib/data.mjs на AERO_КЛИЕНТ · 2026-09-25T09:45 UTC · sha256 285c2b4714598cb4
// СНИМКА · дословни извадки, НЕ СЕ ПИШАТ НА РЪКА: node platforma/proba_karti.mjs snimka <AERO_КЛИЕНТ>
const RE_CENI = /([\d,]+\.\d+)\s*(?:\([^)]*\))?\s*→\s*([\d,]+\.\d+)/;
const RE_VHOD = /вход\s+<?c?o?d?e?>?\s*([\d,]+\.\d+)/;
const golo = (s) => String(s == null ? "" : s).replace(/<[^>]+>/g, "");
const chislo = (s) => {
  const v = parseFloat(String(s).replace(/,/g, "").replace(/[−–]/g, "-"));
  return Number.isFinite(v) ? v : null;
};
const isoUtc = (ms) => new Date(ms).toISOString().slice(0, 19);
function celiOt(g) {
  const out = [];
  const re = /([123])️?⃣\s*([\d,]+\.\d+)\s*\((\d+)\s*п\)/g;
  let m;
  while ((m = re.exec(g)) !== null) out.push(chislo(m[2]));
  if (out.length) return out;
  const red = g.split("\n").find((l) => /цели\s/.test(l));
  if (red) {
    const r2 = /([\d,]+\.\d+)\s*\+(\d+)/g;
    while ((m = r2.exec(red)) !== null) out.push(chislo(m[1]));
  }
  return out;
}
const ZAKON_BROENE = "sdelka";
const ZAKON_POZICII = 1;
const hodPips = (vhod, izhod, dir) => Math.round(Number((((izhod - vhod) * dir) / 0.1).toFixed(6)));
const ZAPIS_D = true;
function dOt(k, ev) {
  const d = ZAPIS_D && k ? k.d : null;
  if (!d || typeof d !== "object" || d.v !== 1 || d.ev !== ev) return null;
  const dir = d.dir === "long" ? 1 : d.dir === "short" ? -1 : 0;
  const entry = Number(d.entry);
  if (!dir || d.entry === null || d.entry === undefined || !Number.isFinite(entry)) return null;
  const n = (x) => (x === null || x === undefined || x === "" || !Number.isFinite(Number(x)) ? null : Number(x));
  const lv = d.levels && typeof d.levels === "object" ? d.levels : {};
  const celi = n(lv.tp1) === null && n(lv.tp2) === null ? [] : [n(lv.tp1), n(lv.tp2)];
  return { dir, entry, sl: n(lv.sl), celi, kind: String(d.kind || ""), px: n(d.exit_px),
    pips: n(d.pips), closes: !!d.closes, be: !!d.be };
}
function sdelkiOtKarti(text, zakonBroene = ZAKON_BROENE, pozicii = ZAKON_POZICII) {
  const poKarti = zakonBroene === "karta";
  const dvePoz = pozicii === 2;                               // пътят назад · старото броене
  const redove = String(text).split(/\r?\n/);
  const spis = [];           // всички входове по ред · затворените остават, за да се разпознае остатъкът
  let ostatak = 0, bezVhod = 0;
  /* 24.09 · ПЛАН_ТОТАЛЕН Н-07 · ПАЗАЧЪТ. Изходна карта на главния слот (exit:*), която не се
     разчете (няма посока или няма «вход → изход»), НЕ се прескача тихо: влиза тук и слиза при
     клиента до live/sdelki_karti.json (поле neprochetni), а екранът казва, че записът е непълен.
     Сделката ѝ не получава число — по-добре празно, отколкото тихо сгрешено число (никога 0). */
  const neprochetni = [];
  const neprochetena = (k, zashto) => neprochetni.push({ utc: String(k.utc || ""), tag: String(k.tag || ""), zashto });
  /* 25.09 · Н-07 · враждебната проба (всяка от 354-те изходни карти счупена поотделно): да се
     прескочи непрочетената карта НЕ стига. Следващата карта на същия вход затваря сделката с
     ГРЕШНО число — цел 2 без цена → стопът «на входа» след нея даваше 0 вместо +130 (20 карти);
     цел 1 без цена → стопът даваше −130 вместо 0 (01.09 12:47). Затова и СДЕЛКАТА на картата
     се бележи nechetim и не получава число (изходният цикъл по-долу я прескача).
     Коя е сделката — точно както я търси редовният път (посока + вход ±0.006, последната):
       · входът се чете («X (hh:mm) →», «стопа на X», «на входа X» — мерено 25.09: 354/354,
         119/119, 6/6 съвпадат с входа) → тази сделка, ако е отворена; ако е затворена, картата
         е остатък и числото не зависи от нея; ако я няма → входът е отпреди записа: слага се
         празна сделка без вход (nechetim), за да се закачат за нея следващите карти, а не да я
         родят наново без цел 1;
       · входът не се чете → ВСИЧКИ отворени сделки в тази посока (в двете, ако и посоката не се
         чете). Не само последната: при две отворени коя е — не се знае, а празното е по-добро
         от грешното число. */
  const vhodOtKarta = (g) => {
    const a = g.match(/([\d,]+\.\d+)\s*(?:\([^)]*\))?\s*→/) || g.match(/стопа\s+на\s+([\d,]+\.\d+)/) || g.match(/на\s+входа\s+([\d,]+\.\d+)/);
    return a ? chislo(a[1]) : null;
  };
  const oznachiNechetimi = (dir, vhod, t) => {
    const posoki = dir ? [dir] : [1, -1];
    if (vhod === null) {
      for (const x of spis) if (x.otv <= t && !x.zatv && posoki.includes(x.dir)) x.nechetim = true;
      return;
    }
    for (const d of posoki) {
      let v = null;
      for (let i = spis.length - 1; i >= 0; i--) {
        const x = spis[i];
        if (x.dir === d && x.otv <= t && Math.abs(x.entry - vhod) <= 0.006) { v = x; break; }
      }
      if (!v) spis.push({ dir: d, entry: vhod, otv: t, sl: null, celi: [], cel: 0, zatv: null, bezVhod: true, nechetim: true });
      else if (!v.zatv) v.nechetim = true;
    }
  };
  for (const red of redove) {
    const l = red.trim();
    if (!l) continue;
    let k;
    try { k = JSON.parse(l); } catch (e) { continue; }
    if (!k || typeof k.tag !== "string" || typeof k.text !== "string") continue;
    const t = Date.parse(/(Z|[+\-]\d\d:?\d\d)$/i.test(k.utc || "") ? k.utc : (k.utc || "") + "Z");
    if (!Number.isFinite(t)) continue;
    const g = golo(k.text);

    if (k.tag === "signal") {
      const ds = dOt(k, "signal");            // 25.09 · Н-08 · от данните, ако ги има
      if (ds) { spis.push({ dir: ds.dir, entry: ds.entry, otv: t, sl: ds.sl, celi: ds.celi, cel: 0, zatv: null }); continue; }
      /* картата ВЛЕЗ. До 14.09 ботът е писал «🟢 КУПИ ЗЛАТО · ПРЕМИУМ 7/8» без думата ВЛЕЗ —
         затова се хваща по «КУПИ/ПРОДАЙ ЗЛАТО» + «вход». «📌 СДЕЛКАТА ТЕЧЕ» и «⏸ БЕЗ ВХОД»
         пишат «ЗЛАТО покупка» / «ЗЛАТО нагоре» и не минават оттук. */
      const m = g.match(/(КУПИ|ПРОДАЙ)\s+(ЗЛАТО|СРЕБРО)/);
      if (!m || m[2] !== "ЗЛАТО") continue;
      const e = g.match(RE_VHOD);
      const entry = e ? chislo(e[1]) : null;
      if (entry === null) continue;
      const s = g.match(/стоп\s+([\d,]+\.\d+)/);
      spis.push({
        dir: m[1] === "КУПИ" ? 1 : -1, entry, otv: t, sl: s ? chislo(s[1]) : null,
        celi: celiOt(g), cel: 0, zatv: null,
      });
      continue;
    }
    /* 22.09 · бот v18.85 · картата «🛡 стопът на входа» (таг exit-be) идва при +40 пипса, ПРЕДИ цел 1.
       Тя НЕ е изход: сделката остава отворена и целите остават. Тук само отбелязва сделката (be40),
       за да се знае после, че стопът е бил на входа → стоп след нея е 0, не −130. Сделката се намира
       по посока + «премести стопа на X» (= входа), а ако входът не съвпадне — по цел 1 от картата. */
    if (/^exit-be\b/.test(k.tag)) {
      const db = dOt(k, "be");                // 25.09 · Н-08 · от данните: посоката и входът
      if (db) {
        for (let i = spis.length - 1; i >= 0; i--) {
          const x = spis[i];
          if (x.dir !== db.dir || x.otv > t || x.zatv) continue;
          if (Math.abs(x.entry - db.entry) <= 0.006) { x.be40 = true; break; }
        }
        continue;
      }
      /* 25.09 · Н-07 · «⏩ в същата проверка дойде и цел 1» (23.09 11:35, 24.09 05:05) е без цени по
         замисъл — следващата карта е цел 1 и тя слага стопа на входа. Не е неразчетена. */
      if (/дойде\s+и\s+цел\s*1/.test(g)) continue;
      const mb = g.match(/ЗЛАТО\s+(покупка|продажба)/);
      /* 25.09 · Н-07 · непрочетена «стопът на входа» → без нея стоп след нея би бил −130 вместо 0 */
      if (!mb) { if (!/СРЕБРО/.test(g)) { neprochetena(k, "без посока"); oznachiNechetimi(0, vhodOtKarta(g), t); } continue; }
      const dirB = mb[1] === "покупка" ? 1 : -1;
      const sb = g.match(/стопа\s+на\s+([\d,]+\.\d+)/);
      const cb = g.match(/1️?⃣\s*([\d,]+\.\d+)/);
      const stopB = sb ? chislo(sb[1]) : null;
      const cel1B = cb ? chislo(cb[1]) : null;
      if (stopB === null && cel1B === null) { neprochetena(k, "без цена"); oznachiNechetimi(dirB, null, t); continue; }
      for (let i = spis.length - 1; i >= 0; i--) {
        const x = spis[i];
        if (x.dir !== dirB || x.otv > t || x.zatv) continue;
        if ((stopB !== null && Math.abs(x.entry - stopB) <= 0.006)
          || (cel1B !== null && Number.isFinite(x.celi[0]) && Math.abs(x.celi[0] - cel1B) <= 0.006)) { x.be40 = true; break; }
      }
      continue;
    }
    if (k.tag.split(":")[0] !== "exit") continue;           // само главният слот
    const dx = dOt(k, "exit");                // 25.09 · Н-08 · от данните, ако ги има
    const vid = dx && dx.kind ? dx.kind : (k.tag.split(":")[1] || "").split("#")[0];
    const m = dx ? [null, dx.dir === 1 ? "покупка" : "продажба"] : g.match(/ЗЛАТО\s+(покупка|продажба)/);
    const f = dx ? [null, null, null] : g.match(RE_CENI);
    const entry = dx ? dx.entry : f ? chislo(f[1]) : null;
    if (!m || entry === null) {
      /* Н-07 · сребърна карта не е «неразчетена» — тя просто не е за нашия инструмент */
      if (!m && /СРЕБРО/.test(g)) continue;
      neprochetena(k, !m ? "без посока" : "без цена");
      oznachiNechetimi(m ? (m[1] === "покупка" ? 1 : -1) : 0, vhodOtKarta(g), t);   // 25.09 · и сделката ѝ остава без число
      continue;
    }
    const dir = m[1] === "покупка" ? 1 : -1;
    const izhod = dx ? dx.px : chislo(f[2]);
    let v = null;
    for (let i = spis.length - 1; i >= 0; i--) {
      const x = spis[i];
      if (x.dir !== dir || x.otv > t || Math.abs(x.entry - entry) > 0.006) continue;
      v = x; break;
    }
    if (!v) { bezVhod++; v = { dir, entry, otv: t, sl: null, celi: [], cel: 0, zatv: null, bezVhod: true }; spis.push(v); }
    if (v.zatv) {
      ostatak++;
      if (!poKarti) continue;                                // остатък от старите три позиции
      /* законът "karta": остатъкът се брои за отделна сделка · същият вход, свое затваряне */
      v = { dir: v.dir, entry: v.entry, otv: v.zatv.t, sl: v.sl, celi: v.celi, cel: v.cel >= 2 ? 1 : v.cel, zatv: null, ostatak: true, nechetim: !!v.nechetim };   // 25.09 · Н-07 · остатъкът наследява непрочетеното
      spis.push(v);
    }
    if (vid === "tp1") { v.cel = Math.max(v.cel, 1); continue; }
    if (vid === "tp2" || vid === "tp3") { v.cel = 2; v.zatv = { t, vid: "tp2", px: izhod }; continue; }
    if (vid === "sl") {
      /* «стопът беше на входа» се познава по ✅ в началото ИЛИ по това, че цел 1 вече е взета.
         Второто не е излишно: 01.09, 16:02 (покупка 4,356.97) картата почва с 🛑 и сборът на бота
         е −48 (гап през стопа на входа), но цел 1 Е взета — по закона на собственика след цел 1
         няма минус, значи 0 (стопът е на входа). Това е единствената карта, в която двете четения
         се различават. */
      const naVhoda = (dx ? dx.be : /^✅/.test(g.trim())) || v.cel >= 1 || !!v.be40;   // be40 · стопът на входа при +40 (v18.85) · Н-08: `be` от данните
      v.zatv = { t, vid: "sl", px: izhod, naVhoda };
      continue;
    }
    const sb = dx ? null : g.match(/сделката донесе\s*([+−\-]?\d+)\s*пипса/i);
    v.zatv = { t, vid, px: izhod, sbor: dx ? (dx.pips === null ? 0 : dx.pips) : sb ? Number(String(sb[1]).replace("−", "-")) : 0, karta: k };
  }

  /* 15.09 14:12 софийско · от тогава картите са по закона с целите 50 / 100–130 и стопа 130.
     По-старите карти (3 позиции, цели 75/120/200) се броят по сегашния закон → zakon: "star". */
  const NOV_ZAKON = Date.parse("2026-09-15T11:12:00Z");
  const out = [];
  for (const v of spis) {
    if (!v.zatv) continue;
    /* 25.09 · Н-07 · сделка с непрочетена карта няма число — нито 0, нито числото от по-късна карта.
       Картата ѝ вече е в neprochetni, затова тук не се брои втори път. */
    if (v.nechetim) continue;
    const z = v.zatv;
    /* Н-07 · обрат / по време без цена на изхода → числото не се знае. Дотук ставаше 0 (тихо
       сгрешено число); сега сделката не влиза в списъка, а картата ѝ — в neprochetni. */
    if (z.vid !== "tp2" && z.vid !== "sl" && !Number.isFinite(z.px)) { neprochetena(z.karta || {}, "без цена на изхода"); continue; }
    /* стопът е на входа при +40, а цел 1 НЕ е взета (бот v18.85) → hit.be вместо hit.tp1:
       числото е същото (0), но платформата не бива да пише «цел 1», щом цел 1 не е падала */
    const be40 = !!v.be40 && v.cel < 1;
    let parts, hit;
    if (dvePoz) {
      /* пътят назад · двете позиции, точно както се броеше до 21.09 */
      if (z.vid === "tp2") { parts = [50, v.dir === 1 ? 130 : 100]; hit = { tp1: true, tp2: true }; }
      else if (z.vid === "sl") { parts = z.naVhoda ? (be40 ? [0, 0] : [50, 0]) : [-130, -130]; hit = z.naVhoda ? (be40 ? { be: true } : { tp1: true }) : {}; }
      else {
        const s = Number.isFinite(z.sbor) ? z.sbor : 0;
        parts = v.cel >= 1 ? [50, Math.max(0, s - 50)] : [Math.round(s / 2), s - Math.round(s / 2)];
        hit = v.cel >= 1 ? { tp1: true } : {};
      }
    } else if (z.vid === "tp2") {
      /* цел 2 затваря ЕДИНСТВЕНАТА позиция · 13 $ при покупка, 10 $ при продажба */
      parts = [v.dir === 1 ? 130 : 100]; hit = { tp1: true, tp2: true };
    } else if (z.vid === "sl") {
      /* след цел 1 стопът е на входа → 0, никога минус; преди цел 1 → целият стоп, −130 */
      parts = [z.naVhoda ? 0 : -130]; hit = z.naVhoda ? (be40 ? { be: true } : { tp1: true }) : {};
    } else {
      /* обрат / по време · позицията излиза на цената от картата («вход → изход»). Взета ли е
         цел 1, стопът вече е на входа — затова не под нулата. Цената я има винаги: карта без
         «→» изобщо не минава оттук (RE_CENI по-горе). Мерено 22.09: 2 обрата в целия запис —
         −67 (08.09) и −14 (10.09), точно ходът, който пише в самата карта. */
      const h = Number.isFinite(z.px) ? hodPips(v.entry, z.px, v.dir) : 0;
      parts = [v.cel >= 1 || be40 ? Math.max(0, h) : h];
      hit = v.cel >= 1 ? { tp1: true } : be40 ? { be: true } : {};
    }
    const sum = parts.reduce((a, x) => a + x, 0);
    /* изход без своята карта ВЛЕЗ (входът е отпреди началото на записа) → часът на входа не се
       измисля: остава празен, а сделката се брои по часа на затварянето */
    const otv = v.bezVhod ? null : isoUtc(v.otv);
    out.push({
      id: (v.dir === 1 ? "long" : "short") + "|" + v.entry.toFixed(2) + "|" + isoUtc(v.otv).slice(0, 16),
      direction: v.dir === 1 ? "long" : "short", entry: v.entry, opened: otv, slot: "main",
      levels: { tp1: v.celi[0] !== undefined ? v.celi[0] : null, tp2: v.celi[1] !== undefined ? v.celi[1] : null, sl: v.sl },
      closed: isoUtc(z.t), hit, exit_kind: z.vid, exit_px: Number.isFinite(z.px) ? z.px : null,
      parts, sum_pips: sum, izvor_zapis: "karti", zakon: v.otv < NOV_ZAKON ? "star" : "nov",
    });
  }
  out.sort((a, b) => (a.closed < b.closed ? -1 : a.closed > b.closed ? 1 : 0));
  return { sdelki: out, ostatak, bezVhod, neprochetni };
}
const RE_OBSHTO = /сделката\s+донесе\s*([+−–\-]?[\d.,]+)\s*пипса/i;
const RE_KRAEN = /(ЗАГУБА|ПЕЧАЛБА)\s*([+−–\-]?[\d.,]+)\s*пипса/i;
function poziciiOtKarti(text) {
  const redove = String(text).split(/\r?\n/);
  const zhivi = new Map();                 // слот|посока|вход → отворената позиция
  const vhodove = [];                      // обявените карти ВЛЕЗ · по тях се познава кое е ДАДЕН сигнал
  const out = [];
  let neprochetni = 0;
  for (const red of redove) {
    const l = red.trim();
    if (!l) continue;
    let k;
    try { k = JSON.parse(l); } catch (e) { continue; }
    if (!k || typeof k.tag !== "string" || typeof k.text !== "string") continue;
    if (k.tag === "signal") {
      const ds = dOt(k, "signal");            // 25.09 · Н-08 · от данните, ако ги има
      if (ds) {
        const td = Date.parse(/(Z|[+\-]\d\d:?\d\d)$/i.test(k.utc || "") ? k.utc : (k.utc || "") + "Z");
        if (Number.isFinite(td)) vhodove.push({ dir: ds.dir === 1 ? "long" : "short", cena: ds.entry, t: td });
        continue;
      }
      /* обявен вход · «🟢🟢 ВЛЕЗ · КУПИ ЗЛАТО … вход 4,432.81». «⏸ ВИЖДАМ … но не я давам»
         (таг «спряна:*») и мислите на мозъка НЕ минават оттук — те не са дадени сигнали. */
      const gs = golo(k.text);
      const ms = gs.match(/(КУПИ|ПРОДАЙ)\s+ЗЛАТО/);
      const es = gs.match(RE_VHOD);
      const ts = Date.parse(/(Z|[+\-]\d\d:?\d\d)$/i.test(k.utc || "") ? k.utc : (k.utc || "") + "Z");
      if (ms && es && Number.isFinite(ts)) {
        const c = chislo(es[1]);
        if (c !== null) vhodove.push({ dir: ms[1] === "КУПИ" ? "long" : "short", cena: c, t: ts });
      }
      continue;
    }
    const koren = k.tag.split(":")[0];
    if (koren !== "exit" && koren !== "exit2") continue;        // brain* и sh-exit не са обявени сделки
    const t = Date.parse(/(Z|[+\-]\d\d:?\d\d)$/i.test(k.utc || "") ? k.utc : (k.utc || "") + "Z");
    if (!Number.isFinite(t)) continue;
    const g = golo(k.text);
    const dx = koren === "exit" ? dOt(k, "exit") : null;   // 25.09 · Н-08 · от данните, ако ги има
    const m = dx ? [null, dx.dir === 1 ? "покупка" : "продажба"] : g.match(/ЗЛАТО\s+(покупка|продажба)/);
    const f = dx ? [""] : g.match(RE_CENI);
    if (!m || !f) { neprochetni += 1; continue; }
    const vhod = dx ? dx.entry : chislo(f[1]);
    if (vhod === null) { neprochetni += 1; continue; }
    const vid = dx && dx.kind ? dx.kind : (k.tag.split(":")[1] || "").split("#")[0];
    const slot = Number((k.tag.match(/#(\d+)/) || [, "1"])[1]);
    /* ходът за тази карта · числото веднага след реда с двете нива */
    const sled = dx ? "" : g.slice(g.indexOf(f[0]) + f[0].length);
    const hod = dx ? dx.pips : chislo((sled.match(/([+−–\-]?[\d.,]+)\s*пипса/) || [])[1]);
    /* сметката на сделката · както ботът я е написал */
    const so = dx ? null : g.match(RE_OBSHTO) || null;
    const kr = dx || so ? null : g.match(RE_KRAEN);
    /* 22.09 · бот v18.85 · «✅ стопът беше на входа · 0 пипса · без загуба» (след exit-be при +40) —
       числото стои в самия първи ред, дори картата да няма «сделката донесе» */
    const nula = !dx && !so && !kr && /стопът беше на входа\s*·\s*0\s*пипса/.test(g);
    const sbor = dx ? dx.pips : so ? chislo(so[1]) : kr ? chislo(kr[2]) * (/ЗАГУБА/i.test(kr[1]) && chislo(kr[2]) > 0 ? -1 : 1) : nula ? 0 : null;
    const kluch = slot + "|" + m[1] + "|" + vhod.toFixed(2);
    let p = zhivi.get(kluch);
    if (!p) {
      p = { slot, direction: m[1] === "покупка" ? "long" : "short", entry: vhod, parva: isoUtc(t), celi: 0, hod_max: null, karti: [] };
      zhivi.set(kluch, p);
    }
    p.karti.push(vid);
    if (vid === "tp1") p.celi = Math.max(p.celi, 1);
    if (vid === "tp2") p.celi = Math.max(p.celi, 2);
    if (vid === "tp3") p.celi = 3;
    if (hod !== null && (p.hod_max === null || Math.abs(hod) > Math.abs(p.hod_max) || hod > p.hod_max)) p.hod_max = hod;
    if (dx ? !dx.closes : !/затворена/.test(g)) continue;
    p.closed = isoUtc(t);
    p.kraj = vid;
    p.pipsove = sbor;
    if (sbor === null) neprochetni += 1;
    /* ДАДЕН СИГНАЛ ли е · трябва обявена карта ВЛЕЗ със същата посока и същия вход, пратена
       ПРЕДИ позицията (до минута разлика) и не по-стара от 3 дни. Мерено 16.09: 256 от 261
       затворени позиции минават; 5-те, които падат, са от 01–03.09 — входът им е отпреди
       началото на записа. От 08.09 минават всичките 209. */
    const t0 = Date.parse(p.parva + "Z");
    const nam = vhodove.filter((v) => v.dir === p.direction && Math.abs(v.cena - p.entry) <= 0.006
      && v.t <= t0 + 60000 && t - v.t <= 3 * 86400000).pop();
    p.daden = !!nam;
    if (nam) p.vhod_utc = isoUtc(nam.t);       // часът на обявяването · за «колко наведнъж»
    out.push(p);
    zhivi.delete(kluch);                    // същият вход по-късно = НОВА позиция, не същата
  }
  out.sort((a, b) => (a.closed < b.closed ? -1 : a.closed > b.closed ? 1 : 0));
  const dadeni = out.filter((p) => p.daden);
  const sbor = dadeni.reduce((a, p) => a + (p.pipsove || 0), 0);
  return {
    pozicii: out,
    otvoreni: [...zhivi.values()].length,
    neprochetni,
    obobshtenie: {
      broi: dadeni.length, pipsove: sbor,
      na_plus: dadeni.filter((p) => (p.pipsove || 0) > 0).length,
      na_minus: dadeni.filter((p) => (p.pipsove || 0) < 0).length,
      glavni: dadeni.filter((p) => p.slot === 1).length,
      bez_obyaven_vhod: out.length - dadeni.length,
    },
  };
}
