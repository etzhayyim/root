from typing import TypedDict
from langgraph.graph import StateGraph, END

class PorousBlockState(TypedDict):
    spec_data: dict
    validation_passed: bool
    approvals: list

def validate_porosity(state: PorousBlockState):
    pore_size = state['spec_data'].get('pore_size', 0)
    state['validation_passed'] = 1 <= pore_size <= 500
    return state

def check_material_safety(state: PorousBlockState):
    if state['validation_passed']:
        state['approvals'].append('Material Safety Verified')
    return state

graph = StateGraph(PorousBlockState)
graph.add_node('validate_porosity', validate_porosity)
graph.add_node('check_material', check_material_safety)
graph.set_entry_point('validate_porosity')
graph.add_edge('validate_porosity', 'check_material')
graph.add_edge('check_material', END)
graph = graph.compile()