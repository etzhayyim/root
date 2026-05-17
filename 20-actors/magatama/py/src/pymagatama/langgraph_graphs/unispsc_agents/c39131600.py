from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class WireProtectionState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_material(state: WireProtectionState):
    material = state['spec_data'].get('material')
    if not material:
        state['validation_errors'].append('Missing material specification')
    return state

def check_compliance(state: WireProtectionState):
    state['is_compliant'] = (len(state['validation_errors']) == 0)
    return state

graph = StateGraph(WireProtectionState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()