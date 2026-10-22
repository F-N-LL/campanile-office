# campanile-office

Daily texts of the traditional Roman Office (Rubrics 1960) in English and Latin,
published on GitHub Pages for the Campanile Mac app:

    https://f-n-ll.github.io/campanile-office/v1/<en|la>/<YYYY-MM-DD>.json

`publish.yml` checks out a pinned commit of
[Divinum Officium](https://github.com/DivinumOfficium/divinum-officium) (MIT),
renders eight hours a day with its Perl engine (`tools/render.sh`), reduces the
HTML to the reader markup (`tools/pack.py`) and deploys the result. It runs on
every push to `main` and monthly, covering a week back and about a year ahead.
The engine runs only on CI.

Each file:

```json
{"date": "2026-10-22", "lang": "en", "title": "…", "tempora": null,
 "source": "Divinum Officium · Rubrics 1960", "ref": "<commit>",
 "hours": {"readings": "<p>…", "lauds": "…", "prime": "…", "midmorning": "…",
           "midday": "…", "midafternoon": "…", "vespers": "…", "compline": "…"}}
```

## Texts

All texts are in the public domain: the Breviarium Romanum and the Vulgate; in
English, the Douay-Rheims Bible, the Marquess of Bute's Roman Breviary (1908),
Britt's *Hymns of the Breviary and Missal* (1922) and Stanbrook Abbey's *Day
Hours of the Church* (1921). Spanish is not published: the Divinum Officium
translation includes texts granted to that project by their owners.
