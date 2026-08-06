"""Step 1 — games that should never have been diagnosed.

Spec: docs/notes/design.short-history-prioritisation.md § The solution, layer 1

Two classes, both measured on the real corpus and both a single PGN tag away
from being excluded:

  berserked   8.0% of games. In an arena a player may **halve their own clock**
              for an extra point. Their errors in that game are a self-inflicted
              time handicap, and S2's entire subject is time pressure — so these
              games do not just add noise, they bias exactly the signal the swarm
              is most confident about.

  abandoned   2.2%. Nobody made a chess decision worth diagnosing.

The precise call is *whose* berserk matters. Berserk is per-player: the tag says
which side did it. If the **opponent** berserked, the diagnosed player's own
clock is untouched and their own decisions are still theirs, so the game stays.
Excluding it would throw away evidence to fix a problem the player does not have.
"""

from __future__ import annotations

from chesscoach.ingest.corpus import ABANDONED, BERSERKED, build_corpus
from chesscoach.ingest.pgn import GameRecord, parse_pgn_text

PGN_HEADER = """[Event "Rated Rapid game"]
[Site "https://lichess.org/{gid}"]
[GameId "{gid}"]
[White "{white}"]
[Black "{black}"]
[Result "1-0"]
[UTCDate "2026.01.01"]
[WhiteElo "1500"]
[BlackElo "1520"]
[Variant "Standard"]
[TimeControl "600+0"]
[Termination "{termination}"]
{extra}
1. e4 e5 2. Nf3 Nc6 1-0
"""


def a_pgn(gid="g1", white="alice", black="bob", termination="Normal", extra="") -> str:
    return PGN_HEADER.format(
        gid=gid, white=white, black=black, termination=termination, extra=extra
    )


def a_game(game_id="g1", white="alice", black="bob", **kwargs) -> GameRecord:
    defaults = dict(
        result="1-0", moves=("e2e4", "e7e5"), clocks=(600.0, 600.0), time_control="600+0"
    )
    return GameRecord(game_id=game_id, white=white, black=black, **{**defaults, **kwargs})


class TestTheTagsAreRead:
    def test_termination_is_kept(self):
        games = parse_pgn_text(a_pgn(termination="Time forfeit"))

        assert games[0].termination == "Time forfeit"

    def test_a_berserk_is_noticed_on_the_side_that_did_it(self):
        games = parse_pgn_text(a_pgn(extra='[WhiteBerserk "true"]'))

        assert games[0].white_berserk is True
        assert games[0].black_berserk is False

    def test_an_ordinary_game_carries_neither(self):
        games = parse_pgn_text(a_pgn())

        assert (games[0].white_berserk, games[0].black_berserk) == (False, False)


class TestWhoseBerserkCounts:
    def test_the_player_berserking_counts(self):
        game = a_game(white="alice", white_berserk=True)

        assert game.berserked_by("alice") is True

    def test_the_opponent_berserking_does_not(self):
        # The player's own clock is untouched, so their decisions are still
        # theirs. Dropping this would discard evidence to fix someone else's
        # problem.
        game = a_game(white="alice", black="bob", black_berserk=True)

        assert game.berserked_by("alice") is False

    def test_username_case_does_not_matter(self):
        game = a_game(white="Alice", white_berserk=True)

        assert game.berserked_by("alice") is True


class TestTheCorpusExcludes:
    def test_a_game_the_player_berserked_is_left_out(self):
        corpus = build_corpus("alice", [a_game("keep"), a_game("drop", white_berserk=True)])

        assert corpus.game_ids == ("keep",)

    def test_a_game_the_opponent_berserked_is_kept(self):
        corpus = build_corpus("alice", [a_game("keep", black_berserk=True)])

        assert corpus.game_ids == ("keep",)

    def test_an_abandoned_game_is_left_out(self):
        corpus = build_corpus(
            "alice", [a_game("keep"), a_game("drop", termination="Abandoned")]
        )

        assert corpus.game_ids == ("keep",)

    def test_a_time_forfeit_is_kept(self):
        # Losing on the clock is a real outcome and squarely S2's subject.
        corpus = build_corpus("alice", [a_game("keep", termination="Time forfeit")])

        assert corpus.game_ids == ("keep",)

    def test_someone_elses_game_is_still_left_out(self):
        corpus = build_corpus("alice", [a_game("theirs", white="bob", black="carol")])

        assert corpus.game_ids == ()


class TestItSaysWhatItDropped:
    def test_the_reasons_are_counted(self):
        corpus = build_corpus(
            "alice",
            [
                a_game("keep"),
                a_game("d1", white_berserk=True),
                a_game("d2", white_berserk=True),
                a_game("d3", termination="Abandoned"),
            ],
        )

        assert dict(corpus.excluded) == {BERSERKED: 2, ABANDONED: 1}

    def test_nothing_dropped_is_recorded_as_nothing(self):
        assert build_corpus("alice", [a_game("keep")]).excluded == ()

    def test_a_game_failing_both_tests_is_counted_once(self):
        corpus = build_corpus(
            "alice", [a_game("d", white_berserk=True, termination="Abandoned")]
        )

        assert sum(count for _, count in corpus.excluded) == 1

    def test_exclusions_reach_the_stored_profile(self):
        corpus = build_corpus("alice", [a_game("keep"), a_game("d", white_berserk=True)])

        assert corpus.to_ref().excluded == ((BERSERKED, 1),)


class TestTheCorpusIdentity:
    def test_excluding_a_game_changes_the_corpus_id(self):
        # The id must mean "these exact games". If a contaminated game silently
        # kept the old id, two different analyses would share provenance.
        clean = build_corpus("alice", [a_game("keep")])
        with_berserk = build_corpus("alice", [a_game("keep"), a_game("b", white_berserk=True)])

        assert clean.corpus_id == with_berserk.corpus_id

    def test_and_the_game_count_is_the_kept_games(self):
        corpus = build_corpus("alice", [a_game("keep"), a_game("b", white_berserk=True)])

        assert corpus.n_games == 1


class TestTheReportSaysSo:
    """The player's own games are being discarded; they are owed the reason."""

    def profile_with(self, excluded):
        from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef

        return PlayerProfile(
            player=PlayerRef(source="lichess", username="alice", band="1400-1800"),
            corpus=CorpusRef(corpus_id="c1", n_games=20, excluded=excluded),
        )

    def test_berserked_games_are_disclosed(self):
        from chesscoach.explainer import render

        report = render(self.profile_with(((BERSERKED, 3),)))

        assert "3" in report and "berserk" in report.lower()

    def test_abandoned_games_are_disclosed(self):
        from chesscoach.explainer import render

        assert "abandoned" in render(self.profile_with(((ABANDONED, 2),))).lower()

    def test_nothing_excluded_says_nothing(self):
        from chesscoach.explainer import render

        assert "berserk" not in render(self.profile_with(())).lower()


def test_exclusions_survive_a_round_trip():
    from chesscoach.profile.io import from_dict, to_dict
    from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef

    profile = PlayerProfile(
        player=PlayerRef(source="lichess", username="alice"),
        corpus=CorpusRef(corpus_id="c1", n_games=20, excluded=((BERSERKED, 3), (ABANDONED, 1))),
    )

    assert from_dict(to_dict(profile)).corpus.excluded == ((BERSERKED, 3), (ABANDONED, 1))
