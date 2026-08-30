"""Drafting a knowledge-base entry, and the things the swarm may not do.

Design: docs/notes/design.knowledge-base.md (Option C)

The guarantees under test are what make Option C safe under R-03:

- the **definition is a retrieved sentence chosen by index**, never model prose;
- `why` and `practice` are **grounded** against the kept notes or dropped;
- `not_this` is **never written** by the swarm;
- nothing drafted is ever `reviewed`.
"""

from __future__ import annotations

import json

import pytest

from chesscoach.knowledge_swarm import (
    KnowledgeCompiler,
    KnowledgeScout,
    KnowledgeSwarm,
    topic_for,
)
from chesscoach.opening_agent import SearchUnavailable
from chesscoach.knowledge import Source

# Two real-looking sentences from a page, and one that defines the thing.
NOTES = (
    "A fork is a move that attacks two or more enemy pieces at the same time.",
    "The knight is the most common forking piece because of its unusual move.",
    "Because the opponent can only save one piece, a fork usually wins material.",
)


class FakeTransport:
    """Returns whatever the model is supposed to have said."""

    def __init__(self, payload) -> None:
        self.payload = payload
        self.prompts: list[str] = []

    def __call__(self, url, body, timeout=None):  # pragma: no cover - shape only
        self.prompts.append(body.get("prompt", ""))
        return {"response": self.payload}


def compiler(payload: dict) -> KnowledgeCompiler:
    return KnowledgeCompiler(transport=FakeTransport(json.dumps(payload)))


def sources() -> tuple[Source, ...]:
    return (Source(url="https://en.wikibooks.org/wiki/Chess", publisher="Wikibooks"),)


class TestTheDefinitionIsNotWritten:
    def test_the_definition_is_a_retrieved_sentence_chosen_by_index(self):
        entry = compiler({"definition": 0, "why": "", "practice": []}).compile(
            "fork", NOTES, sources()
        )
        assert entry.definition == NOTES[0]
        assert entry.quote == NOTES[0]

    def test_a_different_index_selects_a_different_sentence(self):
        entry = compiler({"definition": 2, "why": "", "practice": []}).compile(
            "fork", NOTES, sources()
        )
        assert entry.definition == NOTES[2]

    def test_an_index_outside_the_list_is_dropped_rather_than_clamped(self):
        # An impossible index is a hallucination, not a near miss. Clamping it
        # to the nearest sentence would silently pick one nobody chose.
        entry = compiler({"definition": 99, "why": "", "practice": []}).compile(
            "fork", NOTES, sources()
        )
        assert entry.definition == ""

    def test_prose_in_the_definition_field_yields_nothing(self):
        # The one field the detector review is compared against must be the
        # source's own words or empty -- never the model's.
        entry = compiler(
            {"definition": "a fork attacks two pieces", "why": "", "practice": []}
        ).compile("fork", NOTES, sources())
        assert entry.definition == ""


class TestGrounding:
    def test_an_ungrounded_why_is_dropped(self):
        entry = compiler({
            "definition": 0,
            "why": "Forks are the cornerstone of Najdorf theory and endgame zugzwang.",
            "practice": [],
        }).compile("fork", NOTES, sources())
        assert entry.why == ""

    def test_a_grounded_why_is_kept(self):
        entry = compiler({
            "definition": 0,
            "why": "A fork usually wins material because the opponent can save only one piece.",
            "practice": [],
        }).compile("fork", NOTES, sources())
        assert entry.why

    def test_invented_practice_advice_is_dropped(self):
        # capacity.knowledge records that training-method evidence is thin and
        # coaching's value contested, so unsupported practice advice is exactly
        # the unfalsifiable coaching CLAUDE.md forbids.
        entry = compiler({
            "definition": 0, "why": "",
            "practice": ["Solve twenty puzzles every morning on a tactics trainer."],
        }).compile("fork", NOTES, sources())
        assert entry.practice == ()


class TestWhatTheSwarmMayNotDo:
    def test_it_never_writes_what_the_thing_is_not(self):
        # The web's definition of a fork is the vague one, and the vague one is
        # what the broken detector implemented. That field is the author's.
        entry = compiler({"definition": 0, "why": "", "practice": []}).compile(
            "fork", NOTES, sources()
        )
        assert entry.not_this == ()

    def test_nothing_drafted_is_ever_reviewed(self):
        entry = compiler({"definition": 0, "why": "", "practice": []}).compile(
            "fork", NOTES, sources()
        )
        assert entry.reviewed is False

    def test_no_notes_means_no_entry_and_no_model_call(self):
        transport = FakeTransport(json.dumps({"definition": 0}))
        entry = KnowledgeCompiler(transport=transport).compile("fork", (), ())
        assert entry.definition == ""
        assert transport.prompts == []  # the model was never asked


class TestTheScout:
    def test_it_asks_about_every_real_phrase_for_the_claim(self):
        asked = []

        class Searcher:
            name = "fake"

            def search(self, gap):
                asked.append(gap.query)
                return [("t", "https://example.org/a", "Example")]

        found = KnowledgeScout(Searcher()).find("fork")
        # A claim key is this project's jargon; the literature's words differ,
        # so the Scout asks about each real phrase rather than three ways about
        # one. "double attack" is what Capablanca calls a fork.
        assert any("what is" in q for q in asked)
        assert any("double attack" in q for q in asked)
        assert len(asked) == len(KnowledgeScout(Searcher()).queries("fork"))
        assert len(found) == 1  # the same URL every time is one candidate

    def test_every_query_failing_raises_rather_than_reporting_nothing(self):
        # L-046: "we could not ask" must never read as "nothing was found".
        class Broken:
            name = "broken"

            def search(self, gap):
                raise SearchUnavailable("blocked")

        with pytest.raises(SearchUnavailable):
            KnowledgeScout(Broken()).find("fork")


class TestTopics:
    def test_a_camel_case_motif_gets_the_phrase_writers_use(self):
        # Not "hanging pawn in chess", which is the key de-underscored, but the
        # phrase measured to retrieve chess pages.
        assert topic_for("hangingPawn") == "hanging pawns chess"

    def test_an_unlisted_key_still_gets_a_searchable_phrase(self):
        assert topic_for("some_new_claim") == "some new claim in chess"


class TestEndToEnd:
    def test_it_drafts_an_unreviewed_entry_from_a_page(self):
        # Two things the fixture has to satisfy: the Assessor refuses a page
        # under MIN_PAGE_WORDS (120), and the relevance gate refuses one that is
        # not about chess -- which a page of three sentences about forks, with
        # the word "chess" nowhere in it, is not.
        page = "Chess tactics. " + " ".join(NOTES * 12) + " A chess fork wins chess games."

        class Searcher:
            name = "fake"

            def search(self, gap):
                return [("Forks in chess", "https://example.org/chess-forks", "Example")]

        answers = [
            json.dumps({"keep": [0, 1, 2]}),          # assessor
            json.dumps({"definition": 0, "why": "", "practice": []}),  # compiler
        ]

        class Transport:
            def __call__(self, url, body, timeout=None):
                return {"response": answers.pop(0) if answers else "{}"}

        # An empty shelf, so this tests the WEB path. Book coverage has its own
        # tests; mixing them here would leave the web path unexercised the day
        # the shelf happens to answer.
        from chesscoach.books import BookLibrary

        swarm = KnowledgeSwarm(Searcher(), lambda url: page, transport=Transport(),
                               library=BookLibrary({}))
        entry = swarm.draft("fork")
        assert entry.key == "fork"
        assert entry.reviewed is False
        assert entry.sources and entry.sources[0].publisher == "Example"


class TestItCanSayNoneOfThese:
    """Choosing by index guarantees provenance, not relevance.

    The first live run produced a "definition" of castling that read *"There are
    two possible moves that place a pawn in the centre of the board"* -- a real
    sentence from a real page, about something else. Without a way to refuse,
    the model has to return the least-bad sentence, and a plausible wrong answer
    where "nothing found" was the truth is the worst outcome available.
    """

    def test_minus_one_means_no_definition_was_found(self):
        entry = compiler({"definition": -1, "why": "", "practice": []}).compile(
            "fork", NOTES, sources()
        )
        assert entry.definition == ""
        assert entry.complete is False

    def test_an_entry_that_found_no_definition_cannot_be_endorsed(self):
        from chesscoach.knowledge import KnowledgeBase, NotEndorsed

        kb = KnowledgeBase()
        kb.draft(compiler({"definition": -1, "why": "", "practice": []}).compile(
            "fork", NOTES, sources()
        ))
        with pytest.raises(NotEndorsed):
            kb.endorse("fork")

    def test_the_prompt_tells_the_model_that_refusing_is_normal(self):
        transport = FakeTransport(json.dumps({"definition": -1, "why": "", "practice": []}))
        KnowledgeCompiler(transport=transport).compile("fork", NOTES, sources())
        assert "-1" in transport.prompts[0]


class TestThePromptIsBounded:
    def test_only_the_first_notes_are_offered_to_the_judge(self):
        # A first batch died on an HTTP 500 from a long prompt, losing six
        # claims of completed work. A definition, if the pages contain one, is
        # not in the twentieth sentence.
        many = tuple(f"Sentence number {i} about forks." for i in range(40))
        transport = FakeTransport(json.dumps({"definition": 0, "why": "", "practice": []}))
        KnowledgeCompiler(transport=transport, limit=5).compile("fork", many, sources())
        prompt = transport.prompts[0]
        assert "4. Sentence number 4" in prompt
        assert "Sentence number 5" not in prompt

    def test_the_index_still_refers_to_the_capped_list(self):
        many = tuple(f"Sentence number {i} about forks." for i in range(40))
        entry = KnowledgeCompiler(
            transport=FakeTransport(json.dumps(
                {"definition": 3, "why": "", "practice": []})),
            limit=5,
        ).compile("fork", many, sources())
        assert entry.definition == many[3]


class TestTheRelevanceGate:
    """A page that is not about the topic cannot define it.

    Live runs sourced a "definition" of hanging piece from the Wikipedia article
    for **Black Is King**, a Beyonce film, and one of hanging pawn from **TCEC
    Season 18**. Both mention chess words; neither is about the motif. The
    Assessor picks the best sentences WITHIN a page and never asks whether the
    page is about the thing, so the judge was choosing the least-bad sentence
    from pages that were never relevant.
    """

    from chesscoach.knowledge_swarm import is_about, key_terms, topic_for
    from chesscoach.opening_swarm import Candidate

    def page(self, title, url):
        from chesscoach.opening_swarm import Candidate
        return Candidate(title, url, "example.org", "")

    def test_an_unrelated_page_is_refused(self):
        from chesscoach.knowledge_swarm import is_about, topic_for
        assert not is_about(
            topic_for("hangingPiece"),
            self.page("Black Is King", "https://en.wikipedia.org/wiki/Black_Is_King"),
            "A visual album. It was praised. Chess of life. Beyonce.",
        )

    def test_a_page_about_the_topic_is_kept(self):
        from chesscoach.knowledge_swarm import is_about, topic_for
        assert is_about(
            topic_for("hangingPiece"),
            self.page("Hanging Piece", "http://chessprogramming.org/Hanging_Piece"),
            "A hanging piece is one that is undefended and attacked.",
        )

    def test_the_url_alone_is_enough(self):
        # A page whose title is unhelpful but whose URL names the topic.
        from chesscoach.knowledge_swarm import is_about, topic_for
        assert is_about(topic_for("fork"),
                        self.page("Chess Journal", "https://x.org/chess-royal-fork/"), "")

    def test_the_word_chess_alone_does_not_make_a_page_relevant(self):
        # "in chess" is in every query, so matching on it would pass everything.
        from chesscoach.knowledge_swarm import key_terms, topic_for
        assert "chess" not in key_terms(topic_for("fork"))


class TestThePageMustBeAboutChess:
    """Shared vocabulary is not shared subject matter.

    A live run defined *endgame technique* from **Sensei's Library**, the Go
    wiki: "endgame" and "technique" are Go words too. Measured on the fetched
    pages, that page says "chess" zero times while real chess pages say it 35 to
    3,310 times -- and a flat threshold is not enough either, since a
    constructed-language grammar mentioned chess 4 times in 400 KB.
    """

    def page(self, title="T", url="https://example.org/x"):
        from chesscoach.opening_swarm import Candidate
        return Candidate(title, url, "example.org", "")

    def test_a_go_page_sharing_the_words_is_refused(self):
        from chesscoach.knowledge_swarm import is_about, topic_for
        go = "The endgame in Go rewards technique. " * 40
        assert "chess" not in go.lower()
        assert not is_about(topic_for("endgame_error"), self.page(), go)

    def test_a_chess_page_is_kept(self):
        from chesscoach.knowledge_swarm import is_about, topic_for
        body = "Chess endgame technique is about king activity. " * 40
        assert is_about(topic_for("endgame_error"), self.page(), body)

    def test_a_long_page_mentioning_chess_in_passing_is_refused(self):
        # 4 mentions in 400 KB was a real page: a grammar of a constructed
        # language with a section naming the chess pieces.
        from chesscoach.knowledge_swarm import about_chess
        body = "grammar and vocabulary. " * 20000 + "chess " * 4
        assert len(body) > 400_000
        assert not about_chess(self.page(), body)

    def test_a_short_page_needs_only_a_few_mentions(self):
        from chesscoach.knowledge_swarm import about_chess
        assert about_chess(self.page(), "A chess fork. Chess tactics. Chess.")

    def test_a_fragment_naming_chess_does_not_make_the_page_about_chess(self):
        # The real case: a grammar of a constructed language whose address ends
        # "#Chess_Piece_". A fragment names one section, not the page.
        from chesscoach.knowledge_swarm import about_chess
        body = "grammar and vocabulary. " * 20000 + "chess " * 4
        assert not about_chess(
            self.page(title="Mirad Grammar",
                      url="https://en.wikibooks.org/wiki/Mirad_Grammar#Chess_Piece_"),
            body,
        )

    def test_a_chess_domain_settles_it_however_short_the_page(self):
        from chesscoach.knowledge_swarm import about_chess
        assert about_chess(
            self.page(title="Hanging Piece", url="http://chessprogramming.org/Hanging_Piece"),
            "A hanging piece is undefended.",
        )

    def test_a_title_naming_chess_does_not_settle_it(self):
        # The fourth leak in this gate: a search result titled for chess pointed
        # at a libertarian-communism essay, which supplied "They cater for the
        # moment, and the moment is capitalism" as a definition of king-side
        # pressure. A title is written to attract a click.
        from chesscoach.knowledge_swarm import about_chess
        body = "capitalism and the state. " * 4000 + "chess " * 3
        assert not about_chess(
            self.page(title="Chess and the strategy of pressure",
                      url="http://libcom.org/book/export/html/1185"),
            body,
        )


class TestNeitherSourceStarvesTheOther:
    """Books and the web fail in opposite places, so both must be read.

    Prepending books to one shared budget of four meant the web was never
    reached: across fourteen redrafted entries the sources were 34 books and
    ZERO pages, and `fork` lost a real definition to a game annotation.
    """

    def test_the_web_is_still_read_when_the_shelf_answers(self):
        from chesscoach.books import SHELF, BookLibrary

        page = "Chess forks. " + "A fork is a move attacking two enemy pieces. " * 30
        shelf = {SHELF[0].slug: "A fork attacks two pieces at once in chess. " * 60}

        class Searcher:
            name = "fake"

            def search(self, gap):
                return [("Forks in chess", "https://example.org/chess-forks", "Web")]

        answers = [json.dumps({"keep": [0, 1, 2]})] * 8 + [
            json.dumps({"definition": 0, "why": "", "practice": []})
        ]

        class Transport:
            def __call__(self, url, body, timeout=None):
                return {"response": answers.pop(0) if answers else "{}"}

        swarm = KnowledgeSwarm(Searcher(), lambda url: page, transport=Transport(),
                               library=BookLibrary(shelf))
        entry = swarm.draft("fork")
        publishers = {s.publisher for s in entry.sources}
        assert any("Web" in p for p in publishers), publishers

    def test_the_budgets_are_separate_numbers(self):
        from chesscoach.books import BookLibrary

        swarm = KnowledgeSwarm(None, None, library=BookLibrary({}))
        assert swarm.read_books and swarm.read_web


class TestADefinitionOfTheWrongThing:
    """A page about tactics defines several of them.

    Asked for `fork`, the judge returned "a skewer happens when a chess piece
    attacks an opponent's chessman, which hides a less important piece behind
    it" -- a correct definition, verbatim from a relevant page, of a DIFFERENT
    tactic. Nothing upstream of the judge can see that: the page is about chess,
    the sentence is broad, and it defines something.
    """

    def test_a_definition_of_another_tactic_is_refused(self):
        notes = ("A skewer happens when a piece attacks a man with a less "
                 "important piece behind it.",)
        entry = compiler({"definition": 0, "why": "", "practice": []}).compile(
            "fork", notes, sources()
        )
        assert entry.definition == ""

    def test_a_definition_naming_the_claim_is_kept(self):
        notes = ("A fork is a move that attacks two enemy pieces at once.",)
        entry = compiler({"definition": 0, "why": "", "practice": []}).compile(
            "fork", notes, sources()
        )
        assert entry.definition == notes[0]

    def test_it_matches_the_claims_vocabulary_not_its_key(self):
        # `hangingPiece` is named by "en prise" as readily as by "hanging" --
        # the key is this project's jargon and the sentence will not use it.
        notes = ("To put a piece en prise is to play it so that it may be captured.",)
        entry = compiler({"definition": 0, "why": "", "practice": []}).compile(
            "hangingPiece", notes, sources()
        )
        assert entry.definition == notes[0]
