---
id: cas-exp-e48
title: 'E48 — The agent can always find a link and never the right kind of link'
desc: 'Validation works and earns its place: 90 curated links checked, one dead. Acquisition does not: the agent found a Wikimedia reference for 24 of 24 openings it could ask about, and a reference is the genre already refused for teaching.'
updated: 1788393600000
created: 1788393600000
---

# E48 — Can an agent reproduce resources a person curated by hand?

**Answers:** the author's *"the agent will regenerate all resources for openings that have already
been prepared and you will compare the results"* · **Code:** `chesscoach/opening_agent.py`,
`experiments/e48-opening-agent/` · **Date:** 2026-08-24 ·
**Status:** done — **three stages of four work; the fourth is the whole difficulty**

## The shape the feasibility probe forced

    detect     which openings does this player lean on with no guide?   automated
    acquire    find candidate URLs                                      NOT automatable
    validate   is it alive, and what is it about?                       automated
    record     write it in, unreviewed                                  automated

**There is no free, reliable search API callable from a script.** DuckDuckGo's HTML and lite
endpoints return nothing parseable, its instant-answer API carries no web results, searx.be and
Mojeek return only their own chrome, and everything with a real API wants a key. So the searcher is
injected, and two are supplied: `WikimediaSearcher`, which always works and returns the wrong genre,
and `WorklistSearcher`, which finds nothing and records the exact query that would.

**A recorded gap beats a guessed URL** — the gap gets filled, the guess gets trusted.

## Part 1 — validation works, and immediately earned its place

All 90 curated links, fetched:

| | |
|---|--:|
| reachable | **86 (96 %)** |
| refusing a bot (403) | 3 (3 %) |
| **dead** | **1 (1 %)** |
| own description extracted | 84 (93 %) |

**Owen Defense → HTTP 410 Gone.** That link was in the library and would have been printed to a
player. Link rot was named as this approach's weakness when it was proposed; it took one run to
find an instance, which is the argument for validating rather than trusting.

**403 is counted separately from dead on purpose.** A site refusing a bot is saying "not to you",
not "not there"; folding the two together would delete three good links for the wrong reason.

**The page's own description is usually better than the hand-written title**, and not always:

> hand: *Benoni Defense guide: strategy, traps and variations*
> page: *"Learn the Benoni Defense: Modern, Old and Czech variations, key plans, tactical traps and
> grandmaster games, with playable boards for both sides."*

against one that opens with the etymology of "Ben-Oni". So it is a better **default**, not a
replacement for judgement — and it is taken from the page's own `meta description`, never from body
text, because extracting prose is how a link turns back into a copy.

## Part 2 — acquisition finds something every time, and never the right thing

| | |
|---|--:|
| families the agent found a resource for | **24 / 24 asked** |
| families it could not ask about | 7 (rate limited) |

Every single one is Wikipedia or Wikibooks. **The agent has a 100 % hit rate at finding a reference
and a 0 % hit rate at finding instruction** — and instruction is what the author asked for, having
already read the Wikibooks prose and refused it as too advanced.

That is the measurement the comparison exists to produce: **autonomy costs the entire distinction
between a reference and a guide.** A curated Chessentials or Exeter Chess Club page and an
auto-found Wikipedia article are both links, and only one of them teaches a 1500 anything.

## The defect this run exposed, which is the third of its kind

The first run reported the agent finding resources for **10 of 31**. Every "nothing" was an
**HTTP 429** that `_fetch_json` swallowed into an empty dict — indistinguishable from a genuine
absence. The agent would have recorded "this opening has no resource" for the French Defence.

`SearchUnavailable` is now raised instead, with backoff, and the experiment prints *"could not ask"*
separately from *"found nothing"*. Two tests pin it.

**This is the third time in one session an error has been mistaken for an empty result** — the
`extracts` one-per-request cap, `exintro` on pages with no lead section, and now this. → **L-046**

## Consequence

- ~~**Ship the validator.**~~ **Shipped 2026-08-24.** `Guide` carries `alive`, `checked_on` and
  `summary`; `GuideLibrary.validated()` stamps them and `for_opening` hides anything confirmed dead.
  Run over the real library: **89 reachable, 1 dead, 84 with a page description**, and the Owen
  Defense link is now hidden from players while staying visible to the author as a `dead` entry to
  replace.

  **Validation is a maintenance pass and never a read.** Putting the fetch in `for_opening` would be
  an HTTP call in the report's inner loop — slow, flaky and against C1 — so liveness is stamped into
  the local file and reads filter on the stamp.

  **`alive=None` is not `alive=False`.** Never-checked links stay visible: the author approved one by
  opening it, so absence of a check is not evidence of death. Adding the field would otherwise have
  silently emptied the library, which is L-046's shape again — this time caught in a test before it
  could happen.
- **Use the page description as the default summary**, with the hand-written title kept where it is
  better.
- **Do not ship the Wikimedia searcher as a source of guides.** Its correct role is narrow: a new
  player whose opening has no curated guide gets a labelled reference *and* a worklist entry, so the
  gap is visible rather than papered over.
- **The worklist is the real acquisition path.** The agent says exactly what to search; a person or
  an assistant with a search tool does the searching. That is what actually produced the 90 links.

## Honest limitations

- **Rate limiting is still hitting at 2 s spacing** and 7 of 31 could not be asked. The measured
  24/24 is a hit *rate among askable families*, not a survey of all 31.
- **"Found something" is not "found something good."** Part 2 counts links, and the whole point is
  that the count is the wrong measure — which the note says rather than the number.
- **Detection is untested against a genuinely new player.** The thresholds (≥ 2 games, ≥ 20 % of the
  repertoire) are reasoned, not fitted, and no player outside the review twelve has been run through.
- **Nothing here was reviewed by the author**, so no link the agent produced is usable yet by
  construction.
