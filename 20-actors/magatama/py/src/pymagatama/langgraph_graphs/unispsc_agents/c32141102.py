from typing import TypedDict
from langgraph.graph import StateGraph, END

class AnodeState(TypedDict):
    spec_content: str
    compliance_score: float
    is_approved: bool

def validate_specs(state: AnodeState) -> AnodeState:
    # Simulate CAD and material validation logic
    state['is_approved'] = len(state['spec_content']) > 20
    state['compliance_score'] = 1.0 if state['is_approved'] else 0.0
    return state

graph = StateGraph(AnodeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()