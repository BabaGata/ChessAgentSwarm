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
    "Indian Defense": [
        ("London System: the complete guide (the structure these games reach)",
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
}
