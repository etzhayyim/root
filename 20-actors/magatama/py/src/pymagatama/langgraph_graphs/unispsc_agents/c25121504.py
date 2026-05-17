from typing import TypedDict
from langgraph.graph import StateGraph, END

class RailState(TypedDict):
    locomotive_spec: dict
    validation_results: dict
    is_compliant: bool

def validate_traction(state: RailState):
    spec = state['locomotive_spec']
    compliance = spec.get('tractive_effort_kn', 0) > 200
    return {'validation_results': {'traction': compliance}}

def check_compliance(state: RailState):
    is_valid = all(state['validation_results'].values())
    return {'is_compliant': is_valid}

graph = StateGraph(RailState)
graph.add_node('validate_traction', validate_traction)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_traction')
graph.add_edge('validate_traction', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()