from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SeatState(TypedDict):
    spec_data: dict
    approved: bool
    validation_errors: List[str]

def validate_load_capacity(state: SeatState) -> SeatState:
    load = state['spec_data'].get('load_capacity', 0)
    if load < 120:
        state['validation_errors'].append('Load capacity below industry standard of 120kg')
    return state

def check_compliance(state: SeatState) -> SeatState:
    cert = state['spec_data'].get('bifma_certified', False)
    state['approved'] = cert and len(state['validation_errors']) == 0
    return state

graph = StateGraph(SeatState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
