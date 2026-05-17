from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OfficeProcurementState(TypedDict):
    package_id: str
    components: List[str]
    compliance_checked: bool
    layout_approved: bool

def validate_components(state: OfficeProcurementState):
    return {"compliance_checked": all(c is not None for c in state["components"])}

def verify_layout(state: OfficeProcurementState):
    return {"layout_approved": len(state["components"]) > 0}

graph = StateGraph(OfficeProcurementState)
graph.add_node("validate", validate_components)
graph.add_node("verify", verify_layout)
graph.set_entry_point("validate")
graph.add_edge("validate", "verify")
graph.add_edge("verify", END)
app = graph.compile()