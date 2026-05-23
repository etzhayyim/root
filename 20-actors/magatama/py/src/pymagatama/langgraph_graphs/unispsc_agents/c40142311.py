from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    spec: dict
    approved: bool

def validate_specs(state: PipeState):
    # Basic validation logic for pipe coupling pressure ratings
    rating = state['spec'].get('pressure_rating', 0)
    state['approved'] = rating > 0
    return state

def check_compliance(state: PipeState):
    # Industry standard compliance check
    return {'approved': state['approved'] and state['spec'].get('cert') == 'ASME'}

graph = StateGraph(PipeState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
