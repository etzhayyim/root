from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AnimalProcurementState(TypedDict):
    animal_id: str
    quarantine_status: str
    health_checks: List[str]
    transport_approved: bool

def check_quarantine(state: AnimalProcurementState) -> AnimalProcurementState:
    state['quarantine_status'] = 'verified' if 'passed' in state['health_checks'] else 'pending'
    return state

def validate_transport(state: AnimalProcurementState) -> AnimalProcurementState:
    state['transport_approved'] = state['quarantine_status'] == 'verified'
    return state

graph = StateGraph(AnimalProcurementState)
graph.add_node('quarantine', check_quarantine)
graph.add_node('transport', validate_transport)
graph.add_edge('quarantine', 'transport')
graph.add_edge('transport', END)
graph.set_entry_point('quarantine')
graph = graph.compile()
