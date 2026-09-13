"""Every check from the thesis reviews that a machine can run.

Each one exists because a real reviewer found a real defect this way. The
sections are ordered by how expensive the defect was to miss: a number that
never reached the page outranks a word that reads oddly.

Run:  python .claude/skills/thesis-review/check_thesis.py
"""
from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[3]
THESIS = ROOT / 'Masters-thesis'
SOURCES = sorted((THESIS / 'Poglavlja').glob('*.tex')) + [THESIS / 'report.tex']
DOCX = THESIS / 'Masters-thesis.docx'
BIB = THESIS / 'Src' / 'ref.bib'
NUMBERS = THESIS / 'Src' / 'brojke.tex'

BLOCK = re.compile(
    r'\\begin\{(lstlisting|tikzpicture|axis|equation)\}.*?\\end\{\1\}',
    re.DOTALL)

findings: list[str] = []


def report(title: str, hits: list[str], fatal: bool = True) -> None:
    print(f'\n== {title} ==')
    if not hits:
        print('  u redu')
        return
    for hit in hits[:40]:
        print(f'  {hit}')
    if len(hits) > 40:
        print(f'  ... i još {len(hits) - 40}')
    if fatal:
        findings.extend(hits)


def prose_lines():
    """Lines of running text: no comments, no table rows, no environments."""
    for path in SOURCES:
        text = BLOCK.sub(' ', io.open(path, encoding='utf-8').read())
        for number, line in enumerate(text.split('\n'), start=1):
            stripped = line.strip()
            if (not stripped or stripped.startswith('%')
                    or stripped.startswith('\\begin')
                    or stripped.startswith('\\end')
                    or stripped.startswith(('\\toprule', '\\midrule',
                                            '\\bottomrule'))
                    or stripped.endswith('\\\\')):
                continue
            yield path, number, stripped


def paragraphs():
    for path in SOURCES:
        text = BLOCK.sub(' ', io.open(path, encoding='utf-8').read())
        for chunk in re.split(r'\n\s*\n', text):
            flat = re.sub(r'\s+', ' ', chunk).strip()
            if flat and not flat.startswith('%'):
                yield path, flat


# --- 1. sources: nothing orphaned in either direction ---------------------

def check_sources() -> None:
    bib = io.open(BIB, encoding='utf-8').read()
    entries = set(re.findall(r'@\w+\{([^,]+),', bib))
    cited = set()
    for path in SOURCES:
        for group in re.findall(r'\\cite\{([^}]*)\}',
                                io.open(path, encoding='utf-8').read()):
            cited.update(k.strip() for k in group.split(','))
    hits = [f'zapis bez citata: {key}' for key in sorted(entries - cited)]
    hits += [f'citat bez zapisa: {key}' for key in sorted(cited - entries)]
    report(f'Izvori ({len(entries)} zapisa, {len(cited)} citirano)', hits)

    # A year named in the text with no entry behind it: how Charness (1996)
    # slipped through.
    loose = []
    for path, number, line in prose_lines():
        for match in re.finditer(r'\((1[89]\d\d|20[0-2]\d)\)', line):
            if '\\cite' not in line:
                loose.append(f'{path.name}:{number} godina u zagradi bez '
                             f'citata: {line[:90]}')
    report('Godina navedena bez zapisa', loose)


# --- 2. macros that never reached the page --------------------------------

def check_macros() -> None:
    if not DOCX.exists():
        report('Makroi u dokumentu', ['dokument nije izgrađen'])
        return
    names = set(re.findall(r'\\newcommand\{\\([A-Za-z]+)\}',
                           io.open(NUMBERS, encoding='utf-8').read()))
    names -= {'Pouzdanost', 'Utemeljenost'}  # also ordinary Croatian words
    with zipfile.ZipFile(DOCX) as archive:
        text = archive.read('word/document.xml').decode('utf-8')
    text = re.sub(r'<[^>]+>', ' ', text)
    hits = [f'makro ispisan kao riječ: {name}' for name in sorted(names)
            if re.search(rf'(?<![A-Za-z]){name}(?![A-Za-z])', text)]
    report(f'Makroi u dokumentu ({len(names)} provjereno)', hits)


# --- 3. measured numbers written as literals ------------------------------

LITERAL = re.compile(r'(?<![\\A-Za-z0-9,.])\d+(?:[,.]\d+)?\s*'
                     r'(?:\\,)?\s*(?:\\%|%|bodova|partija|igrača)')
FROM_LITERATURE = ('1600', '2300', '1500', '5,02', '6,85', '1400', '1800',
                   '1880', '1100', '1900', '300')


def check_literals() -> None:
    hits = []
    for path, number, line in prose_lines():
        if any(word in line for word in ('\\cite', '\\label', '\\ref')):
            continue
        for match in LITERAL.finditer(line):
            token = match.group(0).strip()
            if any(token.startswith(known) for known in FROM_LITERATURE):
                continue
            hits.append(f'{path.name}:{number} „{token}” -- {line[:85]}')
    report('Izmjerene brojke izvan makroa', hits, fatal=False)


# --- 4. claims stronger than a measurement --------------------------------

MARKERS = {
    'dokaz': r'\bdokaz(uje|ano|ana|an)\b|\bdokaz da\b',
    'jamstvo': r'\bjamči\b|\bosigurava\b|\bgarantira\b',
    'potvrda': r'\bpotvrđeno\b|\bpotvrđena\b',
    'apsolutno': r'\bsvaki sustav\b|\bu svakom slučaju\b|\bbez iznimke\b',
    'validacija': r'\bvalidiran\w*\b|\bvalidacija sustava\b',
}


def check_claims() -> None:
    hits = []
    for path, number, line in prose_lines():
        for name, pattern in MARKERS.items():
            if re.search(pattern, line):
                hits.append(f'{path.name}:{number} [{name}] {line[:95]}')
    report('Tvrdnje koje treba pročitati', hits, fatal=False)


# --- 5. pairs that must stay together -------------------------------------
# Each was a contradiction a reviewer found: the claim is fine, but only with
# its qualifier in the same paragraph.

PAIRS = [
    (r'ist[ui] poziciju?.{0,60}ist[oj] dubini',
     r'transpozicij|nije potpuna|ograda',
     'determinizam motora bez ograde o transpozicijskoj tablici'),
    (r'\bslaganj\w*\b.{0,60}\d+\\?,?\d*\\?\s*\\?%',
     r'pilot|jedan ocjenjivač|autorica|prag|zaključuje',
     'izmjereno slaganje sa stručnjakom bez napomene da je pregled pilot'),
    (r'izmjeri slabost.{0,60}ponovno izmjeri',
     r'kontroln|bez kontrole',
     'generalizacija o regresiji bez uvjeta o kontrolnoj skupini'),
]


def check_pairs() -> None:
    hits = []
    for path, flat in paragraphs():
        for trigger, required, label in PAIRS:
            if re.search(trigger, flat) and not re.search(required, flat):
                hits.append(f'{path.name}: {label} -- {flat[:100]}')
    report('Tvrdnje bez svoje ograde', hits)


# --- 6. vocabulary the reviews objected to --------------------------------

VOCABULARY = {
    r'\bpopulacij\w*\b': ('populacija', 'izvedeni su iz cijele populacije|'
                          'iz iste populacije|na novu populaciju|'
                          'populaciji u statističkom smislu'),
    r'\breferentna populacija\b': ('stari naziv', None),
}


def check_vocabulary() -> None:
    hits = []
    for path, number, line in prose_lines():
        for pattern, (label, allowed) in VOCABULARY.items():
            if re.search(pattern, line):
                if allowed and re.search(allowed, line):
                    continue
                hits.append(f'{path.name}:{number} [{label}] {line[:90]}')
    report('Rječnik na koji je recenzent prigovorio', hits)


# --- 7. length against the rulebook ---------------------------------------

def check_length() -> None:
    if not DOCX.exists():
        return
    with zipfile.ZipFile(DOCX) as archive:
        text = archive.read('word/document.xml').decode('utf-8')
    field = re.compile(
        r'PAGEREF\s+(\S+)[^<]*</w:instrText>'
        r'(?:(?!fldCharType="end").)*?fldCharType="separate"/></w:r>'
        r'(?:(?!fldCharType="end").)*?<w:t[^>]*>([^<]*)</w:t>', re.DOTALL)
    pages = dict(field.findall(text))
    try:
        body = int(pages['app_1']) - int(pages['ch_1'])
    except (KeyError, ValueError):
        report('Duljina', ['brojevi stranica nisu razriješeni'])
        return
    print('\n== Duljina ==')
    print(f'  tekst bez priloga: {body} stranica '
          f'(pravilnik traži najmanje 40)')
    if body < 40:
        findings.append(f'tekst bez priloga je {body} stranica, ispod 40')


for check in (check_sources, check_macros, check_literals, check_claims,
              check_pairs, check_vocabulary, check_length):
    check()

print()
if findings:
    print(f'{len(findings)} nalaza koje treba riješiti')
    raise SystemExit(1)
print('nema nalaza koji blokiraju predaju')
