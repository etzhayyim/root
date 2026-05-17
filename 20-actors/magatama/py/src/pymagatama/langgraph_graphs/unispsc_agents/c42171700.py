from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    item_id: str
    specs: dict
    is_compliant: bool

def validate_medical_specs(state: ProcurementState):
    required = ['thermal_insulation_rating', 'flame_retardancy_standard', 'sterility_certification']
    state['is_compliant'] = all(k in state['specs'] for k in required)
    return state

def route_procurement(state: ProcurementState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(ProcurementState)
graph.add_node('validator', validate_medical_specs)
graph.add_edge('validator', END)
graph.set_entry_point('validator')
graph = graph.compile()