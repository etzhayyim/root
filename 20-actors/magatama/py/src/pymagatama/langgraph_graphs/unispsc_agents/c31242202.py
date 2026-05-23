from typing import TypedDict
from langgraph.graph import StateGraph, END

class OpticalState(TypedDict):
    spec_data: dict
    is_validated: bool
    export_control_checks: list

def validate_optics(state: OpticalState):
    specs = state['spec_data']
    valid = all(key in specs for key in ['extinction_ratio', 'wavelength_range'])
    return {'is_validated': valid}

def export_check(state: OpticalState):
    checks = ['Dual-Use Review', 'ITAR Compliance']
    return {'export_control_checks': checks}

graph = StateGraph(OpticalState)
graph.add_node('validate', validate_optics)
graph.add_node('export', export_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()
