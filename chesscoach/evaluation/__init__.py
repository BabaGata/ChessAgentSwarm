"""The evaluation harness.

Built before the first agent, deliberately: an evaluation harness written after
the agents is an evaluation harness shaped by the agents.

    splithalf  does a measurement survive being split across the player's games?
    planted    games whose weakness is known by construction
    scoring    did the agent find the planted flaw, and invent nothing else?

The design and the wider space of options are in docs/notes/evaluation.md.
"""
