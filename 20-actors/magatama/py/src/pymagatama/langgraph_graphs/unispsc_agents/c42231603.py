from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    tube_specs: dict
    compliance_check: bool

def validate_biocompatibility(state: ProcurementState):
    # Logic to verify ISO 10993 documentation
    state['compliance_check'] = 'material_iso10993' in state['tube_specs']
    return state

def check_dimensions(state: ProcurementState):
    # Validate French gauge sizing
    state['compliance_check'] = state['tube_specs'].get('french_size', 0) > 0
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_material', validate_biocompatibility)
graph.add_node('check_size', check_dimensions)
graph.add_edge('validate_material', 'check_size')
graph.add_edge('check_size', END)
graph.set_entry_point('validate_material')
