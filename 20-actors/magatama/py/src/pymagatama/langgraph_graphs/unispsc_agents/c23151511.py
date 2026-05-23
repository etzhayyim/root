from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeldingState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_specs(state: WeldingState):
    errors = []
    if not state['spec_data'].get('safety_cert'):
        errors.append('Missing mandatory safety certification')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: WeldingState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(WeldingState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: {'is_compliant': True})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process', END)
compiled_graph = graph.compile()
