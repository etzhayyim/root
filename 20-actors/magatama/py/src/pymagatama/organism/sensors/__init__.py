"""pymagatama.organism.sensors — content / boundary scanners used by
religious-corp tooling (dataset substrate, kaizen, etc.).

Each sensor exposes a single `scan(...)` entry point that returns a
result dict. Sensors are read-only — they never mutate inputs and
never write to PDS. Callers (e7m-dataset, KaizenObserverCell, etc.)
decide what to do with the verdict.
"""
