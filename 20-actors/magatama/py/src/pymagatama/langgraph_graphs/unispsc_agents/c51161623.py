from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PharmaState(TypedDict):
    material_name: str
    quality_docs: List[str]
    compliance_cleared: bool

def validate_gmp(state: PharmaState):
    return {"compliance_cleared": "GMP_Certificate" in state['quality_docs']}

def route_procurement(state: PharmaState):
    return "ready" if state['compliance_cleared'] else "reject"

graph = StateGraph(PharmaState)
graph.add_node("validate", validate_gmp)
graph.add_node("ready", lambda s: {"status": "ready"})
graph.add_node("reject", lambda s: {"status": "reject"})
graph.set_entry_point("validate")
graph.add_edge("validate", "ready")
graph.add_edge("validate", "reject")
compiled_graph = graph.compile()
