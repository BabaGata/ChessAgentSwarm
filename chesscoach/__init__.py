"""Chess Agent Swarm — an adaptive agent swarm that coaches chess players.

The design lives in the Dendron vault under `docs/notes/`, and is the authority
on why anything here is shaped the way it is:

    architecture                  the layers and the data flow
    architecture.player-profile   the artefact every agent reads and writes
    architecture.orchestration    how agents are combined (and why they never talk)
    architecture.confidence       when the swarm may assert something

Layers 1-5 (ingest, analysis, sections, profile, arbiter) are deterministic.
Only the prober, planner and explainer use a language model, and they read the
profile rather than the games.
"""

__version__ = "0.1.0"
