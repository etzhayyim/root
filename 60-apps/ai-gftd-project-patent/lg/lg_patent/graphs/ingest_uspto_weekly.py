"""patent `ingest_uspto_weekly` graph — re-export from pymagatama."""

from pymagatama.langgraph_graphs.patent_ingest_uspto_weekly import build_graph

GRAPH = build_graph()
