"""LangGraph orchestration (Module 9+).

state.py and checkpointer.py are established now, ahead of any node, so
every later agent module (10: Supervisor onward) builds against a fixed
state schema and a working persistence layer instead of each inventing
its own. graph_builder.py starts as an empty skeleton — nodes are added
incrementally as each owning module lands
(docs/architecture/14-testing-and-implementation-plan.md §14.3).
"""
