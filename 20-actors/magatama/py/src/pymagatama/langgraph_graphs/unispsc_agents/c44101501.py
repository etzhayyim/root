from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PhotocopyState(TypedDict):
    model_id: str
    security_cleared: bool
    energy_compliant: bool
    specs: dict

def validate_specs(state: PhotocopyState):
    state['security_cleared'] = state['specs'].get('encryption', False)
    return state

def check_compliance(state: PhotocopyState):
    state['energy_compliant'] = state['specs'].get('energy_rating', 0) >= 5
    return state

graph = StateGraph(PhotocopyState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()