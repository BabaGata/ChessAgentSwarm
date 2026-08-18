Expert review pack
==================

Read `what-the-system-looks-for.txt` first, once, before any player. It lists
everything the swarm can detect and — more usefully — what it is blind to. You
are not being tested on your ability to guess its vocabulary, and a reviewer
who does not know what it looks for cannot tell a gap from an oversight.

The reports in b-the-system/ were regenerated on 2026-08-17 against the
current system. If you filled in a Form B/C before that date, it judged an
older diagnosis: since then the error threshold moved from 10 to 5 win-
probability points (roughly doubling what is detected), a free-pawn detector
arrived, and S7 added three claims about the move you actually played. Form A
answers are unaffected - those are written before the report is opened.

12 players. For each, work in this order:

  1. open  games/<player>.pgn            (or the study link, if provided)
  2. fill  a-your-reading/<player>.txt    <-- before anything else
  3. open  b-the-system/<player>/report.txt
  4. fill  b-the-system/<player>/form.txt

The order matters more than anything else here. Once you have seen the
system's answer you cannot un-see it, and "would you have said this?" is a
different and much more informative question than "do you agree with this?".

There is no need to be kind. A finding you would not have mentioned is the
most useful thing you can report, and the protocol was written down before
you were asked, thresholds included, so a bad result is a result rather than
a disappointment: docs/notes/evaluation.expert-review.md

Roughly 15-20 minutes per player.
