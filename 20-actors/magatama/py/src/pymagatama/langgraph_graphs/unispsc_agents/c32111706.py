from typing import TypedDict
from langgraph.graph import StateGraph, END

class OscillatorState(TypedDict):
    specs: dict
    is_compliant: bool
    export_license_required: bool

def validate_specs(state: OscillatorState):
    s = state['specs']
    # Example validation for frequency stability
    compliant = s.get('frequency_stability_ppm', 100) <= 50
    return {'is_compliant': compliant}

def check_export_control(state: OscillatorState):
    # Dual-use logic: high frequency oscillators may require license
    requires = state['specs'].get('frequency_mhz', 0) > 1000
    return {'export_license_required': requires}

graph = StateGraph(OscillatorState)
graph.add_node('validate', validate_specs)
graph.add_node('export', check_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()