from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DissectionTableState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_material(state: DissectionTableState):
    material = state['specs'].get('material', '').lower()
    if 'non-corrosive' not in material and 'stainless' not in material:
        state['validation_errors'].append('Material must be medical-grade stainless steel.')
    return state

def check_compliance(state: DissectionTableState):
    state['is_compliant'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(DissectionTableState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_compliance')
graph.add_edge('check_compliance', END)

graph = graph.compile()