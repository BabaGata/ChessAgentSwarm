"""Count the patterns the reviewer named, per chapter, and in the author's own
earlier reports for comparison."""
import io
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = pathlib.Path('C:/Users/vujic/Documents/MachineLearning/ChessAgentSwarm')
THESIS = sorted((ROOT / 'Masters-thesis/Poglavlja').glob('*.tex')) + [
    ROOT / 'Masters-thesis/report.tex']
SAMPLES = [ROOT / 'Primjeri/MR_sah_predikcija/report.tex',
           ROOT / 'Primjeri/TIW_Zavrsni_Dokumentacija_AgataVujic/report.tex']

TELLS = {
    'iz toga slijedi': re.compile(r'[Ii]z toga slijedi'),
    'nije X nego Y': re.compile(r'\b(nije|nisu|ne)\b[^.,;]{2,60},? (?:nego|već)\b'),
    'a ne Y': re.compile(r',\s*a ne\b'),
    'podebljani uvod': re.compile(r'(?:^|\n)\\textbf\{[^{}]{6,}?\}'),
    'dvotočje u rečenici': re.compile(r'[a-zčćžšđ]:\s'),
    'kurziv naglasak': re.compile(r'\\emph\{'),
}

AUTHOR = {
    'iz tog razloga': re.compile(r'[Ii]z tog razloga'),
    's obzirom da': re.compile(r'[Ss] obzirom da'),
    'kako bi': re.compile(r'\bKako bi|\bkako bi\b'),
    'dakle': re.compile(r'\bDakle\b|\bdakle\b'),
}


def strip(text: str) -> str:
    text = re.sub(r'\\begin\{(lstlisting|minted|tabular|longtable)\}.*?'
                  r'\\end\{\1\}', ' ', text, flags=re.DOTALL)
    text = re.sub(r'%.*', '', text)
    return text


def words(text: str) -> int:
    return len(re.findall(r'\b[A-Za-zčćžšđČĆŽŠĐ]{2,}\b', text))


def report(paths, title):
    print(f'\n== {title} ==')
    header = f'{"datoteka":28}{"riječi":>7}'
    for name in list(TELLS) + list(AUTHOR):
        header += f'{name[:13]:>15}'
    print(header)
    totals = {name: 0 for name in list(TELLS) + list(AUTHOR)}
    total_words = 0
    for path in paths:
        text = strip(io.open(path, encoding='utf-8').read())
        count = words(text)
        total_words += count
        row = f'{path.name[:27]:28}{count:>7}'
        for name, pattern in {**TELLS, **AUTHOR}.items():
            hits = len(pattern.findall(text))
            totals[name] += hits
            row += f'{hits * 1000 / max(count, 1):>15.1f}'
        print(row)
    row = f'{"NA 1000 RIJEČI":28}{total_words:>7}'
    for name in list(TELLS) + list(AUTHOR):
        row += f'{totals[name] * 1000 / max(total_words, 1):>15.1f}'
    print(row)


report(THESIS, 'diplomski rad')
report(SAMPLES, 'autoričini raniji radovi')
