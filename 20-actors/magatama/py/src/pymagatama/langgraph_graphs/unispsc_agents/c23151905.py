from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeldingGraphState(TypedDict):
    spec_data: dict
    is_verified: bool

def validate_specs(state: WeldingGraphState):
    required = ['input_voltage', 'safety_certification']
    verified = all(k in state['spec_data'] for k in required)
    return {'is_verified': verified}

def route_by_validation(state: WeldingGraphState):
    return 'process' if state['is_verified'] else 'end'

graph = StateGraph(WeldingGraphState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': 'process', 'end': END})
graph.add_node('process', lambda s: {'is_verified': True})
graph.add_edge('process', END)

graph = graph.compile()