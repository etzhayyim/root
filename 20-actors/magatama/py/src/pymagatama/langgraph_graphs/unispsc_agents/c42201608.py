from typing import TypedDict
from langgraph.graph import StateGraph, END

class MRIState(TypedDict):
    console_id: str
    compliance_checked: bool
    is_validated: bool

def validate_specs(state: MRIState):
    print(f'Validating specs for {state["console_id"]}')
    return {"compliance_checked": True}

def check_medical_reqs(state: MRIState):
    print(f'Checking HIPAA/DICOM for {state["console_id"]}')
    return {"is_validated": True}

graph = StateGraph(MRIState)
graph.add_node("validate", validate_specs)
graph.add_node("compliance", check_medical_reqs)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()