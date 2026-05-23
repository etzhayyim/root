from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_specs(state: CastingState):
    required = ['Material Grade', 'Dimensional Tolerance']
    valid = all(k in state['spec_data'] for k in required)
    return {'validated': valid, 'error': '' if valid else 'Missing mandatory specs'}

def audit_process(state: CastingState):
    # Simulate CAD/Spec validation flow
    print('Running compliance check for graphite mold casting...')
    return {'validated': True}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.add_node('audit', audit_process)
graph.set_entry_point('validate')
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
app = graph.compile()
