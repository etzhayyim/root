from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MSAUState(TypedDict):
    device_id: str
    spec_check: bool
    compliance_validated: bool

def validate_specs(state: MSAUState):
    print(f'Validating specs for {state["device_id"]}')
    return {"spec_check": True}

def check_compliance(state: MSAUState):
    print(f'Running regulatory compliance check for {state["device_id"]}')
    return {"compliance_validated": True}

graph = StateGraph(MSAUState)
graph.add_node("validate", validate_specs)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()
