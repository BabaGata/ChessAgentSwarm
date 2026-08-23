Expert review pack
==================

Read `what-the-system-looks-for.txt` first, once, before any player. It lists
everything the swarm can detect and — more usefully — what it is blind to. You
are not being tested on your ability to guess its vocabulary, and a reviewer
who does not know what it looks for cannot tell a gap from an oversight.

The reports in b-the-system/ were regenerated on 2026-08-20, and this time
the change is not only that the system improved.

THE REPORTS NOW COVER THE SAME 20 GAMES YOU READ. They used to be built from
about 50. That was a mistake in the protocol, and a measured one: the swarm
changes its own leading finding 9 times in 12 between a 20-game window and
the full corpus, so most of what your agreement or disagreement measured was
the two of us reading different games. It is now apples to apples.

Three code changes are also in these reports. The coverage gate used to
demand data from 20 games while a 20-game corpus yields 18-19 after the
berserked and abandoned ones are dropped - so it was refusing claims for
arithmetic reasons, and it refused 15 of them across the twelve of you. Two
claims it had been silencing are hanging pieces at nearly twice and over
twice the rate of your rating band. Claims that mostly restate a narrower
one are now suppressed across sections. And the peer rates underneath
everything come from the full 71-player reference rather than a throwaway.

Form A answers are unaffected - those are written before the report is
opened, and about the games rather than the report. No Form B/C was filled
in, so nothing you have written has been invalidated.

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
