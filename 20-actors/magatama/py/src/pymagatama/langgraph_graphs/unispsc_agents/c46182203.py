from typing import TypedDict
from langgraph.graph import StateGraph, END

class BackSupportState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_ergonomic_specs(state: BackSupportState):
    # Business logic for validating ergonomic standards
    state['is_compliant'] = 'ergonomic_cert' in state['spec_data']
    return state

def route_by_compliance(state: BackSupportState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(BackSupportState)
graph.add_node('validate', validate_ergonomic_specs)
graph.add_node('process', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process', END)
graph = graph.compile()
