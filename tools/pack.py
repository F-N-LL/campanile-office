#!/usr/bin/env python3
"""Packs render.sh output into one JSON file per day and language.

    tools/pack.py RAW_DIR OUT_DIR [--ref DO_COMMIT]

Reads RAW_DIR/<English|Latin>/<YYYY-MM-DD>/<Hour>.html and writes
OUT_DIR/<en|la>/<YYYY-MM-DD>.json plus OUT_DIR/index.json. The HTML is reduced
to the reader markup used by Campanile's BundledPrayers: <p>, <br>, <em>, <strong>,
"rubrica" spans for ℣/℟/Ant., and "rubrica sec" paragraphs for headings.
"""

import argparse
import html
import json
import re
from pathlib import Path

LANGS = {"English": "en", "Latin": "la"}
HOURS = {
    "Matutinum": "readings", "Laudes": "lauds", "Prima": "prime", "Tertia": "midmorning",
    "Sexta": "midday", "Nona": "midafternoon", "Vespera": "vespers", "Completorium": "compline",
}
SOURCE = "Divinum Officium · Rubrics 1960"

S = re.S | re.I


def text(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def header(raw):
    """Feast title and, when a saint wins, the day of the season it replaces."""
    m = re.search(r"<P ALIGN=CENTER>(.*?)</P>", raw, S)
    if not m:
        return "", None
    block = m.group(1)
    tempora = re.search(r"Tempora:</SPAN>(.*?)</SPAN>", block, S)
    title = text(re.split(r"<br/?>", block, maxsplit=1, flags=S)[0])
    return title, text(tempora.group(1)) if tempora else None


def inline(cell):
    h = re.sub(r"<DIV ALIGN='right'>.*?</DIV>", "", cell, flags=S)
    h = re.sub(r"<A ID=[^>]*></A>", "", h, flags=S)
    h = re.sub(r"<A [^>]*>(.*?)</A>", r"\1", h, flags=S)
    # Section headings, marked so paragraphs() can lift them out.
    h = re.sub(r"<FONT SIZE='\+1' COLOR=\"red\"><B><I>(.*?)</I></B></FONT>", "<br/>\x01\\1<br/>", h, flags=S)
    # Editorial notes ({from the Psalter…}, [1]) and verse numbers.
    h = re.sub(r"<FONT SIZE='-1' >.*?</FONT>", "", h, flags=S)
    h = re.sub(r"<FONT SIZE='1' COLOR=\"red\">[^<]*</FONT>\s*", "", h, flags=S)
    # Large initials: <G>lory → Glory.
    h = re.sub(r"<FONT SIZE='\+2' COLOR=\"red\"><B><I>(.*?)</I></B></FONT>", r"\1", h, flags=S)
    h = re.sub(r"<span style='color:red; font-size:1\.25em'>✠</span>", '<span class="cross">✠</span>', h, flags=S)
    h = re.sub(r"<FONT COLOR=\"red\"><I>℣\.</I></FONT>", '<span class="rubrica">V.</span>', h, flags=S)
    h = re.sub(r"<FONT COLOR=\"red\"><I>℟\.</I></FONT>", '<span class="rubrica">R.</span>', h, flags=S)
    h = re.sub(r"<FONT COLOR=\"red\">(.*?)</FONT>",
               lambda m: f'<span class="rubrica">{re.sub(r"</?I>", "", m.group(1), flags=S)}</span>', h, flags=S)
    h = re.sub(r"<span class='nigra'>(.*?)</span>", r"\1", h, flags=S)
    h = re.sub(r"</?FONT[^>]*>", "", h, flags=S)
    h = re.sub(r"</?SPAN[^>]*>", "", h, flags=re.S)  # DO's uppercase SPANs; ours are lowercase
    h = re.sub(r"<I>(.*?)</I>", r"<em>\1</em>", h, flags=S)
    h = re.sub(r"<B>(.*?)</B>", r"<strong>\1</strong>", h, flags=S)
    h = h.replace("‡", "").replace("&nbsp;", " ")
    return h


def paragraphs(cell):
    out, cur = [], []

    def flush():
        if cur:
            out.append("<p>" + "<br>".join(cur) + "</p>")
            cur.clear()

    for line in re.split(r"<br\s*/?>", inline(cell), flags=S):
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            flush()
        elif line.startswith("\x01"):
            flush()
            out.append(f'<p class="rubrica sec">{text(line[1:])}</p>')
        elif re.fullmatch(r'<span class="rubrica">[^<]*</span>', line):
            # Psalm and canticle titles, short rubrics.
            flush()
            out.append(f'<p class="rubrica">{text(line)}</p>')
        elif line.startswith('<span class="rubrica">Ant.</span>'):
            flush()
            out.append(f"<p>{line}</p>")
        else:
            cur.append(line)
    flush()
    return "".join(out)


def hour_html(raw):
    cells = re.findall(r"<TD VALIGN='TOP'[^>]*>(.*?)</TD>", raw, S)
    return "".join(paragraphs(c) for c in cells)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--ref", default="")
    args = ap.parse_args()

    index = {"source": SOURCE, "ref": args.ref, "days": {}}
    for folder, code in LANGS.items():
        days = sorted(p for p in (args.raw / folder).glob("????-??-??") if p.is_dir())
        (args.out / code).mkdir(parents=True, exist_ok=True)
        done = []
        for day in days:
            hours, title, tempora = {}, "", None
            for name, key in HOURS.items():
                f = day / f"{name}.html"
                if not f.exists() or f.stat().st_size == 0:
                    continue
                raw = f.read_text(encoding="utf-8")
                if not title:
                    title, tempora = header(raw)
                body = hour_html(raw)
                if body:
                    hours[key] = body
            if len(hours) != len(HOURS):
                print(f"skip {code} {day.name}: {sorted(set(HOURS.values()) - set(hours))} missing")
                continue
            doc = {"date": day.name, "lang": code, "title": title, "tempora": tempora,
                   "source": SOURCE, "ref": args.ref, "hours": hours}
            (args.out / code / f"{day.name}.json").write_text(
                json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            done.append(day.name)
        index["days"][code] = [done[0], done[-1]] if done else []
        print(f"{code}: {len(done)} days")
    (args.out / "index.json").write_text(json.dumps(index, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
