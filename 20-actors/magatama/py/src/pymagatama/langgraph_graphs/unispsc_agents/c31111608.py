from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ExtrusionState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_magnesium_spec(state: ExtrusionState):
    errors = []
    if not state['spec_data'].get('alloy_grade'): errors.append('Missing alloy grade')
    if state['spec_data'].get('thickness', 0) < 0.5: errors.append('Thickness below threshold')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def check_export_controls(state: ExtrusionState):
    # Dual-use logic placeholder
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(ExtrusionState)
graph.add_node('validate', validate_magnesium_spec)
graph.add_node('export_check', check_export_controls)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()