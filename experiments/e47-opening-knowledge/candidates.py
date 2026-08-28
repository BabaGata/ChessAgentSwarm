"""Candidate guide links, one search per opening, none of them invented.

Every URL here appeared in a real search result for that specific opening. None
is constructed by pattern, because a plausible-looking guessed URL is worse than
an obvious gap: the gap gets filled and the guess gets trusted.

**All copyright, and that is fine** — these are links, not copies. What makes
them usable is exactly that the system points rather than quotes.

**All unreviewed.** `GuideLibrary.for_opening` returns nothing from here until the
author marks an entry reviewed, because recommending is endorsing.

Capped at three per opening: the review is one pass, and a fourth link mostly
adds work rather than choice.
"""

from __future__ import annotations

# opening family -> [(title, url, publisher)]
CANDIDATES: dict[str, list[tuple[str, str, str]]] = {
    "French Defense": [
        ("Complete guide for both colours",
         "https://thechessworld.com/articles/openings/french-defense-complete-guide-for-both-colors/",
         "TheChessWorld"),
        ("What every chess player should know about the French",
         "https://chessentials.com/the-french-defence/", "Chessentials"),
        ("Plans, pawn structures and winning ideas",
         "https://thechesscrew.com/blog/french-defense-strategy", "The Chess Crew"),
    ],
    # These players' Queen's Pawn games are mostly the Accelerated London, so the
    # useful search was "London System" rather than the family name. Indian
    # Defense reaches the same structure and shares the links.
    "Queen's Pawn Game": [
        ("London System: the complete guide",
         "https://thechessworld.com/articles/openings/london-system-the-complete-guide/",
         "TheChessWorld"),
        ("The London System: complete guide for club players",
         "https://www.firechess.com/blog/london-system-guide-club-players", "FireChess"),
        ("London System - interactive study",
         "https://listudy.org/en/openings/london-system", "Listudy"),
    ],
    # Scoped to the SUBLINE, not the family. "Indian Defense" is `1. d4 Nf6`,
    # which nobody studies: measured on the review games, 5 of 10 became a
    # London and 5 went elsewhere, so a family-wide London guide is right for
    # half the players and wrong for the other half. `for_opening` now honours
    # subline scope, so these reach only the players who actually get there.
    "Indian Defense: Accelerated London System": [
        ("London System: the complete guide",
         "https://thechessworld.com/articles/openings/london-system-the-complete-guide/",
         "TheChessWorld"),
        ("The London System: complete guide for club players",
         "https://www.firechess.com/blog/london-system-guide-club-players", "FireChess"),
    ],
    "English Opening": [
        ("The ideas behind the English Opening",
         "https://www.exeterchessclub.org.uk/content/ideas-behind-english-opening",
         "Exeter Chess Club"),
        ("English Opening - plans and structures",
         "https://www.albertochueca.com/blog/english-opening/", "IM Alberto Chueca"),
        ("English Opening: setups, key ideas and traps",
         "https://chessdoctrine.com/chess-openings/flank/english-opening/", "Chess Doctrine"),
    ],
    "Sicilian Defense": [
        ("The Alapin: playing the anti-Sicilian as White and Black",
         "https://www.chessable.com/blog/the-alapin-variation/", "Chessable"),
        ("Alapin Sicilian: c3 variation, plans and traps",
         "https://chessdoctrine.com/chess-openings/kings-pawn/sicilian-alapin/", "Chess Doctrine"),
        ("Sicilian Defense guide: main lines and traps",
         "https://chessdoctrine.com/chess-openings/kings-pawn/sicilian-defense/", "Chess Doctrine"),
    ],
    "Caro-Kann Defense": [
        ("Caro-Kann: lines, plans and ideas",
         "https://kingdomofchess.com/caro-kann-defense/", "Kingdom of Chess"),
        ("Complete guide with key lines for both colours",
         "https://www.attackingchess.com/caro-kann-defense-complete-guide-with-key-lines-for-both-white-and-black/",
         "Attacking Chess"),
        ("Caro-Kann prep guide for Black",
         "https://learn.openingdrills.com/black/semi-open/caro-kann-defense/", "OpeningDrills"),
    ],
    "Scandinavian Defense": [
        ("Scandinavian Defense - plans and piece placement",
         "https://www.albertochueca.com/blog/scandinavian-defense/", "IM Alberto Chueca"),
        ("Major ideas for White and Black",
         "https://chessforsharks.co/scandinavian-defense/", "Chess for Sharks"),
        ("Scandinavian Defense - ideas, plans and training",
         "https://freechesstrainer.org/openings/black/e4/scandinavian-defense.html",
         "FreeChessTrainer"),
    ],
    "Italian Game": [
        ("Playing the Italian Game like a pro (includes Giuoco Piano)",
         "https://www.chessable.com/blog/the-italian-game/", "Chessable"),
        ("The complete guide to chess's oldest opening",
         "https://chessiverse.com/blog/italian-game-the-complete-guide-to-chesss-oldest-opening",
         "Chessiverse"),
        ("Key middlegame ideas in the Italian Game (discussion)",
         "https://lichess.org/forum/general-chess-discussion/what-are-the-key-middlegame-ideas-in-the-italian-game",
         "Lichess forum"),
    ],
    "Pirc Defense": [
        ("Pirc Defense - ideas, plans and training",
         "https://freechesstrainer.org/openings/black/e4/pirc-defense.html", "FreeChessTrainer"),
        ("Take the fight to White with the Pirc",
         "https://www.uscfsales.com/blogs/chess-openings/the-pirc-defense-for-black",
         "US Chess Sales"),
        ("How to play the Pirc - plans and main lines",
         "https://ochess.app/openings/pirc-defense", "Ochess"),
    ],
    "Hungarian Opening": [
        ("King's Fianchetto Opening (1.g3): setup, plans and traps",
         "https://chessdoctrine.com/chess-openings/flank/kings-fianchetto/", "Chess Doctrine"),
        ("Surprise them with the King's Fianchetto Opening",
         "https://www.uscfsales.com/blogs/chess-openings/the-kings-fianchetto-opening",
         "US Chess Sales"),
        ("Hungarian Opening - a flexible chess opening",
         "https://www.mychesstutor.com/learn/hungarian-opening", "My Chess Tutor"),
    ],
    "Vienna Game": [
        ("Vienna Game: ideas, plans and main lines",
         "https://betterchess.co/openings/vienna-game", "BetterChess"),
        ("How to play the Vienna Game - complete guide",
         "https://chess.lc/blog/how-to-play-vienna-game", "Chess.lc"),
        ("All you need to know about the Vienna Game",
         "https://www.uscfsales.com/chess-blog/all-you-need-to-know-about-the-vienna-game/",
         "US Chess Sales"),
    ],
    "King's Pawn Game": [
        ("King's Pawn Game 1.e4: practical repertoire for White",
         "https://thechessworld.com/articles/openings/kings-pawn-game-1-e4-practical-repertoire-for-white/",
         "TheChessWorld"),
        ("King's Pawn Opening: the complete guide to mastering 1.e4",
         "https://kingdomofchess.com/kings-pawn-opening/", "Kingdom of Chess"),
        ("What to know before you use it",
         "https://www.uscfsales.com/blogs/chess-openings/kings-pawn-opening-what-to-know-before-you-use-it",
         "US Chess Sales"),
    ],
    "English Defense": [
        ("English Defense - aggressive opening for Black against 1.d4",
         "https://chess-teacher.com/english-defense/", "Chess-Teacher"),
        ("English Defence (reference)",
         "https://en.wikipedia.org/wiki/English_Defence", "Wikipedia"),
    ],
    "Owen Defense": [
        ("The offbeat Owen's: 1.e4 b6",
         "https://www.chessable.com/blog/owens-defense/", "Chessable"),
        ("Owen's Defense: complete guide",
         "https://thechessworld.com/articles/openings/owens-defense-complete-guide/",
         "TheChessWorld"),
        ("Owen's Defense",
         "https://oldschoolchess.com/learn/openings/owens-defense", "Old School Chess"),
    ],
    "Slav Defense": [
        ("Slav Defense: the complete guide",
         "https://thechessworld.com/articles/openings/slav-defense-the-complete-guide/",
         "TheChessWorld"),
        ("How to play the Slav: ideas and variations for both colours",
         "https://chessforsharks.co/slav-defense/", "Chess for Sharks"),
        ("Slav Defense guide: setup and strategies",
         "https://chessdoctrine.com/chess-openings/queens-pawn/slav-defense/", "Chess Doctrine"),
    ],

    # --- the tail: two to four games each, one search apiece ----------------
    "Philidor Defense": [
        ("Philidor Defense: complete guide",
         "https://thechessworld.com/articles/openings/philidor-defense-complete-guide/",
         "TheChessWorld"),
        ("Chess opening basics: the Philidor Defense",
         "https://www.chessable.com/blog/chess-opening-basics-the-philidor-defense/", "Chessable"),
        ("Philidor Defense explained: ideas, lines and tactics",
         "https://chessdoctrine.com/chess-openings/kings-pawn/philidor-defense/", "Chess Doctrine"),
    ],
    "Queen's Gambit Declined": [
        ("The QGD - how to play it as White and Black",
         "https://www.chessable.com/blog/queens-gambit-declined/", "Chessable"),
        ("Who is afraid of the big bad minority attack?",
         "https://www.exeterchessclub.org.uk/content/whos-afraid-big-bad-minority-attack",
         "Exeter Chess Club"),
        ("The minority attack - an essential weapon",
         "https://www.uscfsales.com/blogs/chess-middlegames/chess-minority-attack",
         "US Chess Sales"),
    ],
    "Dutch Defense": [
        ("Dutch Defense - Leningrad and Stonewall",
         "https://www.albertochueca.com/blog/dutch-defense-leningrad-stonewall/",
         "IM Alberto Chueca"),
        ("Dutch Defense guide: variations, ideas and counters",
         "https://chessdoctrine.com/chess-openings/queens-pawn/dutch-defense/", "Chess Doctrine"),
        ("The Dutch Defense: complete guide",
         "https://www.chesslab.academy/openings/dutch-defense/", "Chess Lab Academy"),
    ],
    "Benoni Defense": [
        ("Benoni Defense: complete guide",
         "https://thechessworld.com/articles/openings/the-benoni-defense-complete-guide/",
         "TheChessWorld"),
        ("Benoni Defense guide: strategy, traps and variations",
         "https://chessdoctrine.com/chess-openings/queens-pawn/benoni-defense/", "Chess Doctrine"),
        ("Master the Benoni Defense, Modern Variation",
         "https://www.uscfsales.com/blogs/chess-openings/the-benoni-defense-modern-variation",
         "US Chess Sales"),
    ],
    "Bird Opening": [
        ("How to play Bird's Opening",
         "https://www.chessable.com/blog/how-to-play-birds-opening/", "Chessable"),
        ("Bird's Opening (1.f4): lines, traps and how to counter it",
         "https://chessdoctrine.com/chess-openings/flank/birds-opening/", "Chess Doctrine"),
        ("Bird's Opening - prep guide for White",
         "https://learn.openingdrills.com/white/flank/bird-opening/", "OpeningDrills"),
    ],
    "Scotch Game": [
        ("The Scotch Game - a how-to-play guide for White and Black",
         "https://www.chessable.com/blog/the-scotch-game/", "Chessable"),
        ("Scotch Game for the busy player",
         "https://chessheritage.com/scotch-game-for-the-busy-player-learning-the-essential-5-minutes-of-theory/",
         "Chess Heritage"),
        ("Scotch Gambit guide: main lines, traps and key ideas",
         "https://chessdoctrine.com/chess-openings/kings-pawn/scotch-gambit/", "Chess Doctrine"),
    ],
    "Ruy Lopez": [
        ("The Ruy Lopez: complete guide for club players (1200-2000)",
         "https://chessatlas.net/blog/opening-guides/the-ruy-lopez-a-complete-guide-for-club-players-1200-2000-elo",
         "ChessAtlas"),
        ("Choose the right plan in the Ruy Lopez",
         "https://pawnbreak.com/choose-the-right-plan-in-the-ruy-lopez/", "Pawnbreak"),
        ("Ruy Lopez explained: ideas, plans and common mistakes",
         "https://www.rashadbabaev.com/ruy-lopez-opening-explained-ideas-plans-and-common-mistakes/",
         "Rashad Babaev"),
    ],
    "Petrov's Defense": [
        ("Petrov Defense: lines, traps and plans",
         "https://chessdoctrine.com/chess-openings/kings-pawn/petrov-defense/", "Chess Doctrine"),
        ("Petrov Defense: how to play it and how to counter it",
         "https://simplifychess.com/petrov-defense/index.html", "Simplify Chess"),
        ("Petrov Defense for beginners",
         "https://chessklub.com/chess-openings/petrov-defense/", "Chess Klub"),
    ],
    "Four Knights Game": [
        ("Four Knights Game: opening guide for White and Black",
         "https://www.chessable.com/blog/four-knights-game/", "Chessable"),
        ("Four Knights Game: complete guide",
         "https://thechessworld.com/articles/openings/four-knights-game-complete-guide/",
         "TheChessWorld"),
        ("Four Knights Game: traps and plans for both sides",
         "https://chessdoctrine.com/chess-openings/kings-pawn/four-knights-game/", "Chess Doctrine"),
    ],
    # Thin on dedicated guides - it is usually treated as a Four Knights
    # sideline, so the Four Knights material is the honest second link.
    "Three Knights Opening": [
        ("Three Knights Game (reference)",
         "https://en.wikipedia.org/wiki/Three_Knights_Game", "Wikipedia"),
        ("Four Knights system for White (the position this usually becomes)",
         "https://thechessworld.com/articles/openings/four-knights-system-for-white-complete-guide/",
         "TheChessWorld"),
    ],
    "Englund Gambit": [
        ("Exploring the Englund Gambit against 1.d4",
         "https://chess-teacher.com/englund-gambit/", "Chess-Teacher"),
        ("Englund Gambit: traps, best lines and how to counter it",
         "https://chessdoctrine.com/chess-openings/queens-pawn/englund-gambit/", "Chess Doctrine"),
        ("Englund Gambit - prep guide for Black",
         "https://learn.openingdrills.com/black/flank/englund-gambit/", "OpeningDrills"),
    ],
    "Nimzo-Indian Defense": [
        ("Nimzo-Indian: 10 reasons to play it, for club players",
         "https://thechessworld.com/articles/openings/nimzo-indian-defense-10-reasons-to-play-for-club-players/",
         "TheChessWorld"),
        ("Nimzo-Indian - ideas, plans and training",
         "https://freechesstrainer.org/openings/black/d4/nimzo-indian-defense.html",
         "FreeChessTrainer"),
        ("Nimzo-Indian: variations, plans and traps for Black",
         "https://chessdoctrine.com/chess-openings/queens-pawn/nimzo-indian-defense/",
         "Chess Doctrine"),
    ],
    "King's Indian Defense": [
        ("King's Indian: variations, plans and theory guide",
         "https://chessdoctrine.com/chess-openings/queens-pawn/kings-indian-defense/",
         "Chess Doctrine"),
        ("A comprehensive guide to the King's Indian Defense",
         "https://www.modern-chess.com/opening/kings-indian-defense/", "Modern Chess"),
        ("Crush them with the King's Indian Defense",
         "https://www.houseofstaunton.com/blogs/chess-openings/kings-indian-defense",
         "House of Staunton"),
    ],
    "Zukertort Opening": [
        ("Zukertort Opening: adviser, plans and model games",
         "https://www.chessworld.net/zukertort-opening.asp", "ChessWorld"),
        ("Zukertort Opening (A04)",
         "https://chessiverse.com/resources/openings/zukertort-opening", "Chessiverse"),
        ("Colle-Zukertort system: complete guide for White",
         "https://thechessworld.com/articles/openings/colle-zukertort-system-complete-guide-for-white/",
         "TheChessWorld"),
    ],
    "Van't Kruijs Opening": [
        ("Van't Kruijs Opening (1.e3): lines, counters and traps",
         "https://chessdoctrine.com/chess-openings/kings-pawn/vant-kruijs/", "Chess Doctrine"),
        ("Van't Kruijs Opening 1.e3",
         "https://masterinchess.com/vant-kruijs-opening", "Master in Chess"),
        ("Van't Kruijs Opening (A00)",
         "https://chessiverse.com/resources/openings/van-t-kruijs-opening", "Chessiverse"),
    ],
}

# The book names this as its own family, but it is a Vienna line and the Vienna
# material covers it. Aliased rather than searched again.
CANDIDATES["Vienna Gambit, with Max Lange Defense"] = CANDIDATES["Vienna Game"]
