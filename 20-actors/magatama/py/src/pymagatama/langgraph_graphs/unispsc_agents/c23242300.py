from typing import TypedDict
from langgraph.graph import StateGraph, END

class LatheState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_lathe_specs(state: LatheState):
    errors = []
    if not state['spec_data'].get('safety_certification_ce_iso'):
        errors.append('Missing safety certification')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def check_dual_use(state: LatheState):
    # Simplified mock for high-performance lathe export control checks
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(LatheState)
graph.add_node('validate', validate_lathe_specs)
graph.add_node('export_check', check_dual_use)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()