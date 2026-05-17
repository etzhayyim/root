from typing import TypedDict
from langgraph.graph import StateGraph, END

class VCDState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_vcd_specs(state: VCDState):
    required = ['capacitance_range', 'tuner_ratio', 'reverse_voltage_rating']
    errors = [f'Missing {f}' for f in required if f not in state['spec_data']]
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def export_control_check(state: VCDState):
    if state.get('tuner_ratio', 0) > 20:
        return {'validation_errors': state['validation_errors'] + ['High-ratio tuning restricted']}
    return state

graph = StateGraph(VCDState)
graph.add_node('validate', validate_vcd_specs)
graph.add_node('export_check', export_control_check)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()