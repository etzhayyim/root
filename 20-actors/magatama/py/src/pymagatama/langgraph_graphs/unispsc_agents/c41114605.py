from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class InspectionState(TypedDict):
    device_id: str
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: InspectionState):
    errors = []
    if 'calibration_standard' not in state['spec_data']:
        errors.append('Calibration standard missing')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def route_by_sensitivity(state: InspectionState):
    return 'process_high_sensitivity' if state['spec_data'].get('sensitivity_threshold', 0) > 0.9 else END

graph = StateGraph(InspectionState)
graph.add_node('validate', validate_specs)
graph.add_node('process_high_sensitivity', lambda x: {'is_approved': True})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_sensitivity)
graph.add_edge('process_high_sensitivity', END)
graph = graph.compile()
