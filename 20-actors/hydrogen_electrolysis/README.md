# hydrogen_electrolysis actor

Actor for comparing hydrogen electrolysis efficiency concepts.

Responsibilities:

- calls the Kami Engine simulation package at `40-engine/kami-engine/kami-hydrogen-electrolysis-sim`
- ranks low-temperature water electrolysis candidates
- emits report text and kotoba datom-style records

The actor does not control a physical electrolyzer. It is a deterministic design-comparison actor.

```bash
cd methods
python3 test_electrolysis.py
python3 analyze.py
```

Kotoba deploy dry-run:

```bash
cd kotoba
./deploy.sh
```
