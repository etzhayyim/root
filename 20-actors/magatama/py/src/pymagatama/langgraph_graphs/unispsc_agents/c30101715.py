from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class BeamState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_load_capacity(state: BeamState):
    capacity = state['specifications'].get('load_capacity', 0)
    if capacity < 500:
        state['validation_errors'].append('Load capacity below safety threshold')
        state['is_compliant'] = False
    return state

def check_material_specs(state: BeamState):
    if 'material' not in state['specifications']:
        state['validation_errors'].append('Missing material composition data')
        state['is_compliant'] = False
    return state

graph = StateGraph(BeamState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('check_material', check_material_specs)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'check_material')
graph.add_edge('check_material', END)
graph = graph.compile()