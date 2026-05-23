from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftState(TypedDict):
    inspection_passed: bool
    compliance_docs: list
    next_step: str

def validate_specs(state: AircraftState):
    state['inspection_passed'] = len(state['compliance_docs']) > 3
    return {'next_step': 'approval' if state['inspection_passed'] else 'rejection'}

def approve_procurement(state: AircraftState):
    return {'next_step': 'finalized'}

workflow = StateGraph(AircraftState)
workflow.add_node("validate", validate_specs)
workflow.add_node("approve", approve_procurement)
workflow.set_entry_point("validate")
workflow.add_edge("validate", "approve")
workflow.add_edge("approve", END)
graph = workflow.compile()
