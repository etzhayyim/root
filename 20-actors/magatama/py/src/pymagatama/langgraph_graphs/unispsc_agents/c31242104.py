from typing import TypedDict
from langgraph.graph import StateGraph, END

class OpticalSpecs(TypedDict):
    material: str
    flatness: float
    needs_export_license: bool

def validate_specs(state: OpticalSpecs):
    if state['flatness'] > 0.05:
        return {'status': 'rejected', 'reason': 'Flatness too low'}
    return {'status': 'validated', 'reason': 'Specs within tolerance'}

def check_export_control(state: OpticalSpecs):
    state['needs_export_license'] = True
    return 'flagged'

graph = StateGraph(OpticalSpecs)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_control)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()