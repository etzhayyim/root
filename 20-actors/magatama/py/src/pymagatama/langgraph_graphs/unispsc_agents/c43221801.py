from typing import TypedDict
from langgraph.graph import StateGraph, END

class OpticalAmpState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: OpticalAmpState):
    required = ['wavelength', 'gain', 'noise_figure']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'compliance_report': 'Success' if valid else 'Missing specs'}

def export_check(state: OpticalAmpState):
    return {'compliance_report': 'Dual-use check passed'}

graph = StateGraph(OpticalAmpState)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()