from typing import TypedDict
from langgraph.graph import StateGraph, END

class ParachuteState(TypedDict):
    serial_number: str
    inspection_status: bool
    is_compliant: bool

def validate_certification(state: ParachuteState):
    # Simulate stringent aerospace equipment compliance check
    print(f"Validating certifications for unit: {state['serial_number']}")
    state['is_compliant'] = True if state['inspection_status'] else False
    return state

def workflow_check(state: ParachuteState):
    return "compliant" if state['is_compliant'] else "non_compliant"

graph = StateGraph(ParachuteState)
graph.add_node("validate", validate_certification)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
