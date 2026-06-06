"""karakuri service_resolve (絡繰) cell — R0 coded reference cell.

Resolves a target service against the :representative capability/ToS registry, selects the safest
adapter tier (T1 > T2 browser-use > T3), and loads its two stance axes (official-API + browser-
automation). Unknown service degrades honestly to :unknown-service (G8). No network (G6). .solve()
raises until Council activation; the state_machine transitions are unit-tested.
"""
