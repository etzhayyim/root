from typing import TypedDict
from langgraph.graph import StateGraph, END

class LightingState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: LightingState):
    required = ['IP_rating', 'voltage']
    valid = all(k in state['spec_data'] for k in required)
    return {'is_compliant': valid}

def check_compliance(state: LightingState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(LightingState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()