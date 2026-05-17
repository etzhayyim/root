from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    safety_check: bool
    compliance_docs: List[str]

def validate_safety(state: ProcurementState):
    print(f"Validating safety standards for {state['item_name']}")
    return {"safety_check": True}

def check_documentation(state: ProcurementState):
    print("Verifying compliance documents...")
    return {"compliance_docs": ["ASTM_F963", "EN71"]}

graph = StateGraph(ProcurementState)
graph.add_node("safety", validate_safety)
graph.add_node("docs", check_documentation)
graph.set_entry_point("safety")
graph.add_edge("safety", "docs")
graph.add_edge("docs", END)
graph = graph.compile()