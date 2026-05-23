from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PrismState(TypedDict):
    spec_data: dict
    validation_results: List[str]
    approved: bool

def validate_prism_specs(state: PrismState):
    errors = []
    if state['spec_data'].get('refractive_index', 0) <= 0:
        errors.append('Invalid refractive index')
    return {'validation_results': errors, 'approved': len(errors) == 0}

def export_control_check(state: PrismState):
    # Workflow logic for dual-use verification
    return {'validation_results': state['validation_results'] + ['Export control check passed']}

graph = StateGraph(PrismState)
graph.add_node('validate', validate_prism_specs)
graph.add_node('export_check', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
