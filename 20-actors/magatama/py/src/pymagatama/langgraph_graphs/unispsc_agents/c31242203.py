from typing import TypedDict
from langgraph.graph import StateGraph, END

class DepolarizerState(TypedDict):
    spec_sheet: dict
    validation_results: dict
    needs_export_license: bool

def validate_specs(state: DepolarizerState):
    errors = []
    if state['spec_sheet'].get('Depolarization_Efficiency', 0) < 0.95:
        errors.append('Efficiency below threshold')
    return {'validation_results': {'errors': errors, 'valid': len(errors) == 0}}

def check_dual_use(state: DepolarizerState):
    # Logic for checking high-spec optics against export control thresholds
    is_controlled = state['spec_sheet'].get('Optical_Damage_Threshold', 0) > 10
    return {'needs_export_license': is_controlled}

graph = StateGraph(DepolarizerState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_dual_use)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()