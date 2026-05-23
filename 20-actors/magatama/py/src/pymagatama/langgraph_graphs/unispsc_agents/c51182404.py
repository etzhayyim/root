from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class SupplyState(TypedDict):
    material_name: str
    quality_docs: List[str]
    approved: bool
def validate_coa(state: SupplyState):
    return {"approved": "COA" in state["quality_docs"]}
def route_step(state: SupplyState):
    return "approved" if state["approved"] else END
graph = StateGraph(SupplyState)
graph.add_node("validate", validate_coa)
graph.add_edge("validate", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()
