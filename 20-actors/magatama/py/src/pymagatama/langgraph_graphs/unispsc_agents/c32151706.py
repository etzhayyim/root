from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

class PLCState(TypedDict):
    part_number: str
    spec_check: bool
    compliance_validated: bool

def validate_specs(state: PLCState):
    print(f"Validating power requirements for {state['part_number']}")
    return {"spec_check": True}

def check_export_control(state: PLCState):
    print("Performing dual-use compliance check against ECCN standards")
    return {"compliance_validated": True}

graph = StateGraph(PLCState)
graph.add_node("validate", validate_specs)
graph.add_node("compliance", check_export_control)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()
