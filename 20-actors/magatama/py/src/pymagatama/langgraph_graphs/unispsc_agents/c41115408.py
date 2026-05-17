from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpectrometerState(TypedDict):
    spec_data: dict
    validation_passed: bool
    export_license_required: bool

def validate_specs(state: SpectrometerState):
    # Business logic for instrument range and calibration validation
    range_valid = state['spec_data'].get('spectral_range', 0) > 400
    return {'validation_passed': range_valid}

def check_compliance(state: SpectrometerState):
    # Dual-use regulatory check logic
    return {'export_license_required': True}

graph = StateGraph(SpectrometerState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()