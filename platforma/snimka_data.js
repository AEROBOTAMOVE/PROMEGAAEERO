// СНИМКА · netlify/functions/_lib/data.mjs на AERO_КЛИЕНТ · 2026-10-07T14:26 UTC · sha256 f2c734b0b975a880
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
  let m;
  /* 06.10 · КАРТИТЕ В TELEGRAM · новата карта ВХОД: «ТП1 4,135.38 · +50   ТП2 4,140.38 · +100   ТП3 4,143.38 · +130» */
  const reT = /ТП([123])\s+([\d,]+\.\d+)\s*·\s*\+(\d+)/g;
  while ((m = reT.exec(g)) !== null) out.push(chislo(m[2]));
  if (out.length) return out;
  const re = /([123])️?⃣\s*([\d,]+\.\d+)\s*\((\d+)\s*п\)/g;
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
const ZAKON_POZICII = "tp123";
const hodPips = (vhod, izhod, dir) => Math.round(Number((((izhod - vhod) * dir) / 0.1).toFixed(6)) * 10) / 10;
const TP123_CELI = [50, 100, 130];
const TP123_STOP = 130;
const celPo = (m) => (Number.isFinite(m) ? (m >= 129.95 ? 3 : m >= 99.95 ? 2 : m >= 49.95 ? 1 : 0) : 0);
function tp123Zakon({ m, kind, naVh, hod } = {}) {
  const b = celPo(m);
  if (b) return { best: b, pips: TP123_CELI[b - 1], vid: "cel" + b };
  if (String(kind || "") === "sl") return naVh ? { best: 0, pips: 0, vid: "vhod" } : { best: 0, pips: -TP123_STOP, vid: "stop" };
  if (!Number.isFinite(hod)) return { best: 0, pips: null, vid: "drug" };
  let p = Math.round(hod * 10) / 10;
  if (naVh && p < 0) p = 0;
  return { best: 0, pips: Math.max(p, -TP123_STOP), vid: "drug" };
}
const POL_CEL1 = 50;
const POL_STOP = 130;
const polCel2 = (dir) => (dir > 0 ? 130 : 100);
const polDvoika = (halves, kind) => ({ halves, sum: (halves[0] + halves[1]) / 2, kind });
function polovinZakon(nv, vid, dir, naVh, hod) {
  const v = vid === "tp3" ? "tp2" : String(vid || "");
  if (nv >= 2 || v === "tp2") return polDvoika([POL_CEL1, polCel2(dir)], "tp2");
  if (v === "sl") return polDvoika(nv >= 1 ? [POL_CEL1, 0] : naVh ? [0, 0] : [-POL_STOP, -POL_STOP], "sl");
  const x = Number.isFinite(hod) ? Math.round(hod * 10) / 10 : 0;
  const h2 = nv >= 1 || naVh ? Math.max(0, x) : x;
  return polDvoika([nv >= 1 ? POL_CEL1 : h2, h2], v);
}
const ZAPIS_D = true;
function dOt(k, ev) {
  const d = ZAPIS_D && k ? k.d : null;
  if (!d || typeof d !== "object" || d.v !== 1 || d.ev !== ev) return null;
  const dir = d.dir === "long" ? 1 : d.dir === "short" ? -1 : 0;
  const entry = Number(d.entry);
  if (!dir || d.entry === null || d.entry === undefined || !Number.isFinite(entry)) return null;
  const n = (x) => (x === null || x === undefined || x === "" || !Number.isFinite(Number(x)) ? null : Number(x));
  const lv = d.levels && typeof d.levels === "object" ? d.levels : {};
  const celi = n(lv.tp1) === null && n(lv.tp2) === null ? [] : n(lv.tp3) === null ? [n(lv.tp1), n(lv.tp2)] : [n(lv.tp1), n(lv.tp2), n(lv.tp3)];
  /* 29.09 · бот v18.95 · «ПОЛОВИНАТА НА +50» · записът на сделка на две половини носи
     "mode":"polovin"; на затварящата pips е ЦЯЛАТА сделка (средното на половините: +90/+75/+25/0/−130…),
     halves — двете половини. Без "mode" (старите записи) — досегашното значение, дословно. */
  const pol = d.mode === "polovin";
  const halves = pol && Array.isArray(d.halves) && d.halves.length === 2 && d.halves.every((x) => n(x) !== null)
    ? d.halves.map(n) : null;
  /* 06.10 · бот v18.99 · ЗАКОНЪТ ТП 1·2·3 · "mode":"tp123" · "best" (0–3) · "pips" = резултатът по закона · "closes" */
  const t123 = d.mode === "tp123";
  return { dir, entry, sl: n(lv.sl), celi, kind: String(d.kind || ""), px: n(d.exit_px),
    pips: n(d.pips), closes: !!d.closes, zatvKazano: typeof d.closes === "boolean", be: !!d.be, pol, halves, t123, best: n(d.best) };
}
function sdelkiOtKarti(text, zakonBroene = ZAKON_BROENE, pozicii = ZAKON_POZICII) {
  const poKarti = zakonBroene === "karta";
  const dvePoz = pozicii === 2;                               // пътят назад · старото броене
  const naPol = pozicii === "polovin";                        // 29.09 · законът на половините за цялата история
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
      if (ds) { spis.push(Object.assign({ dir: ds.dir, entry: ds.entry, otv: t, sl: ds.sl, celi: ds.celi, cel: 0, zatv: null, mMax: 0 }, ds.pol ? { pol: true } : {}, ds.t123 || (ds.celi.length >= 3 && Number.isFinite(ds.celi[2]) && Math.abs(ds.celi[2] - ds.entry) / 0.1 <= 130.5) ? { t123: true } : {})); continue; }
      /* картата ВЛЕЗ. До 14.09 ботът е писал «🟢 КУПИ ЗЛАТО · ПРЕМИУМ 7/8» без думата ВЛЕЗ —
         затова се хваща по «КУПИ/ПРОДАЙ ЗЛАТО» + «вход». «📌 СДЕЛКАТА ТЕЧЕ» и «⏸ БЕЗ ВХОД»
         пишат «ЗЛАТО покупка» / «ЗЛАТО нагоре» и не минават оттук. */
      const m = g.match(/(КУПИ|ПРОДАЙ)\s+(ЗЛАТО|СРЕБРО)/);
      if (!m || m[2] !== "ЗЛАТО") continue;
      /* 06.10 · КАРТИТЕ В TELEGRAM · новата карта «🟢 ВХОД · КУПИ ЗЛАТО · 4,130.38» · «СЛ 4,117.38 · −130 пипса» (без `d`) ·
         ПЪТ НАЗАД: plan_rezervi/2026-10-06_tp123_karti_plat/netlify/functions/_lib/data.mjs */
      const eT = g.match(/ВХОД\s*·\s*(?:КУПИ|ПРОДАЙ)\s+ЗЛАТО\s*·\s*([\d,]+\.\d+)/);
      const e = eT || g.match(RE_VHOD);
      const entry = e ? chislo(e[1]) : null;
      if (entry === null) continue;
      const s = eT ? g.match(/(?:^|\n)\s*СЛ\s+([\d,]+\.\d+)/) : g.match(/стоп\s+([\d,]+\.\d+)/);
      const celiV = celiOt(g);
      spis.push({
        dir: m[1] === "КУПИ" ? 1 : -1, entry, otv: t, sl: s ? chislo(s[1]) : null,
        celi: celiV, cel: 0, zatv: null, mMax: 0,
        /* 06.10 · ТП 1·2·3 · новата ВЛЕЗ има три цели до +130 (старата до 15.09 — трета на +200, остатък) */
        t123: celiV.length >= 3 && Number.isFinite(celiV[2]) && Math.abs(celiV[2] - entry) / 0.1 <= 130.5,
      });
      /* 29.09 · бот v18.95 · ВЛЕЗ на сделка на половини казва «1 сделка · 2 половини × лот 0.10» */
      if (/2\s+половини/.test(g)) spis[spis.length - 1].pol = true;
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
    /* 29.09 · бот v18.95 · «ПОЛОВИНАТА НА +50» · сделка на ДВЕ ПОЛОВИНИ по 0.10 лота: цел 1 прибира
       първата, цел 2 затваря втората. Сделката е СРЕДНОТО на половините и ботът го пише: от записа `d`
       ("mode":"polovin", pips на затварящата) или от «сделката донесе N пипса» на ВСЯКА затваряща карта
       (и «✅ ЦЕЛ 1 беше прибрана · втората половина на входа»). Коя сделка е на половини: `d`, картата ВЛЕЗ
       («2 половини») или думите на изходите («прибери половината», «половина 1:», «ЦЕЛ 1 беше прибрана»).
       Сделките отпреди включването нямат нищо от това и остават по закона за една позиция. */
    /* 06.10 · ЗАКОНЪТ ТП 1·2·3 · цената на ЦЕЛ-картата (и при гап) е доказателството колко далеч е стигнала сделката */
    if (/^tp\d$/.test(vid) && Number.isFinite(izhod)) v.mMax = Math.max(v.mMax || 0, hodPips(v.entry, izhod, v.dir));
    if (dx && dx.t123) v.t123 = true;
    if (pozicii === "tp123" && v.t123) {
      /* сделка по новия закон: цел 1 и цел 2 НЕ затварят — затварят цел 3, стопът, обратът, времето (или `closes` на бота) */
      const nT = /^tp(\d)$/.exec(vid);
      if (nT) v.cel = Math.max(v.cel, +nT[1]);
      const zatvT = dx && dx.zatvKazano ? dx.closes : !(nT && +nT[1] < 3);
      if (!zatvT) continue;
      /* 06.10 · КАРТИТЕ В TELEGRAM (картата без `d`) · думите на картата по закона: «сделката: ТПn +N пипса» = стигната цел n ·
         «СЛ на входа · 0 пипса» = стопът беше на входа след +40, без цел (не става цел 1) · «🛑 СЛ на входа» = на входа */
      if (!dx) {
        const tpT = g.match(/сделката:\s*ТП([123])\s*\+/);
        if (tpT) v.cel = Math.max(v.cel, +tpT[1]);
        if (v.cel < 1 && /(?:СЛ на входа|стопът беше на входа)\s*·\s*0\s*пипса/.test(g)) v.be40 = true;
      }
      v.zatv = { t, vid, px: izhod, naVhoda: vid === "sl" && ((dx ? dx.be : /^✅/.test(g.trim()) || /СЛ на входа/.test(g)) || v.cel >= 1 || !!v.be40),
        bota: dx && dx.t123 && dx.pips !== null ? { pips: dx.pips, best: dx.best } : null, karta: k };
      continue;
    }
    if ((dx && dx.pol) || /прибери половината|половина\s+1:|ЦЕЛ 1 беше прибрана/.test(g)) v.pol = true;
    if (vid === "tp1") { v.cel = Math.max(v.cel, 1); continue; }
    if (v.pol && pozicii !== "tp123") {
      const vidP = vid === "tp3" ? "tp2" : vid;
      const sbP = dx ? dx.pips : chislo((g.match(/сделката\s+донесе\s*([+−–\-]?[\d.,]+)\s*пипса/i) || [])[1]);
      const hm = dx ? null : g.match(/половина\s+1:\s*([+−–\-]?[\d.,]+)\s*·\s*половина\s+2:\s*([+−–\-]?[\d.,]+)/);
      const halvesP = dx ? dx.halves : (hm && chislo(hm[1]) !== null && chislo(hm[2]) !== null ? [chislo(hm[1]), chislo(hm[2])] : null);
      if (vidP === "tp2") v.cel = 2;
      /* цел 1 е взета и когато картата ѝ е отпреди записа: половините се различават само след цел 1 */
      else if (/ЦЕЛ 1 беше прибрана/.test(g) || (halvesP && halvesP[0] !== halvesP[1])) v.cel = Math.max(v.cel, 1);
      v.zatv = { t, vid: vidP, px: izhod, pol: true, sbor: sbP, halves: halvesP, karta: k,
        naVhoda: vidP === "sl" && ((dx ? dx.be : /^✅/.test(g.trim())) || v.cel >= 1 || !!v.be40) };
      /* числото на сделката не се чете → без число (никога 0, никога числото по другия закон) */
      if (sbP === null) { neprochetena(k, "без число на сделката"); v.nechetim = true; }
      continue;
    }
    /* 06.10 · ЗАКОНЪТ ТП 1·2·3 · картите на половините (29.09 – 06.10) дават само доказателството: «ЦЕЛ 1 беше прибрана»
       и различните половини на затварящата = цел 1 е стигната; числото им (средното) не се взима */
    if (v.pol && pozicii === "tp123") {
      const hmT = dx ? null : g.match(/половина\s+1:\s*([+−–\-]?[\d.,]+)\s*·\s*половина\s+2:\s*([+−–\-]?[\d.,]+)/);
      const hT = dx ? dx.halves : (hmT && chislo(hmT[1]) !== null && chislo(hmT[2]) !== null ? [chislo(hmT[1]), chislo(hmT[2])] : null);
      if (/ЦЕЛ 1 беше прибрана/.test(g) || (hT && hT[0] !== hT[1])) v.cel = Math.max(v.cel, 1);
    }
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
    if (pozicii === "tp123") {
      /* 06.10 · ЗАКОНЪТ ТП 1·2·3 · същите изходи и същото доказателство за целите като досега (карта ЦЕЛ 1 · v.cel,
         ✅ «стопът беше на входа» · z.naVhoda, карта «стопът на входа» при +40 · be40) + нивата на целите и цената на
         ЦЕЛ-картите → най-високата стигната цел. Картата на бота по новия закон носи числото сама (z.bota). */
      const be40T = !!v.be40 && v.cel < 1;
      const vidT = z.vid === "tp3" && !v.t123 ? "tp2" : z.vid;
      const nvT = vidT === "tp3" ? 3 : vidT === "tp2" ? Math.max(2, v.cel) : vidT === "sl" ? (z.naVhoda && !be40T ? Math.max(1, v.cel) : v.cel) : v.cel;
      const hodT = Number.isFinite(z.px) ? hodPips(v.entry, z.px, v.dir) : null;
      let mT = v.mMax || 0;
      v.celi.forEach((c, i) => { if (i < nvT && Number.isFinite(c)) mT = Math.max(mT, Math.round(Math.abs(c - v.entry) / 0.1)); });
      if (!v.celi.length && nvT) mT = Math.max(mT, nvT >= 3 ? 130 : nvT >= 2 ? polCel2(v.dir) : POL_CEL1);
      if (/^tp\d$/.test(vidT) && hodT !== null) mT = Math.max(mT, hodT);
      const ZT = z.bota ? { best: Math.max(0, Math.min(3, Math.round(z.bota.best || 0))), pips: z.bota.pips, vid: null }
        : tp123Zakon({ m: mT, kind: vidT, naVh: be40T || (vidT === "sl" && z.naVhoda && be40T), hod: hodT });
      if (ZT.vid === null) ZT.vid = ZT.best ? "cel" + ZT.best : vidT === "sl" ? (ZT.pips < 0 ? "stop" : "vhod") : "drug";
      /* Н-07 · обрат / по време без цена на изхода → числото не се знае → не влиза, картата ѝ — в neprochetni */
      if (ZT.pips === null) { neprochetena(z.karta || {}, "без цена на изхода"); continue; }
      const hitT = ZT.best >= 1 ? Object.assign({ tp1: true }, ZT.best >= 2 || nvT >= 2 ? { tp2: true } : {}, ZT.best >= 3 || nvT >= 3 ? { tp3: true } : {})
        : be40T || (vidT === "sl" && ZT.pips === 0) ? { be: true } : {};
      out.push({
        id: (v.dir === 1 ? "long" : "short") + "|" + v.entry.toFixed(2) + "|" + isoUtc(v.otv).slice(0, 16),
        direction: v.dir === 1 ? "long" : "short", entry: v.entry, opened: v.bezVhod ? null : isoUtc(v.otv), slot: "main",
        levels: Object.assign({ tp1: v.celi[0] !== undefined ? v.celi[0] : null, tp2: v.celi[1] !== undefined ? v.celi[1] : null },
          v.t123 && v.celi[2] !== undefined ? { tp3: v.celi[2] } : {}, { sl: v.sl }),
        closed: isoUtc(z.t), hit: hitT, exit_kind: vidT, exit_px: Number.isFinite(z.px) ? z.px : null,
        parts: [ZT.pips], sum_pips: ZT.pips, best: ZT.best, vid: ZT.vid, izvor_zapis: "karti",
        zakon: v.otv < NOV_ZAKON ? "star" : "nov", mode: "tp123",
      });
      continue;
    }
    if (z.pol) {
      /* 29.09 · бот v18.95 · сделка на половини → числото е на СДЕЛКАТА, както ботът го е написал
         (+90/+75 цел 2 · +25 цел 1, после входът · 0 · −130 · обрат/време — средното). Не се преизчислява. */
      const be40p = !!v.be40 && v.cel < 1;
      out.push({
        id: (v.dir === 1 ? "long" : "short") + "|" + v.entry.toFixed(2) + "|" + isoUtc(v.otv).slice(0, 16),
        direction: v.dir === 1 ? "long" : "short", entry: v.entry, opened: v.bezVhod ? null : isoUtc(v.otv), slot: "main",
        levels: { tp1: v.celi[0] !== undefined ? v.celi[0] : null, tp2: v.celi[1] !== undefined ? v.celi[1] : null, sl: v.sl },
        closed: isoUtc(z.t),
        hit: z.vid === "tp2" ? { tp1: true, tp2: true } : v.cel >= 1 ? { tp1: true } : (be40p || (z.vid === "sl" && z.naVhoda)) ? { be: true } : {},
        exit_kind: z.vid, exit_px: Number.isFinite(z.px) ? z.px : null,
        parts: z.halves ? z.halves.slice() : [z.sbor], sum_pips: z.sbor, izvor_zapis: "karti",
        zakon: v.otv < NOV_ZAKON ? "star" : "nov", mode: "polovin",
      });
      continue;
    }
    /* Н-07 · обрат / по време без цена на изхода → числото не се знае. Дотук ставаше 0 (тихо
       сгрешено число); сега сделката не влиза в списъка, а картата ѝ — в neprochetni. */
    if (z.vid !== "tp2" && z.vid !== "sl" && !Number.isFinite(z.px)) { neprochetena(z.karta || {}, "без цена на изхода"); continue; }
    /* стопът е на входа при +40, а цел 1 НЕ е взета (бот v18.85) → hit.be вместо hit.tp1:
       числото е същото (0), но платформата не бива да пише «цел 1», щом цел 1 не е падала */
    const be40 = !!v.be40 && v.cel < 1;
    if (naPol) {
      /* 29.09 · ЗАКОНЪТ НА ПОЛОВИНИТЕ (polovinZakon) · същите изходи и същото доказателство за цел 1 като досега:
         карта ЦЕЛ 1 (v.cel), ✅ «стопът беше на входа» (z.naVhoda), карта «стопът на входа» при +40 (be40) */
      const nvP = z.vid === "tp2" ? 2 : z.vid === "sl" ? (z.naVhoda && !be40 ? Math.max(1, v.cel) : v.cel) : v.cel;
      const P = polovinZakon(nvP, z.vid, v.dir, be40, Number.isFinite(z.px) ? hodPips(v.entry, z.px, v.dir) : null);
      const hitP = z.vid === "tp2" ? { tp1: true, tp2: true } : z.vid === "sl"
        ? (z.naVhoda ? (be40 ? { be: true } : { tp1: true }) : {}) : v.cel >= 1 ? { tp1: true } : be40 ? { be: true } : {};
      out.push({
        id: (v.dir === 1 ? "long" : "short") + "|" + v.entry.toFixed(2) + "|" + isoUtc(v.otv).slice(0, 16),
        direction: v.dir === 1 ? "long" : "short", entry: v.entry, opened: v.bezVhod ? null : isoUtc(v.otv), slot: "main",
        levels: { tp1: v.celi[0] !== undefined ? v.celi[0] : null, tp2: v.celi[1] !== undefined ? v.celi[1] : null, sl: v.sl },
        closed: isoUtc(z.t), hit: hitP, exit_kind: z.vid, exit_px: Number.isFinite(z.px) ? z.px : null,
        parts: P.halves, sum_pips: P.sum, izvor_zapis: "karti", zakon: v.otv < NOV_ZAKON ? "star" : "nov", mode: "polovin",
      });
      continue;
    }
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
      const es = gs.match(/ВХОД\s*·\s*(?:КУПИ|ПРОДАЙ)\s+ЗЛАТО\s*·\s*([\d,]+\.\d+)/) || gs.match(RE_VHOD);   // 06.10 · и картата ВХОД
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
    /* 06.10 · КАРТИТЕ В TELEGRAM (без `d`) · числото на сделката е на първия ред: «🏆 ТП3 · +130 пипса» · «🛑 СЛ · −130 пипса» ·
       «🛑 СЛ на входа · 0 пипса» · «🛑 СЛ на входа · сделката: ТП2 +100 пипса» · «🛑 СЛ · обратен сигнал · −23 пипса» */
    const red1 = g.split("\n")[0];
    const tpS = !dx && !so && !kr && !nula && /^[^А-ЯA-Z]*(?:ТП[123]|СЛ)(?=\s)/.test(red1)
      ? red1.match(/сделката:\s*ТП[123]\s*([+−–\-]?[\d.,]+)\s*пипса/) || red1.match(/·\s*([+−–\-]?\d[\d.,]*)\s*пипса/) : null;
    const sbor = dx ? dx.pips : so ? chislo(so[1]) : kr ? chislo(kr[2]) * (/ЗАГУБА/i.test(kr[1]) && chislo(kr[2]) > 0 ? -1 : 1) : nula ? 0 : tpS ? chislo(tpS[1]) : null;
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
