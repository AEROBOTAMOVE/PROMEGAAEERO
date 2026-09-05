# -*- coding: utf-8 -*-
"""pq_lite.py — четец на parquet БЕЗ pyarrow (чист Python + numpy).

ЗАЩО СЪЩЕСТВУВА (казано, не премълчано): на 02.09.2026 Windows App Control
блокира arrow DLL-ите:
    ImportError: DLL load failed while importing lib:
    An Application Control policy has blocked this file.
Проверено в тази сесия: ctypes.CDLL върху arrow_python.dll → WinError 4551.
Без четец на parquet НИТО ЕДНО число не може да се извади (лентата, решетката и
доставените входове са parquet). Затова е написан този минимален четец.

ОБХВАТ: точно това, което pyarrow пише по подразбиране — thrift compact
метаданни, snappy/uncompressed страници, PLAIN и RLE_DICTIONARY, RLE def-нива.
Всичко извън обхвата ГЪРМИ с ясно съобщение, не се гади.

СВЕРКА: pq_sverka.py сравнява прочетеното с числата, извадени независимо
(np.load кеша на лентата) и с твърденията на самия файл (num_rows, статистики).
"""
from __future__ import annotations

import struct
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------- thrift compact
CT_STOP, CT_TRUE, CT_FALSE, CT_BYTE, CT_I16, CT_I32, CT_I64 = 0, 1, 2, 3, 4, 5, 6
CT_DOUBLE, CT_BINARY, CT_LIST, CT_SET, CT_MAP, CT_STRUCT = 7, 8, 9, 10, 11, 12


class TC:
    """Thrift compact protocol reader."""

    def __init__(self, buf, pos=0):
        self.b = buf
        self.p = pos

    def byte(self):
        v = self.b[self.p]
        self.p += 1
        return v

    def varint(self):
        r = 0
        sh = 0
        while True:
            c = self.b[self.p]
            self.p += 1
            r |= (c & 0x7F) << sh
            if not (c & 0x80):
                return r
            sh += 7

    def zigzag(self):
        n = self.varint()
        return (n >> 1) ^ -(n & 1)

    def binary(self):
        n = self.varint()
        v = bytes(self.b[self.p:self.p + n])
        self.p += n
        return v

    def dbl(self):
        v = struct.unpack_from("<d", self.b, self.p)[0]
        self.p += 8
        return v

    def skip(self, t):
        if t in (CT_TRUE, CT_FALSE):
            return
        if t == CT_BYTE:
            self.p += 1
        elif t in (CT_I16, CT_I32, CT_I64):
            self.varint()
        elif t == CT_DOUBLE:
            self.p += 8
        elif t == CT_BINARY:
            self.binary()
        elif t in (CT_LIST, CT_SET):
            h = self.byte()
            sz = h >> 4
            et = h & 0x0F
            if sz == 15:
                sz = self.varint()
            for _ in range(sz):
                self.skip(et)
        elif t == CT_MAP:
            sz = self.varint()
            if sz:
                kv = self.byte()
                for _ in range(sz):
                    self.skip(kv >> 4)
                    self.skip(kv & 0x0F)
        elif t == CT_STRUCT:
            self.struct(lambda fid, ft, s: False)      # False → struct() го пропуска сам
        else:
            raise ValueError("непознат thrift тип %d" % t)

    def struct(self, on_field):
        """on_field(fid, ftype, self) → True ако е ПРОЧЕЛ полето, иначе се пропуска."""
        last = 0
        while True:
            h = self.byte()
            if h == 0:
                return
            ft = h & 0x0F
            delta = h >> 4
            if delta == 0:
                fid = self.zigzag()
            else:
                fid = last + delta
            last = fid
            if not on_field(fid, ft, self):
                self.skip(ft)

    def list_of(self, reader):
        h = self.byte()
        sz = h >> 4
        et = h & 0x0F
        if sz == 15:
            sz = self.varint()
        return [reader(et, self) for _ in range(sz)]


# --------------------------------------------------------------------- snappy
def snappy_decompress(src: memoryview, expect=None) -> bytearray:
    p = 0
    sh = 0
    n = 0
    while True:
        c = src[p]
        p += 1
        n |= (c & 0x7F) << sh
        if not (c & 0x80):
            break
        sh += 7
    out = bytearray(n)
    o = 0
    L = len(src)
    while p < L:
        tag = src[p]
        t = tag & 0x03
        if t == 0:
            ln = tag >> 2
            p += 1
            if ln >= 60:
                k = ln - 59
                ln = int.from_bytes(src[p:p + k], "little")
                p += k
            ln += 1
            out[o:o + ln] = src[p:p + ln]
            p += ln
            o += ln
            continue
        if t == 1:
            ln = 4 + ((tag >> 2) & 0x07)
            off = ((tag >> 5) << 8) | src[p + 1]
            p += 2
        elif t == 2:
            ln = (tag >> 2) + 1
            off = src[p + 1] | (src[p + 2] << 8)
            p += 3
        else:
            ln = (tag >> 2) + 1
            off = int.from_bytes(src[p + 1:p + 5], "little")
            p += 5
        s = o - off
        if off >= ln:
            out[o:o + ln] = out[s:s + ln]
            o += ln
        else:
            for _ in range(ln):
                out[o] = out[s]
                o += 1
                s += 1
    if expect is not None and o != expect:
        raise ValueError("snappy: %d байта, чакани %d" % (o, expect))
    return out


# --------------------------------------------------------------------- метаданни
PT = {0: "BOOLEAN", 1: "INT32", 2: "INT64", 3: "INT96", 4: "FLOAT", 5: "DOUBLE",
      6: "BYTE_ARRAY", 7: "FLBA"}
ENC = {0: "PLAIN", 2: "PLAIN_DICTIONARY", 3: "RLE", 4: "BIT_PACKED",
       5: "DELTA_BINARY_PACKED", 6: "DELTA_LENGTH_BYTE_ARRAY", 7: "DELTA_BYTE_ARRAY",
       8: "RLE_DICTIONARY", 9: "BYTE_STREAM_SPLIT"}
CODEC = {0: "UNCOMPRESSED", 1: "SNAPPY", 2: "GZIP", 3: "LZO", 4: "BROTLI", 5: "LZ4",
         6: "ZSTD", 7: "LZ4_RAW"}


def _schema_elem(_et, t):
    d = {}

    def f(fid, ft, s):
        if fid == 1:
            d["type"] = s.zigzag(); return True
        if fid == 2:
            d["type_length"] = s.zigzag(); return True
        if fid == 3:
            d["rep"] = s.zigzag(); return True
        if fid == 4:
            d["name"] = s.binary().decode("utf-8"); return True
        if fid == 5:
            d["num_children"] = s.zigzag(); return True
        if fid == 6:
            d["conv"] = s.zigzag(); return True
        return False
    t.struct(f)
    return d


def _colmeta(t):
    d = {}

    def f(fid, ft, s):
        if fid == 1:
            d["type"] = s.zigzag(); return True
        if fid == 2:
            d["enc"] = s.list_of(lambda et, ss: ss.zigzag()); return True
        if fid == 3:
            d["path"] = s.list_of(lambda et, ss: ss.binary().decode("utf-8")); return True
        if fid == 4:
            d["codec"] = s.zigzag(); return True
        if fid == 5:
            d["num_values"] = s.zigzag(); return True
        if fid == 6:
            d["uncomp"] = s.zigzag(); return True
        if fid == 7:
            d["comp"] = s.zigzag(); return True
        if fid == 9:
            d["data_off"] = s.zigzag(); return True
        if fid == 11:
            d["dict_off"] = s.zigzag(); return True
        return False
    t.struct(f)
    return d


def _colchunk(_et, t):
    d = {}

    def f(fid, ft, s):
        if fid == 3:
            d["meta"] = _colmeta(s); return True
        return False
    t.struct(f)
    return d


def _rowgroup(_et, t):
    d = {}

    def f(fid, ft, s):
        if fid == 1:
            d["cols"] = s.list_of(_colchunk); return True
        if fid == 3:
            d["num_rows"] = s.zigzag(); return True
        return False
    t.struct(f)
    return d


def metadata(path):
    path = Path(path)
    with open(path, "rb") as f:
        f.seek(-8, 2)
        tail = f.read(8)
        assert tail[4:] == b"PAR1", "не е parquet"
        mlen = struct.unpack("<I", tail[:4])[0]
        f.seek(-(8 + mlen), 2)
        buf = f.read(mlen)
    t = TC(buf)
    M = {}

    def f(fid, ft, s):
        if fid == 2:
            M["schema"] = s.list_of(_schema_elem); return True
        if fid == 3:
            M["num_rows"] = s.zigzag(); return True
        if fid == 4:
            M["rgs"] = s.list_of(_rowgroup); return True
        if fid == 6:
            M["created_by"] = s.binary().decode("utf-8", "replace"); return True
        return False
    t.struct(f)
    M["path"] = str(path)
    return M


# --------------------------------------------------------------------- страници
def _page_header(buf, pos):
    t = TC(buf, pos)
    d = {}

    def f(fid, ft, s):
        if fid == 1:
            d["ptype"] = s.zigzag(); return True
        if fid == 2:
            d["unc"] = s.zigzag(); return True
        if fid == 3:
            d["cmp"] = s.zigzag(); return True
        if fid == 5:
            sub = {}

            def g(i2, t2, s2):
                if i2 == 1:
                    sub["n"] = s2.zigzag(); return True
                if i2 == 2:
                    sub["enc"] = s2.zigzag(); return True
                if i2 == 3:
                    sub["denc"] = s2.zigzag(); return True
                if i2 == 4:
                    sub["renc"] = s2.zigzag(); return True
                return False
            s.struct(g)
            d["dp"] = sub
            return True
        if fid == 7:
            sub = {}

            def g(i2, t2, s2):
                if i2 == 1:
                    sub["n"] = s2.zigzag(); return True
                if i2 == 2:
                    sub["enc"] = s2.zigzag(); return True
                return False
            s.struct(g)
            d["dict"] = sub
            return True
        if fid == 8:
            sub = {}

            def g(i2, t2, s2):
                if i2 == 1:
                    sub["n"] = s2.zigzag(); return True
                if i2 == 2:
                    sub["nulls"] = s2.zigzag(); return True
                if i2 == 3:
                    sub["rows"] = s2.zigzag(); return True
                if i2 == 4:
                    sub["enc"] = s2.zigzag(); return True
                if i2 == 5:
                    sub["dlen"] = s2.zigzag(); return True
                if i2 == 6:
                    sub["rlen"] = s2.zigzag(); return True
                if i2 == 7:
                    sub["comp"] = (t2 == CT_TRUE); return True
                return False
            s.struct(g)
            d["dp2"] = sub
            return True
        return False
    t.struct(f)
    return d, t.p


def _rle_hybrid(buf, width, n):
    """RLE/bit-packing hybrid → np.int64 масив с n стойности."""
    out = np.empty(n, dtype=np.int64)
    o = 0
    p = 0
    nb = (width + 7) // 8
    L = len(buf)
    while o < n and p < L:
        r = 0
        sh = 0
        while True:
            c = buf[p]
            p += 1
            r |= (c & 0x7F) << sh
            if not (c & 0x80):
                break
            sh += 7
        if r & 1:                                     # bit-packed
            groups = r >> 1
            cnt = groups * 8
            nbytes = groups * width
            raw = np.frombuffer(buf, dtype=np.uint8, count=nbytes, offset=p)
            p += nbytes
            if width == 0:
                vals = np.zeros(cnt, dtype=np.int64)
            else:
                bits = np.unpackbits(raw, bitorder="little").reshape(cnt, width)
                vals = bits.astype(np.int64) @ (1 << np.arange(width, dtype=np.int64))
            k = min(cnt, n - o)
            out[o:o + k] = vals[:k]
            o += k
        else:                                         # RLE run
            cnt = r >> 1
            v = int.from_bytes(buf[p:p + nb], "little") if nb else 0
            p += nb
            k = min(cnt, n - o)
            out[o:o + k] = v
            o += k
    if o != n:
        raise ValueError("RLE: %d от %d стойности" % (o, n))
    return out


NPT = {1: np.int32, 2: np.int64, 4: np.float32, 5: np.float64}


def _plain(raw, ptype, n, tlen=0):
    if ptype == 0:                                    # BOOLEAN, bit-packed
        need = (n + 7) // 8
        a = np.frombuffer(raw, dtype=np.uint8, count=need)
        return np.unpackbits(a, bitorder="little")[:n].astype(bool)
    if ptype in NPT:
        return np.frombuffer(raw, dtype=NPT[ptype], count=n).copy()
    if ptype == 6:                                    # BYTE_ARRAY
        out = []
        p = 0
        mv = memoryview(raw)
        for _ in range(n):
            ln = int.from_bytes(mv[p:p + 4], "little")
            p += 4
            out.append(bytes(mv[p:p + ln]))
            p += ln
        return np.array(out, dtype=object)
    if ptype == 7:
        return np.array([bytes(raw[i * tlen:(i + 1) * tlen]) for i in range(n)], dtype=object)
    raise ValueError("PLAIN за тип %s не е реализиран" % PT.get(ptype, ptype))


def read_columns(path, columns=None):
    """Връща dict име → numpy масив (NaN за null при float, None при обект)."""
    M = metadata(path)
    sch = M["schema"]
    leafs = [s for s in sch[1:] if not s.get("num_children")]
    byname = {s["name"]: s for s in leafs}
    if columns is None:
        columns = [s["name"] for s in leafs]
    want = set(columns)
    res = {c: [] for c in columns}
    with open(path, "rb") as fh:
        for rg in M["rgs"]:
            for cc in rg["cols"]:
                cm = cc["meta"]
                nm = cm["path"][-1]
                if nm not in want:
                    continue
                se = byname[nm]
                opt = se.get("rep", 0) == 1
                res[nm].append(_read_chunk(fh, cm, se, opt))
    out = {}
    for c in columns:
        parts = res[c]
        out[c] = np.concatenate(parts) if len(parts) > 1 else parts[0]
    out["__meta__"] = M
    return out


def _read_chunk(fh, cm, se, opt):
    start = cm.get("dict_off") or cm["data_off"]
    if cm.get("dict_off") and cm["dict_off"] < cm["data_off"]:
        start = cm["dict_off"]
    else:
        start = cm["data_off"]
    fh.seek(start)
    buf = fh.read(cm["comp"])
    mv = memoryview(buf)
    ptype = cm["type"]
    codec = cm["codec"]
    if CODEC.get(codec) not in ("SNAPPY", "UNCOMPRESSED"):
        raise ValueError("компресия %s не е реализирана" % CODEC.get(codec, codec))
    n_total = cm["num_values"]
    pos = 0
    dic = None
    chunks = []
    got = 0
    while got < n_total and pos < len(buf):
        ph, hend = _page_header(buf, pos)
        cl = ph["cmp"]
        body = mv[hend:hend + cl]
        pos = hend + cl
        if codec == 1 and not (ph.get("dp2") and ph["dp2"].get("comp") is False):
            body = memoryview(snappy_decompress(body, ph["unc"]))
        if ph["ptype"] == 2:                                       # DICTIONARY
            dic = _plain(body, ptype, ph["dict"]["n"], se.get("type_length", 0))
            continue
        if ph["ptype"] == 0:                                       # DATA PAGE V1
            n = ph["dp"]["n"]
            enc = ph["dp"]["enc"]
            q = 0
            defl = None
            if opt:
                dl = int.from_bytes(body[0:4], "little")
                defl = _rle_hybrid(bytes(body[4:4 + dl]), 1, n)
                q = 4 + dl
            vals_n = n if defl is None else int(defl.sum())
            payload = body[q:]
        elif ph["ptype"] == 3:                                     # DATA PAGE V2
            h = ph["dp2"]
            n = h["n"]
            enc = h["enc"]
            rl = h.get("rlen", 0)
            dl = h.get("dlen", 0)
            q = rl + dl
            defl = _rle_hybrid(bytes(body[rl:rl + dl]), 1, n) if (opt and dl) else None
            vals_n = n - h.get("nulls", 0)
            payload = body[q:]
        else:
            continue
        if ENC.get(enc) in ("RLE_DICTIONARY", "PLAIN_DICTIONARY"):
            w = payload[0]
            idx = _rle_hybrid(bytes(payload[1:]), w, vals_n)
            v = dic[idx]
        elif ENC.get(enc) == "PLAIN":
            v = _plain(bytes(payload), ptype, vals_n, se.get("type_length", 0))
        elif ENC.get(enc) == "RLE" and ptype == 0:
            dl2 = int.from_bytes(payload[0:4], "little")
            v = _rle_hybrid(bytes(payload[4:4 + dl2]), 1, vals_n).astype(bool)
        else:
            raise ValueError("кодиране %s не е реализирано" % ENC.get(enc, enc))
        if defl is not None and vals_n != n:
            if v.dtype.kind == "f":
                full = np.full(n, np.nan, dtype=v.dtype)
            elif v.dtype.kind == "O":
                full = np.full(n, None, dtype=object)
            else:
                full = np.zeros(n, dtype=v.dtype)
            full[defl.astype(bool)] = v
            v = full
        chunks.append(v)
        got += n
    if got != n_total:
        raise ValueError("прочетени %d от %d стойности" % (got, n_total))
    return np.concatenate(chunks) if len(chunks) > 1 else chunks[0]


def описание(path):
    M = metadata(path)
    print("файл       :", path)
    print("създаден от:", M.get("created_by"))
    print("редове     : %s · row groups: %d" % (format(M["num_rows"], ","), len(M["rgs"])))
    cm0 = M["rgs"][0]["cols"]
    print("%-16s %-10s %-9s %s" % ("колона", "тип", "кодек", "кодирания"))
    for cc in cm0:
        m = cc["meta"]
        print("%-16s %-10s %-9s %s" % (m["path"][-1], PT.get(m["type"]),
                                       CODEC.get(m["codec"]),
                                       [ENC.get(e, e) for e in m["enc"]]))


if __name__ == "__main__":
    import sys
    описание(sys.argv[1])
