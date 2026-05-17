from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HandrailState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_material(state: HandrailState):
    material = state['spec_data'].get('material')
    if not material: state['errors'].append('Material missing')
    return {'validation_passed': len(state['errors']) == 0}

def check_load_compliance(state: HandrailState):
    load = state['spec_data'].get('capacity', 0)
    if load < 500: state['errors'].append('Insufficient load capacity')
    return {'validation_passed': len(state['errors']) == 0}

graph = StateGraph(HandrailState)
graph.add_node('validate', validate_material)
graph.add_node('load_check', check_load_compliance)
graph.add_edge('validate', 'load_check')
graph.add_edge('load_check', END)
graph.set_entry_point('validate')
graph = graph.compile()