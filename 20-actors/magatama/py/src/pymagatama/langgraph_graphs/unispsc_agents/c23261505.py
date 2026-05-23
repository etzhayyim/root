from typing import TypedDict
from langgraph.graph import StateGraph, END

class SLSGraphState(TypedDict):
    spec_params: dict
    validation_results: dict
    status: str

def validate_specs(state: SLSGraphState):
    required = ['laser_power', 'build_volume']
    valid = all(k in state['spec_params'] for k in required)
    return {'validation_results': {'passed': valid}, 'status': 'validated' if valid else 'failed'}

def check_compliance(state: SLSGraphState):
    return {'status': 'compliance_checked'}

graph = StateGraph(SLSGraphState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
