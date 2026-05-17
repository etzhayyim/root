from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    commodity_code: str
    purity_check: bool
    compliance_score: float
    steps: List[str]

def validate_purity(state: MineralState):
    # Simulate purity analysis logic
    is_pure = True 
    return {"purity_check": is_pure, "steps": state["steps"] + ["Purity Validated"]}

def check_compliance(state: MineralState):
    # Simulate regulatory compliance check
    return {"compliance_score": 0.95, "steps": state["steps"] + ["Compliance Checked"]}

graph = StateGraph(MineralState)
graph.add_node("validate_purity", validate_purity)
graph.add_node("check_compliance", check_compliance)
graph.set_entry_point("validate_purity")
graph.add_edge("validate_purity", "check_compliance")
graph.add_edge("check_compliance", END)
graph = graph.compile()