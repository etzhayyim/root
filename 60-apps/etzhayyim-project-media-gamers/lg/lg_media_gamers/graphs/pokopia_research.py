"""media-gamers `pokopia_research` graph — game knowledge research via Pregel provenance loop.

NSID: com.etzhayyim.apps.media_gamers.researchPokopia
Actor: did:web:media-gamers-research.etzhayyim.com

Nodes (7):
  plan_query → collect_sources → extract_claims → cross_check
  → [materialize | publish_lineage] → refresh_policy → END
"""

from kotodama.langgraph_graphs.pokopia_research_agent_loop import build_graph

GRAPH = build_graph()
