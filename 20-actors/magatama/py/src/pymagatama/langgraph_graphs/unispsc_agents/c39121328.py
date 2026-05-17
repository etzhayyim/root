from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    part_number: str
    fire_rating_specs: str
    compliance_docs: List[str]
    is_approved: bool

def validate_fire_rating(state: ProcurementState):
    # Simulate CAD/Spec validation logic
    state['is_approved'] = 'UL' in state['fire_rating_specs']
    return state

def route_by_approval(state: ProcurementState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_fire_rating)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()