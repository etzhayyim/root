from typing import TypedDict
from langgraph.graph import StateGraph, END

class RocketState(TypedDict):
    specs: dict
    validated: bool
    export_compliant: bool

def validate_specs(state: RocketState) -> RocketState:
    required = ['thrust_rating_kn', 'propellant_type']
    state['validated'] = all(k in state['specs'] for k in required)
    return state

def check_compliance(state: RocketState) -> RocketState:
    state['export_compliant'] = state.get('validated', False) and 'certification_standard' in state['specs']
    return state

graph = StateGraph(RocketState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
