---
name: thesis-review
description: Review the master's thesis in Masters-thesis/ the way its outside reviewers did. Use before sending a new build to the mentor, after any round of edits, and before submission. Runs the checks that can be automated and lists the ones that need reading.
---

# Reviewing the thesis

Three outside reviews of this thesis found, between them, one wrong reference,
five numbers that never reached the page, a contradiction spanning five
chapters, and a document that read as more certain than its evidence. None of
those were found by reading harder. They were found by asking the same
questions in the same order every time.

This skill is that order.

## Run the checks first

```
python .claude/skills/thesis-review/check_thesis.py
python Masters-thesis/tools/check_tex.py
python -m pytest Masters-thesis/tools/test_docx.py -q
python .claude/skills/human-prose/check_prose.py Masters-thesis/Poglavlja/*.tex
python .claude/skills/human-prose/check_croatian.py Masters-thesis/Poglavlja/*.tex
python .claude/skills/human-prose/check_style.py
```

Build before checking. `check_thesis.py` reads the built `.docx` for two of its
sections, and a stale build reports a fixed defect as still present.

## What the automated checks cover, and the defect behind each

| Check | Found by a reviewer as |
|---|---|
| every bib entry cited, every citation has an entry | a reference that supported a different claim |
| a year in brackets with no `\cite` | "Charness i suradnici (1996)" with no entry |
| macro names appearing as words in the built document | "Kappa" and "Korekcija×" printed where numbers belong |
| measured numbers written as literals instead of macros | drift between a figure in prose and the one in `brojke.tex` |
| claim-strength markers | "dokaz" where two estimates merely agreed |
| claims missing their qualifier in the same paragraph | Stockfish called deterministic in ch. 2 and measured non-deterministic in ch. 7 |
| vocabulary the reviews objected to | 84 players called a "populacija" |
| pages without appendices against the 40-page floor | the rulebook |

## What no check can do

Read these yourself, every round.

**Does the citation support *this* sentence?** Existence is not support. A real
paper can be attached to a claim it does not make, which is the single hardest
defect to see from inside the document. The full audit lives in the artifact
listed in `docs/notes/thesis.md`; three rows there still need a full-text read.

**Is the conclusion stronger than the measurement?** The rule the reviews
settled on: be as strict with the positive results as the thesis is with its
own negative one. The thesis is unusually good at catching itself on regression
to the mean and must hold the same line elsewhere.

**Pilot or validation?** One reviewer, one player of twelve planned, the
reviewer being the author. Anything built on that is a pilot, and the word has
to appear where the result does, not only in a limitations list.

**Has the process crowded out the evidence?** The methodology chapter is
interesting and long. A reader who comes away impressed by the process rather
than convinced by the results has read the thesis the reviewers warned about.
Ask of each process paragraph: does this raise confidence in a result, or does
it describe how the work was organised?

**Does the novelty claim survive the prior art?** "Prvo izračunaj, govori
zadnji" is a good decision that Arrakis reached independently. The defensible
contribution is the constrained language-model layer plus the evaluation
framework, not the architecture alone.

## Judgement calls already made, so they are not re-litigated

- **Naming the development model.** Claude Code and the Claude family, without
  a version: only recent session logs survive on disk and they cannot speak for
  the whole project. The system's own local models are pinned in the source and
  are named exactly.
- **ADR-0018** (thesis writing as a mission step) is out of the appendix at the
  author's request. The register count stays honest because the intro says the
  table lists decisions about the system.
- **Length.** 46 pages without appendices. The floor is 40 and the target about
  50, so there is little room to cut and none to cut carelessly. Trim
  repetition, never evidence.

## The failure mode of the checks themselves

An earlier checker in this project flagged `detektor` as a Serbism because it
contains `dete`. It was wrong nine times in ten and was therefore ignored.
**When a check produces a false positive, fix the check in the same pass as the
finding.** Two patterns in `check_thesis.py` carry comments saying exactly
which false positive taught them.
