from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_score: float

def validate_specs(state: ProcurementState):
    # Simulate CAD and material specification validation
    state['validated'] = 'material' in state['spec_data']
    state['compliance_score'] = 1.0 if state['validated'] else 0.0
    return state

def route(state: ProcurementState):
    return 'validate' if not state['validated'] else END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()