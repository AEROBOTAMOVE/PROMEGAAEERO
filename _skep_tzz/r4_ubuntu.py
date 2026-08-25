# -*- coding: utf-8 -*-
"""СКЕПТИК Р4: единственото РЕАЛНО частично разцепване на tzdata в Ubuntu —
   пипа ли то точно двата ключа, които ботът ползва?"""
import urllib.request, sys, re
sys.stdout.reconfigure(encoding="utf-8")

def взем(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")

for пакет in ("tzdata", "tzdata-legacy"):
    for изд in ("noble",):     # noble = Ubuntu 24.04 = ubuntu-latest
        url = f"https://packages.ubuntu.com/{изд}/all/{пакет}/filelist"
        try:
            h = взем(url)
        except Exception as e:
            print(f"{пакет}/{изд}: НЕ СЕ ДРЪПНА {type(e).__name__} {e}")
            continue
        редове = re.findall(r"/usr/share/zoneinfo\S*", h)
        ny = [x for x in редове if x.endswith("/America/New_York")]
        sof = [x for x in редове if x.endswith("/Europe/Sofia")]
        print(f"\n=== {пакет} ({изд}) — {len(редове)} файла в /usr/share/zoneinfo ===")
        print("  America/New_York :", ny if ny else "НЯМА ГО В ТОЗИ ПАКЕТ")
        print("  Europe/Sofia     :", sof if sof else "НЯМА ГО В ТОЗИ ПАКЕТ")
        прим = [x for x in редове if "/US/" in x or "EST5EDT" in x or "Calcutta" in x][:5]
        print("  примерни legacy  :", прим if прим else "-")
