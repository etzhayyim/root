from typing import TypedDict
from langgraph.graph import StateGraph, END

class AlarmState(TypedDict):
    device_id: str
    spec_verified: bool
    compliance_check: bool

def validate_specs(state: AlarmState):
    print(f"Validating medical device specs for {state['device_id']}")
    return {"spec_verified": True}

def check_compliance(state: AlarmState):
    print(f"Running regulatory compliance check for medical alarm")
    return {"compliance_check": True}

graph = StateGraph(AlarmState)
graph.add_node("validate_specs", validate_specs)
graph.add_node("compliance_check", check_compliance)
graph.set_entry_point("validate_specs")
graph.add_edge("validate_specs", "compliance_check")
graph.add_edge("compliance_check", END)
compiled_graph = graph.compile()
