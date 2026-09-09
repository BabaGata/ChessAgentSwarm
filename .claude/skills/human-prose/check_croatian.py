"""Find Serbian words and constructions in Croatian text.

    python .claude/skills/human-prose/check_croatian.py <paths...>

A model trained mostly on the larger Serbian and Bosnian web corpora will slip
ekavica, Serbian lexis and the `da` + present construction into Croatian text.

**Every pattern matches whole words.** The first version used stems and was
useless: it flagged `detektor` as `dete`, `rečenica` as `reč`, `vremenski` as
`vreme` and `također` as `takođe`. A checker that is wrong nine times in ten
trains you to ignore it, so the patterns below spell out the inflected forms
instead.

Nothing is rewritten automatically. Some hits are legitimate - a quoted title, a
proper name - and only a reader can tell.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Serbian form -> Croatian form. Written as full alternations, not stems.
EKAVICA = [
    (r'mest(o|a|u|om|ima)', 'mjesto'),
    # Only the nominative: the oblique cases (vremena, vremenu) are identical
    # in Croatian, so matching those flagged correct text.
    (r'vreme\b', 'vrijeme'),
    (r'det(e|eta|etu)\b', 'dijete'),
    (r'reč(|i|ju|ima)\b(?!enic)', 'riječ'),
    (r'sledeć(i|a|e|eg|em|oj)', 'sljedeći'),
    (r'posle\b', 'poslije'),
    (r'gde\b', 'gdje'),
    (r'ovde\b', 'ovdje'),
    (r'uvek\b', 'uvijek'),
    (r'de(o|la)\b', 'dio'),
    (r'uspeh(|a|u|om)\b', 'uspjeh'),
    (r'mer(a|e|i|om|ama)\b(?!ka)', 'mjera'),
    (r'verovatn(o|a|i|e)', 'vjerojatno'),
    (r'primer(|a|u|om|i|ima)\b', 'primjer'),
    (r'obezbed(iti|i|ilo|ila)', 'osigurati'),
    (r'cel(a|i|o|u|om)\b', 'cijeli'),
    (r'promen(a|e|u|om|ama)\b', 'promjena'),
    (r'nedelj(a|e|i|om)\b', 'tjedan'),
]
LEXIS = [
    (r'uslov(|a|i|u|ima)\b', 'uvjet'),
    (r'uticaj(|a|u|em|i)\b', 'utjecaj'),
    (r'saradnj(a|e|i|om)\b', 'suradnja'),
    (r'tačk(a|e|i|om|ama)\b', 'točka'),
    (r'opšt(i|a|e|eg|em|oj)\b', 'opći'),
    (r'hiljad(a|e|u|ama)\b', 'tisuća'),
    (r'porodic(a|e|i|om)\b', 'obitelj'),
    (r'sopstven(i|a|o|og|om)\b', 'vlastiti'),
    (r'zahtev(|a|i|u|ima)\b', 'zahtjev'),
    (r'izveštaj(|a|u|i|ima)\b', 'izvještaj'),
    # Noun forms only. "prevodi" is also the verb prevoditi, which is correct.
    (r'prevod(|a|u|om)\b', 'prijevod'),
    (r'spisak(|a|u)\b', 'popis'),
    (r'vazduh(|a|u)\b', 'zrak'),
    (r'bezbednost(|i|u)\b', 'sigurnost'),
    (r'učešć(e|a|u)\b', 'sudjelovanje'),
    (r'prisustv(o|a|u)\b', 'prisutnost'),
    (r'odsustv(o|a|u)\b', 'odsutnost'),
    (r'takođe\b', 'također'),
    (r'kompjuter(|a|u|i|ima)\b', 'računalo'),
]
MORPHOLOGY = [
    (r'organizov(ati|an|ana|ano)', 'organizirati'),
    (r'definis(ati|an|ana|ano|ali)', 'definirati'),
    (r'analizov(ati|an|ana|ano)', 'analizirati'),
    (r'informis(ati|an|ana|ano)', 'informirati'),
    (r'klasifikov(ati|an|ana|ano)', 'klasificirati'),
    (r'generis(ati|an|ana|ano)', 'generirati'),
    (r'realizov(ati|an|ana|ano)', 'realizirati'),
    (r'identifikov(ati|an|ana|ano)', 'identificirati'),
    (r'kombinov(ati|an|ana|ano)', 'kombinirati'),
]
PRONOUNS = [(r'\bko\b', 'tko'), (r'\bšta\b', 'što')]

DA_PRESENT = re.compile(
    r'\b(treba|trebaju|mora|moraju|može|mogu|želi|nastoji|pokušava)\s+da\s+'
    r'\w+', re.I)
CONSTRUCTIONS = [(r'\bu vezi sa\b', 'u vezi s'),
                 (r'\bpo pitanju\b', 'što se tiče')]

SKIP = re.compile(
    r'\\begin\{lstlisting\}.*?\\end\{lstlisting\}'
    r'|\\begin\{verbatim\}.*?\\end\{verbatim\}'
    r'|\\texttt\{[^}]*\}|\\cite\{[^}]*\}|\\ref\{[^}]*\}|\\label\{[^}]*\}',
    re.S)

GROUPS = (('ekavica', EKAVICA), ('srpska riječ', LEXIS),
          ('nastavak', MORPHOLOGY), ('zamjenica', PRONOUNS),
          ('konstrukcija', CONSTRUCTIONS))


def scan(path: Path) -> list[tuple[int, str, str, str]]:
    raw = path.read_text(encoding='utf-8', errors='replace')
    hits: list[tuple[int, str, str, str]] = []
    for number, line in enumerate(raw.split('\n'), start=1):
        if line.lstrip().startswith('%'):
            continue
        clean = SKIP.sub(' ', line)
        for kind, table in GROUPS:
            for pattern, good in table:
                for m in re.finditer(r'\b' + pattern, clean, re.I):
                    hits.append((number, kind, m.group(0), good))
        for m in DA_PRESENT.finditer(clean):
            hits.append((number, 'da + prezent', m.group(0),
                         'infinitiv ili "da bi"'))
    return hits


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    paths: list[Path] = []
    for arg in argv:
        path = Path(arg)
        paths.extend(sorted(path.glob('*.tex')) if path.is_dir() else [path])

    total = 0
    for path in paths:
        if not path.exists():
            continue
        hits = scan(path)
        if not hits:
            continue
        total += len(hits)
        print(f'\n{path.name}')
        for number, kind, found, good in hits:
            print(f'  r.{number:4d}  [{kind}] "{found}" -> {good}')
    print(f'\nukupno: {total} nalaza u {len(paths)} datoteka')
    if total == 0:
        print('nema pronađenih srbizama')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
