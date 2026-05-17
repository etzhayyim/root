from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PCRState(TypedDict):
    sequence: str
    purity_validated: bool
    thermal_profile: dict
    approved: bool

def validate_sequence(state: PCRState):
    # Business logic for sequence validation
    if len(state['sequence']) > 15: 
        return {'purity_validated': True}
    return {'purity_validated': False}

def check_thermal_compliance(state: PCRState):
    # Logic to confirm Tm compatibility
    return {'approved': state['purity_validated']}

graph = StateGraph(PCRState)
graph.add_node("validate", validate_sequence)
graph.add_node("thermal", check_thermal_compliance)
graph.add_edge("validate", "thermal")
graph.add_edge("thermal", END)
graph.set_entry_point("validate")
graph = graph.compile()