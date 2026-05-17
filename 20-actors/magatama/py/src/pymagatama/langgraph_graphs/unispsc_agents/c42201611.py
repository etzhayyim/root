from typing import TypedDict
from langgraph.graph import StateGraph, END

class MRIProcurementState(TypedDict):
    spec_data: dict
    approved: bool
    validation_log: list

def validate_material(state: MRIProcurementState):
    is_non_magnetic = state['spec_data'].get('is_non_magnetic', False)
    return {'approved': is_non_magnetic, 'validation_log': ['Material check passed' if is_non_magnetic else 'Material check failed']}

def check_compliance(state: MRIProcurementState):
    certs = state['spec_data'].get('certs', [])
    has_iso = 'ISO13485' in certs
    return {'approved': state['approved'] and has_iso, 'validation_log': state['validation_log'] + ['ISO 13485 check completed']}

graph = StateGraph(MRIProcurementState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_compliance')
graph.add_edge('check_compliance', END)
compiled_graph = graph.compile()