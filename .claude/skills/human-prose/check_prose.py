"""Measure the tells of model-written prose in LaTeX or plain text.

    python .claude/skills/human-prose/check_prose.py <paths...>
    python .claude/skills/human-prose/check_prose.py --baseline   # the author's own

Rates are per 1,000 words, so a long chapter and a short one compare fairly.
The author's measured baseline is printed alongside for reference.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Measured over Primjeri/ -- the author's two earlier reports, 4,039 words.
BASELINE = {'aside': 1.0, 'negation': 0.5, 'fragment': 0.0, 'colon': 1.5}
BASELINE_PATHS = (
    'Primjeri/MR_sah_predikcija/report.tex',
    'Primjeri/TIW_Zavrsni_Dokumentacija_AgataVujic/report.tex',
)

ASIDE = re.compile(r'---|(?<= )-(?= )|—|–')
NEGATION = re.compile(
    r'\bnije\b[^.]{1,60}?\bnego\b|\bne samo\b[^.]{1,60}?\bnego\b'
    r'|,\s*a\s+ne\b|\bnije\b[^.]{1,40}?\bveć\b', re.I)
COLON_DRAMA = re.compile(r'\w:\s+[a-zćčžšđ]')
BOLD_CLAUSE = re.compile(r'\\textbf\{[^}]{45,}\}')
TRIPLE = re.compile(r'\b\w+,\s+\w+\s+i\s+\w+\b')
STRIP = re.compile(
    r'\\begin\{lstlisting\}.*?\\end\{lstlisting\}'
    r'|\\begin\{tabular\}.*?\\end\{tabular\}'
    r'|\\begin\{longtable\}.*?\\end\{longtable\}'
    r'|\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}', re.S)


def prose_of(text: str) -> str:
    """Body prose only: no code, no tables, no diagrams, no comments."""
    text = STRIP.sub(' ', text)
    text = '\n'.join(line for line in text.split('\n')
                     if not line.lstrip().startswith('%'))
    return text


def fragments(text: str) -> list[str]:
    """Sentences short enough to be there for effect rather than content."""
    out = []
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        words = [w for w in re.findall(r"[\wćčžšđĆČŽŠĐ']+", sentence)]
        if 1 <= len(words) <= 4 and sentence.strip().endswith('.'):
            out.append(sentence.strip())
    return out


def measure(path: Path) -> dict:
    raw = path.read_text(encoding='utf-8', errors='replace')
    text = prose_of(raw)
    words = len(re.findall(r"[\wćčžšđĆČŽŠĐ']+", text)) or 1
    per_k = 1000 / words
    return {
        'path': path,
        'words': words,
        'aside': len(ASIDE.findall(text)) * per_k,
        'negation': len(NEGATION.findall(text)) * per_k,
        'fragment': len(fragments(text)) * per_k,
        'colon': len(COLON_DRAMA.findall(text)) * per_k,
        'bold_clause': len(BOLD_CLAUSE.findall(text)) * per_k,
        'triple': len(TRIPLE.findall(text)) * per_k,
        'raw_asides': len(ASIDE.findall(text)),
        'worst': worst_lines(raw),
    }


def worst_lines(raw: str, limit: int = 3) -> list[str]:
    scored = []
    for number, line in enumerate(raw.split('\n'), start=1):
        if line.lstrip().startswith('%'):
            continue
        hits = len(ASIDE.findall(line)) + len(NEGATION.findall(line))
        if hits:
            scored.append((hits, number, line.strip()[:96]))
    scored.sort(reverse=True)
    return [f'  line {n}: {t}' for _, n, t in scored[:limit]]


def report(results: list[dict]) -> None:
    print(f"{'file':34s} {'words':>6s} {'aside':>7s} {'negac':>6s} "
          f"{'frag':>6s} {'kolon':>6s} {'bold':>6s}")
    print('-' * 74)
    for r in results:
        print(f"{r['path'].name[:34]:34s} {r['words']:6d} "
              f"{r['aside']:7.1f} {r['negation']:6.1f} {r['fragment']:6.1f} "
              f"{r['colon']:6.1f} {r['bold_clause']:6.1f}")
    total_words = sum(r['words'] for r in results)
    total_asides = sum(r['raw_asides'] for r in results)
    print('-' * 74)
    print(f"{'UKUPNO':34s} {total_words:6d} "
          f"{total_asides * 1000 / max(total_words, 1):7.1f}")
    print(f"{'autoričin uzorak (Primjeri/)':34s} {'':6s} "
          f"{BASELINE['aside']:7.1f} {BASELINE['negation']:6.1f} "
          f"{BASELINE['fragment']:6.1f} {BASELINE['colon']:6.1f}")
    if total_asides:
        print(f"\njedna umetnuta rečenica na {total_words // total_asides} "
              f"riječi (cilj: preko 600)")
    worst = max(results, key=lambda r: r['aside'], default=None)
    if worst and worst['worst']:
        print(f"\nnajgušće u {worst['path'].name}:")
        print('\n'.join(worst['worst']))


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    if argv[0] == '--baseline':
        paths = [Path(p) for p in BASELINE_PATHS]
    else:
        paths = []
        for arg in argv:
            path = Path(arg)
            paths.extend(sorted(path.glob('*.tex')) if path.is_dir()
                         else [path])
    results = [measure(p) for p in paths if p.exists()]
    if not results:
        print('no readable files')
        return 1
    report(results)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
