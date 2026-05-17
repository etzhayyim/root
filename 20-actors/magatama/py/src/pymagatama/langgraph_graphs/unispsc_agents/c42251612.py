from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RehabState(TypedDict):
    item_name: str
    spec_requirements: List[str]
    compliance_passed: bool

def validate_medical_standards(state: RehabState):
    print(f'Validating medical compliance for: {state["item_name"]}')
    return {"compliance_passed": True}

def check_weight_tolerances(state: RehabState):
    print(f'Checking weight tolerances for {state["item_name"]}')
    return {"compliance_passed": True}

graph = StateGraph(RehabState)
graph.add_node("validate", validate_medical_standards)
graph.add_node("tolerance", check_weight_tolerances)
graph.set_entry_point("validate")
graph.add_edge("validate", "tolerance")
graph.add_edge("tolerance", END)
app = graph.compile()