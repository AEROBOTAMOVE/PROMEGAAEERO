/* ═══════════════════════════════════════════════════════════════════════
   П196 10 · ПЛАТФОРМАТА ЧЕТЕ НОВИТЕ КАРТИ — СЪС СОБСТВЕНИТЕ СИ ЧЕТЦИ
   24.09 · v18.90 · прегледът на v18.90 намери три тихи счупвания: картата
   ВЛЕЗ изгуби «цели X +50 · Y +130», «🛡 стопът на входа» изгуби «стопа на X»,
   затварящата изгуби «сделката донесе». Всички проби на бота бяха ЗЕЛЕНИ,
   защото четяха картите с ЧЕТЕЦА НА БОТА (`_запис_позиции`) — а клиентът ги
   чете с ЧЕТЦИТЕ НА ПЛАТФОРМАТА. Тази проба пуска точно тях:
     data.mjs  · sdelkiOtKarti · poziciiOtKarti   (сървърът)
     app.js    · vhodOt · ledgerOt · sglobiSdelki · chastiZatvorena  (екранът)
     profil2.js· vhodOt · sglobiSdelki · chastiZatvorena  (профилът)
   Нищо не се преписва на ръка: функциите се ИЗВАЖДАТ дословно от файловете
   по име (виж `izvadi`) и се пускат в node.

   ОТКЪДЕ СА ЧЕТЦИТЕ
     «snimka»         · снимките до този файл (snimka_*.js). Така върви в CI:
                        repo-то на платформата го няма на GitHub runner-а.
     <AERO_КЛИЕНТ>    · ЖИВИТЕ файлове на платформата на този диск. data.mjs
                        се внася като ИСТИНСКИ модул (import), не като извадка.

   РЕЖИМИ
     node proba_karti.mjs cheti  <snimka|AERO_КЛИЕНТ> <baza.jsonl> <pylen.jsonl> <ot_utc>
     node proba_karti.mjs sverka <AERO_КЛИЕНТ>   · снимката = живото ли е (по функции)
     node proba_karti.mjs snimka <AERO_КЛИЕНТ>   · опреснява снимките от живото
   Изходът е ЕДИН ред JSON на stdout. Грешка → {"greshka": …} и код 2:
   пробата, която не може да прочете, НЕ Е зелена.
   ═══════════════════════════════════════════════════════════════════════ */
import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, join } from "node:path";

const TUK = dirname(fileURLToPath(import.meta.url));

/* кои декларации се вадят от всеки файл и кои функции излизат навън */
const IZVORI = {
  data: {
    pat: "netlify/functions/_lib/data.mjs", snimka: "snimka_data.js",
    imena: ["RE_CENI", "RE_VHOD", "golo", "chislo", "isoUtc", "celiOt", "ZAKON_BROENE",
      "ZAKON_POZICII", "hodPips", "ZAPIS_D", "dOt", "sdelkiOtKarti", "RE_OBSHTO", "RE_KRAEN", "poziciiOtKarti"],
    vrashta: ["sdelkiOtKarti", "poziciiOtKarti"],
  },
  app: {
    pat: "app.js", snimka: "snimka_app.js",
    imena: ["PIP", "BR_CELI", "CELI_K", "STOP_P", "CEL2_P", "ednaPoz", "hodP", "num", "utcDate",
      "ENT", "razEnt", "gol", "ZHARGON", "bezZhargon", "ledgerOt", "prichinaLedger", "RE_CEL",
      "RE_CEL_NOV", "vhodOt", "izhodOt", "beOt", "sglobiSdelki", "chastiZatvorena", "imeCeli",
      "prichinaZatv"],
    vrashta: ["vhodOt", "ledgerOt", "sglobiSdelki", "chastiZatvorena", "prichinaZatv"],
  },
  profil2: {
    pat: "profil2.js", snimka: "snimka_profil2.js",
    imena: ["PIP", "BR_CELI", "STOP_P", "CEL2_P", "ednaPoz", "hodP", "num", "ENT", "razEnt", "gol",
      "RE_CEL", "vhodOt", "izhodOt", "beOt", "sglobiSdelki", "chastiZatvorena", "imeCeli",
      "prichinaZatv"],
    vrashta: ["vhodOt", "sglobiSdelki", "chastiZatvorena", "prichinaZatv"],
  },
};

/** Дословната декларация `ime` от изходния текст. Правилата следват
    оформлението на трите файла: декларацията почва на свой ред; едноредова е,
    ако редът свършва на «;» (или «}» за функция), иначе свършва на първия ред
    със СЪЩИЯ отстъп, който почва със «}», «]» или «)». Среща ли се името
    ≠ 1 път — грешка (двусмислената извадка е по-лоша от липсваща). */
function izvadi(src, ime, fajl) {
  const L = String(src).split(/\r?\n/);
  const re = new RegExp("^(\\s*)(?:export\\s+)?(?:(?:async\\s+)?function\\s+" + ime
    + "\\s*\\(|(?:const|let|var)\\s+" + ime + "\\s*=)");
  const nam = [];
  L.forEach((l, i) => { const m = l.match(re); if (m) nam.push([i, m[1]]); });
  if (nam.length !== 1) throw new Error(fajl + ": «" + ime + "» се среща " + nam.length + " пъти (трябва точно 1)");
  const [i, ind] = nam[0];
  const red = L[i];
  const fn = /^\s*(?:export\s+)?(?:async\s+)?function\s/.test(red);
  const edno = fn ? /\}\s*(\/\/.*)?$/.test(red) : /;\s*(\/\/.*|\/\*.*\*\/)?\s*$/.test(red);
  let j = i;
  if (!edno) {
    j = -1;
    for (let k = i + 1; k < L.length; k++) {
      if (L[k].startsWith(ind) && /^[}\])]/.test(L[k].slice(ind.length))) { j = k; break; }
    }
    if (j < 0) throw new Error(fajl + ": краят на «" + ime + "» не е намерен");
  }
  const out = L.slice(i, j + 1);
  out[0] = out[0].replace(/^(\s*)export\s+/, "$1");
  return out.join("\n");
}

const izvadka = (src, iz, fajl) => iz.imena.map((ime) => izvadi(src, ime, fajl)).join("\n");
const bezGlava = (t) => String(t).split(/\r?\n/).filter((l) => !l.startsWith("// СНИМКА")).join("\n").trim();

function sglobi(kod, iz, ime) {
  try {
    return new Function(kod + "\nreturn { " + iz.vrashta.join(", ") + " };")();
  } catch (e) {
    throw new Error(ime + ": извадката не се сглобява (" + e.message + ")");
  }
}

async function chetci(izvor) {
  const out = { otkade: {} };
  for (const [ime, iz] of Object.entries(IZVORI)) {
    if (izvor === "snimka") {
      const kod = bezGlava(readFileSync(join(TUK, iz.snimka), "utf8"));
      out[ime] = sglobi(kod, iz, iz.snimka);
      out.otkade[ime] = "снимка " + iz.snimka;
    } else if (ime === "data") {
      /* сървърът · ИСТИНСКИЯТ модул, не извадка */
      const m = await import(pathToFileURL(join(izvor, iz.pat)).href);
      out[ime] = { sdelkiOtKarti: m.sdelkiOtKarti, poziciiOtKarti: m.poziciiOtKarti };
      out.otkade[ime] = "живо " + iz.pat + " (import)";
    } else {
      const src = readFileSync(join(izvor, iz.pat), "utf8");
      out[ime] = sglobi(izvadka(src, iz, iz.pat), iz, iz.pat);
      out.otkade[ime] = "живо " + iz.pat + " (извадка)";
    }
  }
  return out;
}

const zapisi = (t) => String(t).split(/\r?\n/).filter((l) => l.trim()).map((l) => {
  try { return JSON.parse(l); } catch (e) { return null; }
}).filter((k) => k && typeof k.tag === "string" && typeof k.text === "string");
const kartaOt = (k) => ({ d: new Date(String(k.utc) + (/(Z|[+\-]\d\d:?\d\d)$/i.test(String(k.utc)) ? "" : "Z")), tag: k.tag, text: k.text });
const r2 = (x) => (Number.isFinite(x) ? Math.round(x * 100) / 100 : x);

function vhodoveOt(sglobiSdelki, chastiZatvorena, prichinaZatv, karti, otMs) {
  const r = sglobiSdelki(karti);
  return (r.vhodove || []).filter((v) => +v.d >= otMs).map((v) => ({
    dir: v.dir, entry: r2(v.entry), maxCel: v.maxCel, be40: !!v.be40,
    tp: (v.tp || []).map((x) => r2(x.px)),
    zatv: v.zatv ? v.zatv.vid : null,
    ch: v.zatv ? chastiZatvorena(v).ch : null,
    prichina: v.zatv ? prichinaZatv(v) : null,
  }));
}

async function cheti(izvor, bazaP, pylenP, ot) {
  const C = await chetci(izvor);
  const baza = readFileSync(bazaP, "utf8");
  const pylen = readFileSync(pylenP, "utf8");
  const otMs = Date.parse(ot + "Z");
  const { sdelkiOtKarti, poziciiOtKarti } = C.data;
  const s0 = sdelkiOtKarti(baza);
  const s1 = sdelkiOtKarti(pylen);
  const p0 = poziciiOtKarti(baza);
  const p1 = poziciiOtKarti(pylen);
  const noviS = s1.sdelki.filter((x) => String(x.closed) >= ot);
  const noviZ = zapisi(pylen).filter((k) => String(k.utc) >= ot);
  const karti = zapisi(pylen).map(kartaOt);
  const vhod = (f) => noviZ.filter((k) => k.tag === "signal").map((k) => {
    const v = f(kartaOt(k));
    return v ? { utc: k.utc, dir: v.dir, entry: r2(v.entry), sl: r2(v.sl), tp: v.tp.map((x) => r2(x.px)) }
      : { utc: k.utc, nishto: true };
  });
  const L = C.app.ledgerOt(noviS) || [];
  return {
    otkade: C.otkade,
    baza: { sdelki: s0.sdelki.length, neprochetni_s: s0.neprochetni.length, bezVhod: s0.bezVhod,
      ostatak: s0.ostatak, neprochetni_p: p0.neprochetni, otvoreni_p: p0.otvoreni },
    pylen: { sdelki: s1.sdelki.length, neprochetni_s: s1.neprochetni.length, bezVhod: s1.bezVhod,
      ostatak: s1.ostatak, neprochetni_p: p1.neprochetni, otvoreni_p: p1.otvoreni },
    stari_nepipnati: JSON.stringify(s0.sdelki) === JSON.stringify(s1.sdelki.filter((x) => String(x.closed) < ot)),
    neprochetni_novi: s1.neprochetni.filter((n) => String(n.utc) >= ot),
    sdelki: noviS.map((x) => ({ direction: x.direction, entry: r2(x.entry), tp1: r2(x.levels.tp1),
      tp2: r2(x.levels.tp2), sl: r2(x.levels.sl), hit: x.hit, exit_kind: x.exit_kind, sum: x.sum_pips })),
    pozicii: p1.pozicii.filter((p) => String(p.closed) >= ot).map((p) => ({ slot: p.slot,
      direction: p.direction, entry: r2(p.entry), kraj: p.kraj, pipsove: p.pipsove, daden: p.daden })),
    vhod_app: vhod(C.app.vhodOt),
    vhod_profil2: vhod(C.profil2.vhodOt),
    ledger: L.map((x) => ({ dir: x.dir, entry: r2(x.entry), vid: x.vid, sbor: x.sbor, be40: !!x.be40,
      vzeti: x.vzeti, tp: x.tp.map((t) => r2(t.px)), prichina: x.prichina })),
    app_karti: vhodoveOt(C.app.sglobiSdelki, C.app.chastiZatvorena, C.app.prichinaZatv, karti, otMs),
    profil2_karti: vhodoveOt(C.profil2.sglobiSdelki, C.profil2.chastiZatvorena, C.profil2.prichinaZatv, karti, otMs),
  };
}

function sverka(koren) {
  const out = {};
  for (const [ime, iz] of Object.entries(IZVORI)) {
    const zhivo = izvadka(readFileSync(join(koren, iz.pat), "utf8"), iz, iz.pat).trim();
    let snimka = null;
    try { snimka = bezGlava(readFileSync(join(TUK, iz.snimka), "utf8")); } catch (e) { snimka = null; }
    out[ime] = snimka === zhivo;
  }
  return out;
}

function snimka(koren) {
  const out = {};
  const den = new Date().toISOString().slice(0, 16);
  for (const [ime, iz] of Object.entries(IZVORI)) {
    const src = readFileSync(join(koren, iz.pat), "utf8");
    const kod = izvadka(src, iz, iz.pat).trim();
    sglobi(kod, iz, iz.pat);                          // сглобява ли се, преди да се запише
    const sha = createHash("sha256").update(src).digest("hex").slice(0, 16);
    writeFileSync(join(TUK, iz.snimka),
      "// СНИМКА · " + iz.pat + " на AERO_КЛИЕНТ · " + den + " UTC · sha256 " + sha + "\n"
      + "// СНИМКА · дословни извадки, НЕ СЕ ПИШАТ НА РЪКА: node platforma/proba_karti.mjs snimka <AERO_КЛИЕНТ>\n"
      + kod + "\n", "utf8");
    out[ime] = { sha, redove: kod.split("\n").length };
  }
  return out;
}

const [rezhim, ...arg] = process.argv.slice(2);
try {
  let rez;
  if (rezhim === "cheti" && arg.length === 4) rez = await cheti(arg[0], arg[1], arg[2], arg[3]);
  else if (rezhim === "sverka" && arg.length === 1) rez = sverka(arg[0]);
  else if (rezhim === "snimka" && arg.length === 1) rez = snimka(arg[0]);
  else throw new Error("употреба: cheti <snimka|AERO_КЛИЕНТ> <baza> <pylen> <ot> · sverka <AERO_КЛИЕНТ> · snimka <AERO_КЛИЕНТ>");
  process.stdout.write(JSON.stringify(rez) + "\n");
} catch (e) {
  process.stdout.write(JSON.stringify({ greshka: String(e && e.stack || e) }) + "\n");
  process.exit(2);
}
