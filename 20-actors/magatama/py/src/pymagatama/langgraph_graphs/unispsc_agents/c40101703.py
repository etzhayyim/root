from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CoolerState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_cooling_capacity(state: CoolerState):
    if state['specs'].get('cooling_capacity', 0) <= 0:
        state['validation_errors'].append('Invalid cooling capacity')
    return state

def check_compliance(state: CoolerState):
    state['approved'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(CoolerState)
graph.add_node('validate', validate_cooling_capacity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
