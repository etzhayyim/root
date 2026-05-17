from typing import TypedDict
from langgraph.graph import StateGraph, END

class SONETState(TypedDict):
    specs: dict
    validation_errors: list
    status: str

def validate_specs(state: SONETState):
    required = ['transmission_rate', 'wavelength']
    errors = [f'missing {f}' for f in required if f not in state['specs']]
    return {'validation_errors': errors, 'status': 'valid' if not errors else 'invalid'}

def export_control_check(state: SONETState):
    # Simulate export license check logic
    return {'status': 'pending_license'}

graph = StateGraph(SONETState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()