from typing import TypedDict
from langgraph.graph import StateGraph, END

class SuspensionState(TypedDict):
    part_id: str
    specs: dict
    validated: bool
    compliance_score: float

def validate_specs(state: SuspensionState):
    # Simulate CAD and physical property validation
    state['validated'] = all(k in state['specs'] for k in ['load_rating', 'material'])
    return state

def check_compliance(state: SuspensionState):
    state['compliance_score'] = 1.0 if state['validated'] else 0.0
    return state

graph = StateGraph(SuspensionState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()