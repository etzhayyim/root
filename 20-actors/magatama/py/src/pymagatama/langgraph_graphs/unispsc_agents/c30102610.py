from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BrassProcurementState(TypedDict):
    alloy_spec: str
    thickness_mm: float
    compliance_docs: List[str]
    validation_status: bool

def validate_specs(state: BrassProcurementState):
    valid = state['alloy_spec'] in ['C2600', 'C2680'] and state['thickness_mm'] > 0
    return {"validation_status": valid}

def check_compliance(state: BrassProcurementState):
    return {"validation_status": state['validation_status'] and 'RoHS' in state['compliance_docs']}

graph = StateGraph(BrassProcurementState)
graph.add_node("validate", validate_specs)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()
